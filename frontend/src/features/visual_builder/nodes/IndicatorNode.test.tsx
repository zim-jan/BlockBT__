import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { IndicatorNode } from './IndicatorNode'
import { ReactFlowProvider } from '@xyflow/react'

vi.mock('../../../store/workflowStore', () => ({
  useWorkflowStore: () => ({
    updateNodeData: vi.fn(),
    selectedNodeId: null,
    setSelectedNodeId: vi.fn(),
  }),
}))

vi.mock('../../../services/api', () => ({
  api: {
    indicators: {
      list: vi.fn(async () => ({ success: true, data: [], error: null })),
    },
  },
}))

function renderNode(data: Record<string, unknown>) {
  const props = { id: 'ind-1', data } as unknown as Parameters<typeof IndicatorNode>[0]
  return render(
    <ReactFlowProvider>
      <IndicatorNode {...props} />
    </ReactFlowProvider>
  )
}

describe('IndicatorNode compact card', () => {
  const baseData = { indicatorType: 'sma_crossover', smaFast: 10, smaSlow: 30 }

  it('renders summary for sma_crossover', () => {
    renderNode(baseData)
    expect(screen.getAllByText('Indicator')[0]).toBeInTheDocument()
    expect(screen.getByText('Fast:')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('Slow:')).toBeInTheDocument()
    expect(screen.getByText('30')).toBeInTheDocument()
  })

  it('does not render Initial Capital field', () => {
    renderNode(baseData)
    expect(screen.queryByText(/Initial Capital/i)).not.toBeInTheDocument()
  })
})
