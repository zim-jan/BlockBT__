import {Handle, Position} from 'reactflow'
import type {SignalNodeData} from '../../../types/types'

interface Props {
  data: SignalNodeData
}

export function SignalNode({ data }: Props) {
  return (
    <div className="rf-node rf-node--signal">
      <Handle type="target" position={Position.Left} id="in" />
      <div className="rf-node__header">
        <span className="rf-node__icon">⚡</span>
        <span className="rf-node__title">Signal Logic</span>
      </div>
      <div className="rf-node__body">
        <div className="rf-signal-badge">
          {data.signalType === 'sma_crossover' ? (
            <>
              <span className="rf-signal-badge__arrow">▲</span>
              <span>Fast SMA crosses above Slow SMA</span>
            </>
          ) : (
            data.signalType
          )}
        </div>
        <p className="rf-hint">Entry on crossover · Exit on reversal</p>
      </div>
      <Handle type="source" position={Position.Right} id="out" />
    </div>
  )
}
