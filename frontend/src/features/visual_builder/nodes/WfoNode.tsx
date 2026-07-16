import {Handle, type Node, type NodeProps, Position} from '@xyflow/react'
import {useWorkflowStore} from '../../../store/workflowStore'
import {useWorkflowOptimization} from '../../../hooks/useWorkflowOptimization'
import type {WfoNodeData} from '../../../types/types'
import {CategoryBadge} from './CategoryBadge'

export type WfoNode = Node<WfoNodeData, 'wfoNode'>

export function WfoNode({ id, data }: NodeProps<WfoNode>) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)
  const { runWfo, isRunning: isExecutionRunning } = useWorkflowOptimization()
  const { jobStatus, windowSize, stepSize, error, results } = data

  // Formatowanie metryk: liczba -> 2 miejsca, brak wartości -> myślnik
  const fmt = (v?: number) => (typeof v === 'number' ? v.toFixed(2) : '—')

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
        {!isPending && !isRunning && (
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

        {isCompleted && !results && (
          <div className="mt-2 text-xs text-green-600 font-medium text-center">
            WFO Complete
          </div>
        )}

        {isCompleted && results && (
          <div
            className="rf-metrics"
            style={{ marginTop: 10, padding: 8, background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 8 }}
          >
            <div style={{ color: '#10b981', fontWeight: 600, fontSize: 11, marginBottom: 4 }}>
              Walk-Forward Results
            </div>

            {results.overall_metrics && (
              <div style={{ fontSize: 10, marginBottom: 4 }}>
                <div>OOS Total Return: {fmt(results.overall_metrics['Total Return [%]'])}%</div>
                <div>OOS Sharpe: {fmt(results.overall_metrics['Sharpe Ratio'])}</div>
              </div>
            )}

            {typeof results.n_windows === 'number' && (
              <div style={{ fontSize: 10, color: '#94a3b8', marginBottom: 4 }}>
                {results.n_windows} windows ({results.n_failed_windows ?? 0} failed)
              </div>
            )}

            {results.best_parameters && (
              <div style={{ fontSize: 10, marginBottom: 4 }}>
                <div style={{ color: '#10b981', fontWeight: 600 }}>Best window params:</div>
                {Object.entries(results.best_parameters).map(([k, v]) => (
                  <div key={k}>{k}: {String(v)}</div>
                ))}
                {results.best_value != null && (
                  <div style={{ color: '#a78bfa' }}>Value: {Number(results.best_value).toFixed(4)}</div>
                )}
              </div>
            )}

            {results.trials && results.trials.length > 0 && (
              <div style={{ fontSize: 9, maxHeight: 120, overflowY: 'auto' }}>
                {results.trials.map((w) => (
                  <div key={w.window_index} style={{ display: 'flex', justifyContent: 'space-between', gap: 6 }}>
                    <span>W{w.window_index}</span>
                    {w.error ? (
                      <span style={{ color: '#f87171' }}>{w.error}</span>
                    ) : (
                      <span>{fmt(w.oos_metrics?.['Total Return [%]'])}% / {fmt(w.oos_metrics?.['Sharpe Ratio'])}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
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
