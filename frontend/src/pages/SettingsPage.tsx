import { useState, useEffect } from 'react'
import { Sidebar } from '../components/layout/Sidebar'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState('data')
  
  // Tabs: 'data', 'engine', 'ai', 'general'
  return (
    <div className="flex h-screen bg-surface text-on-surface overflow-hidden dark font-body">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-background">
        <header className="flex-none p-6 pb-4 border-b border-outline-variant/20 bg-surface-container-low backdrop-blur-sm sticky top-0 z-10">
          <h2 className="font-headline text-xl font-bold tracking-tight">BlockBT Settings</h2>
          <p className="font-label text-sm text-on-surface-variant mt-1">Configure your local backtesting environment.</p>
        </header>
        
        <main className="flex-1 flex flex-col p-6 overflow-hidden bg-background">
            <div className="border-b border-outline-variant/20 mb-6">
                <nav className="-mb-px flex space-x-8">
                  <button 
                    onClick={() => setActiveTab('data')} 
                    className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'data' ? 'border-primary text-primary' : 'border-transparent text-on-surface-variant hover:text-on-surface hover:border-outline-variant'}`}
                  >
                    Data Providers
                  </button>
                  <button 
                    onClick={() => setActiveTab('ai')} 
                    className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'ai' ? 'border-primary text-primary' : 'border-transparent text-on-surface-variant hover:text-on-surface hover:border-outline-variant'}`}
                  >
                    AI System Prompts
                  </button>
                </nav>
            </div>
            
            <div className="flex-1 overflow-y-auto">
                {activeTab === 'data' && <DataSettingsTab />}
                {activeTab === 'ai' && <AIPromptsTab />}
            </div>
        </main>
      </div>
    </div>
  )
}

function DataSettingsTab() {
  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h3 className="text-lg font-medium leading-6 text-on-surface">Yahoo Finance</h3>
        <p className="mt-1 text-sm text-on-surface-variant">Default free historical data source.</p>
        <div className="mt-4">
            <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
                <span className="text-sm font-medium text-on-surface">Status: Ready (No API key required)</span>
            </div>
        </div>
      </div>
    </div>
  )
}

function AIPromptsTab() {
  const queryClient = useQueryClient()
  
  const { data: prompts, isLoading } = useQuery({
    queryKey: ['system-prompts'],
    queryFn: async () => {
      const res = await fetch('/api/settings/prompts')
      if (!res.ok) throw new Error('Failed to fetch prompts')
      return res.json()
    }
  })
  
  const [newPromptName, setNewPromptName] = useState('')
  const [newPromptContent, setNewPromptContent] = useState('')

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch('/api/settings/prompts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newPromptName, content: newPromptContent })
      })
      if (!res.ok) throw new Error('Failed to create prompt')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-prompts'] })
      setNewPromptName('')
      setNewPromptContent('')
    }
  })

  const setDefaultMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`/api/settings/prompts/${id}/default`, { method: 'POST' })
      if (!res.ok) throw new Error('Failed to set default')
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-prompts'] })
    }
  })
  
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`/api/settings/prompts/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete prompt')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-prompts'] })
    }
  })

  if (isLoading) return <div className="text-on-surface-variant p-4">Loading prompts...</div>

  return (
    <div className="max-w-4xl space-y-8">
      <div>
        <h3 className="text-lg font-medium leading-6 text-on-surface">System Prompts</h3>
        <p className="mt-1 text-sm text-on-surface-variant">Manage AI roles and behaviors for backtest analysis.</p>
        
        <div className="mt-6 space-y-4">
            {prompts?.map((prompt: any) => (
                <div key={prompt.id} className={`p-4 rounded-lg border ${prompt.is_default ? 'border-primary bg-primary/5' : 'border-outline-variant/30 bg-surface-container-low'}`}>
                    <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-3">
                            <h4 className="font-semibold text-on-surface">{prompt.name}</h4>
                            {prompt.is_default && (
                                <span className="px-2 py-0.5 rounded text-xs font-medium bg-primary/20 text-primary">Default</span>
                            )}
                        </div>
                        <div className="flex gap-2">
                             {!prompt.is_default && (
                                <button 
                                    onClick={() => setDefaultMutation.mutate(prompt.id)}
                                    className="text-xs px-2 py-1 text-on-surface-variant hover:text-primary transition-colors"
                                >
                                    Set Default
                                </button>
                             )}
                             <button 
                                onClick={() => deleteMutation.mutate(prompt.id)}
                                className="text-xs px-2 py-1 text-on-surface-variant hover:text-red-400 transition-colors"
                                disabled={prompt.is_default}
                             >
                                Delete
                             </button>
                        </div>
                    </div>
                    <pre className="text-sm text-on-surface-variant whitespace-pre-wrap font-sans bg-surface-container-highest p-3 rounded mt-2 border border-outline-variant/20">{prompt.content}</pre>
                </div>
            ))}
        </div>
      </div>
      
      <div className="pt-6 border-t border-outline-variant/20">
        <h4 className="text-md font-medium text-on-surface mb-4">Add New Prompt</h4>
        <div className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-on-surface-variant mb-1">Name</label>
                <input 
                    type="text" 
                    value={newPromptName}
                    onChange={(e) => setNewPromptName(e.target.value)}
                    className="w-full bg-surface-container-high border border-outline-variant/50 rounded p-2 text-on-surface text-sm focus:outline-none focus:border-primary"
                    placeholder="e.g. Aggressive Growth Analyst"
                />
            </div>
            <div>
                <label className="block text-sm font-medium text-on-surface-variant mb-1">Prompt Content</label>
                <textarea 
                    value={newPromptContent}
                    onChange={(e) => setNewPromptContent(e.target.value)}
                    rows={4}
                    className="w-full bg-surface-container-high border border-outline-variant/50 rounded p-2 text-on-surface text-sm focus:outline-none focus:border-primary"
                    placeholder="You are an expert quantitative analyst..."
                />
            </div>
            <button 
                onClick={() => createMutation.mutate()}
                disabled={!newPromptName || !newPromptContent || createMutation.isPending}
                className="px-4 py-2 bg-primary text-on-primary rounded text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
                Save Prompt
            </button>
        </div>
      </div>
    </div>
  )
}
