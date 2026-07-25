import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { X, Loader2, MessageSquare, StickyNote, BarChart2 } from 'lucide-react'
import { request } from '../../services/api'
import { ChatPanel } from '../../features/ai_chat/ChatPanel'
import { NotesWidget } from './NotesWidget'

interface FullJobViewModalProps {
  jobId: number
  strategyId: number
  onClose: () => void
}

export function FullJobViewModal({ jobId, strategyId, onClose }: FullJobViewModalProps) {
  const [tearsheetHtml, setTearsheetHtml] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Right panel state: 'chat' | 'notes'
  const [activePanel, setActivePanel] = useState<'chat' | 'notes'>('notes')

  // Esc zamyka modal (uwaga z testów S7.7).
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  useEffect(() => {
    const fetchTearsheet = async () => {
      try {
        setLoading(true)
        setError(null)
        const response = await request<any>(`/api/results/${jobId}/tearsheet`)
        if (response.success && response.data.html) {
          setTearsheetHtml(response.data.html)
        } else {
          setError('Invalid response from server')
        }
      } catch (err: any) {
        console.error('Error fetching tearsheet:', err)
        setError(err.response?.data?.detail || err.message || 'Failed to load Tearsheet')
      } finally {
        setLoading(false)
      }
    }
    fetchTearsheet()
  }, [jobId])

  return createPortal(
    <div className="fixed top-0 left-0 flex bg-background/95 backdrop-blur-sm" style={{ zIndex: 999999, width: '100vw', height: '100vh' }}>
      
      {/* LEFT: Tearsheet / Stats */}
      <div className="flex-1 flex flex-col h-full bg-background border-r border-outline-variant/20">
        <div className="h-14 border-b border-outline-variant/20 flex items-center px-4 bg-surface-container justify-between shrink-0">
          <div className="flex items-center gap-3 text-on-surface">
            <BarChart2 className="w-5 h-5 text-primary" />
            <h2 className="font-headline font-bold text-lg">Job #{jobId} Results</h2>
          </div>
          
          {/* Przełącznik paneli + zamknięcie. Przycisk zamykania jest normalnym elementem
              flex w pasku nagłówka — jako pływający `absolute` nachodził na te zakładki. */}
          <div className="flex items-center gap-3">
            <div className="flex bg-surface-container-high rounded-lg p-1 border border-outline-variant/30">
              <button
                onClick={() => setActivePanel('notes')}
                className={`px-3 py-1 text-xs font-label rounded-md flex items-center gap-1.5 transition-colors ${activePanel === 'notes' ? 'bg-primary/20 text-primary' : 'text-on-surface-variant hover:text-on-surface'}`}
              >
                <StickyNote className="w-3.5 h-3.5" /> Notes
              </button>
              <button
                onClick={() => setActivePanel('chat')}
                className={`px-3 py-1 text-xs font-label rounded-md flex items-center gap-1.5 transition-colors ${activePanel === 'chat' ? 'bg-primary/20 text-primary' : 'text-on-surface-variant hover:text-on-surface'}`}
              >
                <MessageSquare className="w-3.5 h-3.5" /> AI Chat
              </button>
            </div>

            <button
              onClick={onClose}
              className="w-9 h-9 shrink-0 flex items-center justify-center rounded-full border border-outline-variant/50 bg-surface-container-high text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest transition-colors"
              title="Close full view"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-hidden relative bg-white">
          {loading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/50 text-on-surface-variant">
               <Loader2 className="w-10 h-10 animate-spin mb-4 text-primary" />
               <p className="font-label">Generating Tearsheet...</p>
            </div>
          ) : error ? (
            <div className="absolute inset-0 flex items-center justify-center bg-background p-8">
              <div className="max-w-md w-full bg-error/10 border border-error/30 rounded-lg p-6 text-center">
                <p className="text-error font-medium mb-2">Error loading Tearsheet</p>
                <p className="text-error/80 text-sm">{error}</p>
              </div>
            </div>
          ) : tearsheetHtml ? (
            <iframe
              srcDoc={tearsheetHtml}
              className="w-full h-full border-none"
              title="QuantStats Tearsheet"
              sandbox="allow-scripts allow-same-origin"
            />
          ) : null}
        </div>
      </div>

      {/* RIGHT: Selected Panel */}
      <div className="flex shrink-0 h-full relative shadow-2xl">
        {activePanel === 'chat' ? (
          <div className="h-full w-[420px] flex">
            {/* The ChatPanel already brings its own wrapper and styling.
                We might need to pass an isOpen={true} and an empty onClose just to satisfy it */}
            <ChatPanel jobId={jobId} isOpen={true} onClose={() => {}} />
          </div>
        ) : (
          <NotesWidget strategyId={strategyId} />
        )}
      </div>
      
    </div>,
    document.body
  )
}
