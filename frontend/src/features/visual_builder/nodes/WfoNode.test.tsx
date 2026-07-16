import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { WfoNode } from './WfoNode'
import { ReactFlowProvider } from '@xyflow/react'

// Mock hooka optymalizacji (jak w PortfolioNode.test.tsx)
const mockRunWfo = vi.fn()
vi.mock('../../../hooks/useWorkflowOptimization', () => ({
  useWorkflowOptimization: () => ({
    runWfo: mockRunWfo,
    isRunning: false,
  }),
}))

// Mock workflow store — selektor zawsze zwraca updateNodeData
const mockUpdateNodeData = vi.fn()
vi.mock('../../../store/workflowStore', () => ({
  useWorkflowStore: () => mockUpdateNodeData,
}))

const baseData = {
  windowSize: '365d',
  stepSize: '90d',
}

const completedResults = {
  trials: [
    { window_index: 0, oos_metrics: { 'Total Return [%]': 1.1, 'Sharpe Ratio': 0.5 } },
    { window_index: 1, oos_metrics: { 'Total Return [%]': 2.2, 'Sharpe Ratio': 0.8 } },
    { window_index: 2, error: 'window exploded' },
  ],
  overall_metrics: { 'Total Return [%]': 12.34, 'Sharpe Ratio': 1.23 },
  n_windows: 3,
  n_failed_windows: 1,
  best_parameters: { sma_fast: 7, sma_slow: 30 },
  best_value: 4.56,
}

function renderNode(data: Record<string, unknown>) {
  // WfoNode przyjmuje pełne NodeProps — w teście wystarczą id + data
  const props = { id: 'wfo-1', data } as unknown as Parameters<typeof WfoNode>[0]
  return render(
    <ReactFlowProvider>
      <WfoNode {...props} />
    </ReactFlowProvider>
  )
}

describe('WfoNode', () => {
  it('renders Run WFO button when idle', () => {
    renderNode(baseData)
    expect(screen.getByText(/Run WFO/i)).toBeInTheDocument()
  })

  it('shows spinner and hides Run button while RUNNING', () => {
    renderNode({ ...baseData, jobStatus: 'RUNNING' })
    expect(screen.getByText(/Rolling/i)).toBeInTheDocument()
    expect(screen.queryByText(/Run WFO/i)).not.toBeInTheDocument()
  })

  it('renders overall OOS metrics, best params and per-window rows when COMPLETED', () => {
    renderNode({ ...baseData, jobStatus: 'COMPLETED', results: completedResults })

    // Metryki zbiorcze OOS
    expect(screen.getByText(/12\.34/)).toBeInTheDocument()
    expect(screen.getByText(/1\.23/)).toBeInTheDocument()

    // Najlepsze parametry (najlepsze okno OOS)
    expect(screen.getByText(/sma_fast/)).toBeInTheDocument()

    // Wiersze okien: udane pokazują zwrot OOS, nieudane marker błędu
    expect(screen.getByText(/1\.10/)).toBeInTheDocument()
    expect(screen.getByText(/2\.20/)).toBeInTheDocument()
    expect(screen.getByText(/window exploded/i)).toBeInTheDocument()

    // Licznik okien z awariami
    expect(screen.getByText(/3 windows \(1 failed\)/i)).toBeInTheDocument()
  })

  it('allows re-running WFO after COMPLETED', () => {
    renderNode({ ...baseData, jobStatus: 'COMPLETED', results: completedResults })
    expect(screen.getByText(/Run WFO/i)).toBeInTheDocument()
  })

  it('falls back gracefully when COMPLETED without results payload', () => {
    renderNode({ ...baseData, jobStatus: 'COMPLETED' })
    expect(screen.getByText(/WFO Complete/i)).toBeInTheDocument()
  })

  it('renders error message when FAILED', () => {
    renderNode({ ...baseData, jobStatus: 'FAILED', error: 'boom' })
    expect(screen.getByText(/boom/)).toBeInTheDocument()
  })
})
