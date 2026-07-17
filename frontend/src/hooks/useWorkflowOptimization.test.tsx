import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useWorkflowOptimization } from './useWorkflowOptimization'
import { useWorkflowStore } from '../store/workflowStore'
import type { Node, Edge } from '@xyflow/react'

// Mock klienta API — realny store, sztuczne odpowiedzi backendu
const mockStatus = vi.fn()
vi.mock('../services/api', () => ({
  api: {
    strategies: {
      create: vi.fn(async () => ({ success: true, data: { id: 1 }, error: null })),
    },
    optimizer: {
      trigger: vi.fn(async () => ({ success: true, data: { job_id: 5 }, error: null })),
      triggerWfo: vi.fn(async () => ({ success: true, data: { job_id: 7 }, error: null })),
      status: (jobId: number) => mockStatus(jobId),
    },
  },
}))

const POLL_MS = 2500

function seedWfoCanvas() {
  const nodes: Node[] = [
    {
      id: 'd1',
      type: 'dataNode',
      position: { x: 0, y: 0 },
      data: { symbol: 'AAPL', dataSource: 'yahoo', timeframe: '1d', startDate: '2023-01-01', endDate: '2024-01-01' },
    },
    {
      id: 'i1',
      type: 'indicatorNode',
      position: { x: 0, y: 0 },
      data: { indicatorType: 'sma_crossover', smaFast: 10, smaSlow: 30, initialCapital: 10000 },
    },
    {
      id: 'w1',
      type: 'wfoNode',
      position: { x: 0, y: 0 },
      data: { windowSize: '365d', stepSize: '90d' },
    },
    {
      id: 'p1',
      type: 'portfolioNode',
      position: { x: 0, y: 0 },
      data: { init_cash: 7500, fees: 0.001, slippage: 0.001 },
    },
  ]
  const edges: Edge[] = [
    { id: 'e1', source: 'd1', target: 'i1' },
    { id: 'e2', source: 'i1', target: 'w1' },
  ]
  useWorkflowStore.setState({
    nodes,
    edges,
    isRunning: false,
    activeJobId: null,
    jobStatus: null,
    errorMessage: null,
  })
}

const wfoNodeData = () =>
  useWorkflowStore.getState().nodes.find((n) => n.id === 'w1')?.data as Record<string, any>

function seedOptimizerCanvas(optimizerData: Record<string, unknown> = {}) {
  const nodes: Node[] = [
    {
      id: 'd1',
      type: 'dataNode',
      position: { x: 0, y: 0 },
      data: { symbol: 'AAPL', dataSource: 'yahoo', timeframe: '1d', startDate: '2023-01-01', endDate: '2024-01-01' },
    },
    {
      id: 'i1',
      type: 'indicatorNode',
      position: { x: 0, y: 0 },
      data: { indicatorType: 'sma_crossover', smaFast: 10, smaSlow: 30 },
    },
    {
      id: 'o1',
      type: 'optimizerNode',
      position: { x: 0, y: 0 },
      data: {
        metric: 'Total Return [%]',
        nTrials: 10,
        paramBounds: { sma_fast: { min: 5, max: 20, type: 'int' } },
        ...optimizerData,
      },
    },
  ]
  const edges: Edge[] = [
    { id: 'e1', source: 'd1', target: 'i1' },
    { id: 'e2', source: 'i1', target: 'o1' },
  ]
  useWorkflowStore.setState({
    nodes,
    edges,
    isRunning: false,
    activeJobId: null,
    jobStatus: null,
    errorMessage: null,
  })
}

const optimizerNodeData = () =>
  useWorkflowStore.getState().nodes.find((n) => n.id === 'o1')?.data as Record<string, any>

describe('useWorkflowOptimization — runWfo node-level feedback', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    seedWfoCanvas()
    mockStatus.mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('sets PENDING on the WFO node immediately after trigger', async () => {
    mockStatus.mockResolvedValue({ success: true, data: { status: 'RUNNING' }, error: null })
    const { result } = renderHook(() => useWorkflowOptimization())

    await act(async () => {
      await result.current.runWfo()
    })

    expect(wfoNodeData().jobStatus).toBe('PENDING')
  })

  it('propagates RUNNING to the WFO node while polling', async () => {
    mockStatus.mockResolvedValue({ success: true, data: { status: 'RUNNING' }, error: null })
    const { result } = renderHook(() => useWorkflowOptimization())

    await act(async () => {
      await result.current.runWfo()
    })
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_MS)
    })

    expect(wfoNodeData().jobStatus).toBe('RUNNING')
  })

  it('sends initial_capital read from the Portfolio node init_cash (review 2026-07-16)', async () => {
    mockStatus.mockResolvedValue({ success: true, data: { status: 'RUNNING' }, error: null })
    const { result } = renderHook(() => useWorkflowOptimization())

    await act(async () => {
      await result.current.runWfo()
    })

    const { api } = await import('../services/api')
    const wfoPayload = (api.optimizer.triggerWfo as ReturnType<typeof vi.fn>).mock.calls[0][0]
    expect(wfoPayload.initial_capital).toBe(7500)
  })

  it('stores composed results (trials_data + best_parameters/best_value) on COMPLETED', async () => {
    mockStatus.mockResolvedValue({
      success: true,
      data: {
        status: 'COMPLETED',
        best_parameters: { sma_fast: 7 },
        best_value: 4.56,
        trials_data: {
          trials: [{ window_index: 0, oos_metrics: { 'Total Return [%]': 1.1, 'Sharpe Ratio': 0.5 } }],
          overall_metrics: { 'Total Return [%]': 12.34, 'Sharpe Ratio': 1.23 },
          n_windows: 1,
          n_failed_windows: 0,
        },
      },
      error: null,
    })
    const { result } = renderHook(() => useWorkflowOptimization())

    await act(async () => {
      await result.current.runWfo()
    })
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_MS)
    })

    const data = wfoNodeData()
    expect(data.jobStatus).toBe('COMPLETED')
    expect(data.results.best_parameters).toEqual({ sma_fast: 7 })
    expect(data.results.best_value).toBe(4.56)
    expect(data.results.overall_metrics['Sharpe Ratio']).toBe(1.23)
    expect(data.results.trials).toHaveLength(1)
    expect(useWorkflowStore.getState().isRunning).toBe(false)
  })
})

// Audyt 2026-07-17: runOptimization (w odróżnieniu od runWfo) nie pisał
// statusu do node.data podczas biegu — OptimizerNode nie miał ŻADNEGO
// feedbacku poza COMPLETED (nieudana optymalizacja wyglądała jak brak reakcji).
describe('useWorkflowOptimization — runOptimization node-level feedback', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    mockStatus.mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('sets PENDING on the Optimizer node immediately after trigger and clears stale results', async () => {
    seedOptimizerCanvas({ jobStatus: 'COMPLETED', bestParameters: { sma_fast: 9 }, bestValue: 1.0 })
    mockStatus.mockResolvedValue({ success: true, data: { status: 'RUNNING' }, error: null })
    const { result } = renderHook(() => useWorkflowOptimization())

    await act(async () => {
      await result.current.runOptimization()
    })

    const data = optimizerNodeData()
    expect(data.jobStatus).toBe('PENDING')
    expect(data.bestParameters).toBeUndefined()
    expect(data.bestValue).toBeUndefined()
  })

  it('propagates RUNNING to the Optimizer node while polling', async () => {
    seedOptimizerCanvas()
    mockStatus.mockResolvedValue({ success: true, data: { status: 'RUNNING' }, error: null })
    const { result } = renderHook(() => useWorkflowOptimization())

    await act(async () => {
      await result.current.runOptimization()
    })
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_MS)
    })

    expect(optimizerNodeData().jobStatus).toBe('RUNNING')
  })

  it('writes FAILED and the error message to the node when the job fails', async () => {
    seedOptimizerCanvas()
    mockStatus.mockResolvedValue({
      success: true,
      data: { status: 'FAILED', error_message: 'kaboom' },
      error: null,
    })
    const { result } = renderHook(() => useWorkflowOptimization())

    await act(async () => {
      await result.current.runOptimization()
    })
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_MS)
    })

    const data = optimizerNodeData()
    expect(data.jobStatus).toBe('FAILED')
    expect(data.error).toBe('kaboom')
    expect(useWorkflowStore.getState().isRunning).toBe(false)
  })
})
