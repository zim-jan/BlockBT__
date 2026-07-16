import {useCallback, useMemo, useState} from 'react'
import {ReactFlow, Background, Controls, MiniMap, Panel,} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {useWorkflowStore} from '../../store/workflowStore'
import {api} from '../../services/api'
import {StrategyListModal} from './StrategyListModal'
import FloatingEdge from './edges/FloatingEdge'
import FloatingConnectionLine from './edges/FloatingConnectionLine'

import DataNode from './nodes/DataNode'
import IndicatorNode from './nodes/IndicatorNode'
import {SignalNode} from './nodes/SignalNode'
import {TimeShiftNode} from './nodes/TimeShiftNode'
import {PortfolioNode} from './nodes/PortfolioNode'
import OptimizerNode from './nodes/OptimizerNode'
import {WfoNode} from './nodes/WfoNode'

const nodeTypes: any = {
  dataNode: DataNode,
  indicatorNode: IndicatorNode,
  signalNode: SignalNode,
  timeShiftNode: TimeShiftNode,
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
  } = useWorkflowStore()

  const [isModalOpen, setIsModalOpen] = useState(false)

  // Faza 9.2: typ krawędzi jest pochodną AKTUALNEGO trybu (floating vs default).
  // Wcześniej typ zapisywał się przy utworzeniu krawędzi (defaultEdgeOptions),
  // więc po przełączeniu Easy Connect graf renderował mieszane typy krawędzi.
  const displayEdges = useMemo(
    () => edges.map((e) => ({ ...e, type: isEasyConnectMode ? 'floating' : 'default' })),
    [edges, isEasyConnectMode],
  )

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const handleSave = async () => {
    if (nodes.length === 0) {
      alert('Cannot save an empty strategy.')
      return
    }

    const name = prompt('Enter strategy name:')
    if (!name) return

    const description = prompt('Enter strategy description (optional):') || ''

    try {
      const res = await api.strategies.create({
        name,
        description,
        parameters: { nodes, edges },
      } as any)
      
      if (res.success) {
        alert('Strategy saved successfully!')
      }
    } catch (err) {
      console.error('Failed to save strategy', err)
      alert('Failed to save strategy.')
    }
  }

  return (
    <div style={{ width: '100%', height: '100%' }} className={isEasyConnectMode ? 'easy-connect-active' : ''}>
      <ReactFlow
        nodes={nodes}
        edges={displayEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
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
        <Background gap={16} />
        <Controls />
        <MiniMap nodeStrokeWidth={3} />
        <Panel position="top-left" style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          <button onClick={() => addNode('dataNode')} className="toolbar-btn">Add Data Node</button>
          <button onClick={() => addNode('indicatorNode')} className="toolbar-btn">Add Indicator Node</button>
          <button onClick={() => addNode('signalNode')} className="toolbar-btn">Add Signal Node</button>
          <button onClick={() => addNode('timeShiftNode')} className="toolbar-btn" style={{ backgroundColor: '#f59e0b', color: '#000' }}>⏩ Add TimeShift</button>
          <button onClick={() => addNode('portfolioNode')} className="toolbar-btn">Add Portfolio Node</button>
          <button onClick={() => addNode('optimizerNode')} className="toolbar-btn">Add Optimizer Node</button>
          <button onClick={() => addNode('wfoNode')} className="toolbar-btn">Add WFO Node</button>

          <div style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '8px', padding: '5px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>
             <input 
               type="checkbox" 
               id="easy-connect-toggle" 
               checked={isEasyConnectMode} 
               onChange={toggleEasyConnectMode} 
             />
             <label htmlFor="easy-connect-toggle" style={{ fontSize: '12px', cursor: 'pointer', color: 'white' }}>Easy Connect</label>
          </div>
        </Panel>

        <Panel position="top-right" style={{ display: 'flex', gap: '10px' }}>
          <button onClick={handleSave} className="toolbar-btn" style={{ backgroundColor: '#28a745', color: 'white' }}>SAVE</button>
          <button onClick={() => setIsModalOpen(true)} className="toolbar-btn" style={{ backgroundColor: '#17a2b8', color: 'white' }}>LOAD</button>
          <button onClick={clearCanvas} className="toolbar-btn" style={{ backgroundColor: '#dc3545', color: 'white' }}>CLEAR</button>
        </Panel>
      </ReactFlow>

      <StrategyListModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  )
}
