/**
 * useWorkflowOptimization — hook for triggering and polling Bayesian optimization.
 */

import {useCallback, useEffect, useRef} from 'react'
import {useWorkflowStore} from '../store/workflowStore'
import {api} from '../services/api'
import type {OptimizerNodeData, DataNodeData, IndicatorNodeData, JobStatus, WfoNodeData} from '../types/types'

const POLL_INTERVAL_MS = 2500
const MAX_POLL_ATTEMPTS = 120 // 5-minute hard cap

export function useWorkflowOptimization() {
  const { nodes, edges, isRunning, setJobState, updateOptimizerResult, updateWfoResult, updateNodeData } = useWorkflowStore()
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollTimer.current) {
      clearInterval(pollTimer.current)
      pollTimer.current = null
    }
  }, [])

  const runOptimization = useCallback(async () => {
    if (isRunning) return

    // 1. Identify nodes and validate connections
    const dataNode = nodes.find((n) => n.type === 'dataNode')
    const indicatorNode = nodes.find((n) => n.type === 'indicatorNode')
    const optimizerNode = nodes.find((n) => n.type === 'optimizerNode')

    if (!dataNode || !indicatorNode || !optimizerNode) {
      alert('The canvas must contain a Data node, an Indicator node, and an Optimizer node.')
      return
    }

    // Connections: Data -> Indicator -> Optimizer
    const isDataToIndicator = edges.some(e => e.source === dataNode.id && e.target === indicatorNode.id)
    const isIndicatorToOptimizer = edges.some(e => e.source === indicatorNode.id && e.target === optimizerNode.id)

    if (!isDataToIndicator || !isIndicatorToOptimizer) {
      alert('Required connections: Data -> Indicator -> Optimizer')
      return
    }

    const dData = dataNode.data as unknown as DataNodeData
    const iData = indicatorNode.data as unknown as IndicatorNodeData
    const oData = optimizerNode.data as unknown as OptimizerNodeData
    // Kapitał z bloku Portfolio, jeśli jest na kanwie (review 2026-07-16);
    // flow optymalizacji nie wymaga węzła Portfolio — wtedy default 10000
    const portfolioNode = nodes.find((n) => n.type === 'portfolioNode')
    const initialCapital = Number((portfolioNode?.data as Record<string, unknown> | undefined)?.init_cash ?? 10000)

    setJobState(true, null, 'PENDING')

    try {
      // Create a strategy first (or reuse logic if existing)
      const stratRes = await api.strategies.create({
        name: `Optimization: ${dData.symbol} ${iData.indicatorType} — ${new Date().toLocaleTimeString()}`,
        code_content: "",
        parameters: {
          strategy_type: iData.indicatorType,
          initial_capital: initialCapital,
          symbol: dData.symbol,
        }
      })
      const strategyId = (stratRes.data as any).id

      // Trigger optimization
      const optRes = await api.optimizer.trigger({
        strategy_id: strategyId,
        symbol: dData.symbol,
        data_source: dData.dataSource,
        timeframe: dData.timeframe,
        start_date: dData.startDate,
        end_date: dData.endDate,
        initial_capital: initialCapital,
        metric: oData.metric,
        n_trials: oData.nTrials,
        param_bounds: oData.paramBounds as any,
      })

      const jobId = (optRes.data as any).job_id
      setJobState(true, jobId, 'PENDING')

      let attempts = 0
      pollTimer.current = setInterval(async () => {
        attempts++
        if (attempts > MAX_POLL_ATTEMPTS) {
          stopPolling()
          updateOptimizerResult(null, null, null, 'FAILED', jobId, 'Optimization timed out')
          return
        }

        try {
          const statusRes = await api.optimizer.status(jobId)
          const jobData = statusRes.data as any
          const status = jobData.status as JobStatus

          setJobState(status !== 'COMPLETED' && status !== 'FAILED', jobId, status)

          if (status === 'COMPLETED') {
            stopPolling()
            updateOptimizerResult(
              jobData.best_parameters,
              jobData.best_value,
              jobData.trials_data?.trials || null,
              'COMPLETED',
              jobId
            )
          } else if (status === 'FAILED') {
            stopPolling()
            updateOptimizerResult(null, null, null, 'FAILED', jobId, jobData.error_message)
          }
        } catch (err) {
          console.error('Poll error:', err)
        }
      }, POLL_INTERVAL_MS)

    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setJobState(false, null, 'FAILED', msg)
      updateOptimizerResult(null, null, null, 'FAILED', 0, msg)
    }
  }, [nodes, edges, isRunning, setJobState, updateOptimizerResult, stopPolling])

  const runWfo = useCallback(async () => {
    if (isRunning) return

    const dataNode = nodes.find((n) => n.type === 'dataNode')
    const indicatorNode = nodes.find((n) => n.type === 'indicatorNode')
    const wfoNode = nodes.find((n) => n.type === 'wfoNode')

    if (!dataNode || !indicatorNode || !wfoNode) {
      alert('The canvas must contain Data, Indicator, and Walk-Forward nodes.')
      return
    }

    const isDataToIndicator = edges.some(e => e.source === dataNode.id && e.target === indicatorNode.id)
    const isIndicatorToWfo = edges.some(e => e.source === indicatorNode.id && e.target === wfoNode.id)

    if (!isDataToIndicator || !isIndicatorToWfo) {
      alert('Required connections: Data -> Indicator -> Walk-Forward')
      return
    }

    const dData = dataNode.data as unknown as DataNodeData
    const iData = indicatorNode.data as unknown as IndicatorNodeData
    const wData = wfoNode.data as unknown as WfoNodeData
    // Kapitał z bloku Portfolio, jeśli jest na kanwie (review 2026-07-16)
    const portfolioNode = nodes.find((n) => n.type === 'portfolioNode')
    const initialCapital = Number((portfolioNode?.data as Record<string, unknown> | undefined)?.init_cash ?? 10000)

    setJobState(true, null, 'PENDING')
    // Review 2026-07-16: status musi trafiać też do node.data — WfoNode czyta
    // wyłącznie lokalne data.jobStatus, globalny setJobState nie daje mu feedbacku
    updateNodeData(wfoNode.id, { jobStatus: 'PENDING', error: null, results: undefined })

    try {
      const stratRes = await api.strategies.create({
        name: `WFO: ${dData.symbol} ${iData.indicatorType} — ${new Date().toLocaleTimeString()}`,
        code_content: "",
        parameters: {
          strategy_type: iData.indicatorType,
          initial_capital: initialCapital,
          symbol: dData.symbol,
        }
      })
      const strategyId = (stratRes.data as any).id

      const wfoRes = await api.optimizer.triggerWfo({
        strategy_id: strategyId,
        symbol: dData.symbol,
        data_source: dData.dataSource,
        timeframe: dData.timeframe,
        start_date: dData.startDate,
        end_date: dData.endDate,
        initial_capital: initialCapital,
        window_size: wData.windowSize,
        step_size: wData.stepSize,
      })

      const jobId = (wfoRes.data as any).job_id
      setJobState(true, jobId, 'PENDING')

      let attempts = 0
      pollTimer.current = setInterval(async () => {
        attempts++
        if (attempts > MAX_POLL_ATTEMPTS) {
          stopPolling()
          updateWfoResult(null, 'FAILED', jobId, 'WFO timed out')
          return
        }

        try {
          const statusRes = await api.optimizer.status(jobId)
          const jobData = statusRes.data as any
          const status = jobData.status as JobStatus

          setJobState(status !== 'COMPLETED' && status !== 'FAILED', jobId, status)

          if (status === 'COMPLETED') {
            stopPolling()
            // Kompozycja wyników dla WfoNode: trials_data (okna + metryki zbiorcze OOS)
            // + best_parameters/best_value z poziomu jobu
            updateWfoResult(
              {
                ...(jobData.trials_data ?? {}),
                best_parameters: jobData.best_parameters ?? null,
                best_value: jobData.best_value ?? null,
              },
              'COMPLETED',
              jobId
            )
          } else if (status === 'FAILED') {
            stopPolling()
            updateWfoResult(null, 'FAILED', jobId, jobData.error_message)
          } else {
            updateNodeData(wfoNode.id, { jobStatus: status })
          }
        } catch (err) {
          console.error('Poll error:', err)
        }
      }, POLL_INTERVAL_MS)

    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setJobState(false, null, 'FAILED', msg)
      updateWfoResult(null, 'FAILED', 0, msg)
    }
  }, [nodes, edges, isRunning, setJobState, updateWfoResult, updateNodeData, stopPolling])

  useEffect(() => () => stopPolling(), [stopPolling])

  return { runOptimization, runWfo, isRunning }
}
