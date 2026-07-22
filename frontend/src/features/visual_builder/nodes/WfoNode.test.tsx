import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { WfoNode } from './WfoNode'
import { ReactFlowProvider } from '@xyflow/react'

const mockRunWfo = vi.fn()
vi.mock('../../../hooks/useWorkflowOptimization', () => ({
  useWorkflowOptimization: () => ({
    runWfo: mockRunWfo,
    isRunning: false,
  }),
}))

vi.mock('../../../store/workflowStore', () => ({
  useWorkflowStore: () => ({
    updateNodeData: vi.fn(),
    selectedNodeId: null,
    setSelectedNodeId: vi.fn(),
  }),
}))

const baseData = {
  windowSize: '365d',
  stepSize: '90d',
}

const completedResults = {
  overall_metrics: { 'Total Return [%]': 12.34 },
  n_windows: 3,
}

function renderNode(data: Record<string, unknown>) {
  const props = { id: 'wfo-1', data } as unknown as Parameters<typeof WfoNode>[0]
  return render(
    <ReactFlowProvider>
      <WfoNode {...props} />
    </ReactFlowProvider>
  )
}

describe('WfoNode compact card', () => {
  it('renders Run WFO button when idle', () => {
    renderNode(baseData)
    expect(screen.getByText(/Run WFO/i)).toBeInTheDocument()
  })

  it('renders overall OOS metrics when COMPLETED', () => {
    renderNode({ ...baseData, jobStatus: 'COMPLETED', results: completedResults })
    expect(screen.getByText(/12\.34/)).toBeInTheDocument()
  })

  it('renders error message when FAILED', () => {
    renderNode({ ...baseData, jobStatus: 'FAILED', error: 'boom' })
    expect(screen.getByText(/boom/)).toBeInTheDocument()
  })
})
