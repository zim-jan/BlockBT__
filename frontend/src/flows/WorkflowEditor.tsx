import {useCallback} from 'react'
import ReactFlow, {Background, Controls, MiniMap, Panel,} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import {useWorkflowStore} from '../store/workflowStore'
import {useWorkflowExecution} from '../hooks/useWorkflowExecution'

import {DataNode} from './nodes/DataNode'
import {IndicatorNode} from './nodes/IndicatorNode'
import {SignalNode} from './nodes/SignalNode'
import {PortfolioNode} from './nodes/PortfolioNode'

const nodeTypes = {
  dataNode: DataNode,
  indicatorNode: IndicatorNode,
  signalNode: SignalNode,
  portfolioNode: PortfolioNode,
}

export function WorkflowEditor() {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
  } = useWorkflowStore()

  const { runBacktest, isRunning } = useWorkflowExecution()

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

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
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={16} />
        <Controls />
        <MiniMap nodeStrokeWidth={3} />
        <Panel position="top-center" className="workflow-toolbar" style={{ display: 'flex', gap: '10px', background: '#1a1a1a', padding: '10px', borderRadius: '8px', border: '1px solid #333' }}>
          <button onClick={() => addNode('dataNode')} className="toolbar-btn">Add Data Node</button>
          <button onClick={() => addNode('indicatorNode')} className="toolbar-btn">Add Indicator Node</button>
          <button onClick={() => addNode('signalNode')} className="toolbar-btn">Add Signal Node</button>
          <button onClick={() => addNode('portfolioNode')} className="toolbar-btn">Add Portfolio Node</button>
          <button
            onClick={runBacktest}
            disabled={isRunning}
            className="toolbar-btn run-btn"
            style={{ marginLeft: '20px', backgroundColor: isRunning ? '#555' : '#007bff', color: 'white', fontWeight: 'bold' }}
          >
            {isRunning ? 'RUNNING...' : 'RUN BACKTEST'}
          </button>
        </Panel>
      </ReactFlow>
    </div>
  )
}
