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
vi.mock('../../../store/workflowStore', () => ({
  useWorkflowStore: () => vi.fn(),
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
})

