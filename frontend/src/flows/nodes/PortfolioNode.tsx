import { Handle, Position } from 'reactflow'
import type { PortfolioNodeData } from '../../types'

interface Props {
  data: PortfolioNodeData
}

function MetricRow({ label, value, colorClass }: { label: string; value: string; colorClass?: string }) {
  return (
    <div className="rf-metric-row">
      <span className="rf-metric-label">{label}</span>
      <span className={`rf-metric-value ${colorClass ?? ''}`}>{value}</span>
    </div>
  )
}

function fmt(n: number | null | undefined, decimals = 2, suffix = ''): string {
  if (n == null) return '—'
  return `${n.toFixed(decimals)}${suffix}`
}

export function PortfolioNode({ data }: Props) {
  const { jobStatus, metrics, error } = data

  const isPending = jobStatus === 'PENDING'
  const isRunning = jobStatus === 'RUNNING'
  const isCompleted = jobStatus === 'COMPLETED'
  const isFailed = jobStatus === 'FAILED'

  return (
    <div className={`rf-node rf-node--portfolio ${isCompleted ? 'rf-node--completed' : ''} ${isFailed ? 'rf-node--failed' : ''}`}>
      <Handle type="target" position={Position.Left} id="in" />
      <div className="rf-node__header">
        <span className="rf-node__icon">💼</span>
        <span className="rf-node__title">Portfolio</span>
        {jobStatus && (
          <span className={`rf-status-pill rf-status-pill--${jobStatus.toLowerCase()}`}>
            {isPending && '⏳ Pending'}
            {isRunning && '⚙️ Running'}
            {isCompleted && '✅ Done'}
            {isFailed && '❌ Failed'}
          </span>
        )}
      </div>
      <div className="rf-node__body">
        {!jobStatus && (
          <p className="rf-hint rf-hint--center">Run backtest to see results</p>
        )}
        {(isPending || isRunning) && (
          <div className="rf-spinner-wrap">
            <div className="rf-spinner" />
            <p className="rf-hint">{isPending ? 'Queued...' : 'Executing vectorbt...'}</p>
          </div>
        )}
        {isCompleted && metrics && (
          <div className="rf-metrics">
            <MetricRow
              label="Total Return"
              value={fmt(metrics.total_return_pct, 2, '%')}
              colorClass={(metrics.total_return_pct ?? 0) >= 0 ? 'rf-metric-value--green' : 'rf-metric-value--red'}
            />
            <MetricRow
              label="Sharpe Ratio"
              value={fmt(metrics.sharpe_ratio)}
              colorClass={(metrics.sharpe_ratio ?? 0) >= 0 ? 'rf-metric-value--green' : 'rf-metric-value--red'}
            />
            <MetricRow
              label="Max Drawdown"
              value={fmt(metrics.max_drawdown_pct, 2, '%')}
              colorClass="rf-metric-value--amber"
            />
            <MetricRow label="Trades" value={String(metrics.num_trades ?? '—')} />
            <MetricRow
              label="Final Capital"
              value={metrics.final_capital != null ? `$${metrics.final_capital.toLocaleString('en-US', { maximumFractionDigits: 0 })}` : '—'}
            />
          </div>
        )}
        {isFailed && (
          <p className="rf-hint rf-hint--error">{error ?? 'Engine error'}</p>
        )}
      </div>
    </div>
  )
}
