import React, { useEffect } from 'react'
import { useWorkflowStore } from '../store/workflowStore'
import { X, Sliders, Database, Activity, GitBranch, Briefcase, Zap, RefreshCw, CheckCircle } from 'lucide-react'
import type { DataNodeData, IndicatorNodeData, SignalNodeData, PortfolioNodeData, OptimizerNodeData, WfoNodeData, ParameterBound } from '../types/types'
import { api } from '../services/api'
import { showToast } from '../store/useToastStore'

export const InspectorPanel: React.FC = () => {
  const { nodes, edges, selectedNodeId, setSelectedNodeId, updateNodeData } = useWorkflowStore()

  // Clean lookup: locate active node directly by selectedNodeId
  const selectedNode = nodes.find((n) => n.id === selectedNodeId)

  // Log activation / deactivation of InspectorPanel
  useEffect(() => {
    if (selectedNode) {
      console.log(`[InspectorPanel] 🟢 ACTIVATED for node: id=${selectedNode.id}, type=${selectedNode.type}`, selectedNode.data)
    } else {
      console.log('[InspectorPanel] 🔴 DEACTIVATED (no node selected)')
    }
  }, [selectedNode?.id, selectedNode?.type])

  if (!selectedNode) return null

  const nodeType = selectedNode.type ?? 'unknown'
  const data = selectedNode.data as Record<string, any>

  const getHeaderIcon = () => {
    switch (nodeType) {
      case 'dataNode':
        return <Database className="w-5 h-5 text-blue-400" />
      case 'indicatorNode':
        return <Activity className="w-5 h-5 text-purple-400" />
      case 'signalNode':
        return <GitBranch className="w-5 h-5 text-amber-400" />
      case 'portfolioNode':
        return <Briefcase className="w-5 h-5 text-emerald-400" />
      case 'optimizerNode':
      case 'wfoNode':
        return <Zap className="w-5 h-5 text-pink-400" />
      default:
        return <Sliders className="w-5 h-5 text-indigo-400" />
    }
  }

  const getTitle = () => {
    switch (nodeType) {
      case 'dataNode': return 'Data Source Configuration'
      case 'indicatorNode': return 'Indicator & Logic'
      case 'signalNode': return 'Trading Signal'
      case 'portfolioNode': return 'Portfolio & Risk'
      case 'optimizerNode': return 'Optuna Optimization'
      case 'wfoNode': return 'Walk-Forward Analysis'
      default: return 'Node Editor'
    }
  }

  const handleChange = (key: string, value: any) => {
    updateNodeData(selectedNode.id, { [key]: value })
  }

  return (
    <aside className="flex-none w-96 h-full bg-[#131722] border-l border-white/10 shadow-2xl flex flex-col text-slate-100 relative">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10 bg-[#1c2130]/80 flex-none">
        <div className="flex items-center gap-3">
          {getHeaderIcon()}
          <div>
            <h3 className="text-sm font-semibold text-slate-100">{getTitle()}</h3>
            <span className="text-xs font-mono text-slate-400">{selectedNode.id}</span>
          </div>
        </div>
        <button
          onClick={() => setSelectedNodeId(null)}
          className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          aria-label="Close edit panel"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Form Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {nodeType === 'dataNode' && (
          <DataNodeInspector data={data as DataNodeData} onChange={handleChange} />
        )}

        {nodeType === 'indicatorNode' && (
          <IndicatorNodeInspector data={data as IndicatorNodeData} onChange={handleChange} />
        )}

        {nodeType === 'signalNode' && (
          <SignalNodeInspector data={data as SignalNodeData} onChange={handleChange} />
        )}

        {nodeType === 'portfolioNode' && (
          <PortfolioNodeInspector data={data as PortfolioNodeData} onChange={handleChange} />
        )}

        {nodeType === 'optimizerNode' && (
          <OptimizerNodeInspector
            nodeId={selectedNode.id}
            data={data as OptimizerNodeData}
            nodes={nodes}
            edges={edges}
            onChange={handleChange}
            updateNodeData={updateNodeData}
          />
        )}

        {nodeType === 'wfoNode' && (
          <WfoNodeInspector data={data as WfoNodeData} onChange={handleChange} />
        )}
      </div>
    </aside>
  )
}

// ---------------------------------------------------------------------------
// 1. DataNodeInspector
// ---------------------------------------------------------------------------
const DataNodeInspector: React.FC<{ data: DataNodeData; onChange: (k: string, v: any) => void }> = ({ data, onChange }) => {
  const isSynthetic = data.dataSource === 'synthetic'

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1">Data Source</label>
        <select
          value={data.dataSource ?? 'yahoo'}
          onChange={(e) => onChange('dataSource', e.target.value)}
          className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
        >
          <option value="yahoo">Yahoo Finance (vbt.YFData)</option>
          <option value="alpaca">Alpaca Market Data</option>
          <option value="synthetic">Synthetic (Random-Walk OHLCV)</option>
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1">Ticker Symbol(s)</label>
        <input
          type="text"
          value={data.symbol ?? 'AAPL'}
          onChange={(e) => onChange('symbol', e.target.value.toUpperCase())}
          disabled={isSynthetic}
          className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono disabled:opacity-50"
          placeholder={isSynthetic ? 'SYNTHETIC' : 'e.g. AAPL or AAPL, MSFT, GOOG'}
        />
        <p className="text-[11px] text-slate-400 mt-1">Separate multiple symbols with commas for Multi-Wide simulation.</p>
      </div>

      {!isSynthetic && (
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Start Date</label>
            <input
              type="date"
              value={data.startDate ?? '2023-01-01'}
              onChange={(e) => onChange('startDate', e.target.value)}
              className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">End Date</label>
            <input
              type="date"
              value={data.endDate ?? '2025-01-01'}
              onChange={(e) => onChange('endDate', e.target.value)}
              className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
        </div>
      )}

      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1">Timeframe</label>
        <select
          value={data.timeframe ?? '1d'}
          onChange={(e) => onChange('timeframe', e.target.value)}
          className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
        >
          <option value="1d">1 Day (1d)</option>
          <option value="1h">1 Hour (1h)</option>
          <option value="5m">5 Minutes (5m)</option>
          <option value="15m">15 Minutes (15m)</option>
          <option value="30m">30 Minutes (30m)</option>
          <option value="1w">1 Week (1w)</option>
        </select>
      </div>

      <div className="flex items-center gap-2 pt-2 border-t border-white/10">
        <input
          type="checkbox"
          id="pit-enforce"
          checked={Boolean(data.point_in_time_enforcement ?? true)}
          onChange={(e) => onChange('point_in_time_enforcement', e.target.checked)}
          className="accent-indigo-500 rounded cursor-pointer"
        />
        <label htmlFor="pit-enforce" className="text-xs text-slate-300 cursor-pointer font-medium">
          Point-In-Time Enforcement (No Look-ahead)
        </label>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 2. IndicatorNodeInspector
// ---------------------------------------------------------------------------
const IndicatorNodeInspector: React.FC<{ data: IndicatorNodeData; onChange: (k: string, v: any) => void }> = ({ data, onChange }) => {
  const [registryIndicators, setRegistryIndicators] = React.useState<any[]>([])

  useEffect(() => {
    api.indicators.list()
      .then((res) => { if (res.success && res.data) setRegistryIndicators(res.data) })
      .catch(() => {})
  }, [])

  const isDynamic = !['sma_crossover', 'macd', 'rsi', 'custom'].includes(data.indicatorType)
  const currentRegistryInd = registryIndicators.find((i) => i.name === data.indicatorType)

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1">Indicator Type</label>
        <select
          value={data.indicatorType ?? 'sma_crossover'}
          onChange={(e) => onChange('indicatorType', e.target.value)}
          className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
        >
          <option value="sma_crossover">SMA Crossover</option>
          <option value="macd">MACD (Moving Average Convergence Divergence)</option>
          <option value="rsi">RSI Oscillator</option>
          <option value="custom">Custom Numba JIT Code</option>
          {registryIndicators.length > 0 && (
            <optgroup label="Registry Indicators (Introspection)">
              {registryIndicators.map((ind) => (
                <option key={ind.name} value={ind.name}>
                  {ind.name} ({ind.library || 'vbt'})
                </option>
              ))}
            </optgroup>
          )}
        </select>
      </div>

      {/* SMA Crossover parameters */}
      {data.indicatorType === 'sma_crossover' && (
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Fast Moving Average</label>
            <input
              type="number"
              min={2}
              max={200}
              value={data.smaFast ?? 10}
              onChange={(e) => onChange('smaFast', Number(e.target.value))}
              className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Slow Moving Average</label>
            <input
              type="number"
              min={5}
              max={500}
              value={data.smaSlow ?? 30}
              onChange={(e) => onChange('smaSlow', Number(e.target.value))}
              className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
        </div>
      )}

      {/* MACD parameters */}
      {data.indicatorType === 'macd' && (
        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Fast EMA</label>
            <input
              type="number"
              value={data.macdFast ?? 12}
              onChange={(e) => onChange('macdFast', Number(e.target.value))}
              className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Slow EMA</label>
            <input
              type="number"
              value={data.macdSlow ?? 26}
              onChange={(e) => onChange('macdSlow', Number(e.target.value))}
              className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Signal Line</label>
            <input
              type="number"
              value={data.macdSignal ?? 9}
              onChange={(e) => onChange('macdSignal', Number(e.target.value))}
              className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
        </div>
      )}

      {/* RSI parameters */}
      {data.indicatorType === 'rsi' && (
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">RSI Period (Window)</label>
            <input
              type="number"
              value={Number(data.rsiWindow ?? 14)}
              onChange={(e) => onChange('rsiWindow', Number(e.target.value))}
              className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Oversold (Lower Limit)</label>
              <input
                type="number"
                value={Number(data.rsiLower ?? 30)}
                onChange={(e) => onChange('rsiLower', Number(e.target.value))}
                className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Overbought (Upper Limit)</label>
              <input
                type="number"
                value={Number(data.rsiUpper ?? 70)}
                onChange={(e) => onChange('rsiUpper', Number(e.target.value))}
                className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
          </div>
        </div>
      )}

      {/* Custom Numba JIT sandbox */}
      {data.indicatorType === 'custom' && (
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Indicator Code (Numba JIT Sandbox)</label>
          <textarea
            rows={8}
            value={data.codeContent ?? ''}
            onChange={(e) => onChange('codeContent', e.target.value)}
            placeholder="def custom_signal(close):\n    entries = close > 100\n    exits = close < 90\n    return entries, exits"
            className="w-full bg-[#0b0d14] border border-white/10 rounded-lg p-3 text-xs font-mono text-emerald-400 focus:outline-none focus:border-indigo-500 leading-relaxed resize-none"
          />
        </div>
      )}

      {/* Dynamic Registry parameters */}
      {isDynamic && currentRegistryInd?.params && (
        <div className="space-y-3 pt-2 border-t border-white/10">
          <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">Introspection Parameters</span>
          {currentRegistryInd.params.map((p: any) => (
            <div key={p.name}>
              <label className="block text-xs font-medium text-slate-300 mb-1">{p.name}</label>
              <input
                type={p.type === 'int' || p.type === 'float' ? 'number' : 'text'}
                value={data[p.name] ?? p.default ?? ''}
                onChange={(e) => onChange(p.name, p.type === 'int' ? Number(e.target.value) : e.target.value)}
                className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// 3. SignalNodeInspector
// ---------------------------------------------------------------------------
const SignalNodeInspector: React.FC<{ data: SignalNodeData; onChange: (k: string, v: any) => void }> = ({ data, onChange }) => (
  <div className="space-y-4">
    <div>
      <label className="block text-xs font-medium text-slate-300 mb-1">Logic Operator Type</label>
      <select
        value={data.signalType ?? 'sma_crossover'}
        onChange={(e) => onChange('signalType', e.target.value)}
        className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
      >
        <option value="sma_crossover">Crossover (Signal Crossover)</option>
        <option value="ranking">Ticker Ranking / Sorting</option>
        <option value="mapping">Threshold Mapping</option>
        <option value="distribution">Allocation Weighting</option>
      </select>
    </div>
  </div>
)

// ---------------------------------------------------------------------------
// 4. PortfolioNodeInspector
// ---------------------------------------------------------------------------
const PortfolioNodeInspector: React.FC<{ data: PortfolioNodeData; onChange: (k: string, v: any) => void }> = ({ data, onChange }) => (
  <div className="space-y-4">
    <div>
      <label className="block text-xs font-medium text-slate-300 mb-1">Initial Capital ($)</label>
      <input
        type="number"
        value={data.init_cash ?? 10000}
        onChange={(e) => onChange('init_cash', Number(e.target.value))}
        className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
      />
    </div>

    <div className="grid grid-cols-2 gap-3">
      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1">Fees (%)</label>
        <input
          type="number"
          step="0.01"
          value={data.fees ? Number((data.fees * 100).toFixed(3)) : 0.1}
          onChange={(e) => onChange('fees', Number(e.target.value) / 100)}
          className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1">Slippage (%)</label>
        <input
          type="number"
          step="0.01"
          value={data.slippage ? Number((data.slippage * 100).toFixed(3)) : 0.1}
          onChange={(e) => onChange('slippage', Number(e.target.value) / 100)}
          className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
        />
      </div>
    </div>

    <div className="pt-3 border-t border-white/10 space-y-3">
      <h4 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">Risk Management (SL / TP)</h4>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Stop Loss (%)</label>
          <input
            type="number"
            step="0.1"
            value={data.sl_stop ? Number((data.sl_stop * 100).toFixed(2)) : ''}
            onChange={(e) => onChange('sl_stop', e.target.value ? Number(e.target.value) / 100 : undefined)}
            placeholder="e.g. 2 (2%)"
            className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Take Profit (%)</label>
          <input
            type="number"
            step="0.1"
            value={data.tp_stop ? Number((data.tp_stop * 100).toFixed(2)) : ''}
            onChange={(e) => onChange('tp_stop', e.target.value ? Number(e.target.value) / 100 : undefined)}
            placeholder="e.g. 5 (5%)"
            className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Position Size</label>
          <input
            type="number"
            value={data.size ?? ''}
            onChange={(e) => onChange('size', e.target.value ? Number(e.target.value) : undefined)}
            placeholder="Default (100%)"
            className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Size Type</label>
          <select
            value={data.size_type ?? 'percent'}
            onChange={(e) => onChange('size_type', e.target.value)}
            className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
          >
            <option value="percent">Percent</option>
            <option value="amount">Amount (Shares)</option>
            <option value="value">Value ($)</option>
          </select>
        </div>
      </div>
    </div>
  </div>
)

// ---------------------------------------------------------------------------
// 5. OptimizerNodeInspector
// ---------------------------------------------------------------------------
const OptimizerNodeInspector: React.FC<{
  nodeId: string
  data: OptimizerNodeData
  nodes: any[]
  edges: any[]
  onChange: (k: string, v: any) => void
  updateNodeData: (id: string, data: any) => void
}> = ({ nodeId, data, nodes, edges, onChange, updateNodeData }) => {

  const getConnectedIndicator = () => {
    const edge = edges.find((e) => e.target === nodeId)
    if (!edge) return null
    return nodes.find((n) => n.id === edge.source)
  }

  const handleSyncBounds = () => {
    const indicator = getConnectedIndicator()
    if (!indicator || indicator.type !== 'indicatorNode') {
      showToast.warning('Missing connection', 'Connect an Indicator node to the Optimizer node.')
      return
    }
    const iData = indicator.data as IndicatorNodeData
    let newBounds: Record<string, ParameterBound> = {}

    if (iData.indicatorType === 'macd') {
      newBounds = {
        sma_fast: { min: 5, max: 20, type: 'int' },
        sma_slow: { min: 20, max: 40, type: 'int' },
        macd_signal: { min: 5, max: 15, type: 'int' },
      }
    } else {
      newBounds = {
        sma_fast: { min: 5, max: 20, type: 'int' },
        sma_slow: { min: 25, max: 50, type: 'int' },
      }
    }
    onChange('paramBounds', newBounds)
    showToast.success('Synchronized', 'Parameter ranges synchronized with indicator.')
  }

  const handleApplyToIndicator = () => {
    if (!data.bestParameters) return
    const indicator = getConnectedIndicator()
    if (!indicator || indicator.type !== 'indicatorNode') {
      showToast.warning('Missing connection', 'Connect an Indicator node to the Optimizer node.')
      return
    }

    const mappedParams: Record<string, any> = {}
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
    showToast.success('Applied', 'Best parameters saved to Indicator node!')
  }

  const updateBound = (key: string, bound: Partial<ParameterBound>) => {
    const currentBounds = data.paramBounds ?? {}
    const updated = {
      ...currentBounds,
      [key]: { ...(currentBounds[key] ?? { min: 5, max: 20, type: 'int' }), ...bound },
    }
    onChange('paramBounds', updated)
  }

  const bounds = data.paramBounds ?? {
    sma_fast: { min: 5, max: 20, type: 'int' },
    sma_slow: { min: 25, max: 50, type: 'int' },
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1">Optimization Target Metric</label>
        <select
          value={data.metric ?? 'Total Return [%]'}
          onChange={(e) => onChange('metric', e.target.value)}
          className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
        >
          <option value="Total Return [%]">Total Return [%]</option>
          <option value="Sharpe Ratio">Sharpe Ratio</option>
          <option value="Max Drawdown [%]">Max Drawdown [%]</option>
          <option value="Win Rate [%]">Win Rate [%]</option>
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1">Optuna Trials (n_trials)</label>
        <input
          type="number"
          min={5}
          max={500}
          value={data.nTrials ?? 20}
          onChange={(e) => onChange('nTrials', Number(e.target.value))}
          className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
        />
      </div>

      <div className="pt-3 border-t border-white/10 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-pink-400 uppercase tracking-wider">Parameter Bounds</span>
          <button
            onClick={handleSyncBounds}
            className="flex items-center gap-1 text-[11px] font-medium bg-[#1c2130] hover:bg-[#262c3e] border border-pink-500/30 text-pink-300 px-2 py-1 rounded transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Sync</span>
          </button>
        </div>

        <div className="space-y-2">
          {Object.entries(bounds).map(([key, bound]) => (
            <div key={key} className="bg-[#0b0d14] p-3 rounded-lg border border-white/5 space-y-2">
              <span className="text-xs font-mono font-bold text-slate-200 uppercase">{key}</span>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[10px] text-slate-400 mb-0.5">Min</label>
                  <input
                    type="number"
                    value={bound.min}
                    onChange={(e) => updateBound(key, { min: Number(e.target.value) })}
                    className="w-full bg-[#131722] border border-white/10 rounded px-2 py-1 text-xs text-slate-100 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-slate-400 mb-0.5">Max</label>
                  <input
                    type="number"
                    value={bound.max}
                    onChange={(e) => updateBound(key, { max: Number(e.target.value) })}
                    className="w-full bg-[#131722] border border-white/10 rounded px-2 py-1 text-xs text-slate-100 font-mono"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {data.bestParameters && (
        <div className="p-3 bg-pink-950/30 border border-pink-500/30 rounded-lg space-y-2 mt-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-pink-300">Best Result:</span>
            <button
              onClick={handleApplyToIndicator}
              className="flex items-center gap-1 px-2 py-1 text-[11px] font-semibold bg-emerald-600 hover:bg-emerald-500 text-white rounded transition-colors"
            >
              <CheckCircle className="w-3 h-3" />
              <span>Apply</span>
            </button>
          </div>
          <div className="text-xs font-mono text-slate-300 space-y-1">
            {Object.entries(data.bestParameters).map(([k, v]) => (
              <div key={k}>{k}: <span className="text-pink-400 font-bold">{String(v)}</span></div>
            ))}
            {data.bestValue != null && (
              <div className="pt-1 border-t border-pink-500/20 text-emerald-400">Score: {data.bestValue.toFixed(4)}</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// 6. WfoNodeInspector
// ---------------------------------------------------------------------------
const WfoNodeInspector: React.FC<{ data: WfoNodeData; onChange: (k: string, v: any) => void }> = ({ data, onChange }) => (
  <div className="space-y-4">
    <div>
      <label className="block text-xs font-medium text-slate-300 mb-1">Walk-Forward Mode</label>
      <select
        value={(data as any).mode ?? 'rolling'}
        onChange={(e) => onChange('mode', e.target.value)}
        className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
      >
        <option value="rolling">Rolling (Fixed Sliding Window)</option>
        <option value="anchored">Anchored (Expanding Window)</option>
      </select>
    </div>

    <div>
      <label className="block text-xs font-medium text-slate-300 mb-1">In-Sample Window Size</label>
      <input
        type="text"
        value={data.windowSize ?? '365d'}
        onChange={(e) => onChange('windowSize', e.target.value)}
        className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
        placeholder="e.g. 365d"
      />
    </div>

    <div>
      <label className="block text-xs font-medium text-slate-300 mb-1">Step Size</label>
      <input
        type="text"
        value={data.stepSize ?? '90d'}
        onChange={(e) => onChange('stepSize', e.target.value)}
        className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 font-mono"
        placeholder="e.g. 90d"
      />
    </div>

    <div>
      <label className="block text-xs font-medium text-slate-300 mb-1">Evaluation Metric</label>
      <select
        value={(data as any).metric ?? 'Total Return [%]'}
        onChange={(e) => onChange('metric', e.target.value)}
        className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
      >
        <option value="Total Return [%]">Total Return [%]</option>
        <option value="Sharpe Ratio">Sharpe Ratio</option>
        <option value="Max Drawdown [%]">Max Drawdown [%]</option>
      </select>
    </div>
  </div>
)
