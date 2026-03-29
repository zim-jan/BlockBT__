/**
 * Shared application types for BlockBT Phase 3.
 * Mirrors the backend Pydantic schemas from api.d.ts.
 */

export type JobStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'

export interface BacktestMetrics {
  engine: string
  symbol: string
  sma_fast: number
  sma_slow: number
  n_days: number
  total_return_pct: number | null
  sharpe_ratio: number | null
  max_drawdown_pct: number | null
  win_rate_pct: number | null
  num_trades: number | null
  initial_capital: number
  final_capital: number | null
  equity_curve?: { date: string; value: number }[]
}

export interface BacktestJobData {
  job_id: number
  strategy_id: number
  status: JobStatus
  metrics: BacktestMetrics | null
  total_return_pct: number | null
  sharpe_ratio: number | null
  max_drawdown_pct: number | null
  num_trades: number | null
  final_capital: number | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface StrategyData {
  id: number
  name: string
  description: string
  parameters: Record<string, unknown>
  created_at: string
}

// Custom node data shapes used by React Flow nodes
export interface DataNodeData {
  symbol: string
}

export interface IndicatorNodeData {
  smaFast: number
  smaSlow: number
  initialCapital: number
}

export interface SignalNodeData {
  signalType: 'sma_crossover'
}

export interface PortfolioNodeData {
  jobStatus?: JobStatus
  metrics?: BacktestMetrics | null
  jobId?: number
  error?: string | null
}
