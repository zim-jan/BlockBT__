import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { OptimizerNode } from './OptimizerNode'
import { ReactFlowProvider } from '@xyflow/react'

// Audyt 2026-07-17: OptimizerNode nie renderował stanów FAILED/PENDING/RUNNING —
// nieudana optymalizacja wyglądała jak brak reakcji (błąd połknięty przez UI).

vi.mock('../../../hooks/useWorkflowOptimization', () => ({
  useWorkflowOptimization: () => ({
    runOptimization: vi.fn(),
    isRunning: false,
  }),
}))

// Store używany selektorami: updateNodeData / edges / nodes
const mockUpdateNodeData = vi.fn()
const storeState = { updateNodeData: mockUpdateNodeData, edges: [], nodes: [] }
vi.mock('../../../store/workflowStore', () => ({
  useWorkflowStore: (selector: (s: typeof storeState) => unknown) => selector(storeState),
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

describe('OptimizerNode', () => {
  it('renders Optimize button when idle', () => {
    renderNode(baseData)
    expect(screen.getByText('🚀 Optimize')).toBeInTheDocument()
  })

  it('renders the error message when FAILED', () => {
    renderNode({ ...baseData, jobStatus: 'FAILED', error: 'optymalizacja padła' })
    expect(screen.getByText(/optymalizacja padła/)).toBeInTheDocument()
  })

  it('renders a fallback error label when FAILED without message', () => {
    renderNode({ ...baseData, jobStatus: 'FAILED' })
    expect(screen.getByText(/Optimization failed/i)).toBeInTheDocument()
  })

  it('shows busy state and disables the button while RUNNING (node-level status)', () => {
    renderNode({ ...baseData, jobStatus: 'RUNNING' })
    const button = screen.getByText(/Optimizing/i).closest('button')
    expect(button).not.toBeNull()
    expect(button).toBeDisabled()
  })

  it('shows busy state while PENDING (node-level status)', () => {
    renderNode({ ...baseData, jobStatus: 'PENDING' })
    expect(screen.getByText(/Optimizing/i)).toBeInTheDocument()
  })

  it('still renders best parameters when COMPLETED (regresja)', () => {
    renderNode({
      ...baseData,
      jobStatus: 'COMPLETED',
      bestParameters: { sma_fast: 7 },
      bestValue: 4.56,
    })
    expect(screen.getByText(/Best Found/i)).toBeInTheDocument()
    expect(screen.getByText(/sma_fast/)).toBeInTheDocument()
  })
})
