import { Handle, Position } from '@xyflow/react'
import type { PortfolioNodeData } from '../../../types/types'
import { useWorkflowExecution } from '../../../hooks/useWorkflowExecution'
import { CategoryBadge } from './CategoryBadge'
import { useWorkflowStore } from '../../../store/workflowStore'

export interface PortfolioNodeProps {
  id: string
  data: PortfolioNodeData
  selected?: boolean
}

export function PortfolioNode({ id, data, selected }: PortfolioNodeProps) {
  const { selectedNodeId, setSelectedNodeId } = useWorkflowStore()
  const isSelected = Boolean(selected || selectedNodeId === id)

  const { jobStatus, metrics, error } = data
  const { runBacktest, isRunning: isExecutionRunning, canRunBacktest } = useWorkflowExecution()

  const isPending = jobStatus === 'PENDING'
  const isRunning = jobStatus === 'RUNNING'
  const isCompleted = jobStatus === 'COMPLETED'
  const isFailed = jobStatus === 'FAILED'

  const totalReturn = metrics && 'total_return_pct' in metrics ? metrics.total_return_pct : null
  const feesPct = data.fees ? (data.fees * 100).toFixed(2) : '0.1'
  const slipPct = data.slippage ? (data.slippage * 100).toFixed(2) : '0.1'
  const slPct = data.sl_stop ? (data.sl_stop * 100).toFixed(1) : null
  const tpPct = data.tp_stop ? (data.tp_stop * 100).toFixed(1) : null

  return (
    <div
      onClick={(e) => {
        e.stopPropagation()
        console.log(`[CanvasNode] 🖱️ Clicked PortfolioNode: id=${id}`)
        setSelectedNodeId(id)
      }}
      className={`rf-node rf-node--portfolio bg-[#1c2130] border rounded-xl shadow-lg text-slate-100 p-3 min-w-[220px] cursor-pointer transition-all ${
        isSelected ? 'border-emerald-400 ring-2 ring-emerald-400/50 shadow-emerald-500/20' : isCompleted ? 'border-emerald-500/60 shadow-emerald-500/10' : 'border-emerald-500/30'
      }`}
    >
      <Handle
        type="target"
        position={Position.Left}
        id="in"
        className="easy-connect-handle"
      />
      <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2 react-flow__node-drag-handle">
        <div className="flex items-center gap-2 font-semibold text-xs text-emerald-400">
          <span>Portfolio</span>
        </div>
        <CategoryBadge category="Execution" />
      </div>

      <div className="space-y-1.5 font-mono text-xs">
        {/* Capital */}
        <div className="flex items-center justify-between bg-[#0b0d14] px-2 py-1 rounded border border-white/5">
          <span className="text-slate-400 text-[11px]">Capital:</span>
          <span className="font-bold text-slate-100">${(data.init_cash ?? 10000).toLocaleString()}</span>
        </div>

        {/* Fees & Slippage */}
        <div className="flex items-center justify-between bg-[#0b0d14] px-2 py-1 rounded border border-white/5 text-[11px]">
          <span className="text-slate-400">Costs:</span>
          <span className="text-emerald-300 font-semibold">{feesPct}% fees / {slipPct}% slip</span>
        </div>

        {/* SL / TP Badges if configured */}
        {(slPct || tpPct) && (
          <div className="flex items-center gap-1.5 text-[10px]">
            {slPct && (
              <span className="px-1.5 py-0.5 rounded bg-red-950/60 text-red-400 border border-red-500/30 font-semibold">
                SL: {slPct}%
              </span>
            )}
            {tpPct && (
              <span className="px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 font-semibold">
                TP: {tpPct}%
              </span>
            )}
          </div>
        )}

        {isCompleted && totalReturn != null && (
          <div className="flex items-center justify-between text-xs bg-emerald-950/40 border border-emerald-500/30 px-2 py-1 rounded">
            <span className="text-emerald-400 font-medium">Return:</span>
            <span className={`font-bold ${totalReturn >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(2)}%
            </span>
          </div>
        )}

        {(isPending || isRunning) && (
          <div className="flex items-center justify-center gap-2 text-xs text-blue-400 bg-blue-950/30 py-1 rounded border border-blue-500/20 animate-pulse font-mono">
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
            <span>{isPending ? 'Queued...' : 'Calculating...'}</span>
          </div>
        )}

        {isFailed && (
          <div className="text-[11px] text-red-400 bg-red-950/30 p-1.5 rounded border border-red-500/20 text-center font-mono">
            {error || 'Simulation error'}
          </div>
        )}

        {!jobStatus && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              runBacktest()
            }}
            disabled={isExecutionRunning || !canRunBacktest}
            title={!canRunBacktest ? 'Requires valid node connections and filled parameters' : ''}
            className="w-full py-1.5 mt-1 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isExecutionRunning ? 'Running...' : 'Run Backtest'}
          </button>
        )}
      </div>
    </div>
  )
}
