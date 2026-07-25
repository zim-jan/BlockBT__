import { useQuery } from '@tanstack/react-query'
import { request } from '../../services/api'
import { Loader2 } from 'lucide-react'

interface HistoryWidgetProps {
  onJobSelect: (jobId: number, strategyId: number) => void
}

/** Faza 10: multi-symbol zwraca listę tickerów zamiast stringa. */
function formatSymbol(symbol: unknown): string {
  if (Array.isArray(symbol)) return symbol.join(', ')
  return (symbol as string) || '-'
}

/**
 * Zwraca stopy zwrotu joba. Multi-symbol nie ma `metrics.total_return_pct` —
 * metryki są per ticker (`{ AAPL: { 'Total Return [%]': ... }, ... }`), więc
 * wyciągamy je osobno, zachowując kolejność z kolumny Symbol.
 */
function jobReturns(job: any): { label: string; value: number }[] {
  const metrics = job?.metrics
  if (!metrics) return []

  if (job.is_multi_symbol) {
    return Object.entries(metrics)
      .map(([ticker, m]: [string, any]) => ({ label: ticker, value: m?.['Total Return [%]'] }))
      .filter((r) => typeof r.value === 'number')
  }

  return typeof metrics.total_return_pct === 'number'
    ? [{ label: '', value: metrics.total_return_pct }]
    : []
}

export function HistoryWidget({ onJobSelect }: HistoryWidgetProps) {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ['backtest_jobs'],
    queryFn: async () => {
      const res = await request<any>('/api/backtest/')
      return res.data
    },
    refetchInterval: 15000 // auto-refresh status every 15s
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-primary p-12">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-outline-variant/30">
        <h3 className="font-headline font-semibold text-on-surface">Execution History</h3>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-outline-variant/30 text-on-surface-variant font-label text-xs uppercase">
              <th className="pb-3 font-medium px-2">Job ID</th>
              <th className="pb-3 font-medium px-2">Status</th>
              <th className="pb-3 font-medium px-2">Symbol</th>
              <th className="pb-3 font-medium px-2">Engine</th>
              <th className="pb-3 font-medium px-2">Return</th>
              <th className="pb-3 font-medium px-2">Date</th>
              <th className="pb-3 font-medium px-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs?.map((job: any) => (
              <tr 
                key={job.id} 
                className="border-b border-outline-variant/10 hover:bg-surface-container-high transition-colors group cursor-pointer"
                onClick={() => onJobSelect(job.id, job.strategy_id)}
              >
                <td className="py-3 px-2 text-sm text-on-surface">#{job.id}</td>
                <td className="py-3 px-2">
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    job.status === 'COMPLETED' ? 'bg-green-500/10 text-green-400' :
                    job.status === 'FAILED' ? 'bg-error/10 text-error' :
                    'bg-yellow-500/10 text-yellow-400'
                  }`}>
                    {job.status}
                  </span>
                </td>
                <td className="py-3 px-2 text-sm text-on-surface">{formatSymbol(job.symbol)}</td>
                <td className="py-3 px-2 text-xs text-on-surface-variant">{job.parameters?.engine_name || 'vectorbt-opensource'}</td>
                <td className="py-3 px-2 text-sm font-medium">
                  {(() => {
                    const returns = jobReturns(job)
                    if (returns.length === 0) return '-'
                    return (
                      <span
                        className="inline-flex items-center gap-1"
                        title={returns.map((r) => `${r.label ? r.label + ' ' : ''}${r.value.toFixed(2)}%`).join(', ')}
                      >
                        {returns.map((r, i) => (
                          <span key={r.label || i}>
                            {i > 0 && <span className="text-on-surface-variant mr-1">/</span>}
                            <span className={r.value >= 0 ? 'text-green-400' : 'text-error'}>
                              {r.value.toFixed(2)}%
                            </span>
                          </span>
                        ))}
                      </span>
                    )
                  })()}
                </td>
                <td className="py-3 px-2 text-xs text-on-surface-variant">
                  {new Date(job.created_at).toLocaleString()}
                </td>
                <td className="py-3 px-2 text-right">
                  {/* Jawny przycisk „Open" zamiast ikony ▶ — ta myliła się z uruchomieniem
                      backtestu, a klik i tak tylko otwiera szczegóły (uwaga z testów S6.8). */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onJobSelect(job.id, job.strategy_id)
                    }}
                    className="text-xs font-label px-2.5 py-1 rounded bg-primary/20 text-primary hover:bg-primary/30 transition-colors"
                    title="Open job details"
                  >
                    Open
                  </button>
                </td>
              </tr>
            ))}
            
            {/* Nawiasy są istotne: bez nich wyrażenie parsuje się jako
                `!jobs || (jobs.length === 0 && <tr>)`, więc przy błędzie zapytania
                (`jobs === undefined`) całość daje `true`, które React renderuje jako nic —
                tabela zostaje pusta bez żadnego komunikatu (test manualny S10.3b). */}
            {(!jobs || jobs.length === 0) && (
              <tr>
                <td colSpan={7} className="py-8 text-center text-sm text-on-surface-variant">
                  No backtest jobs found. Run a backtest in the Visual Builder first.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
