import { useQuery } from '@tanstack/react-query'
import { request } from '../../services/api'
import { Loader2, PlayCircle } from 'lucide-react'

interface HistoryWidgetProps {
  onJobSelect: (jobId: number, strategyId: number) => void
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
                <td className="py-3 px-2 text-sm text-on-surface">{job.symbol || '-'}</td>
                <td className="py-3 px-2 text-xs text-on-surface-variant">{job.parameters?.engine_name || 'vectorbt-opensource'}</td>
                <td className="py-3 px-2 text-sm font-medium">
                  {job.metrics?.total_return_pct !== undefined ? (
                    <span className={job.metrics.total_return_pct >= 0 ? 'text-green-400' : 'text-error'}>
                      {job.metrics.total_return_pct.toFixed(2)}%
                    </span>
                  ) : '-'}
                </td>
                <td className="py-3 px-2 text-xs text-on-surface-variant">
                  {new Date(job.created_at).toLocaleString()}
                </td>
                <td className="py-3 px-2 text-right">
                  <button 
                    className="text-primary hover:text-primary/80 transition-colors p-1"
                    title="View Details"
                  >
                    <PlayCircle className="w-5 h-5" />
                  </button>
                </td>
              </tr>
            ))}
            
            {!jobs || jobs.length === 0 && (
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
