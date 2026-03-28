import { useQuery } from '@tanstack/react-query'
import './App.css'
import { WorkflowEditor } from './flows/WorkflowEditor'

interface HealthResponse {
  status: string
}

function LandingBackup({ isLoading, isError, health }: { isLoading: boolean, isError: boolean, health: HealthResponse | undefined }) {
  return (
    <div className="app">
      <header className="app-header">
        <div className="logo-mark">⬡</div>
        <h1 className="app-title">BlockBT</h1>
        <p className="app-subtitle">Self-Hosted Algorithmic Backtesting Platform</p>
        <div className={`status-badge ${isLoading ? 'loading' : isError ? 'error' : 'ok'}`}>
          {isLoading ? '⏳ Connecting...' : isError ? '🔴 API Offline' : `🟢 API ${health?.status}`}
        </div>
      </header>
      <main className="app-main">
        <div className="card-grid">
          <div className="card">
            <div className="card-icon">📊</div>
            <h2>Strategies</h2>
            <p>Design and manage your trading strategies using SMA, MACD, and custom indicators.</p>
            <span className="card-tag">Phase 2</span>
          </div>
          <div className="card">
            <div className="card-icon">⚡</div>
            <h2>Backtest Engine</h2>
            <p>Run historical backtests powered by vectorbt. Air-gapped, fully local, zero cloud.</p>
            <span className="card-tag">Phase 2</span>
          </div>
          <div className="card">
            <div className="card-icon">🔷</div>
            <h2>Flow Builder</h2>
            <p>Visually compose strategy workflows using a drag-and-drop node-based editor (React Flow).</p>
            <span className="card-tag">Phase 3</span>
          </div>
          <div className="card">
            <div className="card-icon">📈</div>
            <h2>Results</h2>
            <p>Analyze equity curves, drawdowns, Sharpe ratios, and trade-level metrics.</p>
            <span className="card-tag">Phase 3</span>
          </div>
        </div>
      </main>
      <footer className="app-footer">
        <p>BlockBT MVP — Phase 1 Bootstrap ✅ &nbsp;|&nbsp; Air-Gapped &nbsp;|&nbsp; Local-only</p>
      </footer>
    </div>
  )
}

function App() {
  const { data: health, isLoading, isError } = useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await fetch('/api/health')
      if (!res.ok) throw new Error('API unreachable')
      return res.json()
    },
    refetchInterval: 10_000,
  })

  // To view the original landing page, swap the return statement
  // return <LandingBackup isLoading={isLoading} isError={isError} health={health} />

  return (
    <div style={{ width: '100vw', height: '100vh', margin: 0, padding: 0 }}>
      {/* Absolute positioned health indicator over the flow canvas */}
      <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 1000 }} className={`status-badge ${isLoading ? 'loading' : isError ? 'error' : 'ok'}`}>
          {isLoading ? '⏳ Connecting...' : isError ? '🔴 API Offline' : `🟢 API ${health?.status}`}
      </div>
      <WorkflowEditor />
    </div>
  )
}

export default App
