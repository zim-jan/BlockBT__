/**
 * OptimizerNode — Bayesian optimization settings (Optuna).
 * 
 * Defines bounds for strategy parameters and optimization trials.
 */

import {Handle, type Node, type NodeProps, Position} from '@xyflow/react'
import {useState} from 'react'
import {useWorkflowStore} from '../../../store/workflowStore'
import {useWorkflowOptimization} from '../../../hooks/useWorkflowOptimization'
import type {IndicatorNodeData, OptimizerNodeData, ParameterBound} from '../../../types/types'
import {OptimizationChart} from './OptimizationChart'
import {CategoryBadge} from './CategoryBadge'

export type OptimizerNode = Node<OptimizerNodeData, 'optimizerNode'>

export function OptimizerNode({ id, data }: NodeProps<OptimizerNode>) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)
  const edges = useWorkflowStore((s) => s.edges)
  const nodes = useWorkflowStore((s) => s.nodes)

  const [showChart, setShowChart] = useState(false)
  const { runOptimization, isRunning } = useWorkflowOptimization()

  const updateBound = (key: string, bound: Partial<ParameterBound>) => {
    const newBounds = { ...data.paramBounds }
    newBounds[key] = { ...newBounds[key], ...bound }
    updateNodeData(id, { paramBounds: newBounds })
  }

  const getConnectedIndicator = () => {
    const sourceEdge = edges.find(e => e.target === id)
    if (!sourceEdge) return null
    return nodes.find(n => n.id === sourceEdge.source)
  }

  const handleSyncBounds = () => {
    const indicator = getConnectedIndicator()
    if (!indicator || indicator.type !== 'indicatorNode') {
      alert('Connect an Indicator node to sync bounds.')
      return
    }

    const iData = indicator.data as unknown as IndicatorNodeData
    let newBounds: Record<string, ParameterBound> = {}

    if (iData.indicatorType === 'macd') {
      newBounds = {
        sma_fast: { min: 5, max: 20, type: 'int' },
        sma_slow: { min: 20, max: 40, type: 'int' },
        macd_signal: { min: 5, max: 15, type: 'int' }
      }
    } else {
      newBounds = {
        sma_fast: { min: 5, max: 20, type: 'int' },
        sma_slow: { min: 25, max: 50, type: 'int' }
      }
    }
    updateNodeData(id as string, { paramBounds: newBounds })
  }

  const handleApplyToIndicator = () => {
    if (!data.bestParameters) return
    const indicator = getConnectedIndicator()
    if (!indicator || indicator.type !== 'indicatorNode') {
      alert('Connect an Indicator node to apply parameters.')
      return
    }

    // Map backend snake_case parameters to frontend camelCase
    const mappedParams: Record<string, any> = {}
    
    // For MACD, the frontend uses macdFast, macdSlow, macdSignal but backend uses sma_fast, sma_slow, macd_signal
    const iData = indicator.data as unknown as IndicatorNodeData
    if (iData.indicatorType === 'macd') {
        if (data.bestParameters.sma_fast !== undefined) mappedParams.macdFast = data.bestParameters.sma_fast
        if (data.bestParameters.sma_slow !== undefined) mappedParams.macdSlow = data.bestParameters.sma_slow
        if (data.bestParameters.macd_signal !== undefined) mappedParams.macdSignal = data.bestParameters.macd_signal
    } else {
        if (data.bestParameters.sma_fast !== undefined) mappedParams.smaFast = data.bestParameters.sma_fast
        if (data.bestParameters.sma_slow !== undefined) mappedParams.smaSlow = data.bestParameters.sma_slow
    }

    updateNodeData(indicator.id as string, mappedParams)
    alert('Parameters applied to Indicator node!')
  }

  // Audyt 2026-07-17: stany PENDING/RUNNING/FAILED z node.data (parytet z WfoNode) —
  // wcześniej jedynym renderowanym stanem był COMPLETED, a błędy znikały bez śladu.
  const isPending = data.jobStatus === 'PENDING'
  const isNodeRunning = data.jobStatus === 'RUNNING'
  const isCompleted = data.jobStatus === 'COMPLETED'
  const isFailed = data.jobStatus === 'FAILED'
  const isBusy = isRunning || isPending || isNodeRunning

  return (
    <div
      className={`rf-node rf-node--optimizer ${isCompleted ? 'rf-node--completed' : ''} ${isFailed ? 'rf-node--failed' : ''}`}
      style={{ minWidth: showChart ? 320 : 210 }}
    >
      <Handle type="target" position={Position.Left} style={{ zIndex: 10 }} />
      <div className="rf-node__header react-flow__node-drag-handle">
        <span className="rf-node__icon">🧪</span>
        <span className="rf-node__title">Optimizer</span>
        <CategoryBadge category="Meta" />
        {data.jobStatus && (
          <span className={`rf-status-pill ${
            isPending ? 'rf-status-pill--pending' :
            isNodeRunning ? 'rf-status-pill--running' :
            isCompleted ? 'rf-status-pill--completed' :
            'rf-status-pill--failed'
          }`}>
            {isPending && '⏳'}
            {isNodeRunning && '⚙️'}
            {isCompleted && '✅'}
            {isFailed && '❌'}
          </span>
        )}
      </div>

      <div className="rf-node__body">
        <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
          <button 
            onClick={handleSyncBounds}
            className="rf-btn"
            style={{ flex: 1, padding: '4px 8px', fontSize: '11px' }}
          >
            🔄 Sync
          </button>
          <button
            onClick={runOptimization}
            disabled={isBusy}
            className="rf-btn-primary"
            style={{
              flex: 1.5,
              padding: '4px 8px',
              fontSize: '11px',
              backgroundColor: isBusy ? '#475569' : '#10b981',
              whiteSpace: 'nowrap'
            }}
          >
            {isBusy ? '⏳ Optimizing' : '🚀 Optimize'}
          </button>
        </div>

        <label className="rf-label">Target Metric</label>
        <select
          value={data.metric}
          onChange={(e) => updateNodeData(id as string, { metric: e.target.value })}
          className="rf-input"
        >
          <option value="Total Return [%]">Total Return [%]</option>
          <option value="Sharpe Ratio">Sharpe Ratio</option>
          <option value="Max Drawdown [%]">Max Drawdown [%]</option>
          <option value="Win Rate [%]">Win Rate [%]</option>
        </select>

        <label className="rf-label">Number of Trials</label>
        <input
          type="number"
          min={5}
          max={200}
          value={data.nTrials}
          onChange={(e) => updateNodeData(id as string, { nTrials: Number(e.target.value) })}
          className="rf-input"
        />

        <div style={{ marginTop: 12, borderTop: '1px solid var(--border)', paddingTop: 8 }}>
          <div style={{ fontSize: 11, color: '#a78bfa', fontWeight: 600, marginBottom: 4 }}>PARAM BOUNDS</div>
          
          {Object.entries(data.paramBounds as Record<string, ParameterBound>).map(([key, bound]) => (
            <div key={key} style={{ marginBottom: 8, padding: 6, background: 'rgba(0,0,0,0.2)', borderRadius: 6 }}>
              <div style={{ fontSize: 10, color: '#f8fafc', fontWeight: 700, marginBottom: 2 }}>{key.toUpperCase()}</div>
              <div style={{ display: 'flex', gap: 4 }}>
                <div style={{ flex: 1 }}>
                  <label className="rf-label" style={{ fontSize: 9, marginBottom: 1 }}>Min</label>
                  <input
                    type="number"
                    value={bound.min}
                    onChange={(e) => updateBound(key, { min: Number(e.target.value) })}
                    className="rf-input"
                    style={{ padding: '2px 4px', fontSize: 11 }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="rf-label" style={{ fontSize: 9, marginBottom: 1 }}>Max</label>
                  <input
                    type="number"
                    value={bound.max}
                    onChange={(e) => updateBound(key, { max: Number(e.target.value) })}
                    className="rf-input"
                    style={{ padding: '2px 4px', fontSize: 11 }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {data.jobStatus === 'COMPLETED' && data.bestParameters && (
          <div className="rf-metrics" style={{ marginTop: 10, padding: 8, background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <div style={{ color: '#10b981', fontWeight: 600, fontSize: 11 }}>Best Found:</div>
              <button 
                onClick={handleApplyToIndicator}
                className="rf-btn-primary"
                style={{ fontSize: 9, padding: '2px 6px', background: '#059669' }}
              >
                📥 Apply
              </button>
            </div>
            <div style={{ fontSize: 10 }}>
              {Object.entries(data.bestParameters as Record<string, any>).map(([k, v]) => (
                <div key={k}>{k}: {v as React.ReactNode}</div>
              ))}
              <div style={{ marginTop: 4, color: '#a78bfa' }}>Value: {(data.bestValue as number)?.toFixed(4)}</div>
            </div>

            {(data.trials as any[]) && (data.trials as any[]).length > 0 && (
              <button 
                onClick={() => setShowChart(!showChart)}
                className="rf-btn"
                style={{ width: '100%', marginTop: 8, fontSize: 10 }}
              >
                {showChart ? '📉 Hide Chart' : '📈 Show Chart'}
              </button>
            )}

            {showChart && data.trials && (
              <OptimizationChart trials={data.trials as any[]} metricName={data.metric as string} />
            )}
          </div>
        )}

        {isFailed && (
          <p className="rf-hint rf-hint--error text-center mt-2">
            {(data.error as string) ?? 'Optimization failed'}
          </p>
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

export default OptimizerNode
