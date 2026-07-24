import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { OptimizerNode } from './OptimizerNode'
import { ReactFlowProvider } from '@xyflow/react'

vi.mock('../../../hooks/useWorkflowOptimization', () => ({
  useWorkflowOptimization: () => ({
    runOptimization: vi.fn(),
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
  metric: 'Total Return [%]',
  nTrials: 20,
  paramBounds: { sma_fast: { min: 5, max: 20, type: 'int' } },
}

function renderNode(data: Record<string, unknown>) {
  const props = { id: 'opt-1', data } as unknown as Parameters<typeof OptimizerNode>[0]
  return render(
    <ReactFlowProvider>
      <OptimizerNode {...props} />
    </ReactFlowProvider>
  )
}

describe('OptimizerNode compact card', () => {
  it('renders Run Optimization button when idle', () => {
    renderNode(baseData)
    expect(screen.getByText('Run Optimization')).toBeInTheDocument()
  })

  it('renders the error message when FAILED', () => {
    renderNode({ ...baseData, jobStatus: 'FAILED', error: 'optymalizacja padła' })
    expect(screen.getByText(/optymalizacja padła/)).toBeInTheDocument()
  })

  it('renders a fallback error label when FAILED without message', () => {
    renderNode({ ...baseData, jobStatus: 'FAILED' })
    expect(screen.getByText(/Optimization error/i)).toBeInTheDocument()
  })

  it('shows best score when COMPLETED', () => {
    renderNode({
      ...baseData,
      jobStatus: 'COMPLETED',
      bestValue: 4.56,
    })
    expect(screen.getByText('Best Score:')).toBeInTheDocument()
    expect(screen.getByText('4.56')).toBeInTheDocument()
  })
})
