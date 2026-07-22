import {WorkflowEditor} from '../features/visual_builder/WorkflowEditor'
import {MainLayout} from '../components/layout/MainLayout'
import {useWorkflowStore} from '../store/workflowStore'
import {SaveStrategyModal} from '../features/visual_builder/SaveStrategyModal'
import {StrategyListModal} from '../features/visual_builder/StrategyListModal'
import {ResultsOverlay} from '../components/ResultsOverlay'

export function BuilderPage() {
  const isSaveModalOpen = useWorkflowStore((s) => s.isSaveModalOpen)
  const setIsSaveModalOpen = useWorkflowStore((s) => s.setIsSaveModalOpen)
  const isLoadModalOpen = useWorkflowStore((s) => s.isLoadModalOpen)
  const setIsLoadModalOpen = useWorkflowStore((s) => s.setIsLoadModalOpen)

  return (
    <>
      <MainLayout>
        <WorkflowEditor />
      </MainLayout>
      <SaveStrategyModal isOpen={isSaveModalOpen} onClose={() => setIsSaveModalOpen(false)} />
      <StrategyListModal isOpen={isLoadModalOpen} onClose={() => setIsLoadModalOpen(false)} />
      <ResultsOverlay />
    </>
  )
}

