import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { IndicatorNode } from './IndicatorNode'
import { ReactFlowProvider } from '@xyflow/react'

// Mock workflow store — selektor zawsze zwraca updateNodeData
vi.mock('../../../store/workflowStore', () => ({
  useWorkflowStore: () => vi.fn(),
}))

// Mock API (IndicatorNode pobiera listę wskaźników z registry)
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

describe('IndicatorNode', () => {
  const baseData = { indicatorType: 'sma_crossover', smaFast: 10, smaSlow: 30 }

  it('renders SMA fields for sma_crossover', () => {
    renderNode(baseData)
    expect(screen.getByText(/Fast SMA/i)).toBeInTheDocument()
    expect(screen.getByText(/Slow SMA/i)).toBeInTheDocument()
  })

  it('does not render Initial Capital field — capital belongs to the Portfolio block (review 2026-07-16)', () => {
    renderNode(baseData)
    expect(screen.queryByText(/Initial Capital/i)).not.toBeInTheDocument()
  })
})
