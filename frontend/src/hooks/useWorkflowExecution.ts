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

import {useCallback, useEffect, useRef} from 'react'
import {useWorkflowStore} from '../store/workflowStore'
import {api} from '../services/api'
import type {components} from '../services/api.d'
import type {BacktestMetrics, DataNodeData, IndicatorNodeData, JobStatus} from '../types/types'

const POLL_INTERVAL_MS = 2500
const MAX_POLL_ATTEMPTS = 120 // 5-minute hard cap

export function useWorkflowExecution() {
  const { nodes, edges, isRunning, setJobState, updatePortfolioResult, resetExecution, exportDAG } = useWorkflowStore()
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollTimer.current) {
      clearInterval(pollTimer.current)
      pollTimer.current = null
    }
  }, [])

  const runBacktest = useCallback(async () => {
    if (isRunning) return

    // 1. Extract and validate nodes
    const dataNode = nodes.find((n) => n.type === 'dataNode')
    const indicatorNode = nodes.find((n) => n.type === 'indicatorNode')
    const portfolioNode = nodes.find((n) => n.type === 'portfolioNode')

    if (!dataNode || !indicatorNode || !portfolioNode) {
      alert('The canvas must contain a Data node, an Indicator node, and a Portfolio node.')
      return
    }

    // Edge validation is delegated to backend GraphParser via /api/backtest/dag
    if (edges.length === 0) {
      alert('Nodes must be connected. Use edges to link Data → Indicator → Portfolio.')
      return
    }

    const dData = dataNode.data as unknown as DataNodeData
    const iData = indicatorNode.data as unknown as IndicatorNodeData

    const symbol: string = dData.symbol ?? 'AAPL'
    const dataSource: string = dData.dataSource ?? 'yahoo'
    const startDate: string = dData.startDate ?? '2023-01-01'
    const endDate: string = dData.endDate ?? '2025-01-01'

    const indicatorType: string = iData.indicatorType ?? 'sma_crossover'
    const smaFast: number = Number(iData.smaFast ?? 10)
    const smaSlow: number = Number(iData.smaSlow ?? 30)
    const initialCapital: number = Number(iData.initialCapital ?? 10000)
    const codeContent: string = iData.codeContent ?? ""

    // SMA validation (only for SMA crossover)
    if (indicatorType === 'sma_crossover' && smaFast >= smaSlow) {
      alert('Fast SMA must be smaller than Slow SMA.')
      return
    }

    setJobState(true, null, 'PENDING')

    try {
      // 2. Build strategy name based on indicator type
      let strategyName = ""
      if (indicatorType === 'macd') {
        strategyName = `${symbol} MACD(${iData.macdFast ?? 12}/${iData.macdSlow ?? 26}/${iData.macdSignal ?? 9})`
      } else if (indicatorType === 'custom') {
        strategyName = `${symbol} Custom Logic`
      } else {
        strategyName = `${symbol} SMA(${smaFast}/${smaSlow})`
      }

      const dagPayload = exportDAG()

      const stratRes = await api.strategies.create({
        code_content: codeContent,
        name: `${strategyName} — ${new Date().toLocaleTimeString()} (DAG)`,
        description: `Created from WorkflowEditor [${dataSource}] with DAG`,
        parameters: dagPayload as Record<string, unknown>
      })
      const strategyId = (stratRes.data as { id: number }).id

      // 3. Trigger backtest using DAG endpoint
      const jobRes = await api.backtest.triggerDag({
        strategy_id: strategyId,
        dag: dagPayload
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
            console.log('✅ useWorkflowExecution: COMPLETED. Raw jobData:', jobData)
            
            // Map metrics safely, ensuring we pull from both root and nested object
            const jd = jobData as any
            const rawMetrics = (jd.metrics || {}) as Record<string, any>
            const finalMetrics: BacktestMetrics = {
              engine: jd.parameters?.engine ?? 'vectorbt',
              symbol: symbol,
              data_source: dataSource,
              strategy_type: indicatorType,
              sma_fast: smaFast,
              sma_slow: smaSlow,
              n_days: 0, // Calculated later or ignored for now
              initial_capital: initialCapital,
              total_return_pct: jd.total_return_pct ?? rawMetrics.total_return_pct ?? 0,
              sharpe_ratio: jd.sharpe_ratio ?? rawMetrics.sharpe_ratio ?? 0,
              max_drawdown_pct: jd.max_drawdown_pct ?? rawMetrics.max_drawdown_pct ?? 0,
              num_trades: jd.num_trades ?? rawMetrics.num_trades ?? 0,
              final_capital: jd.final_capital ?? rawMetrics.final_capital ?? initialCapital,
              win_rate_pct: rawMetrics.win_rate_pct ?? 0,
              equity_curve: jd.equity_curve || rawMetrics.equity_curve,
            }
            
            console.log('📦 useWorkflowExecution: Formatted metrics for store:', finalMetrics)

            updatePortfolioResult(
              finalMetrics,
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
  }, [nodes, edges, isRunning, setJobState, updatePortfolioResult, stopPolling])

  // Cleanup polling timer on unmount to prevent memory leaks
  useEffect(() => () => stopPolling(), [stopPolling])

  return { runBacktest, stopPolling: () => { stopPolling(); resetExecution() }, isRunning }
}
