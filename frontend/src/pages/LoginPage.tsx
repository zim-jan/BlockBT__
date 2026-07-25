import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { useAuthStore } from '../store/authStore'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    api.auth.authStatus()
      .then((res) => {
        if (!res.data.auth_enabled) {
          navigate('/', { replace: true })
        }
      })
      .catch(() => {})
  }, [navigate])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const res = await api.auth.login({ username, password })
      if (res.success && res.data) {
        useAuthStore.getState().login(res.data.access_token, {
          id: res.data.user_id,
          username: res.data.username,
          role: res.data.role
        })
        navigate('/')
      } else {
        setError(res.error || 'Login failed')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred during login')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background overflow-hidden font-body text-on-surface">
      {/* Background glow orb */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[100px] pointer-events-none" />
      
      <div className="relative z-10 w-full max-w-md p-8 bg-surface-container-low border border-outline-variant/20 rounded-none backdrop-blur-md shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="font-headline text-4xl font-bold tracking-tight mb-2" style={{
            background: 'linear-gradient(to right, var(--accent-cyan, #06b6d4), var(--accent-violet, #8b5cf6))',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            BlockBT
          </h1>
          <p className="text-on-surface-variant font-label text-sm tracking-wide uppercase">Algorithmic Backtesting Platform</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-on-surface-variant mb-1">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-surface-container border border-outline-variant/30 rounded-none p-3 text-on-surface focus:outline-hidden focus:border-primary transition-colors"
                placeholder="Enter username"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-on-surface-variant mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-surface-container border border-outline-variant/30 rounded-none p-3 text-on-surface focus:outline-hidden focus:border-primary transition-colors"
                placeholder="Enter password"
                required
              />
            </div>
          </div>

          {error && (
            <div className="text-error text-sm font-medium text-center">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-primary text-on-primary py-3 px-4 rounded-none font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
        
        <div className="mt-8 text-center">
          <p className="text-[10px] text-on-surface-variant/50 font-label tracking-widest uppercase">v2.0.0 · Air-Gapped</p>
        </div>
      </div>
    </div>
  )
}
