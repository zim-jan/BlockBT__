import {Handle, Position} from '@xyflow/react'
import {useWorkflowStore} from '../../store/workflowStore'
import type {DataNodeData} from '../../types'

interface Props {
  id: string
  data: DataNodeData
}

export function DataNode({ id, data }: Props) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)

  return (
    <div className="rf-node rf-node--data">
      <div className="rf-node__header react-flow__node-drag-handle">
        <span className="rf-node__icon">📡</span>
        <span className="rf-node__title">Data Source</span>
      </div>
      <div className="rf-node__body">
        <label className="rf-label">Ticker Symbol</label>
        <input
          id={`${id}-symbol`}
          className="rf-input"
          value={data.symbol}
          placeholder="e.g. AAPL"
          onChange={(e) => updateNodeData(id, { symbol: e.target.value.toUpperCase() })}
        />
        <p className="rf-hint">Synthetic OHLCV data generated for MVP</p>
      </div>
      {/* Easy Connect Handle */}
      <Handle 
        type="source" 
        position={Position.Right} 
        id="out" 
        className="easy-connect-handle"
      />
    </div>
  )
}
