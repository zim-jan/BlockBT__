import { Handle, type Node, type NodeProps, Position } from '@xyflow/react'
import { useWorkflowStore } from '../../../store/workflowStore'
import type { TimeShiftNodeData } from '../../../types/types'
import { CategoryBadge } from './CategoryBadge'

export type TimeShiftNode = Node<TimeShiftNodeData, 'timeShiftNode'>

export function TimeShiftNode({ id, data }: NodeProps<TimeShiftNode>) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)

  return (
    <div className="rf-node rf-node--timeshift">
      <Handle type="target" position={Position.Left} style={{ zIndex: 10 }} />
      <div className="rf-node__header react-flow__node-drag-handle">
        <span className="rf-node__icon">⏩</span>
        <span className="rf-node__title">Time Shift</span>
        <CategoryBadge category="LogicOperators" />
      </div>
      <div className="rf-node__body">
        <p className="rf-hint rf-hint--center" style={{ marginBottom: '8px', fontWeight: 600, color: '#f59e0b' }}>
          ⚠️ Look-ahead Bias Prevention
        </p>
        <label className="rf-label">fshift(n) — Shift Periods</label>
        <input
          type="number"
          min={1}
          max={10}
          value={data.shift_periods ?? 1}
          onChange={(e) =>
            updateNodeData(id as string, {
              shift_periods: Math.max(1, parseInt(e.target.value) || 1),
            } as any)
          }
          className="rf-input"
        />
        <p className="rf-hint" style={{ marginTop: '6px' }}>
          Shifts signal mask by <strong>{data.shift_periods ?? 1}</strong> period{(data.shift_periods ?? 1) > 1 ? 's' : ''} forward to prevent using future data for current decisions.
        </p>
      </div>
      <Handle
        type="source"
        position={Position.Right}
        className="easy-connect-handle"
      />
    </div>
  )
}
