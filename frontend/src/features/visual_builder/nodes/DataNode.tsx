import { Handle, type Node, type NodeProps, Position } from '@xyflow/react'
import type { DataNodeData } from '../../../types/types'
import { CategoryBadge } from './CategoryBadge'
import { useWorkflowStore } from '../../../store/workflowStore'

export type DataNode = Node<DataNodeData, 'dataNode'>

export function DataNode({ id, data, selected }: NodeProps<DataNode>) {
  const { selectedNodeId, setSelectedNodeId } = useWorkflowStore()
  const isSelected = Boolean(selected || selectedNodeId === id)

  const isSynthetic = data.dataSource === 'synthetic'
  const sourceLabel =
    data.dataSource === 'alpaca'
      ? 'Alpaca'
      : isSynthetic
        ? 'Synthetic'
        : 'Yahoo Finance'

  return (
    <div
      onClick={(e) => {
        e.stopPropagation()
        console.log(`[CanvasNode] 🖱️ Clicked DataNode: id=${id}`)
        setSelectedNodeId(id)
      }}
      className={`rf-node rf-node--data bg-[#1c2130] border rounded-xl shadow-lg text-slate-100 p-3 min-w-[220px] cursor-pointer transition-all ${
        isSelected ? 'border-blue-400 ring-2 ring-blue-400/50 shadow-blue-500/20' : 'border-blue-500/30'
      }`}
    >
      <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2 react-flow__node-drag-handle">
        <div className="flex items-center gap-2 font-semibold text-xs text-blue-400">
          <span>Data Source</span>
        </div>
        <CategoryBadge category="DataIngestion" />
      </div>

      <div className="space-y-1.5 font-mono text-xs">
        {/* Source & PIT Badge */}
        <div className="flex items-center justify-between bg-[#0b0d14] px-2 py-1 rounded border border-white/5">
          <span className="text-slate-400 text-[11px]">Źródło:</span>
          <span className="font-semibold text-blue-300 text-[11px]">{sourceLabel}</span>
        </div>

        {/* Symbol */}
        <div className="flex items-center justify-between bg-[#0b0d14] px-2 py-1 rounded border border-white/5">
          <span className="text-slate-400 text-[11px]">Symbol:</span>
          <span className="font-bold text-slate-100 truncate max-w-[120px]">{data.symbol || 'AAPL'}</span>
        </div>

        {/* Date range */}
        {!isSynthetic && (
          <div className="flex items-center justify-between text-[11px] text-slate-300 bg-[#0b0d14] px-2 py-1 rounded border border-white/5">
            <span className="text-slate-400">Okres:</span>
            <span>{data.startDate || '2023-01-01'} → {data.endDate || '2025-01-01'}</span>
          </div>
        )}

        {/* Timeframe & PIT status */}
        <div className="flex items-center justify-between text-[11px] bg-[#0b0d14] px-2 py-1 rounded border border-white/5">
          <span className="text-indigo-400 font-semibold uppercase">{data.timeframe || '1d'}</span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${data.point_in_time_enforcement !== false ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30' : 'bg-amber-950 text-amber-400 border border-amber-500/30'}`}>
            {data.point_in_time_enforcement !== false ? 'PIT ON' : 'PIT OFF'}
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

export default DataNode
