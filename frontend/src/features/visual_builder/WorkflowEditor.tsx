import {useCallback, useMemo} from 'react'
import {ReactFlow, Background, Controls, MiniMap, Panel,} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {useWorkflowStore} from '../../store/workflowStore'
import {showToast} from '../../store/useToastStore'
import FloatingEdge from './edges/FloatingEdge'
import FloatingConnectionLine from './edges/FloatingConnectionLine'

import DataNode from './nodes/DataNode'
import IndicatorNode from './nodes/IndicatorNode'
import {SignalNode} from './nodes/SignalNode'
import {PortfolioNode} from './nodes/PortfolioNode'
import OptimizerNode from './nodes/OptimizerNode'
import {WfoNode} from './nodes/WfoNode'
import { Trash2, Save, FolderOpen, Play, BarChart2, Plus } from 'lucide-react'
import { useWorkflowExecution } from '../../hooks/useWorkflowExecution'

const nodeTypes: any = {
  dataNode: DataNode,
  indicatorNode: IndicatorNode,
  signalNode: SignalNode,
  portfolioNode: PortfolioNode,
  optimizerNode: OptimizerNode,
  wfoNode: WfoNode,
}

const edgeTypes: any = {
  floating: FloatingEdge,
}

export function WorkflowEditor() {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
    clearCanvas,
    isEasyConnectMode,
    toggleEasyConnectMode,
    selectedNodeId,
    setSelectedNodeId,
    setIsSaveModalOpen,
    setIsLoadModalOpen,
    setIsResultsOpen
  } = useWorkflowStore()

  const { runBacktest, isRunning, canRunBacktest } = useWorkflowExecution()


  const isNodeSelected = Boolean(selectedNodeId || nodes.some((n) => n.selected))

  const displayEdges = useMemo(
    () => edges.map((e) => ({ ...e, type: isEasyConnectMode ? 'floating' : 'default' })),
    [edges, isEasyConnectMode],
  )

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const handleOpenSave = () => {
    console.log('[WorkflowEditor] Clicked Zapisz button', { nodesLength: nodes.length });
    if (nodes.length === 0) {
      alert('Pusta kanwa - dodaj węzły');
      showToast.warning('Pusta kanwa', 'Dodaj węzły przed zapisaniem strategii.')
      return
    }
    console.log('[WorkflowEditor] Setting isSaveModalOpen to true');
    setIsSaveModalOpen(true)
  }

  return (
    <div className={`w-full h-full relative overflow-hidden bg-[#0b0d14] ${isEasyConnectMode ? 'easy-connect-active' : ''}`}>
      <ReactFlow
        nodes={nodes}
        edges={displayEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={(_, node) => setSelectedNodeId(node.id)}
        onPaneClick={() => setSelectedNodeId(null)}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onDragOver={onDragOver}
        deleteKeyCode={['Backspace', 'Delete']}
        fitView
        connectionRadius={40}
        proOptions={{ hideAttribution: true }}
        connectionLineComponent={isEasyConnectMode ? FloatingConnectionLine : undefined}
        defaultEdgeOptions={{ animated: true }}
      >
        <Background gap={16} color="rgba(255, 255, 255, 0.08)" />
        <Controls />
        <MiniMap nodeStrokeWidth={3} maskColor="rgba(11, 13, 20, 0.7)" />

        {/* Left Toolbar: Add Nodes */}
        <Panel position="top-left" className="flex flex-col gap-2 bg-[#131722] p-3 rounded-xl border border-white/20 shadow-2xl">
          <div className="text-[12px] font-bold text-slate-200 uppercase tracking-wider mb-1 flex items-center gap-1.5 border-b border-white/10 pb-1.5">
            <Plus className="w-4 h-4 text-indigo-400" /> <span>Dodaj Węzeł</span>
          </div>
          <button onClick={() => addNode('dataNode')} className="px-3 py-1.5 text-xs font-semibold bg-[#1c2130] hover:bg-[#262c3e] border border-blue-500/40 text-blue-300 hover:text-blue-200 rounded-lg transition-colors text-left flex items-center gap-1">
            + Data Source
          </button>
          <button onClick={() => addNode('indicatorNode')} className="px-3 py-1.5 text-xs font-semibold bg-[#1c2130] hover:bg-[#262c3e] border border-purple-500/40 text-purple-300 hover:text-purple-200 rounded-lg transition-colors text-left flex items-center gap-1">
            + Indicator
          </button>
          <button onClick={() => addNode('signalNode')} className="px-3 py-1.5 text-xs font-semibold bg-[#1c2130] hover:bg-[#262c3e] border border-amber-500/40 text-amber-300 hover:text-amber-200 rounded-lg transition-colors text-left flex items-center gap-1">
            + Signal Logic
          </button>
          <button onClick={() => addNode('portfolioNode')} className="px-3 py-1.5 text-xs font-semibold bg-[#1c2130] hover:bg-[#262c3e] border border-emerald-500/40 text-emerald-300 hover:text-emerald-200 rounded-lg transition-colors text-left flex items-center gap-1">
            + Portfolio
          </button>
          <button onClick={() => addNode('optimizerNode')} className="px-3 py-1.5 text-xs font-semibold bg-[#1c2130] hover:bg-[#262c3e] border border-pink-500/40 text-pink-300 hover:text-pink-200 rounded-lg transition-colors text-left flex items-center gap-1">
            + Optuna Optimizer
          </button>
          <button onClick={() => addNode('wfoNode')} className="px-3 py-1.5 text-xs font-semibold bg-[#1c2130] hover:bg-[#262c3e] border border-pink-500/40 text-pink-300 hover:text-pink-200 rounded-lg transition-colors text-left flex items-center gap-1">
            + WFO Node
          </button>

          <div className="mt-2 pt-2 border-t border-white/10 flex items-center gap-2">
            <input 
              type="checkbox" 
              id="easy-connect-toggle" 
              checked={isEasyConnectMode} 
              onChange={toggleEasyConnectMode}
              className="accent-indigo-500 rounded cursor-pointer"
            />
            <label htmlFor="easy-connect-toggle" className="text-xs text-slate-200 cursor-pointer font-semibold">Easy Connect</label>
          </div>
        </Panel>

        {/* Right Toolbar: Global Actions (Shifts left when InspectorPanel opens) */}
        <Panel position="top-right" className={`flex items-center gap-2.5 bg-[#131722]/90 backdrop-blur-md p-2.5 rounded-xl border border-white/10 shadow-xl transition-all duration-300 ${isNodeSelected ? 'mr-96' : ''}`}>
          <button
            onClick={runBacktest}
            disabled={isRunning || !canRunBacktest}
            title={!canRunBacktest ? 'Dodaj wymagane węzły (Data, Indicator, Portfolio) i połącz je krawędziami' : ''}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>{isRunning ? 'Uruchamianie...' : 'RUN BACKTEST'}</span>
          </button>

          <button onClick={handleOpenSave} className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium bg-[#1c2130] hover:bg-[#262c3e] border border-white/10 text-slate-200 rounded-lg transition-colors">
            <Save className="w-3.5 h-3.5 text-indigo-400" />
            <span>Zapisz</span>
          </button>

          <button onClick={() => setIsLoadModalOpen(true)} className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium bg-[#1c2130] hover:bg-[#262c3e] border border-white/10 text-slate-200 rounded-lg transition-colors">
            <FolderOpen className="w-3.5 h-3.5 text-cyan-400" />
            <span>Wczytaj</span>
          </button>

          <button onClick={clearCanvas} className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium bg-[#1c2130] hover:bg-red-500/20 border border-red-500/30 text-red-400 rounded-lg transition-colors">
            <Trash2 className="w-3.5 h-3.5" />
            <span>Wyczyść</span>
          </button>

          <button 
            onClick={() => {
              console.log('[WorkflowEditor] Clicked Pokaz Wyniki');
              setIsResultsOpen(true);
            }} 
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/30 text-indigo-300 rounded-lg transition-colors ml-2"
          >
            <BarChart2 className="w-4 h-4" />
            <span>Pokaż Wyniki</span>
          </button>
        </Panel>
      </ReactFlow>

    </div>
  )
}
