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
})

