import React, { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { useWorkflowStore } from '../store/workflowStore'
import { Bot, X, BarChart2, Loader2 } from 'lucide-react'
import Plot from './PlotlyPlot'
import { useChatStore } from '../store/chatStore'
import type { PortfolioNodeData, MultiBacktestResult } from '../types/types'

function parseEquityCurve(rawCurve: any): { x: string[]; y: number[] } | null {
  if (!rawCurve) return null

  // Format A: { dates: [...], equity: [...] } or { dates: [...], values: [...] }
  if (typeof rawCurve === 'object' && !Array.isArray(rawCurve)) {
    if (Array.isArray(rawCurve.dates) && (Array.isArray(rawCurve.equity) || Array.isArray(rawCurve.values))) {
      return {
        x: rawCurve.dates.map(String),
        y: (rawCurve.equity || rawCurve.values).map(Number),
      }
    }
  }

  // Format B: Array of objects [{ date: "...", value: ... }, ...]
  if (Array.isArray(rawCurve)) {
    const x: string[] = []
    const y: number[] = []
    for (const pt of rawCurve) {
      if (typeof pt === 'object' && pt !== null) {
        const dateVal = pt.date ?? pt.x ?? pt.timestamp
        const numVal = pt.value ?? pt.y ?? pt.equity ?? pt.close
        if (dateVal != null && numVal != null) {
          x.push(String(dateVal))
          y.push(Number(numVal))
        }
      } else if (typeof pt === 'number') {
        y.push(pt)
      }
    }
    if (y.length > 0) {
      if (x.length < y.length) {
        for (let i = x.length; i < y.length; i++) x.push(String(i))
      }
      return { x, y }
    }
  }

  return null
}

export const ResultsOverlay: React.FC = () => {
  const nodes = useWorkflowStore((s) => s.nodes)
  const activeJobId = useWorkflowStore((s) => s.activeJobId)
  const isResultsOpen = useWorkflowStore((s) => s.isResultsOpen)
  const setIsResultsOpen = useWorkflowStore((s) => s.setIsResultsOpen)
  const openChat = useChatStore((s) => s.openChat)

  const [activeTab, setActiveTab] = useState<'overview' | 'chart' | 'tearsheet'>('overview')
  const [tearsheetHtml, setTearsheetHtml] = useState<string | null>(null)
  const [isTearsheetLoading, setIsTearsheetLoading] = useState(false)

  const portfolioNode = nodes.find((n) => n.type === 'portfolioNode')
  const pData = (portfolioNode?.data as PortfolioNodeData) ?? {}
  const { metrics, jobStatus, jobId } = pData
  const hasValidMetrics = !!metrics && (jobStatus === 'COMPLETED' || ('total_return_pct' in metrics && !!metrics.total_return_pct))

  const effectiveJobId = jobId ?? activeJobId

  const isMulti = !!metrics && (metrics as MultiBacktestResult).is_multi_symbol === true
  const multiData = isMulti ? (metrics as MultiBacktestResult) : null

  // Fetch tearsheet HTML when tearsheet tab is active
  useEffect(() => {
    if (activeTab === 'tearsheet' && effectiveJobId && isResultsOpen) {
      setIsTearsheetLoading(true)
      fetch(`/api/results/${effectiveJobId}/tearsheet`)
        .then((res) => res.json())
        .then((resData) => {
          if (resData?.data?.html) {
            setTearsheetHtml(resData.data.html)
          } else if (typeof resData?.data === 'string') {
            setTearsheetHtml(resData.data)
          } else {
            setTearsheetHtml('<p style="color:#9ca3af;padding:2rem;font-family:sans-serif;">Brak danych HTML z raportu QuantStats.</p>')
          }
        })
        .catch((err) => {
          console.error('[ResultsOverlay] Failed to load tearsheet:', err)
          setTearsheetHtml(`<p style="color:#ef4444;padding:2rem;font-family:sans-serif;">Błąd pobierania raportu: ${err.message || 'Nieznany błąd'}</p>`)
        })
        .finally(() => setIsTearsheetLoading(false))
    }
  }, [activeTab, effectiveJobId, isResultsOpen])

  if (!isResultsOpen) return null

  // Build equity curve traces using robust parser
  let traces: any[] = []
  if (hasValidMetrics) {
    if (!isMulti && metrics && 'equity_curve' in metrics && metrics.equity_curve) {
      const parsed = parseEquityCurve(metrics.equity_curve)
      if (parsed) {
        traces.push({
          x: parsed.x,
          y: parsed.y,
          type: 'scatter',
          mode: 'lines',
          name: 'Equity ($)',
          line: { color: '#10b981', width: 2 },
        })
      }
    } else if (isMulti && multiData?.equity_curve) {
      Object.entries(multiData.equity_curve).forEach(([symbol, rawCurve]: [string, any]) => {
        const parsed = parseEquityCurve(rawCurve)
        if (parsed) {
          traces.push({
            x: parsed.x,
            y: parsed.y,
            type: 'scatter',
            mode: 'lines',
            name: symbol,
            line: { width: 1.5 },
          })
        }
      })
    }
  }

  return createPortal(
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(11, 13, 20, 0.96)',
        backdropFilter: 'blur(8px)',
        zIndex: 100000,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Overlay Header Bar */}
      <div className="flex items-center justify-between px-6 h-16 border-b border-white/10 bg-[#1c2130] select-none">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-lg font-semibold text-slate-100">
            <span>📊 Wyniki Symulacji</span>
          </div>

          {hasValidMetrics && (
            <div className="flex items-center gap-1 bg-[#0b0d14] p-1 rounded-lg border border-white/10">
              <button
                onClick={() => setActiveTab('overview')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeTab === 'overview' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Przegląd
              </button>
              <button
                onClick={() => setActiveTab('chart')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeTab === 'chart' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Wykres Equity
              </button>
              <button
                onClick={() => setActiveTab('tearsheet')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeTab === 'tearsheet' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                QuantStats Tearsheet
              </button>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          {effectiveJobId && (
            <button
              onClick={() => openChat(effectiveJobId)}
              className="flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 hover:bg-indigo-600/30 transition-colors"
            >
              <Bot className="w-3.5 h-3.5" />
              <span>Czatuj z AI Analyst</span>
            </button>
          )}

          <button
            onClick={() => setIsResultsOpen(false)}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Overlay Content */}
      <div className="flex-1 overflow-y-auto p-8 text-slate-100">
        {!hasValidMetrics ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-slate-400 gap-4">
            <div className="p-4 bg-[#1c2130] rounded-full border border-white/10">
              <BarChart2 className="w-12 h-12 text-indigo-400" />
            </div>
            <h3 className="text-xl font-bold text-slate-200">Brak Dostępnych Wyników Symulacji</h3>
            <p className="text-sm text-slate-400 max-w-md text-center">
              Uruchom symulację backtestu na kanwie, aby wygenerować wykresy equity, wskaźniki Sharpe/Drawdown oraz raporty QuantStats.
            </p>
          </div>
        ) : (
          <>
            {activeTab === 'overview' && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-[#1c2130] p-4 rounded-xl border border-white/10">
                  <span className="text-xs text-slate-400 font-medium uppercase">Total Return</span>
                  <p className="text-2xl font-bold text-emerald-400 mt-1">
                    {metrics && 'total_return_pct' in metrics && metrics.total_return_pct != null
                      ? `${Number(metrics.total_return_pct).toFixed(2)}%`
                      : '—'}
                  </p>
                </div>

                <div className="bg-[#1c2130] p-4 rounded-xl border border-white/10">
                  <span className="text-xs text-slate-400 font-medium uppercase">Sharpe Ratio</span>
                  <p className="text-2xl font-bold text-indigo-400 mt-1">
                    {metrics && 'sharpe_ratio' in metrics && metrics.sharpe_ratio != null
                      ? Number(metrics.sharpe_ratio).toFixed(2)
                      : '—'}
                  </p>
                </div>

                <div className="bg-[#1c2130] p-4 rounded-xl border border-white/10">
                  <span className="text-xs text-slate-400 font-medium uppercase">Max Drawdown</span>
                  <p className="text-2xl font-bold text-amber-400 mt-1">
                    {metrics && 'max_drawdown_pct' in metrics && metrics.max_drawdown_pct != null
                      ? `${Number(metrics.max_drawdown_pct).toFixed(2)}%`
                      : '—'}
                  </p>
                </div>

                <div className="bg-[#1c2130] p-4 rounded-xl border border-white/10">
                  <span className="text-xs text-slate-400 font-medium uppercase">Final Capital</span>
                  <p className="text-2xl font-bold text-slate-100 mt-1 font-mono">
                    {metrics && 'final_capital' in metrics && metrics.final_capital != null
                      ? `$${Number(metrics.final_capital).toLocaleString('en-US', { maximumFractionDigits: 0 })}`
                      : '—'}
                  </p>
                </div>
              </div>
            )}

            {activeTab === 'chart' && (
              <div className="w-full h-full min-h-[450px] bg-[#0b0d14] p-4 rounded-xl border border-white/10 flex flex-col">
                {traces.length > 0 ? (
                  <Plot
                    data={traces}
                    layout={{
                      autosize: true,
                      margin: { l: 50, r: 30, b: 50, t: 30 },
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      font: { color: '#9ca3af' },
                      xaxis: { gridcolor: 'rgba(255,255,255,0.05)', title: { text: 'Data' } },
                      yaxis: { gridcolor: 'rgba(255,255,255,0.05)', title: { text: 'Kapitał ($)' } },
                    }}
                    config={{ responsive: true }}
                    style={{ width: '100%', height: '100%', minHeight: '400px' }}
                    useResizeHandler
                  />
                ) : (
                  <div className="flex items-center justify-center h-full min-h-[400px] text-slate-400 text-sm">
                    Brak skompletowanych punktów wykresu equity.
                  </div>
                )}
              </div>
            )}

            {activeTab === 'tearsheet' && (
              <div className="w-full h-full min-h-[550px] rounded-xl overflow-hidden border border-white/10 bg-white relative">
                {isTearsheetLoading ? (
                  <div className="flex items-center justify-center h-[550px] bg-[#0b0d14] text-slate-300 gap-2">
                    <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
                    <span>Ładowanie raportu QuantStats...</span>
                  </div>
                ) : (
                  <iframe
                    srcDoc={tearsheetHtml ?? ''}
                    title="QuantStats Tearsheet"
                    className="w-full h-full min-h-[550px] border-0"
                  />
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>,
    document.body
  )
}


