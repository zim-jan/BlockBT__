import {Handle, Position} from '@xyflow/react'
import type {MetricValue, MultiBacktestResult, NormalizedMetrics, PortfolioNodeData} from '../../../types/types'
import {useChatStore} from '../../../store/chatStore'
import {useWorkflowStore} from '../../../store/workflowStore'
import {useWorkflowExecution} from '../../../hooks/useWorkflowExecution'
import Plot from '../../../components/PlotlyPlot'
import {CategoryBadge} from './CategoryBadge'

interface Props {
  id: string
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

/** Wspólna tabela metryk — reużywana zarówno dla single-symbol, jak i każdego symbolu w multi-symbol. */
function MetricTable({ metrics }: { metrics: NormalizedMetrics }) {
  return (
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
    </div>
  )
}

/** Normalizuje surowy słownik metryk z backendu (klucze typu "Total Return [%]") do NormalizedMetrics. */
function normalizeRawMetrics(raw: Record<string, MetricValue> | undefined): NormalizedMetrics {
  const num = (v: MetricValue | undefined): number | null => (typeof v === 'number' ? v : v == null ? null : Number(v))
  return {
    total_return_pct: num(raw?.['Total Return [%]']),
    sharpe_ratio: num(raw?.['Sharpe Ratio']),
    max_drawdown_pct: num(raw?.['Max Drawdown [%]']),
    num_trades: num(raw?.['Total Trades']),
    final_capital: num(raw?.['Final Value']),
  }
}

function isMultiResult(metrics: PortfolioNodeData['metrics']): metrics is MultiBacktestResult {
  return !!metrics && (metrics as MultiBacktestResult).is_multi_symbol === true
}

export function PortfolioNode({ id, data }: Props) {
  const { jobStatus, metrics, error, jobId } = data
  const openChat = useChatStore(state => state.openChat)
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)
  const { runBacktest, isRunning: isExecutionRunning } = useWorkflowExecution()

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
          <CategoryBadge category="Execution" />
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
        {/* Transaction Cost Controls — always visible */}
        <div className="rf-cost-controls" style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
          <div style={{ flex: 1 }}>
            <label className="rf-label" style={{ fontSize: '11px' }}>Fees (%)</label>
            <input
              type="number"
              min={0.0001}
              step={0.0001}
              value={data.fees ?? 0.001}
              onChange={(e) => updateNodeData(id, { fees: Math.max(0.0001, parseFloat(e.target.value) || 0.001) } as any)}
              className="rf-input"
              style={{ fontSize: '12px' }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label className="rf-label" style={{ fontSize: '11px' }}>Slippage (%)</label>
            <input
              type="number"
              min={0.0001}
              step={0.0001}
              value={data.slippage ?? 0.001}
              onChange={(e) => updateNodeData(id, { slippage: Math.max(0.0001, parseFloat(e.target.value) || 0.001) } as any)}
              className="rf-input"
              style={{ fontSize: '12px' }}
            />
          </div>
        </div>

        {/* Risk Controls — Stop Loss / Take Profit / Position Size (Faza 12) */}
        {/* UI pokazuje SL/TP w %, ale store i DAG JSON trzymają ułamek 0..1 (backend ExecutionParams.sl_stop/tp_stop) */}
        <div className="rf-risk-controls" style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
          <div style={{ flex: 1 }}>
            <label htmlFor={`${id}-sl`} className="rf-label" style={{ fontSize: '11px' }}>Stop Loss [%]</label>
            <input
              id={`${id}-sl`}
              type="number"
              min={0}
              max={100}
              step={0.1}
              placeholder="brak"
              value={data.sl_stop != null ? data.sl_stop * 100 : ''}
              onChange={(e) => {
                const raw = e.target.value
                if (raw === '') {
                  updateNodeData(id, { sl_stop: undefined } as any)
                  return
                }
                const pct = parseFloat(raw)
                if (!Number.isFinite(pct)) return
                const clamped = Math.min(100, Math.max(0, pct))
                updateNodeData(id, { sl_stop: clamped / 100 } as any)
              }}
              className="rf-input"
              style={{ fontSize: '12px' }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label htmlFor={`${id}-tp`} className="rf-label" style={{ fontSize: '11px' }}>Take Profit [%]</label>
            <input
              id={`${id}-tp`}
              type="number"
              min={0}
              max={100}
              step={0.1}
              placeholder="brak"
              value={data.tp_stop != null ? data.tp_stop * 100 : ''}
              onChange={(e) => {
                const raw = e.target.value
                if (raw === '') {
                  updateNodeData(id, { tp_stop: undefined } as any)
                  return
                }
                const pct = parseFloat(raw)
                if (!Number.isFinite(pct)) return
                const clamped = Math.min(100, Math.max(0, pct))
                updateNodeData(id, { tp_stop: clamped / 100 } as any)
              }}
              className="rf-input"
              style={{ fontSize: '12px' }}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label htmlFor={`${id}-size`} className="rf-label" style={{ fontSize: '11px' }}>Position Size</label>
            <input
              id={`${id}-size`}
              type="number"
              min={0.0001}
              step={0.01}
              placeholder="brak"
              value={data.size ?? ''}
              onChange={(e) => {
                const raw = e.target.value
                if (raw === '') {
                  updateNodeData(id, { size: undefined } as any)
                  return
                }
                const val = parseFloat(raw)
                if (!Number.isFinite(val) || val <= 0) return
                updateNodeData(id, { size: val } as any)
              }}
              className="rf-input"
              style={{ fontSize: '12px' }}
            />
            {/* size_type — backend interpretuje `size` zaleznie od tej jednostki (Faza 12) */}
            <select
              id={`${id}-size-type`}
              aria-label="Size unit"
              value={data.size_type ?? 'amount'}
              onChange={(e) => updateNodeData(id, { size_type: e.target.value as PortfolioNodeData['size_type'] } as any)}
              className="rf-input"
              style={{ fontSize: '11px', marginTop: '4px' }}
            >
              <option value="amount">amount</option>
              <option value="value">value</option>
              <option value="percent">percent</option>
            </select>
          </div>
        </div>

        {!jobStatus && (
          <div className="flex flex-col items-center gap-3 py-2">
            <p className="rf-hint rf-hint--center italic">Ready for analysis</p>
            <button
              onClick={runBacktest}
              disabled={isExecutionRunning}
              className="rf-btn rf-btn-primary w-full"
              style={{ position: 'relative', zIndex: 10 }}
            >
              {isExecutionRunning ? 'Running...' : 'Run Backtest'}
            </button>
          </div>
        )}
        {(isPending || isRunning) && (
          <div className="rf-spinner-wrap flex flex-col items-center justify-center py-4">
            <div className="rf-spinner animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mb-2" />
            <p className="rf-hint">{isPending ? 'Queued...' : 'Executing vectorbt...'}</p>
          </div>
        )}

        {/* SINGLE-symbol — niezmienione zachowanie */}
        {isCompleted && metrics && !isMultiResult(metrics) && (
          <div className="rf-metrics-wrap">
            <MetricTable metrics={metrics} />

            {metrics.equity_curve && metrics.equity_curve.length > 0 && (
              <div className="rf-chart mt-4 border rounded overflow-hidden bg-white" style={{ height: '150px' }}>
                <Plot
                  data={[
                    {
                      x: metrics.equity_curve.map(d => d.date),
                      y: metrics.equity_curve.map(d => d.value),
                      type: 'scatter',
                      mode: 'lines',
                      marker: { color: '#3b82f6' },
                      fill: 'tozeroy',
                      fillcolor: 'rgba(59, 130, 246, 0.1)',
                    },
                  ]}
                  layout={{
                    autosize: true,
                    margin: { l: 0, r: 0, b: 0, t: 0 },
                    xaxis: { visible: false },
                    yaxis: { visible: false },
                    showlegend: false,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                  }}
                  config={{ displayModeBar: false, responsive: true }}
                  style={{ width: '100%', height: '100%' }}
                  useResizeHandler
                />
              </div>
            )}

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

        {/* MULTI-symbol — akordeon metryk per symbol + jeden wykres equity z N seriami */}
        {isCompleted && metrics && isMultiResult(metrics) && (
          <div className="rf-metrics-wrap rf-metrics-wrap--multi">
            {(metrics.symbols ?? Object.keys(metrics.metrics ?? {})).map((symbol, idx) => (
              <details key={symbol} open={idx === 0} className="rf-metrics-accordion mb-2">
                <summary className="rf-metrics-accordion__summary font-medium cursor-pointer">{symbol}</summary>
                <MetricTable metrics={normalizeRawMetrics(metrics.metrics?.[symbol])} />
              </details>
            ))}

            {metrics.equity_curve && Object.keys(metrics.equity_curve).length > 0 && (
              <div className="rf-chart mt-4 border rounded overflow-hidden bg-white" style={{ height: '180px' }}>
                <Plot
                  data={Object.entries(metrics.equity_curve).map(([sym, points]) => ({
                    x: points.map((p) => p.date),
                    y: points.map((p) => p.value),
                    name: sym,
                    type: 'scatter' as const,
                    mode: 'lines' as const,
                  }))}
                  layout={{
                    autosize: true,
                    margin: { l: 0, r: 0, b: 0, t: 0 },
                    xaxis: { visible: false },
                    yaxis: { visible: false },
                    showlegend: true,
                    legend: { orientation: 'h', font: { size: 9 } },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                  }}
                  config={{ displayModeBar: false, responsive: true }}
                  style={{ width: '100%', height: '100%' }}
                  useResizeHandler
                />
              </div>
            )}

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
