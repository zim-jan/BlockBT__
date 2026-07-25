import { useState, useEffect } from 'react'
import { Sidebar } from '../components/layout/Sidebar'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { 
  Database, 
  Bot, 
  Users, 
  CheckCircle2, 
  AlertTriangle, 
  Plus, 
  Edit2, 
  Trash2, 
  Shield, 
  UserPlus, 
  Check, 
  X,
  Server,
  Lock,
  Loader2
} from 'lucide-react'

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'data' | 'ai' | 'users'>('data')

  return (
    <div className="flex h-screen bg-surface text-on-surface overflow-hidden dark font-body">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-background">
        {/* Header */}
        <header className="flex-none px-8 py-5 border-b border-outline-variant/20 bg-surface-container-low backdrop-blur-sm sticky top-0 z-10 flex items-center justify-between">
          <div>
            <h2 className="font-headline text-2xl font-bold tracking-tight text-on-surface">Settings</h2>
            <p className="font-label text-xs text-on-surface-variant/80 mt-1.5 leading-relaxed">Configure environment data, AI analysis prompts, and user access control.</p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 bg-surface-container border border-outline-variant/30 text-on-surface-variant font-label text-xs">
            <Server className="w-3.5 h-3.5 text-primary" />
            <span>Air-Gapped Local Environment</span>
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 flex flex-col p-8 overflow-y-auto bg-background">
          <div className="max-w-5xl w-full mx-auto space-y-6">
            {/* Tabs */}
            <div className="border-b border-outline-variant/20">
              <nav className="-mb-px flex space-x-8">
                <button
                  onClick={() => setActiveTab('data')}
                  className={`whitespace-nowrap py-3.5 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${
                    activeTab === 'data'
                      ? 'border-primary text-primary font-semibold'
                      : 'border-transparent text-on-surface-variant hover:text-on-surface hover:border-outline-variant/50'
                  }`}
                >
                  <Database className="w-4 h-4" />
                  <span>Data Providers</span>
                </button>
                <button
                  onClick={() => setActiveTab('ai')}
                  className={`whitespace-nowrap py-3.5 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${
                    activeTab === 'ai'
                      ? 'border-primary text-primary font-semibold'
                      : 'border-transparent text-on-surface-variant hover:text-on-surface hover:border-outline-variant/50'
                  }`}
                >
                  <Bot className="w-4 h-4" />
                  <span>AI System Prompts</span>
                </button>
                <button
                  onClick={() => setActiveTab('users')}
                  className={`whitespace-nowrap py-3.5 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2 ${
                    activeTab === 'users'
                      ? 'border-primary text-primary font-semibold'
                      : 'border-transparent text-on-surface-variant hover:text-on-surface hover:border-outline-variant/50'
                  }`}
                >
                  <Users className="w-4 h-4" />
                  <span>User Management</span>
                </button>
              </nav>
            </div>

            {/* Tab Views */}
            {activeTab === 'data' && <DataSettingsTab />}
            {activeTab === 'ai' && <AIPromptsTab />}
            {activeTab === 'users' && <UsersTab />}
          </div>
        </main>
      </div>
    </div>
  )
}

function DataSettingsTab() {
  return (
    <div className="space-y-6">
      {/* Yahoo Finance Card */}
      <div className="bg-surface-container-low border border-outline-variant/20 p-6 space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-outline-variant/15">
          <div>
            <h3 className="font-headline text-lg font-bold text-on-surface flex items-center gap-2">
              <Database className="w-5 h-5 text-primary" /> Yahoo Finance Provider
            </h3>
            <p className="font-label text-xs text-on-surface-variant mt-0.5">Primary connector for downloading free market historical price series.</p>
          </div>
          <span className="px-2.5 py-1 text-[11px] font-medium tracking-wide uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" /> Ready (No API Key Required)
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-on-surface-variant pt-2">
          <div className="bg-surface-container border border-outline-variant/20 p-3.5 space-y-1">
            <span className="font-semibold text-on-surface block">Default Data Source</span>
            <p>Fetches OHLCV price series via `yfinance` connector with automatic Parquet caching.</p>
          </div>
          <div className="bg-surface-container border border-outline-variant/20 p-3.5 space-y-1">
            <span className="font-semibold text-on-surface block">Offline Resilience</span>
            <p>Downloaded market data is cached in binary Parquet files for repeated offline backtests.</p>
          </div>
        </div>
      </div>

      {/* Cache Info Card */}
      <div className="bg-surface-container-low border border-outline-variant/20 p-6 space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-outline-variant/15">
          <div>
            <h3 className="font-headline text-lg font-bold text-on-surface flex items-center gap-2">
              <Server className="w-5 h-5 text-primary" /> Parquet Storage Cache
            </h3>
            <p className="font-label text-xs text-on-surface-variant mt-0.5">Local binary cache directory stored under `backend/data/cache`.</p>
          </div>
        </div>
        <div className="text-xs text-on-surface-variant">
          <p>Cache TTL is set to <code className="text-primary bg-surface-container px-1.5 py-0.5">24 hours</code>. Re-downloading triggers automatically when requested date ranges fall outside cached bounds.</p>
        </div>
      </div>
    </div>
  )
}

function AIPromptsTab() {
  const queryClient = useQueryClient()

  const { data: ollamaStatus, isLoading: isLoadingStatus } = useQuery({
    queryKey: ['ollama-status'],
    queryFn: async () => {
      return await api.settings.getOllamaStatus()
    },
    refetchInterval: 10000,
  })

  const { data: prompts, isLoading } = useQuery({
    queryKey: ['system-prompts'],
    queryFn: async () => {
      const res = await api.settings.getPrompts()
      return res.data
    }
  })

  const [editingId, setEditingId] = useState<number | null>(null)
  const [promptName, setPromptName] = useState('')
  const [promptContent, setPromptContent] = useState('')
  const [showForm, setShowForm] = useState(false)

  const createMutation = useMutation({
    mutationFn: async () => {
      return await api.settings.createPrompt({ name: promptName, content: promptContent })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-prompts'] })
      handleCancel()
    }
  })

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (!editingId) return
      return await api.settings.updatePrompt(editingId, { name: promptName, content: promptContent })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-prompts'] })
      handleCancel()
    }
  })

  const setDefaultMutation = useMutation({
    mutationFn: async (id: number) => {
      return await api.settings.setDefaultPrompt(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-prompts'] })
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.settings.deletePrompt(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system-prompts'] })
    }
  })

  const handleEdit = (prompt: any) => {
    setEditingId(prompt.id)
    setPromptName(prompt.name)
    setPromptContent(prompt.content)
    setShowForm(true)
  }

  const handleCancel = () => {
    setEditingId(null)
    setPromptName('')
    setPromptContent('')
    setShowForm(false)
  }

  if (isLoading) return <div className="text-on-surface-variant p-4 text-xs font-label">Loading AI prompts...</div>

  return (
    <div className="space-y-6">
      {/* Ollama Connection Status Card */}
      <div className="bg-surface-container-low border border-outline-variant/20 p-6 space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-outline-variant/15">
          <div>
            <h3 className="font-headline text-lg font-bold text-on-surface flex items-center gap-2">
              <Server className="w-5 h-5 text-primary" /> Ollama Local LLM Server
            </h3>
            <p className="font-label text-xs text-on-surface-variant mt-0.5">
              Status of your local Ollama instance for executing report generation.
            </p>
          </div>
          {isLoadingStatus ? (
            <span className="px-2.5 py-1 text-[11px] font-medium tracking-wide uppercase bg-surface-container text-on-surface-variant border border-outline-variant/30">
              Checking status...
            </span>
          ) : ollamaStatus?.available ? (
            <span className="px-2.5 py-1 text-[11px] font-medium tracking-wide uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" /> Ollama Connected
            </span>
          ) : (
            <span className="px-2.5 py-1 text-[11px] font-medium tracking-wide uppercase bg-red-500/10 text-red-400 border border-red-500/20 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" /> Ollama Unreachable
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-on-surface-variant">
          <div className="bg-surface-container border border-outline-variant/20 p-3.5 space-y-1">
            <span className="font-semibold text-on-surface block">Server URL</span>
            <code className="text-primary font-mono">{ollamaStatus?.base_url || 'http://localhost:11434'}</code>
          </div>
          <div className="bg-surface-container border border-outline-variant/20 p-3.5 space-y-1">
            <span className="font-semibold text-on-surface block">Target Model</span>
            <code className="text-primary font-mono">{ollamaStatus?.model || 'llama3'}</code>
            {ollamaStatus?.available && !ollamaStatus?.model_installed && (
              <p className="text-amber-400 text-[11px] mt-1 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Model not pulled yet (`ollama pull {ollamaStatus?.model}`)
              </p>
            )}
          </div>
          <div className="bg-surface-container border border-outline-variant/20 p-3.5 space-y-1">
            <span className="font-semibold text-on-surface block">Installed Models</span>
            {ollamaStatus?.installed_models && ollamaStatus.installed_models.length > 0 ? (
              <p className="font-mono text-[11px] text-on-surface">{ollamaStatus.installed_models.join(', ')}</p>
            ) : (
              <p className="text-on-surface-variant/70 italic text-[11px]">No models found or server offline</p>
            )}
          </div>
        </div>
      </div>

      {/* Prompts List Card */}
      <div className="bg-surface-container-low border border-outline-variant/20 p-6 space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-outline-variant/15">
          <div>
            <h3 className="font-headline text-lg font-bold text-on-surface flex items-center gap-2">
              <Bot className="w-5 h-5 text-primary" /> AI Analyst Roles & System Prompts
            </h3>
            <p className="font-label text-xs text-on-surface-variant mt-0.5">Customize prompts used by LLM assistants to generate backtest diagnostic reports.</p>
          </div>
          {!showForm && (
            <button
              onClick={() => { setShowForm(true); setEditingId(null); setPromptName(''); setPromptContent('') }}
              className="px-3 py-1.5 bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 text-xs font-medium uppercase tracking-wider transition-colors flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" /> Add Prompt
            </button>
          )}
        </div>

        {/* Form Overlay / Section */}
        {showForm && (
          <div className="bg-surface-container border border-outline-variant/30 p-5 space-y-4">
            <h4 className="font-headline text-sm font-bold text-on-surface flex items-center gap-2">
              {editingId ? <Edit2 className="w-4 h-4 text-primary" /> : <Plus className="w-4 h-4 text-primary" />}
              {editingId ? 'Edit System Prompt' : 'Create New System Prompt'}
            </h4>
            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-on-surface-variant font-medium mb-1">Role / Prompt Name</label>
                <input
                  type="text"
                  value={promptName}
                  onChange={(e) => setPromptName(e.target.value)}
                  className="w-full bg-surface-container-low border border-outline-variant/40 p-2.5 text-on-surface focus:outline-hidden focus:border-primary"
                  placeholder="e.g. Risk Conservative Analyst"
                />
              </div>
              <div>
                <label className="block text-on-surface-variant font-medium mb-1">System Prompt Content</label>
                <textarea
                  value={promptContent}
                  onChange={(e) => setPromptContent(e.target.value)}
                  rows={6}
                  className="w-full bg-surface-container-low border border-outline-variant/40 p-2.5 text-on-surface font-mono text-xs focus:outline-hidden focus:border-primary"
                  placeholder="You are a quantitative analyst specializing in..."
                />
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => editingId ? updateMutation.mutate() : createMutation.mutate()}
                disabled={!promptName || !promptContent || createMutation.isPending || updateMutation.isPending}
                className="px-4 py-2 bg-primary text-on-primary font-medium text-xs uppercase tracking-wider hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-1.5"
              >
                <Check className="w-3.5 h-3.5" /> {editingId ? 'Save Changes' : 'Create Prompt'}
              </button>
              <button
                onClick={handleCancel}
                className="px-4 py-2 border border-outline-variant/40 text-on-surface-variant font-medium text-xs uppercase tracking-wider hover:bg-surface-container-high transition-colors flex items-center gap-1.5"
              >
                <X className="w-3.5 h-3.5" /> Cancel
              </button>
            </div>
          </div>
        )}

        {/* Existing Prompts Cards */}
        <div className="space-y-4">
          {prompts?.map((prompt: any) => (
            <div
              key={prompt.id}
              className={`p-4 border transition-colors ${
                prompt.is_default ? 'border-primary/40 bg-primary/5' : 'border-outline-variant/20 bg-surface-container'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <h4 className="font-semibold text-sm text-on-surface">{prompt.name}</h4>
                  {prompt.is_default && (
                    <span className="px-2 py-0.5 text-[10px] font-medium tracking-wide uppercase bg-primary/20 text-primary border border-primary/30 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Default Role
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleEdit(prompt)}
                    className="p-1.5 text-on-surface-variant hover:text-primary transition-colors"
                    title="Edit prompt"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  {!prompt.is_default && (
                    <button
                      onClick={() => setDefaultMutation.mutate(prompt.id)}
                      className="px-2 py-1 text-[11px] border border-outline-variant/30 text-on-surface-variant hover:text-primary hover:border-primary/40 transition-colors"
                    >
                      Make Default
                    </button>
                  )}
                  <button
                    onClick={() => deleteMutation.mutate(prompt.id)}
                    className="p-1.5 text-on-surface-variant hover:text-error transition-colors disabled:opacity-30"
                    disabled={prompt.is_default}
                    title={prompt.is_default ? "Cannot delete default prompt" : "Delete prompt"}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              <pre className="text-xs text-on-surface-variant whitespace-pre-wrap font-mono bg-surface-container-low p-3 border border-outline-variant/15 overflow-x-auto max-h-48">
                {prompt.content}
              </pre>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function UsersTab() {
  const queryClient = useQueryClient()
  const [authEnabled, setAuthEnabled] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState({ username: '', password: '', role: 'user' })

  // Load auth settings
  useEffect(() => {
    api.auth.authStatus()
      .then(res => setAuthEnabled(res.data.auth_enabled))
      .catch(console.error)
  }, [])

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const res = await api.auth.listUsers()
      return res.data
    },
    enabled: authEnabled
  })

  const toggleAuthMutation = useMutation({
    mutationFn: async (enabled: boolean) => {
      await api.settings.update({ auth_enabled: enabled })
      return enabled
    },
    onSuccess: (enabled) => {
      setAuthEnabled(enabled)
      if (enabled) queryClient.invalidateQueries({ queryKey: ['users'] })
    }
  })

  const createMutation = useMutation({
    mutationFn: async () => {
      return await api.auth.createUser(formData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      handleCancel()
    }
  })

  const updateMutation = useMutation({
    mutationFn: async (params: { id: number; payload: any }) => {
      return await api.auth.updateUser(params.id, params.payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      handleCancel()
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      return await api.auth.deleteUser(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    }
  })

  const handleEdit = (user: any) => {
    setEditingId(user.id)
    setFormData({ username: user.username, password: '', role: user.role })
    setShowAddForm(true)
  }

  const handleCancel = () => {
    setShowAddForm(false)
    setEditingId(null)
    setFormData({ username: '', password: '', role: 'user' })
  }

  return (
    <div className="space-y-6">
      {/* Toggle Auth Card */}
      <div className="bg-surface-container-low border border-outline-variant/20 p-6 space-y-4">
        <div className="flex items-center justify-between pb-4 border-b border-outline-variant/15">
          <div className="flex items-start gap-3">
            <Shield className="w-5 h-5 text-primary mt-0.5" />
            <div>
              <h3 className="font-headline text-lg font-bold text-on-surface">Platform Authentication & Security</h3>
              <p className="font-label text-xs text-on-surface-variant mt-0.5">
                Enable login guard and per-user data scoping (`WHERE user_id = X`).
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => toggleAuthMutation.mutate(!authEnabled)}
            disabled={toggleAuthMutation.isPending}
            className={`inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold tracking-wide uppercase transition-all duration-150 border cursor-pointer select-none rounded ${
              authEnabled
                ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/25 active:scale-[0.98]'
                : 'bg-surface-container text-on-surface-variant border-outline-variant/40 hover:bg-surface-container-high hover:text-on-surface active:scale-[0.98]'
            } ${toggleAuthMutation.isPending ? 'opacity-70 cursor-wait' : ''}`}
          >
            <span className={`w-2 h-2 rounded-full ${authEnabled ? 'bg-emerald-400 animate-pulse' : 'bg-outline-variant'}`} />
            <span>{authEnabled ? 'Auth Enabled' : 'Auth Disabled'}</span>
            {toggleAuthMutation.isPending && (
              <Loader2 className="w-3.5 h-3.5 animate-spin ml-1 text-primary" />
            )}
          </button>
        </div>

        {/* Warning Alert */}
        <div className="px-4 py-3 bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>
            Toggling authentication state requires a backend restart for all session endpoints to fully adapt.
          </span>
        </div>
      </div>

      {/* User Management Section */}
      {authEnabled && (
        <div className="bg-surface-container-low border border-outline-variant/20 p-6 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-outline-variant/15">
            <div>
              <h3 className="font-headline text-lg font-bold text-on-surface flex items-center gap-2">
                <Users className="w-5 h-5 text-primary" /> Account Directory
              </h3>
              <p className="font-label text-xs text-on-surface-variant mt-0.5">Manage user credentials and admin permissions.</p>
            </div>
            {!showAddForm && (
              <button
                onClick={() => setShowAddForm(true)}
                className="px-3 py-1.5 bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 text-xs font-medium uppercase tracking-wider transition-colors flex items-center gap-1.5"
              >
                <UserPlus className="w-3.5 h-3.5" /> Add User
              </button>
            )}
          </div>

          {/* Form */}
          {showAddForm && (
            <div className="bg-surface-container border border-outline-variant/30 p-5 space-y-4">
              <h4 className="font-headline text-sm font-bold text-on-surface flex items-center gap-2">
                {editingId ? <Edit2 className="w-4 h-4 text-primary" /> : <UserPlus className="w-4 h-4 text-primary" />}
                {editingId ? 'Edit User Credentials' : 'Register New User'}
              </h4>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 text-xs">
                <div>
                  <label className="block text-on-surface-variant font-medium mb-1">Username</label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full bg-surface-container-low border border-outline-variant/40 p-2 text-on-surface focus:outline-hidden focus:border-primary"
                    placeholder="Username"
                  />
                </div>
                <div>
                  <label className="block text-on-surface-variant font-medium mb-1">
                    {editingId ? 'Password (blank to keep)' : 'Password'}
                  </label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full bg-surface-container-low border border-outline-variant/40 p-2 text-on-surface focus:outline-hidden focus:border-primary"
                    placeholder="Password"
                  />
                </div>
                <div>
                  <label className="block text-on-surface-variant font-medium mb-1">Role</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full bg-surface-container-low border border-outline-variant/40 p-2 text-on-surface focus:outline-hidden focus:border-primary"
                  >
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={() =>
                    editingId ? updateMutation.mutate({ id: editingId, payload: formData }) : createMutation.mutate()
                  }
                  disabled={!formData.username || (!editingId && !formData.password) || createMutation.isPending || updateMutation.isPending}
                  className="px-4 py-2 bg-primary text-on-primary font-medium text-xs uppercase tracking-wider hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Check className="w-3.5 h-3.5" /> {editingId ? 'Save Changes' : 'Create User'}
                </button>
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 border border-outline-variant/40 text-on-surface-variant font-medium text-xs uppercase tracking-wider hover:bg-surface-container-high transition-colors flex items-center gap-1.5"
                >
                  <X className="w-3.5 h-3.5" /> Cancel
                </button>
              </div>
            </div>
          )}

          {/* User Table */}
          {isLoading ? (
            <div className="text-xs text-on-surface-variant p-4 font-label">Loading users...</div>
          ) : (
            <div className="border border-outline-variant/20 overflow-hidden">
              <table className="min-w-full divide-y divide-outline-variant/20 text-xs">
                <thead className="bg-surface-container">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-on-surface-variant uppercase tracking-wider">Username</th>
                    <th className="px-4 py-3 text-left font-semibold text-on-surface-variant uppercase tracking-wider">Role</th>
                    <th className="px-4 py-3 text-left font-semibold text-on-surface-variant uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left font-semibold text-on-surface-variant uppercase tracking-wider">Created</th>
                    <th className="px-4 py-3 text-right font-semibold text-on-surface-variant uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-surface-container-low divide-y divide-outline-variant/15">
                  {users?.map((user: any) => (
                    <tr key={user.id} className="hover:bg-surface-container transition-colors">
                      <td className="px-4 py-3 font-medium text-on-surface">{user.username}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 text-[10px] font-medium tracking-wide uppercase border ${
                            user.role === 'admin'
                              ? 'bg-primary/20 text-primary border-primary/30'
                              : 'bg-surface-container-highest text-on-surface-variant border-outline-variant/20'
                          }`}
                        >
                          {user.role}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {user.is_active ? (
                          <span className="text-emerald-400 font-medium flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Active
                          </span>
                        ) : (
                          <span className="text-on-surface-variant/60 flex items-center gap-1">
                            <Lock className="w-3 h-3" /> Inactive
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-on-surface-variant">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleEdit(user)}
                            className="p-1 text-on-surface-variant hover:text-primary transition-colors"
                            title="Edit user"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => deleteMutation.mutate(user.id)}
                            className="p-1 text-on-surface-variant hover:text-error transition-colors"
                            title="Delete user"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
