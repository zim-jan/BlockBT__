/**
 * BlockBT typed API client — Phase 3.
 * All requests go via Vite's proxy (/api → http://127.0.0.1:8000).
 * Typed against the generated api.d.ts schemas.
 */

import type { components } from './api.d'
import type { BacktestJobData, StrategyData } from '../types'

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

type ApiResponse<T> = { success: boolean; data: T; error: string | null }

export const api = {
  health: {
    get: () => request<{ status: string; version: string }>('/api/health'),
  },

  strategies: {
    list: () => request<ApiResponse<StrategyData[]>>('/api/strategies/'),
    get: (id: number) => request<ApiResponse<StrategyData>>(`/api/strategies/${id}`),
    create: (payload: components['schemas']['StrategyCreate']) =>
      request<ApiResponse<StrategyData>>('/api/strategies/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },

  backtest: {
    trigger: (payload: components['schemas']['BacktestRequest']) =>
      request<ApiResponse<BacktestJobData>>('/api/backtest/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    status: (jobId: number) =>
      request<ApiResponse<BacktestJobData>>(`/api/backtest/${jobId}`),
    list: () => request<ApiResponse<BacktestJobData[]>>('/api/backtest/'),
  },

  workflows: {
    list: () => request<ApiResponse<unknown[]>>('/api/workflows/'),
    save: (payload: components['schemas']['WorkflowCreate']) =>
      request<ApiResponse<unknown>>('/api/workflows/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },

  results: {
    analyze: (jobId: number) =>
      request<components['schemas']['AIAnalysisResponse']>(`/api/results/${jobId}/analyze`, {
        method: 'POST',
      }),
    getChat: (jobId: number) =>
      request<components['schemas']['ChatMessageResponse'][]>(`/api/results/${jobId}/chat`),
    sendChat: (jobId: number, payload: components['schemas']['ChatRequest']) =>
      request<components['schemas']['ChatMessageResponse']>(`/api/results/${jobId}/chat`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  },
}
