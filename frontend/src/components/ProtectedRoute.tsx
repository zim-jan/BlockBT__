import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { api } from '../services/api'

export function ProtectedRoute() {
  const { isAuthenticated } = useAuthStore()
  const [authRequired, setAuthRequired] = useState<boolean | null>(null)

  useEffect(() => {
    api.auth.authStatus()
      .then((res) => setAuthRequired(res.data.auth_enabled))
      .catch(() => setAuthRequired(false)) // If backend unreachable, skip auth
  }, [])

  // Loading state
  if (authRequired === null) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-on-surface-variant font-label text-sm animate-pulse">
          Loading...
        </div>
      </div>
    )
  }

  // Auth not required — pass through
  if (!authRequired) {
    return <Outlet />
  }

  // Auth required but not logged in — redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
