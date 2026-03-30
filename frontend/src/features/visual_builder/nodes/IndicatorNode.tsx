/**
 * IndicatorNode — configurable strategy indicator.
 *
 * Supports:
 *   - SMA Crossover: Fast SMA / Slow SMA window periods
 *   - MACD: Fast / Slow / Signal window periods
 */

import { Handle, Position, type NodeProps } from 'reactflow'
import { useWorkflowStore } from '../../../store/workflowStore'
import type { IndicatorNodeData, IndicatorType } from '../../../types/types'

export function IndicatorNode({ id, data }: NodeProps<IndicatorNodeData>) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)
  const isMACD = data.indicatorType === 'macd'

  return (
    <div className="react-flow__node-indicator" style={nodeStyle}>
      <div style={headerStyle}>📈 Indicator</div>

      {/* Strategy type selector */}
      <label style={labelStyle}>Strategy Type</label>
      <select
        value={data.indicatorType}
        onChange={(e) => updateNodeData(id, { indicatorType: e.target.value as IndicatorType })}
        style={selectStyle}
      >
        <option value="sma_crossover">SMA Crossover</option>
        <option value="macd">MACD</option>
      </select>

      {/* SMA Crossover parameters */}
      {!isMACD && (
        <>
          <label style={labelStyle}>Fast SMA</label>
          <input
            type="number"
            min={2}
            max={200}
            value={data.smaFast}
            onChange={(e) => updateNodeData(id, { smaFast: Number(e.target.value) })}
            style={inputStyle}
          />

          <label style={labelStyle}>Slow SMA</label>
          <input
            type="number"
            min={5}
            max={500}
            value={data.smaSlow}
            onChange={(e) => updateNodeData(id, { smaSlow: Number(e.target.value) })}
            style={inputStyle}
          />
        </>
      )}

      {/* MACD parameters */}
      {isMACD && (
        <>
          <label style={labelStyle}>Fast Period</label>
          <input
            type="number"
            min={2}
            max={100}
            value={data.macdFast ?? 12}
            onChange={(e) => updateNodeData(id, { macdFast: Number(e.target.value) })}
            style={inputStyle}
          />

          <label style={labelStyle}>Slow Period</label>
          <input
            type="number"
            min={5}
            max={200}
            value={data.macdSlow ?? 26}
            onChange={(e) => updateNodeData(id, { macdSlow: Number(e.target.value) })}
            style={inputStyle}
          />

          <label style={labelStyle}>Signal Period</label>
          <input
            type="number"
            min={2}
            max={50}
            value={data.macdSignal ?? 9}
            onChange={(e) => updateNodeData(id, { macdSignal: Number(e.target.value) })}
            style={inputStyle}
          />
        </>
      )}

      {/* Portfolio capital */}
      <label style={labelStyle}>Initial Capital ($)</label>
      <input
        type="number"
        min={100}
        step={1000}
        value={data.initialCapital}
        onChange={(e) => updateNodeData(id, { initialCapital: Number(e.target.value) })}
        style={inputStyle}
      />

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
  minWidth: 190,
  color: '#e2e8f0',
  fontFamily: "'Inter', system-ui, sans-serif",
  fontSize: 13,
}

const headerStyle: React.CSSProperties = {
  fontWeight: 700,
  fontSize: 14,
  marginBottom: 10,
  color: '#a78bfa',
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

const selectStyle: React.CSSProperties = {
  ...inputStyle,
  cursor: 'pointer',
}

export default IndicatorNode
