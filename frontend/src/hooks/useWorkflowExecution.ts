/**
 * useWorkflowExecution — connects the canvas to the backend.
 *
 * Flow:
 *  1. Read DataNode + IndicatorNode data from the Zustand store.
 *  2. POST /api/strategies/ to create/reuse a strategy.
 *  3. POST /api/backtest/ with the extracted parameters.
 *  4. Poll GET /api/backtest/{job_id} every 2.5s until COMPLETED or FAILED.
 *  5. Write results back to the PortfolioNode via updatePortfolioResult.
 */

import { useCallback, useRef } from 'react'
import { useWorkflowStore } from '../store/workflowStore'
import { api } from '../services/api'
import type { BacktestMetrics, JobStatus } from '../types/types'

const POLL_INTERVAL_MS = 2500
const MAX_POLL_ATTEMPTS = 120 // 5 minutes hard cap

export function useWorkflowExecution() {
  const { nodes, isRunning, setJobState, updatePortfolioResult, resetExecution } = useWorkflowStore()
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollTimer.current) {
      clearInterval(pollTimer.current)
      pollTimer.current = null
    }
  }, [])

  const runBacktest = useCallback(async () => {
    if (isRunning) return

    // 1. Extract parameters from canvas nodes
    const dataNode = nodes.find((n) => n.type === 'dataNode')
    const indicatorNode = nodes.find((n) => n.type === 'indicatorNode')

    if (!dataNode || !indicatorNode) {
      alert('The canvas must contain a Data node and an Indicator node.')
      return
    }

    const symbol: string = dataNode.data?.symbol ?? 'SYNTHETIC'
    const smaFast: number = Number(indicatorNode.data?.smaFast ?? 10)
    const smaSlow: number = Number(indicatorNode.data?.smaSlow ?? 30)
    const initialCapital: number = Number(indicatorNode.data?.initialCapital ?? 10000)

    if (smaFast >= smaSlow) {
      alert('Fast SMA must be smaller than Slow SMA.')
      return
    }

    setJobState(true, null, 'PENDING')

    try {
      // 2. Create strategy record
      const stratRes = await api.strategies.create({
        name: `${symbol} SMA(${smaFast}/${smaSlow}) — ${new Date().toLocaleTimeString()}`,
        description: 'Created from WorkflowEditor',
        parameters: { symbol, sma_fast: smaFast, sma_slow: smaSlow, initial_capital: initialCapital },
      })
      const strategyId = (stratRes.data as { id: number }).id

      // 3. Trigger backtest
      const jobRes = await api.backtest.trigger({
        strategy_id: strategyId,
        symbol,
        sma_fast: smaFast,
        sma_slow: smaSlow,
        initial_capital: initialCapital,
      })
      const jobId = jobRes.data.job_id
      setJobState(true, jobId, 'PENDING')

      // 4. Poll for completion
      let attempts = 0
      pollTimer.current = setInterval(async () => {
        attempts++
        if (attempts > MAX_POLL_ATTEMPTS) {
          stopPolling()
          updatePortfolioResult(null, 'FAILED', jobId, 'Timed out after 5 minutes')
          return
        }
        try {
          const statusRes = await api.backtest.status(jobId)
          const jobData = statusRes.data
          const status = jobData.status as JobStatus

          setJobState(status !== 'COMPLETED' && status !== 'FAILED', jobId, status)

          if (status === 'COMPLETED') {
            stopPolling()
            updatePortfolioResult(
              jobData.metrics as BacktestMetrics | null,
              'COMPLETED',
              jobId
            )
          } else if (status === 'FAILED') {
            stopPolling()
            updatePortfolioResult(null, 'FAILED', jobId, jobData.error_message)
          }
        } catch (err) {
          console.error('Poll error:', err)
        }
      }, POLL_INTERVAL_MS)

    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setJobState(false, null, 'FAILED', msg)
      updatePortfolioResult(null, 'FAILED', 0, msg)
    }
  }, [nodes, isRunning, setJobState, updatePortfolioResult, stopPolling])

  return { runBacktest, stopPolling: () => { stopPolling(); resetExecution() }, isRunning }
}
