import {Handle, Position} from '@xyflow/react'
import {useWorkflowStore} from '../../store/workflowStore'
import type {IndicatorNodeData} from '../../types'

interface Props {
  id: string
  data: IndicatorNodeData
}

export function IndicatorNode({ id, data }: Props) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)

  const update = (field: keyof IndicatorNodeData, value: string) => {
    const num = parseFloat(value)
    if (!isNaN(num) && num > 0) updateNodeData(id, { [field]: num })
  }

  return (
    <div className="rf-node rf-node--indicator">
      <Handle type="target" position={Position.Left} id="in" />
      <div className="rf-node__header">
        <span className="rf-node__icon">📈</span>
        <span className="rf-node__title">SMA Indicator</span>
      </div>
      <div className="rf-node__body">
        <div className="rf-field-row">
          <div className="rf-field">
            <label className="rf-label">Fast SMA</label>
            <input
              id={`${id}-fast`}
              className="rf-input rf-input--number"
              type="number"
              min={1}
              max={200}
              value={data.smaFast}
              onChange={(e) => update('smaFast', e.target.value)}
            />
          </div>
          <div className="rf-field">
            <label className="rf-label">Slow SMA</label>
            <input
              id={`${id}-slow`}
              className="rf-input rf-input--number"
              type="number"
              min={1}
              max={500}
              value={data.smaSlow}
              onChange={(e) => update('smaSlow', e.target.value)}
            />
          </div>
        </div>
        <label className="rf-label">Initial Capital ($)</label>
        <input
          id={`${id}-capital`}
          className="rf-input rf-input--number"
          type="number"
          min={100}
          step={1000}
          value={data.initialCapital}
          onChange={(e) => update('initialCapital', e.target.value)}
        />
      </div>
      <Handle type="source" position={Position.Right} id="out" />
    </div>
  )
}
