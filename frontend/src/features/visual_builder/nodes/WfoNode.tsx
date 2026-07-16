import {Handle, type Node, type NodeProps, Position} from '@xyflow/react'
import {useWorkflowStore} from '../../../store/workflowStore'
import {useWorkflowOptimization} from '../../../hooks/useWorkflowOptimization'
import type {WfoNodeData} from '../../../types/types'
import {CategoryBadge} from './CategoryBadge'

export type WfoNode = Node<WfoNodeData, 'wfoNode'>

export function WfoNode({ id, data }: NodeProps<WfoNode>) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)
  const { runWfo, isRunning: isExecutionRunning } = useWorkflowOptimization()
  const { jobStatus, windowSize, stepSize, error } = data

  const isPending = jobStatus === 'PENDING'
  const isRunning = jobStatus === 'RUNNING'
  const isCompleted = jobStatus === 'COMPLETED'
  const isFailed = jobStatus === 'FAILED'

  return (
    <div className={`rf-node rf-node--optimizer ${isCompleted ? 'rf-node--completed' : ''} ${isFailed ? 'rf-node--failed' : ''}`}>
      <Handle type="target" position={Position.Left} style={{ zIndex: 10 }} />
      <div className="rf-node__header react-flow__node-drag-handle">
        <span className="rf-node__icon">🔄</span>
        <span className="rf-node__title">Walk-Forward</span>
        <CategoryBadge category="Meta" />
        {jobStatus && (
          <span className={`rf-status-pill ${
            isPending ? 'rf-status-pill--pending' :
            isRunning ? 'rf-status-pill--running' :
            isCompleted ? 'rf-status-pill--completed' :
            'rf-status-pill--failed'
          }`}>
            {isPending && '⏳'}
            {isRunning && '⚙️'}
            {isCompleted && '✅'}
            {isFailed && '❌'}
          </span>
        )}
      </div>

      <div className="rf-node__body">
        {!jobStatus && (
          <button 
            onClick={runWfo}
            disabled={isExecutionRunning}
            className="rf-btn rf-btn-primary w-full mb-2"
            style={{ position: 'relative', zIndex: 10, background: '#6366f1' }}
          >
            {isExecutionRunning ? 'Rolling...' : 'Run WFO'}
          </button>
        )}
        <label className="rf-label">Window Size</label>
        <input
          type="text"
          value={windowSize}
          onChange={(e) => updateNodeData(id as string, { windowSize: e.target.value })}
          className="rf-input"
          placeholder="e.g. 365d"
        />

        <label className="rf-label">Step Size</label>
        <input
          type="text"
          value={stepSize}
          onChange={(e) => updateNodeData(id as string, { stepSize: e.target.value })}
          className="rf-input"
          placeholder="e.g. 90d"
        />

        {(isPending || isRunning) && (
          <div className="flex flex-col items-center py-2">
            <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full mb-1" />
            <p className="rf-hint">{isRunning ? 'Rolling...' : 'Queued'}</p>
          </div>
        )}

        {isCompleted && (
          <div className="mt-2 text-xs text-green-600 font-medium text-center">
            WFO Complete
          </div>
        )}

        {isFailed && (
          <p className="rf-hint rf-hint--error text-center mt-2">{error ?? 'WFO failed'}</p>
        )}
      </div>

      <Handle type="source" position={Position.Right} className="easy-connect-handle" />
    </div>
  )
}
