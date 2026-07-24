import { Handle, type Node, type NodeProps, Position } from '@xyflow/react'
import type { SignalNodeData } from '../../../types/types'
import { CategoryBadge } from './CategoryBadge'
import { useWorkflowStore } from '../../../store/workflowStore'

export type SignalNode = Node<SignalNodeData, 'signalNode'>

export function SignalNode({ id, data, selected }: NodeProps<SignalNode>) {
  const { selectedNodeId, setSelectedNodeId } = useWorkflowStore()
  const isSelected = Boolean(selected || selectedNodeId === id)

  const labelMap: Record<string, string> = {
    sma_crossover: 'Crossover',
    ranking: 'Ticker Ranking',
    mapping: 'Threshold Mapping',
    distribution: 'Allocation Weighting',
  }

  return (
    <div
      onClick={(e) => {
        e.stopPropagation()
        console.log(`[CanvasNode] 🖱️ Clicked SignalNode: id=${id}`)
        setSelectedNodeId(id)
      }}
      className={`rf-node rf-node--signal bg-[#1c2130] border rounded-xl shadow-lg text-slate-100 p-3 min-w-[220px] cursor-pointer transition-all ${
        isSelected ? 'border-amber-400 ring-2 ring-amber-400/50 shadow-amber-500/20' : 'border-amber-500/30'
      }`}
    >
      <Handle type="target" position={Position.Left} style={{ zIndex: 10 }} />
      
      <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2 react-flow__node-drag-handle">
        <div className="flex items-center gap-2 font-semibold text-xs text-amber-400">
          <span>Signal Logic</span>
        </div>
        <CategoryBadge category="LogicOperators" />
      </div>

      <div className="space-y-1.5 font-mono text-xs">
        <div className="flex items-center justify-between bg-[#0b0d14] px-2 py-1 rounded border border-white/5">
          <span className="text-slate-400 text-[11px]">Logic Type:</span>
          <span className="font-bold text-amber-300 text-[11px]">
            {labelMap[data.signalType] || data.signalType || 'Crossover'}
          </span>
        </div>
      </div>

      <Handle 
        type="source" 
        position={Position.Right} 
        className="easy-connect-handle"
      />
    </div>
  )
}
