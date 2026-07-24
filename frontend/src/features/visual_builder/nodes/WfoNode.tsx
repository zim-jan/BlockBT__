import { Handle, type Node, type NodeProps, Position } from '@xyflow/react'
import { useWorkflowOptimization } from '../../../hooks/useWorkflowOptimization'
import type { WfoNodeData } from '../../../types/types'
import { CategoryBadge } from './CategoryBadge'
import { useWorkflowStore } from '../../../store/workflowStore'

export type WfoNode = Node<WfoNodeData, 'wfoNode'>

export function WfoNode({ id, data, selected }: NodeProps<WfoNode>) {
  const { selectedNodeId, setSelectedNodeId } = useWorkflowStore()
  const isSelected = Boolean(selected || selectedNodeId === id)

  const { runWfo, isRunning: isExecutionRunning } = useWorkflowOptimization()
  const { jobStatus, windowSize, stepSize, error, results } = data
  const mode = (data as any).mode ?? 'rolling'
  const metric = (data as any).metric ?? 'Total Return [%]'

  const isCompleted = jobStatus === 'COMPLETED'
  const isFailed = jobStatus === 'FAILED'

  return (
    <div
      onClick={(e) => {
        e.stopPropagation()
        console.log(`[CanvasNode] 🖱️ Clicked WfoNode: id=${id}`)
        setSelectedNodeId(id)
      }}
      className={`rf-node rf-node--optimizer bg-[#1c2130] border rounded-xl shadow-lg text-slate-100 p-3 min-w-[220px] cursor-pointer transition-all ${
        isSelected ? 'border-pink-400 ring-2 ring-pink-400/50 shadow-pink-500/20' : isCompleted ? 'border-pink-500/60 shadow-pink-500/10' : 'border-pink-500/30'
      }`}
    >
      <Handle type="target" position={Position.Left} style={{ zIndex: 10 }} />

      <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2 react-flow__node-drag-handle">
        <div className="flex items-center gap-2 font-semibold text-xs text-pink-400">
          <span>Walk-Forward</span>
        </div>
        <CategoryBadge category="Meta" />
      </div>

      <div className="space-y-1.5 font-mono text-xs">
        {/* Window & Step */}
        <div className="flex items-center justify-between bg-[#0b0d14] px-2 py-1 rounded border border-white/5">
          <span className="text-slate-400 text-[11px]">Window / Step:</span>
          <span className="font-bold text-slate-100">{windowSize || '365d'} / {stepSize || '90d'}</span>
        </div>

        {/* Mode & Metric */}
        <div className="flex items-center justify-between bg-[#0b0d14] px-2 py-1 rounded border border-white/5 text-[11px]">
          <span className="text-slate-400 capitalize">{mode}</span>
          <span className="text-pink-300 font-semibold truncate max-w-[100px]">{metric}</span>
        </div>

        {isCompleted && results?.overall_metrics && (
          <div className="flex items-center justify-between text-xs bg-pink-950/40 border border-pink-500/30 px-2 py-1 rounded">
            <span className="text-pink-300 font-medium">OOS Return:</span>
            <span className="font-bold text-emerald-400">{results.overall_metrics['Total Return [%]']?.toFixed(2)}%</span>
          </div>
        )}

        {isFailed && (
          <div className="text-[11px] text-red-400 bg-red-950/30 p-1.5 rounded border border-red-500/20 text-center font-mono">
            {error || 'WFO error'}
          </div>
        )}

        <button
          onClick={(e) => {
            e.stopPropagation()
            runWfo()
          }}
          disabled={isExecutionRunning}
          className="w-full py-1.5 mt-1 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors shadow-md disabled:opacity-50"
        >
          {isExecutionRunning ? 'Processing WFO...' : 'Run WFO'}
        </button>
      </div>

      <Handle type="source" position={Position.Right} className="easy-connect-handle" />
    </div>
  )
}

export default WfoNode
