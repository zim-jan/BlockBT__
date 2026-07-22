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

export type IndicatorType = 'sma_crossover' | 'macd' | 'rsi' | 'custom' | string

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
  allocation?: AllocationAnalysis | null
}

// ───────────────────────────────────────────────
// ADR-0009: analiza alokacji kapitału po backteście
// ───────────────────────────────────────────────

/** Statystyki alokacji per symbol (wartości w %) */
export interface AllocationSummaryRow {
  avg_exposure_pct: number | null
  max_exposure_pct: number | null
  time_in_market_pct: number | null
  final_equity_share_pct: number | null
}

/** Timeline wag (ułamki 0..1: symbole + "cash") + summary per symbol */
export interface AllocationAnalysis {
  timeline: {
    dates: string[]
    weights: Record<string, number[]>
  }
  summary: Record<string, AllocationSummaryRow>
}

// ───────────────────────────────────────────────
// Faza 10: Multi-symbol backtest types
// ───────────────────────────────────────────────

/** Wartość pojedynczej metryki w surowym słowniku z backendu (np. "Total Return [%]") */
export type MetricValue = number | string | null

/** Punkt krzywej equity */
export interface EquityPoint {
  date: string
  value: number
}

/** Znormalizowany podzbiór metryk używany przez MetricTable (wspólny dla single i multi) */
export interface NormalizedMetrics {
  total_return_pct?: number | null
  sharpe_ratio?: number | null
  max_drawdown_pct?: number | null
  num_trades?: number | null
  final_capital?: number | null
}

/** Wynik backtestu dla wielu symboli jednocześnie (Faza 10 — broadcasting) */
export interface MultiBacktestResult {
  is_multi_symbol: true
  symbols: string[]
  metrics: Record<string, Record<string, MetricValue>>
  equity_curve: Record<string, EquityPoint[]>
  allocation?: AllocationAnalysis | null
}

export interface BacktestJobData {
  job_id: number
  strategy_id: number
  status: JobStatus
  metrics: BacktestMetrics | Record<string, Record<string, MetricValue>> | null
  total_return_pct: number | null
  sharpe_ratio: number | null
  max_drawdown_pct: number | null
  num_trades: number | null
  final_capital: number | null
  error_message: string | null
  created_at: string
  completed_at: string | null
  // Faza 10 (review): pola multi-symbol z backendu (GET /api/backtest/{id})
  is_multi_symbol?: boolean
  symbols?: string[]
  equity_curve?: EquityPoint[] | Record<string, EquityPoint[]>
  parameters?: Record<string, unknown>
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
  macdFast?: number
  macdSlow?: number
  macdSignal?: number
  codeContent?: string
  error?: string | null
}

export interface SignalNodeData extends Record<string, unknown> {
  signalType: 'sma_crossover' | 'ranking' | 'mapping' | 'distribution'
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
  /** Stop Loss jako ułamek 0..1 (backend ExecutionParams.sl_stop). UI pokazuje %, store trzyma ułamek. */
  sl_stop?: number
  /** Take Profit jako ułamek 0..1 (backend ExecutionParams.tp_stop). UI pokazuje %, store trzyma ułamek. */
  tp_stop?: number
  /** Rozmiar pozycji — interpretacja zależna od size_type (backend ExecutionParams.size). */
  size?: number
  size_type?: 'amount' | 'value' | 'percent'
  jobStatus?: JobStatus
  metrics?: BacktestMetrics | MultiBacktestResult | null
  jobId?: number
  error?: string | null
  isOutdated?: boolean
}

/** Raport pojedynczego okna WFO (backend: WalkForwardOptimizer._evaluate_window). */
export interface WfoWindowReport {
  window_index: number
  is_start?: string
  is_end?: string
  oos_start?: string
  oos_end?: string
  best_params?: Record<string, any>
  oos_metrics?: Record<string, number>
  /** Obecny tylko dla okien zakończonych awarią (fault tolerance per okno). */
  error?: string
}

/** Wyniki WFO składane w hooku: trials_data z GET /api/optimizer/{id} + best_parameters/best_value jobu. */
export interface WfoResults {
  trials?: WfoWindowReport[]
  overall_metrics?: Record<string, number>
  n_windows?: number
  n_failed_windows?: number
  mode?: string
  best_parameters?: Record<string, any> | null
  best_value?: number | null
}

export interface WfoNodeData extends Record<string, unknown> {
  windowSize: string
  stepSize: string
  jobStatus?: JobStatus
  jobId?: number
  results?: WfoResults | null
  error?: string | null
  isOutdated?: boolean
}
