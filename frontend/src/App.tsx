import { useQuery } from '@tanstack/react-query'
import './App.css'
import { WorkflowEditor } from './flows/WorkflowEditor'
import { MainLayout } from './components/Layout/MainLayout'
import { SlideOutChatPanel } from './components/ChatPanel/SlideOutChatPanel'

interface HealthResponse {
  status: string
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

  return (
    <MainLayout>
      {/* Absolute positioned health indicator over the flow canvas */}
      <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 1000 }} className={`status-badge ${isLoading ? 'loading' : isError ? 'error' : 'ok'}`}>
          {isLoading ? '⏳ Connecting...' : isError ? '🔴 API Offline' : `🟢 API ${health?.status}`}
      </div>
      <WorkflowEditor />
      <SlideOutChatPanel />
    </MainLayout>
  )
}

export default App
