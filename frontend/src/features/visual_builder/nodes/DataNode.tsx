/**
 * DataNode — source selector, symbol, date range, and timeframe.
 *
 * Supports three data sources:
 *   - Yahoo Finance (real market data via yfinance + Parquet cache)
 *   - Alpaca (requires API key — configured in Settings)
 *   - Synthetic (random-walk OHLCV — no network needed)
 */

import { Handle, Position, type NodeProps } from 'reactflow'
import { useWorkflowStore } from '../../../store/workflowStore'
import type { DataNodeData, DataSourceType } from '../../../types/types'

const TIMEFRAMES = ['1d', '1h', '5m', '15m', '30m', '1w'] as const

export function DataNode({ id, data }: NodeProps<DataNodeData>) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)

  const isSynthetic = data.dataSource === 'synthetic'

  return (
    <div className="react-flow__node-data" style={nodeStyle}>
      <div style={headerStyle}>📊 Data Source</div>

      {/* Data source selector */}
      <label style={labelStyle}>Source</label>
      <select
        value={data.dataSource}
        onChange={(e) => updateNodeData(id, { dataSource: e.target.value as DataSourceType })}
        style={selectStyle}
      >
        <option value="yahoo">Yahoo Finance</option>
        <option value="alpaca">Alpaca</option>
        <option value="synthetic">Synthetic</option>
      </select>

      {/* Symbol */}
      <label style={labelStyle}>Symbol</label>
      <input
        value={data.symbol}
        onChange={(e) => updateNodeData(id, { symbol: e.target.value.toUpperCase() })}
        placeholder={isSynthetic ? 'SYNTHETIC' : 'AAPL'}
        style={inputStyle}
        disabled={isSynthetic}
      />

      {/* Date range — hidden for synthetic */}
      {!isSynthetic && (
        <>
          <label style={labelStyle}>Start Date</label>
          <input
            type="date"
            value={data.startDate}
            onChange={(e) => updateNodeData(id, { startDate: e.target.value })}
            style={inputStyle}
          />

          <label style={labelStyle}>End Date</label>
          <input
            type="date"
            value={data.endDate}
            onChange={(e) => updateNodeData(id, { endDate: e.target.value })}
            style={inputStyle}
          />
        </>
      )}

      {/* Timeframe */}
      <label style={labelStyle}>Timeframe</label>
      <select
        value={data.timeframe}
        onChange={(e) => updateNodeData(id, { timeframe: e.target.value })}
        style={selectStyle}
      >
        {TIMEFRAMES.map((tf) => (
          <option key={tf} value={tf}>{tf}</option>
        ))}
      </select>

      {isSynthetic && (
        <div style={hintStyle}>Random-walk OHLCV — no network needed</div>
      )}

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
  minWidth: 200,
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

const hintStyle: React.CSSProperties = {
  fontSize: 10,
  color: '#64748b',
  marginTop: 8,
  fontStyle: 'italic',
}

export default DataNode
