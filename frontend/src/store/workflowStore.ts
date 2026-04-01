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
} from 'reactflow'
import type {
    BacktestMetrics,
    DataNodeData,
    IndicatorNodeData,
    JobStatus,
    PortfolioNodeData,
    SignalNodeData,
} from '../types/types'

// ---------------------------------------------------------------------------
// Initial canvas nodes — the four-step pipeline as a starting template
// ---------------------------------------------------------------------------

const initialNodes: Node[] = [
  {
    id: 'data-1',
    type: 'dataNode',
    position: { x: 60, y: 200 },
    data: { symbol: 'AAPL', dataSource: 'yahoo', startDate: '2023-01-01', endDate: '2025-01-01', timeframe: '1d' } satisfies DataNodeData,
  },
  {
    id: 'indicator-1',
    type: 'indicatorNode',
    position: { x: 320, y: 160 },
    data: { indicatorType: 'sma_crossover', smaFast: 10, smaSlow: 30, initialCapital: 10000 } satisfies IndicatorNodeData,
  },
  {
    id: 'signal-1',
    type: 'signalNode',
    position: { x: 600, y: 200 },
    data: { signalType: 'sma_crossover' } satisfies SignalNodeData,
  },
  {
    id: 'portfolio-1',
    type: 'portfolioNode',
    position: { x: 860, y: 140 },
    data: {} satisfies PortfolioNodeData,
  },
]

const initialEdges: Edge[] = [
  { id: 'e1', source: 'data-1', target: 'indicator-1', animated: true },
  { id: 'e2', source: 'indicator-1', target: 'signal-1', animated: true },
  { id: 'e3', source: 'signal-1', target: 'portfolio-1', animated: true },
]

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

  // Node data setters
  updateNodeData: (nodeId: string, data: Partial<DataNodeData & IndicatorNodeData & PortfolioNodeData>) => void
  addNode: (type: string) => void
  setJobState: (isRunning: boolean, jobId: number | null, status: JobStatus | null, error?: string | null) => void
  updatePortfolioResult: (metrics: BacktestMetrics | null, status: JobStatus, jobId: number, error?: string | null) => void
  resetExecution: () => void
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

  updateNodeData: (nodeId, data) =>
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, ...data } } : n
      ),
    })),

  addNode: (type) => {
    nodeCounter++
    const id = `${type}-${nodeCounter}`
    const baseX = 100 + (get().nodes.length * 80) % 600
    const baseY = 100 + (Math.floor(get().nodes.length / 4) * 120)

    const defaultData: Record<string, unknown> = {
      dataNode: { symbol: 'AAPL', dataSource: 'yahoo', startDate: '2023-01-01', endDate: '2025-01-01', timeframe: '1d' },
      indicatorNode: { indicatorType: 'sma_crossover', smaFast: 10, smaSlow: 30, initialCapital: 10000 },
      signalNode: { signalType: 'sma_crossover' },
      portfolioNode: {},
    }

    set((s) => ({
      nodes: [
        ...s.nodes,
        {
          id,
          type,
          position: { x: baseX, y: baseY },
          data: defaultData[type] ?? {},
        },
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

  resetExecution: () =>
    set((s) => ({
      isRunning: false,
      activeJobId: null,
      jobStatus: null,
      errorMessage: null,
      nodes: s.nodes.map((n) =>
        n.type === 'portfolioNode'
          ? { ...n, data: { jobStatus: undefined, metrics: undefined, jobId: undefined, error: undefined } }
          : n
      ),
    })),
}))
