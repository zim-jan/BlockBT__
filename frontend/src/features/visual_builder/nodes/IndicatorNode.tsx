import { Handle, type Node, type NodeProps, Position } from '@xyflow/react'
import type { IndicatorNodeData } from '../../../types/types'
import { CategoryBadge } from './CategoryBadge'
import { useWorkflowStore } from '../../../store/workflowStore'

export type IndicatorNode = Node<IndicatorNodeData, 'indicatorNode'>

export function IndicatorNode({ id, data, selected }: NodeProps<IndicatorNode>) {
  const { selectedNodeId, setSelectedNodeId } = useWorkflowStore()
  const isSelected = Boolean(selected || selectedNodeId === id)

  const isCustom = data.indicatorType === 'custom'
  const isMACD = data.indicatorType === 'macd'
  const isRSI = data.indicatorType === 'rsi'
  const isSMA = data.indicatorType === 'sma_crossover'

  return (
    <div
      onClick={(e) => {
        e.stopPropagation()
        console.log(`[CanvasNode] 🖱️ Clicked IndicatorNode: id=${id}`)
        setSelectedNodeId(id)
      }}
      className={`rf-node rf-node--indicator bg-[#1c2130] border rounded-xl shadow-lg text-slate-100 p-3 min-w-[220px] cursor-pointer transition-all ${
        isSelected ? 'border-purple-400 ring-2 ring-purple-400/50 shadow-purple-500/20' : 'border-purple-500/30'
      }`}
    >
      <Handle type="target" position={Position.Left} style={{ zIndex: 10 }} />
      
      <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2 react-flow__node-drag-handle">
        <div className="flex items-center gap-2 font-semibold text-xs text-purple-400">
          <span>Indicator</span>
        </div>
        <CategoryBadge category="Indicators" />
      </div>

      <div className="space-y-1.5 font-mono text-xs">
        {/* Indicator Type Header */}
        <div className="flex items-center justify-between bg-[#0b0d14] px-2 py-1 rounded border border-white/5">
          <span className="text-slate-400 text-[11px]">Indicator:</span>
          <span className="font-bold text-purple-300 capitalize text-[11px]">{data.indicatorType || 'SMA'}</span>
        </div>

        {/* SMA parameters */}
        {isSMA && (
          <div className="grid grid-cols-2 gap-1.5 text-[11px] bg-[#0b0d14] p-1.5 rounded border border-white/5">
            <div className="flex justify-between px-1">
              <span className="text-slate-400">Fast:</span>
              <span className="font-bold text-slate-100">{data.smaFast ?? 10}</span>
            </div>
            <div className="flex justify-between px-1">
              <span className="text-slate-400">Slow:</span>
              <span className="font-bold text-slate-100">{data.smaSlow ?? 30}</span>
            </div>
          </div>
        )}

        {/* MACD parameters */}
        {isMACD && (
          <div className="grid grid-cols-3 gap-1 text-[10px] bg-[#0b0d14] p-1.5 rounded border border-white/5 text-center">
            <div>
              <span className="block text-slate-400">Fast</span>
              <span className="font-bold text-purple-300">{data.macdFast ?? 12}</span>
            </div>
            <div>
              <span className="block text-slate-400">Slow</span>
              <span className="font-bold text-purple-300">{data.macdSlow ?? 26}</span>
            </div>
            <div>
              <span className="block text-slate-400">Signal</span>
              <span className="font-bold text-purple-300">{data.macdSignal ?? 9}</span>
            </div>
          </div>
        )}

        {/* RSI parameters */}
        {isRSI && (
          <div className="space-y-1 text-[11px] bg-[#0b0d14] p-1.5 rounded border border-white/5">
            <div className="flex justify-between">
              <span className="text-slate-400">Window:</span>
              <span className="font-bold text-slate-100">{String(data.rsiWindow ?? 14)}</span>
            </div>
            <div className="flex justify-between text-[10px]">
              <span className="text-slate-400">Limits:</span>
              <span className="text-purple-300 font-semibold">{String(data.rsiLower ?? 30)} / {String(data.rsiUpper ?? 70)}</span>
            </div>
          </div>
        )}

        {/* Custom Numba JIT badge */}
        {isCustom && (
          <div className="text-[11px] text-emerald-400 bg-emerald-950/40 p-1.5 rounded border border-emerald-500/30 text-center font-semibold">
            Numba JIT Sandbox Code
          </div>
        )}
      </div>

      <Handle 
        type="source" 
        position={Position.Right} 
        className="easy-connect-handle"
      />
    </div>
  )
}

export default IndicatorNode
