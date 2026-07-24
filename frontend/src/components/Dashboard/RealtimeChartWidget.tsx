console.log("RealtimeChartWidget loaded");
import { useEffect, useState, useMemo } from 'react'
import Plot from '../../components/PlotlyPlot'
import { request } from '../../services/api'
import { Loader2, Settings, Plus, X } from 'lucide-react'

interface Indicator {
  id: string
  type: 'SMA' | 'EMA' | 'RSI' | 'MACD'
  period: number
}

interface ChartConfig {
  symbols: string[]
  activeSymbol: string
  interval: string
  indicators: Indicator[]
}

const DEFAULT_CONFIG: ChartConfig = {
  symbols: ['BTC-USD', 'ETH-USD', 'SPY', 'QQQ', 'AAPL', 'TSLA'],
  activeSymbol: 'BTC-USD',
  interval: '5m',
  indicators: []
}

export function RealtimeChartWidget() {
  const [config, setConfig] = useState<ChartConfig>(() => {
    try {
      const saved = localStorage.getItem('blockbt_chart_config')
      if (saved) {
        const parsed = JSON.parse(saved)
        return {
          ...DEFAULT_CONFIG,
          ...parsed,
          symbols: parsed.symbols || DEFAULT_CONFIG.symbols,
          indicators: parsed.indicators || DEFAULT_CONFIG.indicators
        }
      }
    } catch (e) {
      console.error('Failed to parse config from localStorage', e)
    }
    return DEFAULT_CONFIG
  })
  
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showSettings, setShowSettings] = useState(false)
  const [newSymbol, setNewSymbol] = useState('')

  // Settings form states
  const [newIndType, setNewIndType] = useState<'SMA'|'EMA'|'RSI'|'MACD'>('SMA')
  const [newIndPeriod, setNewIndPeriod] = useState<number>(14)

  useEffect(() => {
    localStorage.setItem('blockbt_chart_config', JSON.stringify(config))
  }, [config])

  const fetchData = async () => {
    try {
      const inds = encodeURIComponent(JSON.stringify(config.indicators))
      const res = await request<any>(`/api/data/realtime?symbol=${config.activeSymbol}&interval=${config.interval}&indicators=${inds}`)
      setData(res.data || [])
    } catch (e) {
      console.error('Failed to fetch realtime data', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setLoading(true)
    fetchData()
    
    const timer = setInterval(() => {
      fetchData()
    }, 60000)
    
    return () => clearInterval(timer)
  }, [config.activeSymbol, config.interval, config.indicators])

  const handleAddSymbol = (e: React.FormEvent) => {
    e.preventDefault()
    if (newSymbol.trim() && !config.symbols.includes(newSymbol.trim().toUpperCase())) {
      setConfig(prev => ({
        ...prev,
        symbols: [...prev.symbols, newSymbol.trim().toUpperCase()],
        activeSymbol: newSymbol.trim().toUpperCase()
      }))
      setNewSymbol('')
    }
  }

  const handleRemoveSymbol = (sym: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setConfig(prev => {
      const newSymbols = prev.symbols.filter(s => s !== sym)
      return {
        ...prev,
        symbols: newSymbols,
        activeSymbol: prev.activeSymbol === sym ? (newSymbols[0] || '') : prev.activeSymbol
      }
    })
  }

  const handleAddIndicator = () => {
    setConfig(prev => ({
      ...prev,
      indicators: [...prev.indicators, { id: Math.random().toString(36).substring(7), type: newIndType, period: newIndPeriod }]
    }))
  }

  const handleRemoveIndicator = (id: string) => {
    setConfig(prev => ({
      ...prev,
      indicators: prev.indicators.filter(i => i.id !== id)
    }))
  }

  const chartData = useMemo(() => {
    if (!data.length) return []
    
    const x = data.map(d => d.date)
    const traces: any[] = [
      {
        x,
        open: data.map(d => d.open),
        high: data.map(d => d.high),
        low: data.map(d => d.low),
        close: data.map(d => d.close),
        type: 'candlestick',
        name: config.activeSymbol,
        increasing: { line: { color: '#26a69a' } },
        decreasing: { line: { color: '#ef5350' } }
      }
    ]

    // Overlay indicators (SMA, EMA)
    const colors = ['#f59e0b', '#3b82f6', '#ec4899', '#8b5cf6']
    let colorIdx = 0
    config.indicators.forEach(ind => {
      if (ind.type === 'SMA' || ind.type === 'EMA') {
        const colName = `${ind.type}_${ind.period}`
        if (data[0] && colName in data[0]) {
          traces.push({
            x,
            y: data.map(d => d[colName]),
            type: 'scatter',
            mode: 'lines',
            name: `${ind.type}(${ind.period})`,
            line: { color: colors[colorIdx % colors.length], width: 1.5 }
          })
          colorIdx++
        }
      }
    })

    return traces
  }, [data, config])

  const layout = {
    title: false,
    dragmode: 'zoom' as const,
    margin: { l: 50, r: 20, t: 20, b: 40 },
    showlegend: true,
    legend: { x: 0, y: 1, bgcolor: 'rgba(0,0,0,0)' },
    xaxis: {
      rangeslider: { visible: false },
      type: 'date' as const,
      gridcolor: '#2b3139',
      tickfont: { color: '#8b949e' }
    },
    yaxis: {
      autorange: true,
      gridcolor: '#2b3139',
      tickfont: { color: '#8b949e' }
    },
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { family: 'Inter, sans-serif', color: '#8b949e' }
  }

  return (
    <div className="w-full h-full flex flex-col relative bg-surface-container">
      <div className="relative flex items-center justify-between p-4 border-b border-outline-variant/20 bg-surface-container-low shrink-0 z-10">
        <div className="flex items-center gap-4">
          <h3 className="font-headline font-semibold text-on-surface flex items-center gap-2">
            Market Data
            {loading && <Loader2 className="w-4 h-4 animate-spin text-primary" />}
          </h3>
          
          <div className="flex bg-surface-container-high rounded-md border border-outline-variant/30 overflow-hidden">
            <select 
              value={config.activeSymbol}
              onChange={(e) => setConfig({...config, activeSymbol: e.target.value})}
              className="bg-transparent text-on-surface text-xs font-semibold px-3 py-1.5 focus:outline-none cursor-pointer border-r border-outline-variant/30 appearance-none"
            >
              {config.symbols.map(sym => (
                <option key={sym} value={sym}>{sym}</option>
              ))}
            </select>
            <select 
              value={config.interval}
              onChange={(e) => setConfig({...config, interval: e.target.value})}
              className="bg-transparent text-on-surface-variant text-xs px-3 py-1.5 focus:outline-none cursor-pointer appearance-none"
            >
              <option value="1m">1m</option>
              <option value="5m">5m</option>
              <option value="15m">15m</option>
              <option value="1h">1h</option>
              <option value="1d">1d</option>
            </select>
          </div>
        </div>
        
        <button 
          onClick={() => setShowSettings(!showSettings)}
          className={`relative p-2 rounded-md transition-colors z-50 ${showSettings ? 'bg-primary/20 text-primary' : 'bg-surface-container-high text-on-surface-variant hover:text-on-surface'}`}
        >
          <Settings className="w-4 h-4 relative z-50" />
        </button>
      </div>

      {showSettings && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-md bg-surface-container-highest border border-outline-variant/30 rounded-lg shadow-2xl p-6 font-body text-sm flex flex-col max-h-full">
            <div className="flex items-center justify-between mb-4 shrink-0">
              <h4 className="text-base font-semibold text-on-surface">Chart Settings</h4>
              <button 
                onClick={() => setShowSettings(false)}
                className="p-1 hover:bg-surface-variant rounded text-on-surface-variant hover:text-on-surface transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="overflow-y-auto space-y-4 pr-2">
            
            {/* Symbols manager */}
            <div>
              <h4 className="font-semibold text-on-surface mb-2 text-xs uppercase tracking-wider">Symbols</h4>
              <form onSubmit={handleAddSymbol} className="flex gap-2 mb-2">
                <input 
                  type="text" 
                  value={newSymbol} 
                  onChange={e => setNewSymbol(e.target.value)} 
                  placeholder="Add symbol (e.g. MSFT)" 
                  className="flex-1 bg-surface-container border border-outline-variant/40 rounded px-2 py-1 text-xs text-on-surface focus:border-primary focus:outline-none uppercase"
                />
                <button type="submit" className="bg-primary/20 text-primary hover:bg-primary/30 p-1 rounded transition-colors">
                  <Plus className="w-4 h-4" />
                </button>
              </form>
              <div className="flex flex-wrap gap-1">
                {config.symbols.map(sym => (
                  <span key={sym} className="inline-flex items-center gap-1 bg-surface-container-low border border-outline-variant/20 rounded px-2 py-0.5 text-[10px] text-on-surface">
                    {sym}
                    {config.symbols.length > 1 && (
                      <X className="w-3 h-3 cursor-pointer hover:text-error" onClick={(e) => handleRemoveSymbol(sym, e)} />
                    )}
                  </span>
                ))}
              </div>
            </div>

            <div className="border-t border-outline-variant/20 my-2"></div>

            {/* Indicators manager */}
            <div>
              <h4 className="font-semibold text-on-surface mb-2 text-xs uppercase tracking-wider">Indicators</h4>
              <div className="flex gap-2 mb-2">
                <select 
                  value={newIndType} 
                  onChange={e => setNewIndType(e.target.value as any)}
                  className="bg-surface-container border border-outline-variant/40 rounded px-2 py-1 text-xs text-on-surface focus:border-primary focus:outline-none"
                >
                  <option value="SMA">SMA</option>
                  <option value="EMA">EMA</option>
                  {/* RSI i MACD wyłączone graficznie dla prostej integracji na głównym wykresie OHLC */}
                </select>
                <input 
                  type="number" 
                  value={newIndPeriod} 
                  onChange={e => setNewIndPeriod(parseInt(e.target.value) || 1)} 
                  className="w-16 bg-surface-container border border-outline-variant/40 rounded px-2 py-1 text-xs text-on-surface focus:border-primary focus:outline-none"
                  min="1"
                />
                <button onClick={handleAddIndicator} className="bg-primary/20 text-primary hover:bg-primary/30 p-1 rounded transition-colors flex-1 flex justify-center">
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              <div className="flex flex-col gap-1">
                {config.indicators.length === 0 && <span className="text-xs text-on-surface-variant">No indicators added.</span>}
                {config.indicators.map(ind => (
                  <div key={ind.id} className="flex items-center justify-between bg-surface-container-low border border-outline-variant/20 rounded px-2 py-1 text-xs text-on-surface">
                    <span>{ind.type} ({ind.period})</span>
                    <X className="w-3.5 h-3.5 cursor-pointer text-on-surface-variant hover:text-error" onClick={() => handleRemoveIndicator(ind.id)} />
                  </div>
                ))}
              </div>
            </div>

            </div>
          </div>
        </div>
      )}
      
      <div className="flex-1 w-full relative min-h-0">
        {data.length > 0 ? (
          <div className="absolute inset-0">
            <Plot
              data={chartData}
              layout={layout}
              useResizeHandler={true}
              style={{ width: '100%', height: '100%' }}
              config={{ responsive: true, displayModeBar: false }}
            />
          </div>
        ) : (
          !loading && <div className="flex items-center justify-center h-full text-on-surface-variant font-label text-sm">No data available for {config.activeSymbol}</div>
        )}
      </div>
    </div>
  )
}
