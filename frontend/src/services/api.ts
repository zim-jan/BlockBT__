/**
 * BlockBT typed API client — Phase 3.
 * All requests go via Vite's proxy (/api → http://127.0.0.1:8000).
 * Typed against the generated api.d.ts schemas.
 */

import type {components} from './api.d'
import type {BacktestJobData, StrategyData} from '../types/types'
import { useAuthStore } from '../store/authStore'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const method = options?.method || 'GET';
  const requestBody = options?.body ? JSON.parse(options.body as string) : undefined;
  const token = useAuthStore.getState().token
  
  // Log request structure (skip health check to avoid spam; tylko w DEV — review 2026-07-15)
  if (import.meta.env.DEV && path !== '/api/health') {
    console.group(`🚀 API Request: ${method} ${path}`);
    console.log('URL:', `${BASE_URL}${path}`);
    if (requestBody) {
      console.log('Body:', requestBody);
    }
    if (options?.headers) {
      console.log('Headers:', options.headers);
    }
    console.groupEnd();
  }

  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options?.headers,
      },
      ...options,
    })
    
    if (!res.ok) {
      if (res.status === 401 && token) {
        useAuthStore.getState().logout()
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
      const text = await res.text()
      if (path !== '/api/health') {
        console.error(`❌ API Error ${res.status}: ${method} ${path}`, text);
      }
      throw new Error(`API ${res.status}: ${text}`)
    }
    
    const data = await res.json() as Promise<T>;
    
    if (import.meta.env.DEV && path !== '/api/health') {
      console.group(`✅ API Response: ${method} ${path}`);
      console.log('Status:', res.status);
      console.log('Data:', data);
      console.groupEnd();
    }
    
    return data;
  } catch (error) {
    if (path !== '/api/health') {
      console.error(`💥 API Request Failed: ${method} ${path}`, error);
    }
    throw error;
  }
}

type ApiResponse<T> = { success: boolean; data: T; error: string | null }

export const api = {
  health: {
    get: () => request<{ status: string; version: string }>('/api/health'),
  },

  auth: {
    login: (payload: { username: string; password: string }) =>
      request<ApiResponse<{ access_token: string; token_type: string; user_id: number; username: string; role: string }>>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    me: () => request<ApiResponse<{ id: number; username: string; role: string; is_active: boolean; created_at: string }>>('/api/auth/me'),
    authStatus: () => request<ApiResponse<{ auth_enabled: boolean }>>('/api/auth/auth-status'),
    listUsers: () => request<ApiResponse<{ id: number; username: string; role: string; is_active: boolean; created_at: string }[]>>('/api/auth/users'),
    createUser: (payload: { username: string; password: string; role?: string }) =>
      request<ApiResponse<{ id: number; username: string; role: string; is_active: boolean; created_at: string }>>('/api/auth/users', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    updateUser: (id: number, payload: { username?: string; password?: string; role?: string; is_active?: boolean }) =>
      request<ApiResponse<{ id: number; username: string; role: string; is_active: boolean; created_at: string }>>(`/api/auth/users/${id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      }),
    deleteUser: (id: number) =>
      request<ApiResponse<null>>(`/api/auth/users/${id}`, { method: 'DELETE' }),
  },

  strategies: {
    list: () => request<ApiResponse<StrategyData[]>>('/api/strategies/'),
    get: (id: number) => request<ApiResponse<StrategyData>>(`/api/strategies/${id}`),
    create: (payload: components['schemas']['StrategyCreate']) =>
      request<ApiResponse<StrategyData>>('/api/strategies/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    update: (id: number, payload: components['schemas']['StrategyCreate']) =>
      request<ApiResponse<StrategyData>>(`/api/strategies/${id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      }),
    delete: (id: number) =>
      request<ApiResponse<{ id: string }>>(`/api/strategies/${id}`, {
        method: 'DELETE',
      }),
  },

  backtest: {
    trigger: (payload: components['schemas']['BacktestRequest']) =>
      request<ApiResponse<BacktestJobData>>('/api/backtest/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    triggerDag: (payload: { strategy_id: number; dag: any }) =>
      request<ApiResponse<BacktestJobData>>('/api/backtest/dag', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    status: (jobId: number) =>
      request<ApiResponse<BacktestJobData>>(`/api/backtest/${jobId}`),
    list: () => request<ApiResponse<BacktestJobData[]>>('/api/backtest/'),
  },

  indicators: {
    list: () => request<ApiResponse<any[]>>('/api/indicators/'),
  },

  optimizer: {
    trigger: (payload: components['schemas']['OptimizationRequest']) =>
      request<ApiResponse<{ job_id: number }>>('/api/optimizer/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    triggerWfo: (payload: components['schemas']['WalkForwardRequest']) =>
      request<ApiResponse<{ job_id: number }>>('/api/optimizer/wfo', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    status: (jobId: number) =>
      request<ApiResponse<any>>(`/api/optimizer/${jobId}`),
    list: () => request<ApiResponse<any[]>>('/api/optimizer/'),
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
