/**
 * Shared application types for BlockBT Phase 3.
 * Mirrors the backend Pydantic schemas from api.d.ts.
 */

export type JobStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'

export type DataSourceType = 'yahoo' | 'alpaca' | 'synthetic'

export type IndicatorType = 'sma_crossover' | 'macd' | 'custom'

export interface BacktestMetrics {
  engine: string
  symbol: string
  data_source?: string
  strategy_type?: string
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
  code_content: string
  parameters: Record<string, unknown>
  created_at: string
}

// Custom node data shapes used by React Flow nodes
export interface DataNodeData {
  symbol: string
  dataSource: DataSourceType
  startDate: string
  endDate: string
  timeframe: string
}

export interface IndicatorNodeData {
  indicatorType: IndicatorType
  smaFast: number
  smaSlow: number
  initialCapital: number
  macdFast?: number
  macdSlow?: number
  macdSignal?: number
  codeContent?: string
}

export interface SignalNodeData {
  signalType: 'sma_crossover'
}

export interface ParameterBound {
  min: number
  max: number
  step?: number
  type: 'int' | 'float'
}

export interface OptunaTrial {
  number: number
  value: number | null
  params: Record<string, any>
  state: string
}

export interface OptimizerNodeData {
  metric: string
  nTrials: number
  paramBounds: Record<string, ParameterBound>
  jobStatus?: JobStatus
  jobId?: number
  bestParameters?: Record<string, any>
  bestValue?: number
  trials?: OptunaTrial[]
  error?: string | null
}

export interface PortfolioNodeData {
  jobStatus?: JobStatus
  metrics?: BacktestMetrics | null
  jobId?: number
  error?: string | null
}
