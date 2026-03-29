import { create } from 'zustand'

interface Message {
  role: 'user' | 'ai'
  content: string
}

interface ChatState {
  isOpen: boolean
  simId: number | null
  messages: Message[]
  isLoading: boolean
  input: string
  openChat: (simId: number) => void
  closeChat: () => void
  setInput: (value: string) => void
  sendMessage: (content: string) => void
  _triggerInitialAnalysis: (simId: number) => Promise<void>
}

export const useChatStore = create<ChatState>((set, get) => ({
  isOpen: false,
  simId: null,
  messages: [],
  isLoading: false,
  input: '',

  openChat: (simId: number) => {
    // If opening the same simId again, just open the panel, don't clear messages
    const isNew = get().simId !== simId
    set({ isOpen: true })

    if (isNew) {
      set({
        simId,
        messages: [],
        isLoading: false,
        input: ''
      })
      get()._triggerInitialAnalysis(simId)
    }
  },

  closeChat: () => {
    set({ isOpen: false })
  },

  setInput: (value: string) => {
    set({ input: value })
  },

  sendMessage: (content: string) => {
    // For now, it just mocks adding the message and logs to console
    set(state => ({
      messages: [...state.messages, { role: 'user', content }],
      input: ''
    }))

    console.log("Follow-up chat to be implemented in Phase 6")

    // Mock response for followups just so it doesn't look dead
    set({ isLoading: true })
    setTimeout(() => {
      set(state => ({
        messages: [...state.messages, { role: 'ai', content: "I am a basic MVP assistant. Advanced follow-up chat will be implemented in Phase 6." }],
        isLoading: false
      }))
    }, 1000)
  },

  _triggerInitialAnalysis: async (simId: number) => {
    set({
      isLoading: true,
      messages: [{ role: 'user', content: "Analyze the backtest results for this strategy." }]
    })

    try {
      // POST /api/results/{sim_id}/analyze
      const response = await fetch(`http://127.0.0.1:8000/api/results/${simId}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'blockbt-secret-key-123'
        }
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()

      set(state => ({
        messages: [...state.messages, { role: 'ai', content: data.report }],
        isLoading: false
      }))
    } catch (err: any) {
      set(state => ({
        messages: [...state.messages, { role: 'ai', content: `**Error:** Could not analyze results.\n\nDetails: ${err.message}` }],
        isLoading: false
      }))
    }
  }
}))
