/**
 * Shared application types for BlockBT.
 * Mirrors the backend Pydantic schemas (dag.py).
 */

// ───────────────────────────────────────────────
// Phase 9: DAG Architecture Types
// ───────────────────────────────────────────────

/** The 5 architectural node categories (must match backend dag.py) */
export type NodeCategory =
  | 'DataIngestion'
  | 'Indicators'
  | 'LogicOperators'
  | 'Execution'
  | 'Meta'

/** Maps React Flow node type strings → backend DAG categories */
export const NODE_TYPE_CATEGORY_MAP: Record<string, NodeCategory> = {
  dataNode: 'DataIngestion',
  indicatorNode: 'Indicators',
  signalNode: 'LogicOperators',
  timeShiftNode: 'LogicOperators',
  portfolioNode: 'Execution',
  optimizerNode: 'Meta',
  wfoNode: 'Meta',
}

/** Single node in the exported DAG payload */
export interface DAGNode {
  id: string
  type: string
  category: NodeCategory
  position: { x: number; y: number }
  params: Record<string, unknown>
}

/** Edge in the exported DAG payload */
export interface DAGEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string | null
  targetHandle?: string | null
}

/** Meta node — references target_nodes by ID */
export interface DAGMetaNode extends DAGNode {
  category: 'Meta'
  target_nodes: string[]
}

/** Complete DAG graph payload sent to backend */
export interface DAGGraph {
  nodes: DAGNode[]
  edges: DAGEdge[]
  meta_nodes: DAGMetaNode[]
}

// ───────────────────────────────────────────────
// Core types
// ───────────────────────────────────────────────

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
export interface DataNodeData extends Record<string, unknown> {
  symbol: string
  dataSource: DataSourceType
  startDate: string
  endDate: string
  timeframe: string
}

export interface IndicatorNodeData extends Record<string, unknown> {
  indicatorType: IndicatorType
  smaFast: number
  smaSlow: number
  initialCapital: number
  macdFast?: number
  macdSlow?: number
  macdSignal?: number
  codeContent?: string
}

export interface SignalNodeData extends Record<string, unknown> {
  signalType: 'sma_crossover' | 'ranking' | 'mapping' | 'distribution'
}

export interface TimeShiftNodeData extends Record<string, unknown> {
  operator_type: 'time_shift'
  shift_periods: number
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

export interface OptimizerNodeData extends Record<string, unknown> {
  metric: string
  nTrials: number
  paramBounds: Record<string, ParameterBound>
  jobStatus?: JobStatus
  jobId?: number
  bestParameters?: Record<string, any>
  bestValue?: number
  trials?: OptunaTrial[]
  error?: string | null
  isOutdated?: boolean
}

export interface PortfolioNodeData extends Record<string, unknown> {
  init_cash?: number
  fees?: number
  slippage?: number
  jobStatus?: JobStatus
  metrics?: BacktestMetrics | null
  jobId?: number
  error?: string | null
  isOutdated?: boolean
}

export interface WfoNodeData extends Record<string, unknown> {
  windowSize: string
  stepSize: string
  jobStatus?: JobStatus
  jobId?: number
  results?: any
  error?: string | null
  isOutdated?: boolean
}
