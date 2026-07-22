import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { WorkflowEditor } from './WorkflowEditor'
import { ReactFlowProvider } from '@xyflow/react'
import { useWorkflowStore } from '../../store/workflowStore'

const renderWithProvider = (component: React.ReactNode) => {
  return render(
    <ReactFlowProvider>
      <div style={{ width: 800, height: 600 }}>
        {component}
      </div>
    </ReactFlowProvider>
  )
}

describe('WorkflowEditor', () => {
  beforeEach(() => {
    useWorkflowStore.getState().clearCanvas()
  })

  it('renders correctly', () => {
    renderWithProvider(<WorkflowEditor />)
    expect(screen.getByText(/Data Source/i)).toBeInTheDocument()
    expect(screen.getByText(/Zapisz/i)).toBeInTheDocument()
  })

  it('toggles Easy Connect mode', () => {
    renderWithProvider(<WorkflowEditor />)
    const toggle = screen.getByLabelText(/Easy Connect/i) as HTMLInputElement
    
    expect(toggle.checked).toBe(false)
    
    fireEvent.click(toggle)
    expect(toggle.checked).toBe(true)
    expect(useWorkflowStore.getState().isEasyConnectMode).toBe(true)
  })

  it('adds a node when button is clicked', async () => {
    renderWithProvider(<WorkflowEditor />)
    const addDataBtn = screen.getByText(/\+ Data Source/i)
    
    fireEvent.click(addDataBtn)
    
    await waitFor(() => {
      expect(useWorkflowStore.getState().nodes.length).toBe(1)
      expect(useWorkflowStore.getState().nodes[0].type).toBe('dataNode')
    })
  })
})
