import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { PortfolioNode } from './PortfolioNode'
import { ReactFlowProvider } from '@xyflow/react'

// Mock the hook
const mockRunBacktest = vi.fn()
vi.mock('../../../hooks/useWorkflowExecution', () => ({
  useWorkflowExecution: () => ({
    runBacktest: mockRunBacktest,
    isRunning: false,
  }),
}))

// Mock chat store
vi.mock('../../../store/chatStore', () => ({
  useChatStore: () => vi.fn(),
}))

// Mock workflow store
const mockUpdateNodeData = vi.fn()
vi.mock('../../../store/workflowStore', () => ({
  useWorkflowStore: () => mockUpdateNodeData,
}))

describe('PortfolioNode', () => {
  const defaultData = {
    jobStatus: undefined,
    metrics: undefined,
    jobId: undefined,
    error: undefined,
  }

  it('renders "Run Backtest" button when no jobStatus', () => {
    render(
      <ReactFlowProvider>
        <PortfolioNode id="portfolio-1" data={defaultData} />
      </ReactFlowProvider>
    )
    
    expect(screen.getByText(/Ready for analysis/i)).toBeInTheDocument()
    const runBtn = screen.getByText(/Run Backtest/i)
    expect(runBtn).toBeInTheDocument()
    
    fireEvent.click(runBtn)
    expect(mockRunBacktest).toHaveBeenCalled()
  })

  it('renders metrics when status is COMPLETED', () => {
    const dataWithMetrics = {
      ...defaultData,
      jobStatus: 'COMPLETED' as const,
      metrics: {
        engine: 'vectorbt',
        symbol: 'AAPL',
        sma_fast: 10,
        sma_slow: 50,
        n_days: 252,
        initial_capital: 10000,
        win_rate_pct: 55,
        total_return_pct: 15.5,
        sharpe_ratio: 1.8,
        max_drawdown_pct: -5.2,
        num_trades: 10,
        final_capital: 11550,
        equity_curve: [],
      },
    }

    render(
      <ReactFlowProvider>
        <PortfolioNode id="portfolio-2" data={dataWithMetrics} />
      </ReactFlowProvider>
    )
    
    expect(screen.getByText(/15.50%/)).toBeInTheDocument()
    expect(screen.getByText(/1.80/)).toBeInTheDocument()
  })

  it('renders per-symbol accordions and a multi-trace chart for multi-symbol results', () => {
    const dataWithMultiMetrics = {
      ...defaultData,
      jobStatus: 'COMPLETED' as const,
      metrics: {
        is_multi_symbol: true,
        symbols: ['AAPL', 'MSFT'],
        metrics: {
          AAPL: {
            'Total Return [%]': 1.2,
            'Sharpe Ratio': 0.5,
            'Max Drawdown [%]': -3.0,
            'Total Trades': 4,
            'Final Value': 10120.0,
            'Win Rate [%]': 50.0,
          },
          MSFT: {
            'Total Return [%]': 2.4,
            'Sharpe Ratio': 0.8,
            'Max Drawdown [%]': -2.0,
            'Total Trades': 6,
            'Final Value': 10240.0,
            'Win Rate [%]': 60.0,
          },
        },
        equity_curve: {
          AAPL: [{ date: '2024-01-01', value: 10000.0 }, { date: '2024-01-02', value: 10120.0 }],
          MSFT: [{ date: '2024-01-01', value: 10000.0 }, { date: '2024-01-02', value: 10240.0 }],
        },
      },
    }

    render(
      <ReactFlowProvider>
        <PortfolioNode id="portfolio-3" data={dataWithMultiMetrics as any} />
      </ReactFlowProvider>
    )

    // Both symbol accordion sections rendered
    expect(screen.getByText('AAPL')).toBeInTheDocument()
    expect(screen.getByText('MSFT')).toBeInTheDocument()

    // AAPL metrics normalized and displayed (Total Return -> 1.20%)
    expect(screen.getByText(/1.20%/)).toBeInTheDocument()
  })

  it('renders SL/TP/Size risk fields and writes fraction values to store', () => {
    mockUpdateNodeData.mockClear()

    render(
      <ReactFlowProvider>
        <PortfolioNode id="portfolio-4" data={defaultData} />
      </ReactFlowProvider>
    )

    const slInput = screen.getByLabelText(/Stop Loss/i) as HTMLInputElement
    const tpInput = screen.getByLabelText(/Take Profit/i) as HTMLInputElement
    const sizeInput = screen.getByLabelText(/Position Size/i) as HTMLInputElement

    fireEvent.change(slInput, { target: { value: '5' } })
    expect(mockUpdateNodeData).toHaveBeenCalledWith('portfolio-4', { sl_stop: 0.05 })

    fireEvent.change(tpInput, { target: { value: '10' } })
    expect(mockUpdateNodeData).toHaveBeenCalledWith('portfolio-4', { tp_stop: 0.1 })

    fireEvent.change(sizeInput, { target: { value: '100' } })
    expect(mockUpdateNodeData).toHaveBeenCalledWith('portfolio-4', { size: 100 })
  })

  it('renders Initial Capital field and writes init_cash to store (review 2026-07-16)', () => {
    mockUpdateNodeData.mockClear()

    render(
      <ReactFlowProvider>
        <PortfolioNode id="portfolio-6" data={defaultData} />
      </ReactFlowProvider>
    )

    const capInput = screen.getByLabelText(/Initial Capital/i) as HTMLInputElement
    fireEvent.change(capInput, { target: { value: '5000' } })
    expect(mockUpdateNodeData).toHaveBeenCalledWith('portfolio-6', { init_cash: 5000 })
  })

  it('renders SL as percent from stored fraction', () => {
    render(
      <ReactFlowProvider>
        <PortfolioNode id="portfolio-5" data={{ ...defaultData, sl_stop: 0.075 }} />
      </ReactFlowProvider>
    )

    const slInput = screen.getByLabelText(/Stop Loss/i) as HTMLInputElement
    expect(slInput.value).toBe('7.5')
  })
})


// ADR-0009: sekcja analizy alokacji kapitału (timeline wag + summary per symbol)
describe('PortfolioNode — analiza alokacji (ADR-0009)', () => {
  const defaultData = { jobStatus: undefined, metrics: undefined, jobId: undefined, error: undefined }

  const singleAllocation = {
    timeline: {
      dates: ['2024-01-01', '2024-01-02'],
      weights: { AAPL: [0.0, 0.6], cash: [1.0, 0.4] },
    },
    summary: {
      AAPL: {
        avg_exposure_pct: 42.5,
        max_exposure_pct: 100.0,
        time_in_market_pct: 61.3,
        final_equity_share_pct: 100.0,
      },
    },
  }

  const singleMetrics = {
    engine: 'vectorbt',
    symbol: 'AAPL',
    total_return_pct: 15.5,
    sharpe_ratio: 1.8,
    max_drawdown_pct: -5.2,
    num_trades: 10,
    final_capital: 11550,
    equity_curve: [],
  }

  it('renders allocation summary for single-symbol results', () => {
    render(
      <ReactFlowProvider>
        <PortfolioNode
          id="portfolio-a1"
          data={{
            ...defaultData,
            jobStatus: 'COMPLETED' as const,
            metrics: { ...singleMetrics, allocation: singleAllocation } as any,
          }}
        />
      </ReactFlowProvider>
    )

    expect(screen.getByText(/Allocation/i)).toBeInTheDocument()
    expect(screen.getByText('42.5%')).toBeInTheDocument()
    expect(screen.getByText('61.3%')).toBeInTheDocument()
  })

  it('renders allocation rows per symbol for multi-symbol results', () => {
    const multiMetrics = {
      is_multi_symbol: true,
      symbols: ['ALFA', 'BETA'],
      metrics: {
        ALFA: { 'Total Return [%]': 1.0 },
        BETA: { 'Total Return [%]': 2.0 },
      },
      equity_curve: {},
      allocation: {
        timeline: {
          dates: ['2024-01-01'],
          weights: { ALFA: [0.3], BETA: [0.2], cash: [0.5] },
        },
        summary: {
          ALFA: {
            avg_exposure_pct: 33.3,
            max_exposure_pct: 90.0,
            time_in_market_pct: 44.4,
            final_equity_share_pct: 55.1,
          },
          BETA: {
            avg_exposure_pct: 22.2,
            max_exposure_pct: 80.0,
            time_in_market_pct: 66.6,
            final_equity_share_pct: 44.9,
          },
        },
      },
    }

    render(
      <ReactFlowProvider>
        <PortfolioNode id="portfolio-a2" data={{ ...defaultData, jobStatus: 'COMPLETED' as const, metrics: multiMetrics as any }} />
      </ReactFlowProvider>
    )

    expect(screen.getByText(/Allocation/i)).toBeInTheDocument()
    expect(screen.getByText('55.1%')).toBeInTheDocument()
    expect(screen.getByText('44.9%')).toBeInTheDocument()
  })

  it('omits the allocation section when the result has no allocation block', () => {
    render(
      <ReactFlowProvider>
        <PortfolioNode
          id="portfolio-a3"
          data={{ ...defaultData, jobStatus: 'COMPLETED' as const, metrics: singleMetrics as any }}
        />
      </ReactFlowProvider>
    )

    expect(screen.queryByText(/Allocation/i)).toBeNull()
  })
})


// Audyt 2026-07-17: wpisanie 0 w SL/TP wysyłało sl_stop/tp_stop = 0, a backend
// wymaga gt=0 → 422 z surowym komunikatem Pydantic. Zero = wyczyszczenie stopa.
describe('PortfolioNode — SL/TP zero (audyt 2026-07-17)', () => {
  const defaultData = { jobStatus: undefined, metrics: undefined, jobId: undefined, error: undefined }

  it('treats 0 in Stop Loss as clearing the stop (undefined), not sl_stop=0', () => {
    mockUpdateNodeData.mockClear()
    render(
      <ReactFlowProvider>
        <PortfolioNode id="portfolio-5" data={defaultData} />
      </ReactFlowProvider>
    )

    const slInput = screen.getByLabelText(/Stop Loss/i) as HTMLInputElement
    fireEvent.change(slInput, { target: { value: '0' } })

    expect(mockUpdateNodeData).toHaveBeenCalledWith('portfolio-5', { sl_stop: undefined })
  })

  it('treats 0 in Take Profit as clearing the stop (undefined), not tp_stop=0', () => {
    mockUpdateNodeData.mockClear()
    render(
      <ReactFlowProvider>
        <PortfolioNode id="portfolio-5" data={defaultData} />
      </ReactFlowProvider>
    )

    const tpInput = screen.getByLabelText(/Take Profit/i) as HTMLInputElement
    fireEvent.change(tpInput, { target: { value: '0' } })

    expect(mockUpdateNodeData).toHaveBeenCalledWith('portfolio-5', { tp_stop: undefined })
  })
})
