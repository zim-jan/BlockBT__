/**
 * OptimizerNode — Bayesian optimization settings (Optuna).
 * 
 * Defines bounds for strategy parameters and optimization trials.
 */

import {Handle, type NodeProps, Position} from 'reactflow'
import {useState} from 'react'
import {useWorkflowStore} from '../../../store/workflowStore'
import {useWorkflowOptimization} from '../../../hooks/useWorkflowOptimization'
import type {IndicatorNodeData, OptimizerNodeData, ParameterBound} from '../../../types/types'
import {OptimizationChart} from './OptimizationChart'

export function OptimizerNode({ id, data }: NodeProps<OptimizerNodeData>) {
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

    const iData = indicator.data as IndicatorNodeData
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
    updateNodeData(id, { paramBounds: newBounds })
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
    const iData = indicator.data as IndicatorNodeData
    if (iData.indicatorType === 'macd') {
        if (data.bestParameters.sma_fast !== undefined) mappedParams.macdFast = data.bestParameters.sma_fast
        if (data.bestParameters.sma_slow !== undefined) mappedParams.macdSlow = data.bestParameters.sma_slow
        if (data.bestParameters.macd_signal !== undefined) mappedParams.macdSignal = data.bestParameters.macd_signal
    } else {
        if (data.bestParameters.sma_fast !== undefined) mappedParams.smaFast = data.bestParameters.sma_fast
        if (data.bestParameters.sma_slow !== undefined) mappedParams.smaSlow = data.bestParameters.sma_slow
    }

    updateNodeData(indicator.id, mappedParams)
    alert('Parameters applied to Indicator node!')
  }

  return (
    <div className="react-flow__node-optimizer" style={{ ...nodeStyle, minWidth: showChart ? 320 : 210 }}>
      <div style={headerStyle}>🧪 Optimizer (Optuna)</div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
        <button 
          onClick={handleSyncBounds}
          style={{ ...btnStyle, background: '#334155', flex: 1 }}
        >
          🔄 Sync Bounds
        </button>
        <button 
          onClick={runOptimization}
          disabled={isRunning}
          style={{ 
            ...btnStyle, 
            background: isRunning ? '#475569' : '#10b981', 
            flex: 1.5,
            whiteSpace: 'nowrap'
          }}
        >
          {isRunning ? '⏳ Optimizing' : '🚀 Optimize'}
        </button>
      </div>

      <label style={labelStyle}>Target Metric</label>
      <select
        value={data.metric}
        onChange={(e) => updateNodeData(id, { metric: e.target.value })}
        style={selectStyle}
      >
        <option value="Total Return [%]">Total Return [%]</option>
        <option value="Sharpe Ratio">Sharpe Ratio</option>
        <option value="Max Drawdown [%]">Max Drawdown [%]</option>
        <option value="Win Rate [%]">Win Rate [%]</option>
      </select>

      <label style={labelStyle}>Number of Trials</label>
      <input
        type="number"
        min={5}
        max={200}
        value={data.nTrials}
        onChange={(e) => updateNodeData(id, { nTrials: Number(e.target.value) })}
        style={inputStyle}
      />

      <div style={{ marginTop: 12, borderTop: '1px solid #334155', paddingTop: 8 }}>
        <div style={{ fontSize: 11, color: '#a78bfa', fontWeight: 600, marginBottom: 4 }}>PARAM BOUNDS</div>
        
        {Object.entries(data.paramBounds).map(([key, bound]) => (
          <div key={key} style={{ marginBottom: 8, padding: 6, background: 'rgba(0,0,0,0.2)', borderRadius: 6 }}>
            <div style={{ fontSize: 10, color: '#f8fafc', fontWeight: 700, marginBottom: 2 }}>{key.toUpperCase()}</div>
            <div style={{ display: 'flex', gap: 4 }}>
              <div style={{ flex: 1 }}>
                <label style={miniLabelStyle}>Min</label>
                <input
                  type="number"
                  value={bound.min}
                  onChange={(e) => updateBound(key, { min: Number(e.target.value) })}
                  style={miniInputStyle}
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={miniLabelStyle}>Max</label>
                <input
                  type="number"
                  value={bound.max}
                  onChange={(e) => updateBound(key, { max: Number(e.target.value) })}
                  style={miniInputStyle}
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {data.jobStatus === 'COMPLETED' && data.bestParameters && (
        <div style={resultBoxStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <div style={{ color: '#10b981', fontWeight: 600 }}>Best Found:</div>
            <button 
              onClick={handleApplyToIndicator}
              style={{ ...btnStyle, fontSize: 9, padding: '2px 6px', background: '#059669' }}
            >
              📥 Apply
            </button>
          </div>
          <div style={{ fontSize: 10 }}>
            {Object.entries(data.bestParameters).map(([k, v]) => (
              <div key={k}>{k}: {v}</div>
            ))}
            <div style={{ marginTop: 4, color: '#a78bfa' }}>Value: {data.bestValue?.toFixed(4)}</div>
          </div>

          {data.trials && data.trials.length > 0 && (
            <button 
              onClick={() => setShowChart(!showChart)}
              style={{ ...btnStyle, width: '100%', marginTop: 8, background: '#475569', fontSize: 10 }}
            >
              {showChart ? '📉 Hide Chart' : '📈 Show Chart'}
            </button>
          )}

          {showChart && data.trials && (
            <OptimizationChart trials={data.trials} metricName={data.metric} />
          )}
        </div>
      )}

      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  )
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const nodeStyle: React.CSSProperties = {
  background: 'linear-gradient(135deg, #1e293b, #0f172a)',
  border: '1px solid #334155',
  borderRadius: 12,
  padding: '12px 16px',
  minWidth: 210,
  color: '#e2e8f0',
  fontFamily: "'Inter', system-ui, sans-serif",
  fontSize: 13,
}

const headerStyle: React.CSSProperties = {
  fontWeight: 700,
  fontSize: 14,
  marginBottom: 10,
  color: '#38bdf8',
  letterSpacing: '0.02em',
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 11,
  color: '#94a3b8',
  marginTop: 6,
  marginBottom: 2,
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
}

const miniLabelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 9,
  color: '#64748b',
  marginBottom: 1,
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '5px 8px',
  borderRadius: 6,
  border: '1px solid #475569',
  background: '#1e293b',
  color: '#e2e8f0',
  fontSize: 13,
  outline: 'none',
  boxSizing: 'border-box',
}

const btnStyle: React.CSSProperties = {
  border: 'none',
  borderRadius: 4,
  padding: '4px 8px',
  color: 'white',
  fontSize: 11,
  fontWeight: 600,
  cursor: 'pointer',
}

const miniInputStyle: React.CSSProperties = {
  ...inputStyle,
  padding: '2px 4px',
  fontSize: 11,
}

const selectStyle: React.CSSProperties = {
  ...inputStyle,
  cursor: 'pointer',
}

const resultBoxStyle: React.CSSProperties = {
  marginTop: 10,
  padding: 8,
  background: 'rgba(16, 185, 129, 0.1)',
  border: '1px solid rgba(16, 185, 129, 0.3)',
  borderRadius: 8,
  fontSize: 11,
}

export default OptimizerNode
