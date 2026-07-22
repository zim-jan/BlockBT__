import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { DataNode } from './DataNode'
import { ReactFlowProvider } from '@xyflow/react'

const updateNodeData = vi.fn()
const setSelectedNodeId = vi.fn()
vi.mock('../../../store/workflowStore', () => ({
  useWorkflowStore: () => ({
    updateNodeData,
    selectedNodeId: null,
    setSelectedNodeId,
  }),
}))

function renderNode(data: Record<string, unknown>) {
  const props = { id: 'data-1', data } as unknown as Parameters<typeof DataNode>[0]
  return render(
    <ReactFlowProvider>
      <DataNode {...props} />
    </ReactFlowProvider>
  )
}

const baseData = {
  symbol: 'AAPL',
  dataSource: 'yahoo',
  startDate: '2023-01-01',
  endDate: '2025-01-01',
  timeframe: '1d',
}

describe('DataNode compact card', () => {
  it('renders symbol, date range, timeframe, and PIT badge', () => {
    renderNode(baseData)

    expect(screen.getByText('Data Source')).toBeInTheDocument()
    expect(screen.getByText('AAPL')).toBeInTheDocument()
    expect(screen.getByText(/2023-01-01 → 2025-01-01/)).toBeInTheDocument()
    expect(screen.getByText('1d')).toBeInTheDocument()
    expect(screen.getByText('PIT ON')).toBeInTheDocument()
  })
})
