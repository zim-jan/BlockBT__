/**
 * BlockBT API client — Phase 1 stub.
 * All requests go via Vite's proxy (/api → http://127.0.0.1:8000).
 *
 * In Phase 2 this module will be augmented with generated types from
 * `npm run generate-api` (openapi-typescript → api.d.ts).
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

// ── Health ──────────────────────────────────────────────────────────────────

export const api = {
  health: {
    get: () => request<{ status: string }>('/api/health'),
  },

  strategies: {
    list: () => request<{ success: boolean; data: unknown[] }>('/api/strategies/'),
    get:  (id: string) => request<{ success: boolean; data: unknown }>(`/api/strategies/${id}`),
    create: (payload: unknown) =>
      request<{ success: boolean; data: unknown }>('/api/strategies/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },

  backtest: {
    trigger: (payload: unknown) =>
      request<{ success: boolean; data: { job_id: string; status: string } }>('/api/backtest/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    status: (jobId: string) =>
      request<{ success: boolean; data: unknown }>(`/api/backtest/${jobId}`),
  },

  workflows: {
    list: () => request<{ success: boolean; data: unknown[] }>('/api/workflows/'),
    get:  (id: string) => request<{ success: boolean; data: unknown }>(`/api/workflows/${id}`),
    save: (payload: unknown) =>
      request<{ success: boolean; data: unknown }>('/api/workflows/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },
}
