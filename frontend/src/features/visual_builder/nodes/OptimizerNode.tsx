import { Handle, type Node, type NodeProps, Position } from '@xyflow/react'
import { useWorkflowOptimization } from '../../../hooks/useWorkflowOptimization'
import type { OptimizerNodeData, ParameterBound } from '../../../types/types'
import { CategoryBadge } from './CategoryBadge'
import { useWorkflowStore } from '../../../store/workflowStore'

export type OptimizerNode = Node<OptimizerNodeData, 'optimizerNode'>

export function OptimizerNode({ id, data, selected }: NodeProps<OptimizerNode>) {
  const { selectedNodeId, setSelectedNodeId } = useWorkflowStore()
  const isSelected = Boolean(selected || selectedNodeId === id)

  const { runOptimization, isRunning } = useWorkflowOptimization()

  const isCompleted = data.jobStatus === 'COMPLETED'
  const isFailed = data.jobStatus === 'FAILED'

  const bounds = (data.paramBounds ?? {}) as Record<string, ParameterBound>
  const boundsSummary = Object.entries(bounds)
    .map(([k, b]) => `${k.replace('sma_', '')}: ${b.min}..${b.max}`)
    .join(', ')

  return (
    <div
      onClick={(e) => {
        e.stopPropagation()
        console.log(`[CanvasNode] 🖱️ Clicked OptimizerNode: id=${id}`)
        setSelectedNodeId(id)
      }}
      className={`rf-node rf-node--optimizer bg-[#1c2130] border rounded-xl shadow-lg text-slate-100 p-3 min-w-[220px] cursor-pointer transition-all ${
        isSelected ? 'border-pink-400 ring-2 ring-pink-400/50 shadow-pink-500/20' : isCompleted ? 'border-pink-500/60 shadow-pink-500/10' : 'border-pink-500/30'
      }`}
    >
      <Handle type="target" position={Position.Left} style={{ zIndex: 10 }} />

      <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2 react-flow__node-drag-handle">
        <div className="flex items-center gap-2 font-semibold text-xs text-pink-400">
          <span>Optimizer (Optuna)</span>
        </div>
        <CategoryBadge category="Meta" />
      </div>

      <div className="space-y-1.5 font-mono text-xs">
        {/* Metric */}
        <div className="flex items-center justify-between bg-[#0b0d14] px-2 py-1 rounded border border-white/5">
          <span className="text-slate-400 text-[11px]">Metryka:</span>
          <span className="font-bold text-pink-400 text-[11px] truncate max-w-[110px]">{data.metric || 'Total Return [%]'}</span>
        </div>

        {/* Trials */}
        <div className="flex items-center justify-between bg-[#0b0d14] px-2 py-1 rounded border border-white/5">
          <span className="text-slate-400 text-[11px]">Próby:</span>
          <span className="font-bold text-slate-100">{data.nTrials ?? 20} trials</span>
        </div>

        {/* Parameter bounds summary */}
        {boundsSummary && (
          <div className="bg-[#0b0d14] px-2 py-1 rounded border border-white/5 text-[10px] text-slate-300 truncate">
            <span className="text-pink-300 font-semibold">Zakresy: </span>
            <span>{boundsSummary}</span>
          </div>
        )}

        {isCompleted && data.bestValue != null && (
          <div className="flex items-center justify-between text-xs bg-pink-950/40 border border-pink-500/30 px-2 py-1 rounded">
            <span className="text-pink-300 font-medium">Best Score:</span>
            <span className="font-bold text-pink-400">{data.bestValue.toFixed(2)}</span>
          </div>
        )}

        {isFailed && (
          <div className="text-[11px] text-red-400 bg-red-950/30 p-1.5 rounded border border-red-500/20 text-center font-mono">
            {data.error || 'Błąd optymalizacji'}
          </div>
        )}

        <button
          onClick={(e) => {
            e.stopPropagation()
            runOptimization()
          }}
          disabled={isRunning}
          className="w-full py-1.5 mt-1 text-xs font-semibold bg-pink-600 hover:bg-pink-500 text-white rounded-lg transition-colors shadow-md disabled:opacity-50"
        >
          {isRunning ? 'Optymalizowanie...' : 'Run Optimization'}
        </button>
      </div>
    </div>
  )
}

export default OptimizerNode
