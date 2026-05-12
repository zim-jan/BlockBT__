/**
 * DataNode — source selector, symbol, date range, and timeframe.
 *
 * Supports three data sources:
 *   - Yahoo Finance (real market data via yfinance + Parquet cache)
 *   - Alpaca (requires API key — configured in Settings)
 *   - Synthetic (random-walk OHLCV — no network needed)
 */

import {Handle, type NodeProps, Position} from '@xyflow/react'
import {useWorkflowStore} from '../../../store/workflowStore'
import type {DataNodeData, DataSourceType} from '../../../types/types'

const TIMEFRAMES = ['1d', '1h', '5m', '15m', '30m', '1w'] as const

export function DataNode({ id, data }: NodeProps<DataNodeData>) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)

  const isSynthetic = data.dataSource === 'synthetic'

  return (
    <div className="rf-node rf-node--data">
      <div className="rf-node__header react-flow__node-drag-handle">
        <span className="rf-node__icon">📊</span>
        <span className="rf-node__title">Data Source</span>
      </div>

      <div className="rf-node__body">
        {/* Data source selector */}
        <label className="rf-label">Source</label>
        <select
          value={data.dataSource}
          onChange={(e) => updateNodeData(id, { dataSource: e.target.value as DataSourceType })}
          className="rf-input"
        >
          <option value="yahoo">Yahoo Finance</option>
          <option value="alpaca">Alpaca</option>
          <option value="synthetic">Synthetic</option>
        </select>

        {/* Symbol */}
        <label className="rf-label">Symbol</label>
        <input
          value={data.symbol}
          onChange={(e) => updateNodeData(id, { symbol: e.target.value.toUpperCase() })}
          placeholder={isSynthetic ? 'SYNTHETIC' : 'AAPL'}
          className="rf-input"
          disabled={isSynthetic}
        />

        {/* Date range — hidden for synthetic */}
        {!isSynthetic && (
          <>
            <label className="rf-label">Start Date</label>
            <input
              type="date"
              value={data.startDate}
              onChange={(e) => updateNodeData(id, { startDate: e.target.value })}
              className="rf-input"
            />

            <label className="rf-label">End Date</label>
            <input
              type="date"
              value={data.endDate}
              onChange={(e) => updateNodeData(id, { endDate: e.target.value })}
              className="rf-input"
            />
          </>
        )}

        {/* Timeframe */}
        <label className="rf-label">Timeframe</label>
        <select
          value={data.timeframe}
          onChange={(e) => updateNodeData(id, { timeframe: e.target.value })}
          className="rf-input"
        >
          {TIMEFRAMES.map((tf) => (
            <option key={tf} value={tf}>{tf}</option>
          ))}
        </select>

        {isSynthetic && (
          <div className="rf-hint">Random-walk OHLCV — no network needed</div>
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

export default DataNode
