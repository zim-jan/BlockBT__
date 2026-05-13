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
    OptimizerNodeData,
    PortfolioNodeData,
    WfoNodeData,
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
  updateNodeData: (nodeId: string, data: Partial<DataNodeData & IndicatorNodeData & PortfolioNodeData & OptimizerNodeData>) => void
  addNode: (type: string) => void
  setJobState: (isRunning: boolean, jobId: number | null, status: JobStatus | null, error?: string | null) => void
  updatePortfolioResult: (metrics: BacktestMetrics | null, status: JobStatus, jobId: number, error?: string | null) => void
  updateOptimizerResult: (bestParams: Record<string, any> | null, bestValue: number | null, trials: any[] | null, status: JobStatus, jobId: number, error?: string | null) => void
  updateWfoResult: (results: any, status: JobStatus, jobId: number, error?: string | null) => void
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
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, ...data } } : n
      ),
    })),

  clearCanvas: () => set({ nodes: [], edges: [] }),

  setWorkflow: (nodes, edges) => set({ nodes, edges }),

  addNode: (type) => {
    nodeCounter++
    const id = `${type}-${nodeCounter}`
    const baseX = 100 + (get().nodes.length * 80) % 600
    const baseY = 100 + (Math.floor(get().nodes.length / 4) * 120)

    const defaultData: Record<string, Record<string, unknown>> = {
      dataNode: { symbol: 'AAPL', dataSource: 'yahoo', startDate: '2023-01-01', endDate: '2025-01-01', timeframe: '1d' },
      indicatorNode: { indicatorType: 'sma_crossover', smaFast: 10, smaSlow: 30, initialCapital: 10000 },
      signalNode: { signalType: 'sma_crossover' },
      portfolioNode: {},
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
          ? { ...n, data: { ...n.data, jobStatus: status, metrics, jobId, error } satisfies PortfolioNodeData }
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
          ? { ...n, data: { ...n.data as OptimizerNodeData, jobStatus: status, bestParameters: bestParams ?? undefined, bestValue: bestValue ?? undefined, trials: trials ?? undefined, jobId, error } }
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
          ? { ...n, data: { ...n.data as WfoNodeData, jobStatus: status, results, jobId, error } }
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
          return { ...n, data: { jobStatus: undefined, metrics: undefined, jobId: undefined, error: undefined } }
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
