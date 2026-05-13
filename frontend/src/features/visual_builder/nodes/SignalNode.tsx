import {Handle, type Node, type NodeProps, Position} from '@xyflow/react'
import {useWorkflowStore} from '../../../store/workflowStore'
import type {SignalNodeData} from '../../../types/types'
import {CategoryBadge} from './CategoryBadge'

export type SignalNode = Node<SignalNodeData, 'signalNode'>

export function SignalNode({ id, data }: NodeProps<SignalNode>) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)

  return (
    <div className="rf-node rf-node--signal">
      <Handle type="target" position={Position.Left} style={{ zIndex: 10 }} />
      <div className="rf-node__header react-flow__node-drag-handle">
        <span className="rf-node__icon">⚡</span>
        <span className="rf-node__title">Signal Logic</span>
        <CategoryBadge category="LogicOperators" />
      </div>
      <div className="rf-node__body">
        <label className="rf-label">Action Type</label>
        <select
          value={data.signalType}
          onChange={(e) => updateNodeData(id as string, { signalType: e.target.value as any })}
          className="rf-input"
        >
          <option value="sma_crossover">Crossover</option>
          <option value="ranking">Ranking (Vectorized)</option>
          <option value="mapping">Mapping (FlexArray)</option>
          <option value="distribution">Distribution Analysis</option>
        </select>

        <div className="rf-signal-badge">
          {data.signalType === 'sma_crossover' && (
            <>
              <span className="rf-signal-badge__arrow">▲</span>
              <span>Fast crosses above Slow</span>
            </>
          )}
          {data.signalType === 'ranking' && <span>Sort assets by indicator value</span>}
          {data.signalType === 'mapping' && <span>Map signals across parameters</span>}
          {data.signalType === 'distribution' && <span>Analyze outcome distribution</span>}
        </div>
        <p className="rf-hint">Native vbt vectorization applied</p>
      </div>
      <Handle 
        type="source" 
        position={Position.Right} 
        className="easy-connect-handle"
      />
    </div>
  )
}
