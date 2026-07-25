import { useState } from 'react'
import { MainLayout } from '../components/layout/MainLayout'
import { RealtimeChartWidget } from '../components/Dashboard/RealtimeChartWidget'
import { HistoryWidget } from '../components/Dashboard/HistoryWidget'
import { FullJobViewModal } from '../components/Dashboard/FullJobViewModal'

export function DashboardPage() {
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [selectedStrategyId, setSelectedStrategyId] = useState<number | null>(null)

  const handleJobSelect = (jobId: number, strategyId: number) => {
    setSelectedJobId(jobId)
    setSelectedStrategyId(strategyId)
  }

  const closeFullView = () => {
    setSelectedJobId(null)
    setSelectedStrategyId(null)
  }

  return (
    <MainLayout>
      {/* Bez content-visibility: auto — size containment zeruje wymiary kontenera wykresu
          przy montowaniu, Plotly mierzy 0x0 i wpada w domyślne 700x450, wychodząc poza kartę
          i nachodząc na listę historii (test manualny S2.1/S5.1/S5.2, 2026-07-25). */}
      <div className="flex flex-col h-full overflow-y-auto bg-background p-6 gap-6">
        <header>
          <h1 className="text-3xl font-headline font-bold text-on-surface">Dashboard</h1>
          <p className="text-on-surface-variant font-label mt-1">Real-time market data & backtest history</p>
        </header>

        {/* Real-time chart widget — overflow-hidden trzyma płótno Plotly w granicach karty. */}
        <div className="w-full h-96 bg-surface-container rounded-lg border border-outline-variant/30 shrink-0 relative overflow-hidden">
          <RealtimeChartWidget />
        </div>

        {/* Jobs History List */}
        <div className="flex-1 bg-surface-container rounded-lg border border-outline-variant/30 overflow-hidden flex flex-col">
          <HistoryWidget onJobSelect={handleJobSelect} />
        </div>
      </div>

      {selectedJobId !== null && (
        <FullJobViewModal 
          jobId={selectedJobId} 
          strategyId={selectedStrategyId || 0} 
          onClose={closeFullView} 
        />
      )}
    </MainLayout>
  )
}
