import {Handle, Position} from '@xyflow/react'
import type {PortfolioNodeData} from '../../../types/types'
import {useChatStore} from '../../../store/chatStore'

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
  const { jobStatus, metrics, error, jobId } = data
  const openChat = useChatStore(state => state.openChat)

  const isPending = jobStatus === 'PENDING'
  const isRunning = jobStatus === 'RUNNING'
  const isCompleted = jobStatus === 'COMPLETED'
  const isFailed = jobStatus === 'FAILED'

  return (
    <div className={`rf-node rf-node--portfolio ${isCompleted ? 'rf-node--completed' : ''} ${isFailed ? 'rf-node--failed' : ''}`}>
      <Handle 
        type="target" 
        position={Position.Left} 
        id="in" 
        className="easy-connect-handle"
      />
      <div className="rf-node__header react-flow__node-drag-handle">
        <div className="flex items-center gap-2">
          <span className="rf-node__icon text-xl">💼</span>
          <span className="rf-node__title font-semibold">Portfolio</span>
        </div>
        {jobStatus && (
          <span className={`rf-status-pill ${
            isPending ? 'rf-status-pill--pending' :
            isRunning ? 'rf-status-pill--running' :
            isCompleted ? 'rf-status-pill--completed' :
            'rf-status-pill--failed'
          }`}>
            {isPending && '⏳ Pending'}
            {isRunning && '⚙️ Running'}
            {isCompleted && '✅ Done'}
            {isFailed && '❌ Failed'}
          </span>
        )}
      </div>
      <div className="rf-node__body">
        {!jobStatus && (
          <p className="rf-hint rf-hint--center italic">Run backtest to see results</p>
        )}
        {(isPending || isRunning) && (
          <div className="rf-spinner-wrap flex flex-col items-center justify-center py-4">
            <div className="rf-spinner animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mb-2" />
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
              value={metrics.final_capital != null ? `$${Number(metrics.final_capital).toLocaleString('en-US', { maximumFractionDigits: 0 })}` : '—'}
            />
            <div className="rf-action-row mt-4 flex justify-center">
              <button
                onClick={() => {
                  if (jobId) openChat(jobId);
                }}
                title="Analyze via AI"
                className="w-full py-2 bg-blue-50 text-blue-600 border border-blue-200 rounded font-medium hover:bg-blue-100 transition-colors shadow-sm flex items-center justify-center gap-2"
                style={{ position: 'relative', zIndex: 10 }}
              >
                <span className="text-lg">✨</span> Analyze Results
              </button>
            </div>
          </div>
        )}
        {isFailed && (
          <p className="rf-hint rf-hint--error text-center mt-2">{error ?? 'Engine error'}</p>
        )}
      </div>
    </div>
  )
}
