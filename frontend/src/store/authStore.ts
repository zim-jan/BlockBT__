import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { useWorkflowStore } from './workflowStore'

interface UserInfo {
  id: number
  username: string
  role: string
}

interface AuthState {
  token: string | null
  user: UserInfo | null
  isAuthenticated: boolean
  login: (token: string, user: UserInfo) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      login: (token, user) => {
        // Clear canvas to ensure new user starts with a clean slate
        useWorkflowStore.getState().clearCanvas()
        set({ token, user, isAuthenticated: true })
      },
      logout: () => {
        // Clear canvas on logout so previous user's strategy is not leaked
        useWorkflowStore.getState().clearCanvas()
        set({ token: null, user: null, isAuthenticated: false })
      },
    }),
    { name: 'blockbt-auth' }
  )
)
