/**
 * IndicatorNode — configurable strategy indicator.
 *
 * Supports:
 *   - SMA Crossover: Fast SMA / Slow SMA window periods
 *   - MACD: Fast / Slow / Signal window periods
 */

import { useEffect, useState } from 'react'
import {Handle, type Node, type NodeProps, Position} from '@xyflow/react'
import {useWorkflowStore} from '../../../store/workflowStore'
import type {IndicatorNodeData, IndicatorType} from '../../../types/types'
import { api } from '../../../services/api'

export type IndicatorNode = Node<IndicatorNodeData, 'indicatorNode'>

export function IndicatorNode({ id, data }: NodeProps<IndicatorNode>) {
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData)
  const [availableIndicators, setAvailableIndicators] = useState<any[]>([])
  
  useEffect(() => {
    api.indicators.list().then(res => {
      if (res.success) setAvailableIndicators(res.data)
    }).catch(err => console.error("Failed to fetch indicators:", err))
  }, [])

  const isMACD = data.indicatorType === 'macd'
  const isCustom = data.indicatorType === 'custom'
  const isDynamic = !['sma_crossover', 'macd', 'custom'].includes(data.indicatorType)

  return (
    <div className="rf-node rf-node--indicator">
      <Handle type="target" position={Position.Left} style={{ zIndex: 10 }} />
      <div className="rf-node__header react-flow__node-drag-handle">
        <span className="rf-node__icon">📈</span>
        <span className="rf-node__title">Indicator</span>
      </div>

      <div className="rf-node__body">
        {/* Strategy type selector */}
        <label className="rf-label">Strategy Type</label>
        <select
          value={data.indicatorType}
          onChange={(e) => updateNodeData(id as string, { indicatorType: e.target.value as IndicatorType })}
          className="rf-input"
        >
          <option value="sma_crossover">SMA Crossover (Native)</option>
          <option value="macd">MACD (Native)</option>
          <option value="custom">Custom Code</option>
          <optgroup label="Registry Indicators">
            {availableIndicators.map(ind => (
              <option key={ind.name} value={ind.name}>{ind.name} ({ind.library})</option>
            ))}
          </optgroup>
        </select>

        {/* Dynamic Parameters from Registry */}
        {isDynamic && (
          <div className="rf-dynamic-params">
             {availableIndicators.find(i => i.name === data.indicatorType)?.params.map((p: any) => (
               <div key={p.name}>
                 <label className="rf-label">{p.name}</label>
                 <input
                   type={p.type === 'int' ? 'number' : 'text'}
                   value={data[p.name] ?? p.default}
                   onChange={(e) => updateNodeData(id as string, { [p.name]: p.type === 'int' ? Number(e.target.value) : e.target.value })}
                   className="rf-input"
                 />
               </div>
             ))}
          </div>
        )}

        {/* SMA Crossover parameters */}
        {data.indicatorType === 'sma_crossover' && (
          <>
            <label className="rf-label">Fast SMA</label>
            <input
              type="number"
              min={2}
              max={200}
              value={data.smaFast}
              onChange={(e) => updateNodeData(id as string, { smaFast: Number(e.target.value) })}
              className="rf-input"
            />

            <label className="rf-label">Slow SMA</label>
            <input
              type="number"
              min={5}
              max={500}
              value={data.smaSlow}
              onChange={(e) => updateNodeData(id as string, { smaSlow: Number(e.target.value) })}
              className="rf-input"
            />
          </>
        )}

        {/* MACD parameters */}
        {isMACD && !isCustom && (
          <>
            <label className="rf-label">Fast Period</label>
            <input
              type="number"
              min={2}
              max={100}
              value={data.macdFast ?? 12}
              onChange={(e) => updateNodeData(id as string, { macdFast: Number(e.target.value) })}
              className="rf-input"
            />

            <label className="rf-label">Slow Period</label>
            <input
              type="number"
              min={5}
              max={200}
              value={data.macdSlow ?? 26}
              onChange={(e) => updateNodeData(id as string, { macdSlow: Number(e.target.value) })}
              className="rf-input"
            />

            <label className="rf-label">Signal Period</label>
            <input
              type="number"
              min={2}
              max={50}
              value={data.macdSignal ?? 9}
              onChange={(e) => updateNodeData(id as string, { macdSignal: Number(e.target.value) })}
              className="rf-input"
            />
          </>
        )}

        {/* Custom Code editor */}
        {isCustom && (
          <>
            <label className="rf-label">Python / vectorbt Code</label>
            <textarea
              rows={8}
              value={data.codeContent ?? "entries = close.vbt.indicators.RSI.run().rsi_below(30)\nexits = close.vbt.indicators.RSI.run().rsi_above(70)"}
              onChange={(e) => updateNodeData(id as string, { codeContent: e.target.value })}
              className="rf-input"
              style={{ fontFamily: 'monospace', fontSize: '11px', resize: 'vertical' }}
              placeholder="entries = ...\nexits = ..."
            />
            <div className="rf-hint">
              Available: <code>close</code>, <code>vbt</code>, <code>np</code>, <code>pd</code>.<br/>
              Must define <code>entries</code> and <code>exits</code>.
            </div>
          </>
        )}

        {/* Portfolio capital */}
        <label className="rf-label">Initial Capital ($)</label>
        <input
          type="number"
          min={100}
          step={1000}
          value={data.initialCapital}
          onChange={(e) => updateNodeData(id as string, { initialCapital: Number(e.target.value) })}
          className="rf-input"
        />
      </div>

      <Handle 
        type="source" 
        position={Position.Right} 
        className="easy-connect-handle"
      />
    </div>
  )
}

export default IndicatorNode
