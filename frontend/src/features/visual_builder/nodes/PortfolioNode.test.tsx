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

describe('PortfolioNode', () => {
  const defaultData = {
    jobStatus: null,
    metrics: null,
    jobId: null,
    error: null,
  }

  it('renders "Run Backtest" button when no jobStatus', () => {
    render(
      <ReactFlowProvider>
        <PortfolioNode data={defaultData} id="test-id" type="portfolioNode" selected={false} zIndex={0} isConnectable={true} />
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
        <PortfolioNode data={dataWithMetrics} id="test-id" type="portfolioNode" selected={false} zIndex={0} isConnectable={true} />
      </ReactFlowProvider>
    )
    
    expect(screen.getByText(/15.50%/)).toBeInTheDocument()
    expect(screen.getByText(/1.80/)).toBeInTheDocument()
  })
})
