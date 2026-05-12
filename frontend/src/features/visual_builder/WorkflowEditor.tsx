import {useCallback, useState} from 'react'
import ReactFlow, {Background, Controls, MiniMap, Panel,} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {useWorkflowStore} from '../../store/workflowStore'
import {useWorkflowExecution} from '../../hooks/useWorkflowExecution'
import {api} from '../../services/api'
import {StrategyListModal} from './StrategyListModal'

import {DataNode} from './nodes/DataNode'
import {IndicatorNode} from './nodes/IndicatorNode'
import {SignalNode} from './nodes/SignalNode'
import {PortfolioNode} from './nodes/PortfolioNode'
import {OptimizerNode} from './nodes/OptimizerNode'

const nodeTypes = {
  dataNode: DataNode,
  indicatorNode: IndicatorNode,
  signalNode: SignalNode,
  portfolioNode: PortfolioNode,
  optimizerNode: OptimizerNode,
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
  } = useWorkflowStore()

  const { runBacktest, isRunning } = useWorkflowExecution()
  const [isModalOpen, setIsModalOpen] = useState(false)

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
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        onDragOver={onDragOver}
        deleteKeyCode={['Backspace', 'Delete']}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={16} />
        <Controls />
        <MiniMap nodeStrokeWidth={3} />
        <Panel position="top-left" style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          <button onClick={() => addNode('dataNode')} className="toolbar-btn">Add Data Node</button>
          <button onClick={() => addNode('indicatorNode')} className="toolbar-btn">Add Indicator Node</button>
          <button onClick={() => addNode('signalNode')} className="toolbar-btn">Add Signal Node</button>
          <button onClick={() => addNode('portfolioNode')} className="toolbar-btn">Add Portfolio Node</button>
          <button onClick={() => addNode('optimizerNode')} className="toolbar-btn">Add Optimizer Node</button>
        </Panel>

        <Panel position="top-right" style={{ display: 'flex', gap: '10px' }}>
          <button onClick={handleSave} className="toolbar-btn" style={{ backgroundColor: '#28a745', color: 'white' }}>SAVE</button>
          <button onClick={() => setIsModalOpen(true)} className="toolbar-btn" style={{ backgroundColor: '#17a2b8', color: 'white' }}>LOAD</button>
          <button onClick={clearCanvas} className="toolbar-btn" style={{ backgroundColor: '#dc3545', color: 'white' }}>CLEAR</button>
        </Panel>

        <Panel position="top-center" className="workflow-toolbar" style={{ display: 'flex', gap: '10px', background: '#1a1a1a', padding: '10px', borderRadius: '8px', border: '1px solid #333' }}>
          <button
            onClick={runBacktest}
            disabled={isRunning}
            className="toolbar-btn run-btn"
            style={{ backgroundColor: isRunning ? '#555' : '#007bff', color: 'white', fontWeight: 'bold', padding: '8px 20px' }}
          >
            {isRunning ? 'RUNNING...' : 'RUN BACKTEST'}
          </button>
        </Panel>
      </ReactFlow>

      <StrategyListModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  )
}
