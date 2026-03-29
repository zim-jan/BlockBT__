import { useQuery } from '@tanstack/react-query'
import './App.css'
import { WorkflowEditor } from './flows/WorkflowEditor'
import { MainLayout } from './components/Layout/MainLayout'
import { ChatPanel } from './components/ChatPanel'
import { useChatStore } from './store/chatStore'

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

  const { isOpen, jobId, closeChat } = useChatStore()

  return (
    <MainLayout>
      {/* Absolute positioned health indicator over the flow canvas */}
      <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 1000 }} className={`status-badge ${isLoading ? 'loading' : isError ? 'error' : 'ok'}`}>
          {isLoading ? '⏳ Connecting...' : isError ? '🔴 API Offline' : `🟢 API ${health?.status}`}
      </div>
      <WorkflowEditor />
      <ChatPanel isOpen={isOpen} jobId={jobId} onClose={closeChat} />
    </MainLayout>
  )
}

export default App
