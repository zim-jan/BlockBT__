import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { DataNode } from './DataNode'
import { ReactFlowProvider } from '@xyflow/react'

// Mock workflow store — selektor zawsze zwraca updateNodeData
vi.mock('../../../store/workflowStore', () => ({
  useWorkflowStore: () => vi.fn(),
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

describe('DataNode — źródło synthetic (review 2026-07-16)', () => {
  it('symbol input is editable and multi-ticker hint visible for synthetic', () => {
    renderNode({ ...baseData, dataSource: 'synthetic', symbol: 'SYNTA,SYNTB' })

    const symbolInput = screen.getByDisplayValue('SYNTA,SYNTB') as HTMLInputElement
    expect(symbolInput).not.toBeDisabled()
    expect(screen.getByText(/Wiele tickerów/i)).toBeInTheDocument()
  })

  it('date range inputs are visible for synthetic (generator spans start→end)', () => {
    renderNode({ ...baseData, dataSource: 'synthetic' })

    expect(screen.getByText(/Start Date/i)).toBeInTheDocument()
    expect(screen.getByText(/End Date/i)).toBeInTheDocument()
  })
})
