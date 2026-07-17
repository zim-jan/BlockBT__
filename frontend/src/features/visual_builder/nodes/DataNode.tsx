/**
 * DataNode — source selector, symbol, date range, and timeframe.
 *
 * Supports three data sources:
 *   - Yahoo Finance (real market data via yfinance + Parquet cache)
 *   - Alpaca (requires API key — configured in Settings)
 *   - Synthetic (random-walk OHLCV — no network needed)
 */

import {Handle, type Node, type NodeProps, Position} from '@xyflow/react'
import {useWorkflowStore} from '../../../store/workflowStore'
import type {DataNodeData, DataSourceType} from '../../../types/types'
import {CategoryBadge} from './CategoryBadge'

const TIMEFRAMES = ['1d', '1h', '5m', '15m', '30m', '1w'] as const

const MAX_SYNTHETIC_TICKERS = 50
const TICKER_LENGTH = 4

/** Losowy 4-literowy ticker (A–Z) dla generatora synthetic. */
function randomTicker(): string {
  let ticker = ''
  for (let i = 0; i < TICKER_LENGTH; i++) {
    ticker += String.fromCharCode(65 + Math.floor(Math.random() * 26))
  }
  return ticker
}

/** N unikalnych losowych tickerów jako string "AAAA,BBBB,..." (format pola symbol). */
function generateRandomTickers(count: number): string {
  const tickers = new Set<string>()
  while (tickers.size < count) {
    tickers.add(randomTicker())
  }
  return [...tickers].join(',')
}

/** Liczba tickerów zapisanych aktualnie w polu symbol. */
function tickerCount(symbol: string): number {
  return symbol.split(',').map((t) => t.trim()).filter(Boolean).length
}

export type DataNode = Node<DataNodeData, 'dataNode'>

export function DataNode({ id, data }: NodeProps<DataNode>) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)

  const isSynthetic = data.dataSource === 'synthetic'

  return (
    <div className="rf-node rf-node--data">
      <div className="rf-node__header react-flow__node-drag-handle">
        <span className="rf-node__icon">📊</span>
        <span className="rf-node__title">Data Source</span>
        <CategoryBadge category="DataIngestion" />
      </div>

      <div className="rf-node__body">
        {/* Data source selector */}
        <label className="rf-label">Source</label>
        <select
          value={data.dataSource}
          onChange={(e) => {
            const source = e.target.value as DataSourceType
            if (source === 'synthetic') {
              // Synthetic: tickery są zawsze losowe — przełączenie źródła
              // wymienia dotychczasowe symbole, zachowując ich liczbę
              updateNodeData(id as string, {
                dataSource: source,
                symbol: generateRandomTickers(Math.max(1, tickerCount(data.symbol))),
              })
              return
            }
            updateNodeData(id as string, { dataSource: source })
          }}
          className="rf-input"
        >          <option value="yahoo">Yahoo Finance</option>
          <option value="alpaca">Alpaca</option>
          <option value="synthetic">Synthetic</option>
        </select>

        {isSynthetic ? (
          <>
            {/* Synthetic: użytkownik podaje tylko liczbę serii — nazwy losujemy */}
            <label className="rf-label">Number of tickers</label>
            <input
              type="number"
              min={1}
              max={MAX_SYNTHETIC_TICKERS}
              step={1}
              value={tickerCount(data.symbol)}
              onChange={(e) => {
                const parsed = Number.parseInt(e.target.value, 10)
                if (Number.isNaN(parsed)) return
                const count = Math.min(MAX_SYNTHETIC_TICKERS, Math.max(1, parsed))
                updateNodeData(id as string, { symbol: generateRandomTickers(count) })
              }}
              className="rf-input"
            />
            <div className="rf-hint" style={{ fontSize: '11px' }}>
              {data.symbol.split(',').filter(Boolean).join(', ') || '—'}
            </div>
          </>
        ) : (
          <>
            {/* Symbol — multi-ticker działa dla źródeł realnych (review 2026-07-16) */}
            <label className="rf-label">Symbol</label>
            <input
              value={data.symbol}
              onChange={(e) => updateNodeData(id as string, { symbol: e.target.value.toUpperCase() })}
              placeholder="AAPL, MSFT"
              className="rf-input"
            />
            <div className="rf-hint" style={{ fontSize: '11px' }}>Wiele tickerów: rozdziel przecinkami</div>
          </>
        )}

        {/* Date range — generator synthetic też respektuje zakres dat */}
        <label className="rf-label">Start Date</label>
        <input
          type="date"
          value={data.startDate}
          onChange={(e) => updateNodeData(id as string, { startDate: e.target.value })}
          className="rf-input"
        />

        <label className="rf-label">End Date</label>
        <input
          type="date"
          value={data.endDate}
          onChange={(e) => updateNodeData(id as string, { endDate: e.target.value })}
          className="rf-input"
        />

        {/* Timeframe */}
        <label className="rf-label">Timeframe</label>
        <select
          value={data.timeframe}
          onChange={(e) => updateNodeData(id as string, { timeframe: e.target.value })}
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
