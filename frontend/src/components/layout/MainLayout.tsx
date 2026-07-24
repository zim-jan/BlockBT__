import type {ReactNode} from 'react'
import {Sidebar} from './Sidebar'
import {MetricCard} from '../ui/MetricCard'
import {Activity, Minus, TrendingDown, TrendingUp} from 'lucide-react'
import {useWorkflowStore} from '../../store/workflowStore'
import type {PortfolioNodeData} from '../../types/types'
import {useQuery} from '@tanstack/react-query'
import {InspectorPanel} from '../InspectorPanel'
import {ChatPanel} from '../../features/ai_chat/ChatPanel'
import {useChatStore} from '../../store/chatStore'

interface HealthResponse {
  status: string
}

interface MainLayoutProps {
  children: ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const { isOpen: isChatOpen, jobId, closeChat } = useChatStore()
  const nodes = useWorkflowStore((state) => state.nodes)
  const portfolioNode = nodes.find((n) => n.type === 'portfolioNode')
  const rawMetrics = (portfolioNode?.data as PortfolioNodeData)?.metrics
  // Faza 10: sidebar podsumowanie pokazujemy tylko dla wyniku single-symbol (multi ma metryki per-ticker)
  const metrics = rawMetrics && !('is_multi_symbol' in rawMetrics) ? rawMetrics : null

  const totalReturn = metrics?.total_return_pct ?? 0
  const sharpeRatio = metrics?.sharpe_ratio ?? 0
  const maxDrawdown = metrics?.max_drawdown_pct ?? 0

  const hasMetrics = !!metrics

  const getReturnStatus = (value: number) => {
    if (!hasMetrics) return 'neutral'
    return value >= 0 ? 'positive' : 'negative'
  }

  const getSharpeStatus = (value: number) => {
    if (!hasMetrics) return 'neutral'
    return value >= 1 ? 'positive' : value < 0 ? 'negative' : 'neutral'
  }

  const getDrawdownStatus = (value: number) => {
    if (!hasMetrics) return 'neutral'
    return value < -20 ? 'negative' : 'neutral'
  }

  const { data: health, isLoading, isError } = useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await fetch('/api/health')
      if (!res.ok) throw new Error('API unreachable')
      return res.json()
    },
    refetchInterval: 10_000,
  })

  return (
    <div className="flex h-screen bg-surface text-on-surface overflow-hidden dark font-body">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-background">
        <header className="flex-none p-6 pb-4 border-b border-outline-variant/20 bg-surface-container-low backdrop-blur-sm sticky top-0 z-10 flex justify-between items-center relative">
            <div>
              <h2 className="font-headline text-xl font-bold tracking-tight">Strategy Builder</h2>
              <p className="font-label text-sm text-on-surface-variant mt-1">Design, test, and optimize trading strategies.</p>
            </div>
            <div className="flex gap-4 items-center">
                <div className={`status-badge ${isLoading ? 'loading' : isError ? 'error' : 'ok'}`}>
                    {isLoading ? '⏳ Connecting...' : isError ? '🔴 API Offline' : `🟢 API ${health?.status}`}
                </div>
            </div>
        </header>

        <main className="flex-1 flex flex-col p-6 gap-6 overflow-hidden bg-background">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-none">
            <MetricCard
              title="Total Return"
              value={hasMetrics ? `${totalReturn.toFixed(2)}%` : '--'}
              status={getReturnStatus(totalReturn)}
              icon={hasMetrics ? (totalReturn >= 0 ? TrendingUp : TrendingDown) : Minus}
            />
            <MetricCard
              title="Sharpe Ratio"
              value={hasMetrics ? sharpeRatio.toFixed(2) : '--'}
              status={getSharpeStatus(sharpeRatio)}
              icon={Activity}
            />
            <MetricCard
              title="Max Drawdown"
              value={hasMetrics ? `${maxDrawdown.toFixed(2)}%` : '--'}
              status={getDrawdownStatus(maxDrawdown)}
              icon={hasMetrics ? TrendingDown : Minus}
            />
          </div>

          <div className="flex-1 bg-surface-container-lowest border border-outline-variant/30 relative shadow-inner overflow-hidden flex flex-col">
            {children}
          </div>
        </main>
      </div>
      <ChatPanel isOpen={isChatOpen} jobId={jobId} onClose={closeChat} />
      <InspectorPanel />
    </div>
  )
}
