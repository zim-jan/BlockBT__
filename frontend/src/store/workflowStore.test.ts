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
