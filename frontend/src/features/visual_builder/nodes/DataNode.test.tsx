import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { DataNode } from './DataNode'
import { ReactFlowProvider } from '@xyflow/react'

// Mock workflow store — selektor dostaje stub stanu ze współdzielonym updateNodeData
const updateNodeData = vi.fn()
vi.mock('../../../store/workflowStore', () => ({
  useWorkflowStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ updateNodeData }),
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

/** Parsuje symbol z wywołania updateNodeData na listę tickerów. */
function tickersFromLastCall(): string[] {
  const lastCall = updateNodeData.mock.calls.at(-1)
  expect(lastCall).toBeDefined()
  const payload = lastCall?.[1] as { symbol?: string }
  expect(typeof payload.symbol).toBe('string')
  return (payload.symbol as string).split(',').filter(Boolean)
}

beforeEach(() => {
  updateNodeData.mockClear()
})

describe('DataNode — źródło synthetic: liczba tickerów zamiast nazw', () => {
  it('shows a ticker-count spinbutton instead of the symbol text input', () => {
    renderNode({ ...baseData, dataSource: 'synthetic', symbol: 'SYNTA,SYNTB' })

    expect(screen.queryByDisplayValue('SYNTA,SYNTB')).toBeNull()
    expect(screen.getByText(/Number of tickers/i)).toBeInTheDocument()
    const countInput = screen.getByRole('spinbutton') as HTMLInputElement
    expect(countInput.value).toBe('2')
  })

  it('changing the count generates that many unique random tickers', () => {
    renderNode({ ...baseData, dataSource: 'synthetic', symbol: 'SYNTA' })

    const countInput = screen.getByRole('spinbutton')
    fireEvent.change(countInput, { target: { value: '4' } })

    const tickers = tickersFromLastCall()
    expect(tickers).toHaveLength(4)
    expect(new Set(tickers).size).toBe(4)
    for (const t of tickers) {
      expect(t).toMatch(/^[A-Z]{4}$/)
    }
  })

  it('switching source to synthetic regenerates random tickers (keeps count)', () => {
    renderNode({ ...baseData, dataSource: 'yahoo', symbol: 'AAPL,MSFT' })

    const sourceSelect = screen.getByDisplayValue('Yahoo Finance')
    fireEvent.change(sourceSelect, { target: { value: 'synthetic' } })

    const lastCall = updateNodeData.mock.calls.at(-1)
    expect(lastCall?.[1]).toMatchObject({ dataSource: 'synthetic' })
    const tickers = tickersFromLastCall()
    expect(tickers).toHaveLength(2)
    expect(tickers).not.toContain('AAPL')
  })

  it('shows the generated tickers as a read-only hint', () => {
    renderNode({ ...baseData, dataSource: 'synthetic', symbol: 'QWER,ZXCV' })

    expect(screen.getByText(/QWER, ZXCV/)).toBeInTheDocument()
  })

  it('date range inputs are visible for synthetic (generator spans start→end)', () => {
    renderNode({ ...baseData, dataSource: 'synthetic' })

    expect(screen.getByText(/Start Date/i)).toBeInTheDocument()
    expect(screen.getByText(/End Date/i)).toBeInTheDocument()
  })
})

describe('DataNode — źródła realne zachowują pole Symbol', () => {
  it('yahoo keeps the editable symbol input and no spinbutton', () => {
    renderNode({ ...baseData, dataSource: 'yahoo', symbol: 'AAPL,MSFT' })

    const symbolInput = screen.getByDisplayValue('AAPL,MSFT') as HTMLInputElement
    expect(symbolInput).not.toBeDisabled()
    expect(screen.queryByRole('spinbutton')).toBeNull()
    expect(screen.getByText(/Wiele tickerów/i)).toBeInTheDocument()
  })
})
