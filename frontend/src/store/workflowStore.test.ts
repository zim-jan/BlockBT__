import { describe, it, expect, beforeEach } from 'vitest'
import { useWorkflowStore } from './workflowStore'

describe('workflowStore', () => {
  beforeEach(() => {
    useWorkflowStore.getState().clearCanvas()
  })

  it('resets execution nodes when a dependency node is updated', () => {
    const store = useWorkflowStore.getState()
    
    // Add nodes
    store.addNode('dataNode')
    store.addNode('portfolioNode')
    
    const nodes = useWorkflowStore.getState().nodes
    const dataNode = nodes.find(n => n.type === 'dataNode')!
    const portfolioNode = nodes.find(n => n.type === 'portfolioNode')!
    
    // Set some execution data
    useWorkflowStore.getState().updateNodeData(portfolioNode.id, { 
      jobStatus: 'COMPLETED',
      metrics: { total_return_pct: 10 } as any,
      jobId: 123,
      error: null,
      isOutdated: false
    } as any)
    
    // Update data node (dependency)
    useWorkflowStore.getState().updateNodeData(dataNode.id, { symbol: 'TSLA' })
    
    const updatedNodes = useWorkflowStore.getState().nodes
    const updatedPortfolioNode = updatedNodes.find(n => n.id === portfolioNode.id)!
    
    expect(updatedPortfolioNode.data.jobStatus).toBeUndefined()
    expect(updatedPortfolioNode.data.metrics).toBeUndefined()
    expect(updatedPortfolioNode.data.jobId).toBeUndefined()
    expect(updatedPortfolioNode.data.error).toBeUndefined()
    expect(updatedPortfolioNode.data.isOutdated).toBeUndefined()
  })

  it('clears isOutdated when result arrives', () => {
    const store = useWorkflowStore.getState()
    
    store.addNode('portfolioNode')
    const portfolioNodeId = useWorkflowStore.getState().nodes[0].id
    
    // Manually set to outdated
    useWorkflowStore.getState().updateNodeData(portfolioNodeId, { isOutdated: true })
    expect(useWorkflowStore.getState().nodes[0].data.isOutdated).toBe(true)
    
    // Update result
    useWorkflowStore.getState().updatePortfolioResult({ 
        engine: 'vbt', symbol: 'AAPL', sma_fast: 10, sma_slow: 30, n_days: 100,
        total_return_pct: 10, sharpe_ratio: 1, max_drawdown_pct: 5, win_rate_pct: 50,
        num_trades: 10, initial_capital: 10000, final_capital: 11000
    }, 'COMPLETED', 123)
    
    expect(useWorkflowStore.getState().nodes[0].data.isOutdated).toBe(false)
  })

  it('resetExecution preserves portfolio config (fees/slippage/sl_stop/tp_stop/size) — regresja Fazy 12', () => {
    const store = useWorkflowStore.getState()
    store.addNode('portfolioNode')
    const portfolioNodeId = useWorkflowStore.getState().nodes[0].id

    // Konfiguracja ryzyka + wynik wykonania
    useWorkflowStore.getState().updateNodeData(portfolioNodeId, {
      sl_stop: 0.05, tp_stop: 0.1, size: 100, size_type: 'value',
      jobStatus: 'COMPLETED', metrics: { total_return_pct: 10 } as any, jobId: 7,
    } as any)

    useWorkflowStore.getState().resetExecution()

    const node = useWorkflowStore.getState().nodes.find(n => n.id === portfolioNodeId)!
    // Pola wykonania wyczyszczone
    expect(node.data.jobStatus).toBeUndefined()
    expect(node.data.metrics).toBeUndefined()
    // Konfiguracja PRZETRWAŁA reset
    expect(node.data.sl_stop).toBe(0.05)
    expect(node.data.tp_stop).toBe(0.1)
    expect(node.data.size).toBe(100)
    expect(node.data.size_type).toBe('value')
    expect(node.data.init_cash).toBe(10000)
    expect(node.data.fees).toBe(0.001)
  })

  // Review 2026-07-16: edycja JAKIEGOKOLWIEK pola w JAKIMKOLWIEK bloku czyści
  // błędy bloków; wyniki udanych przebiegów zostają (poza resetem zależności).
  describe('auto-czyszczenie błędów przy edycji pól', () => {
    it('clears own error and FAILED status when editing a failed portfolio node', () => {
      const store = useWorkflowStore.getState()
      store.addNode('portfolioNode')
      const portfolioId = useWorkflowStore.getState().nodes.find(n => n.type === 'portfolioNode')!.id

      useWorkflowStore.getState().updatePortfolioResult(null, 'FAILED', 1, 'boom')
      useWorkflowStore.getState().updateNodeData(portfolioId, { fees: 0.002 } as any)

      const portfolio = useWorkflowStore.getState().nodes.find(n => n.id === portfolioId)!
      expect(portfolio.data.error).toBeUndefined()
      expect(portfolio.data.jobStatus).toBeUndefined()
      expect(portfolio.data.fees).toBe(0.002)
    })

    it('clears own error when editing a failed optimizer node', () => {
      const store = useWorkflowStore.getState()
      store.addNode('optimizerNode')
      const optimizerId = useWorkflowStore.getState().nodes.find(n => n.type === 'optimizerNode')!.id

      useWorkflowStore.getState().updateOptimizerResult(null, null, null, 'FAILED', 1, 'boom')
      useWorkflowStore.getState().updateNodeData(optimizerId, { nTrials: 50 } as any)

      const optimizer = useWorkflowStore.getState().nodes.find(n => n.id === optimizerId)!
      expect(optimizer.data.error).toBeUndefined()
      expect(optimizer.data.jobStatus).toBeUndefined()
    })

    it('clears own error when editing a failed WFO node', () => {
      const store = useWorkflowStore.getState()
      store.addNode('wfoNode')
      const wfoId = useWorkflowStore.getState().nodes.find(n => n.type === 'wfoNode')!.id

      useWorkflowStore.getState().updateWfoResult(null, 'FAILED', 1, 'boom')
      useWorkflowStore.getState().updateNodeData(wfoId, { windowSize: '180d' } as any)

      const wfo = useWorkflowStore.getState().nodes.find(n => n.id === wfoId)!
      expect(wfo.data.error).toBeUndefined()
      expect(wfo.data.jobStatus).toBeUndefined()
      expect(wfo.data.windowSize).toBe('180d')
    })

    it('clears errors on OTHER blocks too (any edit anywhere clears all errors)', () => {
      const store = useWorkflowStore.getState()
      store.addNode('portfolioNode')
      store.addNode('wfoNode')
      const nodes = useWorkflowStore.getState().nodes
      const portfolioId = nodes.find(n => n.type === 'portfolioNode')!.id
      const wfoId = nodes.find(n => n.type === 'wfoNode')!.id

      useWorkflowStore.getState().updateWfoResult(null, 'FAILED', 1, 'boom')
      // Edycja pola w INNYM bloku (portfolio) musi zdjąć błąd z WFO
      useWorkflowStore.getState().updateNodeData(portfolioId, { fees: 0.002 } as any)

      const wfo = useWorkflowStore.getState().nodes.find(n => n.id === wfoId)!
      expect(wfo.data.error).toBeUndefined()
      expect(wfo.data.jobStatus).toBeUndefined()
    })

    it('clears indicator sandbox error on its own edit (przyszły writer Fazy 11)', () => {
      const store = useWorkflowStore.getState()
      store.addNode('indicatorNode')
      const indicatorId = useWorkflowStore.getState().nodes.find(n => n.type === 'indicatorNode')!.id

      useWorkflowStore.getState().updateNodeData(indicatorId, { error: 'sandbox error' } as any)
      useWorkflowStore.getState().updateNodeData(indicatorId, { smaFast: 15 } as any)

      const indicator = useWorkflowStore.getState().nodes.find(n => n.id === indicatorId)!
      expect(indicator.data.error).toBeUndefined()
      expect(indicator.data.smaFast).toBe(15)
    })

    it('keeps successful results when editing the execution node itself', () => {
      const store = useWorkflowStore.getState()
      store.addNode('portfolioNode')
      const portfolioId = useWorkflowStore.getState().nodes.find(n => n.type === 'portfolioNode')!.id

      useWorkflowStore.getState().updatePortfolioResult({ total_return_pct: 10 } as any, 'COMPLETED', 1)
      useWorkflowStore.getState().updateNodeData(portfolioId, { fees: 0.002 } as any)

      const portfolio = useWorkflowStore.getState().nodes.find(n => n.id === portfolioId)!
      expect(portfolio.data.jobStatus).toBe('COMPLETED')
      expect(portfolio.data.metrics).toEqual({ total_return_pct: 10 })
    })
  })

  // Audyt 2026-07-17: zmiana TOPOLOGII (connect/disconnect krawędzi) musi
  // invalidować wyniki i czyścić błędy tak samo jak edycja pól — przepięcie
  // grafu zostawiało stare metryki COMPLETED jako rzekomo aktualne.
  describe('inwalidacja przy zmianach krawędzi', () => {
    it('onConnect resets execution results and clears errors everywhere', () => {
      const store = useWorkflowStore.getState()
      store.addNode('dataNode')
      store.addNode('portfolioNode')
      store.addNode('wfoNode')
      const nodes = useWorkflowStore.getState().nodes
      const dataId = nodes.find(n => n.type === 'dataNode')!.id
      const portfolioId = nodes.find(n => n.type === 'portfolioNode')!.id
      const wfoId = nodes.find(n => n.type === 'wfoNode')!.id

      useWorkflowStore.getState().updatePortfolioResult({ total_return_pct: 10 } as any, 'COMPLETED', 1)
      useWorkflowStore.getState().updateWfoResult(null, 'FAILED', 2, 'boom')

      useWorkflowStore.getState().onConnect({
        source: dataId, target: portfolioId, sourceHandle: null, targetHandle: null,
      })

      const after = useWorkflowStore.getState().nodes
      const portfolio = after.find(n => n.id === portfolioId)!
      const wfo = after.find(n => n.id === wfoId)!
      expect(portfolio.data.jobStatus).toBeUndefined()
      expect(portfolio.data.metrics).toBeUndefined()
      expect(wfo.data.error).toBeUndefined()
      expect(wfo.data.jobStatus).toBeUndefined()
      // Krawędź faktycznie dodana
      expect(useWorkflowStore.getState().edges).toHaveLength(1)
    })

    it('onEdgesChange remove resets execution results', () => {
      const store = useWorkflowStore.getState()
      store.addNode('dataNode')
      store.addNode('portfolioNode')
      const nodes = useWorkflowStore.getState().nodes
      const dataId = nodes.find(n => n.type === 'dataNode')!.id
      const portfolioId = nodes.find(n => n.type === 'portfolioNode')!.id

      useWorkflowStore.getState().onConnect({
        source: dataId, target: portfolioId, sourceHandle: null, targetHandle: null,
      })
      const edgeId = useWorkflowStore.getState().edges[0].id
      useWorkflowStore.getState().updatePortfolioResult({ total_return_pct: 10 } as any, 'COMPLETED', 1)

      useWorkflowStore.getState().onEdgesChange([{ type: 'remove', id: edgeId }])

      const portfolio = useWorkflowStore.getState().nodes.find(n => n.id === portfolioId)!
      expect(portfolio.data.jobStatus).toBeUndefined()
      expect(portfolio.data.metrics).toBeUndefined()
      expect(useWorkflowStore.getState().edges).toHaveLength(0)
    })

    it('onEdgesChange select does NOT reset results', () => {
      const store = useWorkflowStore.getState()
      store.addNode('dataNode')
      store.addNode('portfolioNode')
      const nodes = useWorkflowStore.getState().nodes
      const dataId = nodes.find(n => n.type === 'dataNode')!.id
      const portfolioId = nodes.find(n => n.type === 'portfolioNode')!.id

      useWorkflowStore.getState().onConnect({
        source: dataId, target: portfolioId, sourceHandle: null, targetHandle: null,
      })
      const edgeId = useWorkflowStore.getState().edges[0].id
      useWorkflowStore.getState().updatePortfolioResult({ total_return_pct: 10 } as any, 'COMPLETED', 1)

      useWorkflowStore.getState().onEdgesChange([{ type: 'select', id: edgeId, selected: true }])

      const portfolio = useWorkflowStore.getState().nodes.find(n => n.id === portfolioId)!
      expect(portfolio.data.jobStatus).toBe('COMPLETED')
      expect(portfolio.data.metrics).toEqual({ total_return_pct: 10 })
    })

    it('konfiguracja bloków przeżywa inwalidację topologii', () => {
      const store = useWorkflowStore.getState()
      store.addNode('dataNode')
      store.addNode('portfolioNode')
      const nodes = useWorkflowStore.getState().nodes
      const dataId = nodes.find(n => n.type === 'dataNode')!.id
      const portfolioId = nodes.find(n => n.type === 'portfolioNode')!.id
      useWorkflowStore.getState().updateNodeData(portfolioId, { sl_stop: 0.05 } as any)

      useWorkflowStore.getState().onConnect({
        source: dataId, target: portfolioId, sourceHandle: null, targetHandle: null,
      })

      const portfolio = useWorkflowStore.getState().nodes.find(n => n.id === portfolioId)!
      expect(portfolio.data.sl_stop).toBe(0.05)
      expect(portfolio.data.init_cash).toBe(10000)
    })
  })

  // TimeShift usunięty (review 2026-07-16): silnik auto-shiftuje sygnały;
  // kaskadę inwalidacji pinujemy na signalNode (nadal węzeł zależności)
  it('updating signalNode invalidates downstream execution nodes', () => {
    const store = useWorkflowStore.getState()
    store.addNode('signalNode')
    store.addNode('portfolioNode')
    const nodes = useWorkflowStore.getState().nodes
    const signalId = nodes.find(n => n.type === 'signalNode')!.id
    const portfolioId = nodes.find(n => n.type === 'portfolioNode')!.id

    useWorkflowStore.getState().updateNodeData(portfolioId, {
      jobStatus: 'COMPLETED', metrics: { total_return_pct: 10 } as any, jobId: 5,
    } as any)

    useWorkflowStore.getState().updateNodeData(signalId, { signalType: 'ranking' } as any)

    const portfolio = useWorkflowStore.getState().nodes.find(n => n.id === portfolioId)!
    expect(portfolio.data.jobStatus).toBeUndefined()
    expect(portfolio.data.metrics).toBeUndefined()
  })

  it('exportDAG splits comma-separated symbol into an array (multi-symbol)', () => {
    const store = useWorkflowStore.getState()
    store.addNode('dataNode')
    const dataNodeId = useWorkflowStore.getState().nodes[0].id

    useWorkflowStore.getState().updateNodeData(dataNodeId, { symbol: 'AAPL, MSFT' })

    const dag = useWorkflowStore.getState().exportDAG()
    const dataDagNode = dag.nodes.find((n) => n.id === dataNodeId)!

    expect(dataDagNode.params.symbol).toEqual(['AAPL', 'MSFT'])
  })

  it('exportDAG keeps a single symbol as a plain string (single-symbol, unchanged)', () => {
    const store = useWorkflowStore.getState()
    store.addNode('dataNode')
    const dataNodeId = useWorkflowStore.getState().nodes[0].id

    useWorkflowStore.getState().updateNodeData(dataNodeId, { symbol: 'AAPL' })

    const dag = useWorkflowStore.getState().exportDAG()
    const dataDagNode = dag.nodes.find((n) => n.id === dataNodeId)!

    expect(dataDagNode.params.symbol).toBe('AAPL')
  })
})
