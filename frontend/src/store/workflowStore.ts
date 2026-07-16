/**
 * Zustand store for React Flow workflow state.
 * Manages nodes, edges, execution status.
 */

import {create} from 'zustand'
import {
    addEdge,
    applyEdgeChanges,
    applyNodeChanges,
    type Edge,
    type Node,
    type OnConnect,
    type OnEdgesChange,
    type OnNodesChange,
} from '@xyflow/react'
import type {
    BacktestMetrics,
    DAGGraph,
    DataNodeData,
    IndicatorNodeData,
    JobStatus,
    MultiBacktestResult,
    OptimizerNodeData,
    PortfolioNodeData,
    WfoNodeData,
    WfoResults,
} from '../types/types'
import { NODE_TYPE_CATEGORY_MAP } from '../types/types'

// ---------------------------------------------------------------------------
// Initial canvas nodes — empty for testing
// ---------------------------------------------------------------------------

const initialNodes: Node[] = []
const initialEdges: Edge[] = []

// ---------------------------------------------------------------------------
// Store interface
// ---------------------------------------------------------------------------

interface WorkflowState {
  nodes: Node[]
  edges: Edge[]
  onNodesChange: OnNodesChange
  onEdgesChange: OnEdgesChange
  onConnect: OnConnect

  // Execution state
  isRunning: boolean
  activeJobId: number | null
  jobStatus: JobStatus | null
  errorMessage: string | null

  // UI state
  isEasyConnectMode: boolean
  toggleEasyConnectMode: () => void

  // Node data setters
  updateNodeData: (nodeId: string, data: Partial<DataNodeData & IndicatorNodeData & PortfolioNodeData & OptimizerNodeData & WfoNodeData>) => void
  addNode: (type: string) => void
  setJobState: (isRunning: boolean, jobId: number | null, status: JobStatus | null, error?: string | null) => void
  updatePortfolioResult: (metrics: BacktestMetrics | MultiBacktestResult | null, status: JobStatus, jobId: number, error?: string | null) => void
  updateOptimizerResult: (bestParams: Record<string, any> | null, bestValue: number | null, trials: any[] | null, status: JobStatus, jobId: number, error?: string | null) => void
  updateWfoResult: (results: WfoResults | null, status: JobStatus, jobId: number, error?: string | null) => void
  resetExecution: () => void
  clearCanvas: () => void
  setWorkflow: (nodes: Node[], edges: Edge[]) => void
  exportDAG: () => DAGGraph
}

let nodeCounter = 10

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: initialNodes,
  edges: initialEdges,

  onNodesChange: (changes) =>
    set((s) => ({ nodes: applyNodeChanges(changes, s.nodes) })),

  onEdgesChange: (changes) =>
    set((s) => ({ edges: applyEdgeChanges(changes, s.edges) })),

  onConnect: (connection) =>
    set((s) => ({ edges: addEdge({ ...connection, animated: true }, s.edges) })),

  isRunning: false,
  activeJobId: null,
  jobStatus: null,
  errorMessage: null,

  isEasyConnectMode: false,
  toggleEasyConnectMode: () => set((s) => ({ isEasyConnectMode: !s.isEasyConnectMode })),

  updateNodeData: (nodeId, data) =>
    set((s) => {
      const updatedNode = s.nodes.find((n) => n.id === nodeId)
      const isDependencyNode = updatedNode && ['dataNode', 'indicatorNode', 'signalNode', 'timeShiftNode'].includes(updatedNode.type ?? '')
      
      return {
        nodes: s.nodes.map((n) => {
          if (n.id === nodeId) {
            return { ...n, data: { ...n.data, ...data } }
          }
          // If a dependency node was updated, reset execution nodes completely
          if (isDependencyNode && ['portfolioNode', 'optimizerNode', 'wfoNode'].includes(n.type ?? '')) {
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const { jobStatus, metrics, jobId, error, isOutdated, results, bestParameters, bestValue, trials, ...restData } = n.data as any;
            return { ...n, data: restData }
          }
          return n
        }),
      }
    }),

  clearCanvas: () => set({ nodes: [], edges: [] }),

  setWorkflow: (nodes, edges) => set({ nodes, edges }),

  addNode: (type) => {
    nodeCounter++
    const id = `${type}-${nodeCounter}`
    const baseX = 100 + (get().nodes.length * 80) % 600
    const baseY = 100 + (Math.floor(get().nodes.length / 4) * 120)

    const defaultData: Record<string, Record<string, unknown>> = {
      dataNode: {
        symbol: 'AAPL', dataSource: 'yahoo', startDate: '2023-01-01', endDate: '2025-01-01', timeframe: '1d',
        point_in_time_enforcement: true // NOWE
      },
      indicatorNode: { indicatorType: 'sma_crossover', smaFast: 10, smaSlow: 30 },
      signalNode: {
        signalType: 'sma_crossover',
        operator_type: 'time_shift', // NOWE (Domyślnie wymuszamy shift)
        shift_periods: 1
      },
      timeShiftNode: {
        operator_type: 'time_shift',
        shift_periods: 1
      },
      portfolioNode: {
        init_cash: 10000,
        fees: 0.001,     // NOWE (Wymuszone przez backend)
        slippage: 0.001  // NOWE (Wymuszone przez backend)
      },
      optimizerNode: { 
        metric: 'Total Return [%]', 
        nTrials: 20, 
        paramBounds: {
          sma_fast: { min: 5, max: 20, type: 'int' },
          sma_slow: { min: 25, max: 50, type: 'int' }
        }
      },
      wfoNode: {
        windowSize: '365d',
        stepSize: '90d'
      },
    }

    const category = NODE_TYPE_CATEGORY_MAP[type] ?? 'DataIngestion'

    set((s) => ({
      nodes: [
        ...s.nodes,
        {
          id,
          type,
          position: { x: baseX, y: baseY },
          data: { ...((defaultData[type] ?? {}) as Record<string, unknown>), category },
        } as Node,
      ],
    }))
  },

  setJobState: (isRunning, jobId, status, error = null) =>
    set({ isRunning, activeJobId: jobId, jobStatus: status, errorMessage: error }),

  updatePortfolioResult: (metrics, status, jobId, error = null) =>
    set((s) => ({
      activeJobId: jobId,
      jobStatus: status,
      isRunning: false,
      errorMessage: error ?? null,
      nodes: s.nodes.map((n) =>
        n.type === 'portfolioNode'
          ? { ...n, data: { ...n.data, jobStatus: status, metrics, jobId, error, isOutdated: false } satisfies PortfolioNodeData }
          : n
      ),
    })),

  updateOptimizerResult: (bestParams, bestValue, trials, status, jobId, error = null) =>
    set((s) => ({
      activeJobId: jobId,
      jobStatus: status,
      isRunning: false,
      errorMessage: error ?? null,
      nodes: s.nodes.map((n) =>
        n.type === 'optimizerNode'
          ? { ...n, data: { ...n.data as OptimizerNodeData, jobStatus: status, bestParameters: bestParams ?? undefined, bestValue: bestValue ?? undefined, trials: trials ?? undefined, jobId, error, isOutdated: false } }
          : n
      ),
    })),

  updateWfoResult: (results, status, jobId, error = null) =>
    set((s) => ({
      activeJobId: jobId,
      jobStatus: status,
      isRunning: false,
      errorMessage: error ?? null,
      nodes: s.nodes.map((n) =>
        n.type === 'wfoNode'
          ? { ...n, data: { ...n.data as WfoNodeData, jobStatus: status, results, jobId, error, isOutdated: false } }
          : n
      ),
    })),

  resetExecution: () =>
    set((s) => ({
      isRunning: false,
      activeJobId: null,
      jobStatus: null,
      errorMessage: null,
      nodes: s.nodes.map((n) => {
        if (n.type === 'portfolioNode') {
          // FIX (review 2026-07-15): spread ...n.data — inaczej reset kasował init_cash/fees/slippage/sl_stop/tp_stop/size (Faza 12)
          return { ...n, data: { ...n.data, jobStatus: undefined, metrics: undefined, jobId: undefined, error: undefined } }
        }
        if (n.type === 'optimizerNode') {
          return { ...n, data: { ...n.data, jobStatus: undefined, bestParameters: undefined, bestValue: undefined, trials: undefined, jobId: undefined, error: undefined } }
        }
        if (n.type === 'wfoNode') {
          return { ...n, data: { ...n.data as WfoNodeData, jobStatus: undefined, results: undefined, jobId: undefined, error: undefined } }
        }
        return n
      }),
    })),

  exportDAG: () => {
    const { nodes, edges } = get()
    const metaTypes = new Set(['optimizerNode', 'wfoNode'])

    const dagNodes = nodes
      .filter((n) => !metaTypes.has(n.type ?? ''))
      .map((n) => {
        const category = NODE_TYPE_CATEGORY_MAP[n.type ?? ''] ?? 'DataIngestion'
        const { jobStatus: _js, metrics: _m, jobId: _jid, error: _e, category: _cat, ...params } = n.data as Record<string, unknown>

        // Faza 10: DataIngestion — symbol wspiera wiele tickerów (rozdzielone przecinkami)
        if (category === 'DataIngestion' && typeof params.symbol === 'string') {
          const raw = params.symbol as string
          // Review Fazy 10: trim + upper + filtracja pustych + DEDUPLIKACJA (kolizja kolumn po unstack)
          const tickers = Array.from(
            new Set(raw.split(',').map((s) => s.trim().toUpperCase()).filter(Boolean)),
          )
          // Review Fazy 10: dokladnie 1 ticker → string (spojnosc z single-symbol), inaczej lista
          params.symbol = tickers.length <= 1 ? (tickers[0] ?? '') : tickers
        }

        return {
          id: n.id,
          type: n.type ?? 'unknown',
          category,
          position: n.position,
          params,
        }
      })

    const metaNodes = nodes
      .filter((n) => metaTypes.has(n.type ?? ''))
      .map((n) => {
        // Infer target_nodes: nodes that this meta node connects to via edges
        const targetIds = edges
          .filter((e) => e.source === n.id)
          .map((e) => e.target)
        const { jobStatus: _js, jobId: _jid, error: _e, category: _cat, ...params } = n.data as Record<string, unknown>
        return {
          id: n.id,
          type: n.type ?? 'unknown',
          category: 'Meta' as const,
          position: n.position,
          params,
          target_nodes: targetIds,
        }
      })

    // Exclude edges from/to meta nodes (they use target_nodes instead)
    const dagEdges = edges
      .filter((e) => {
        const sourceNode = nodes.find((n) => n.id === e.source)
        const targetNode = nodes.find((n) => n.id === e.target)
        return !metaTypes.has(sourceNode?.type ?? '') && !metaTypes.has(targetNode?.type ?? '')
      })
      .map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: (e as any).sourceHandle ?? null,
        targetHandle: (e as any).targetHandle ?? null,
      }))

    return { nodes: dagNodes, edges: dagEdges, meta_nodes: metaNodes }
  },
}))
