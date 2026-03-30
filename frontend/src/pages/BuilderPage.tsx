import { WorkflowEditor } from '../features/visual_builder/WorkflowEditor'
import { MainLayout } from '../components/layout/MainLayout'
import { ChatPanel } from '../features/ai_chat/ChatPanel'
import { useChatStore } from '../store/chatStore'

export function BuilderPage() {
  const { isOpen, jobId, closeChat } = useChatStore()

  return (
    <MainLayout>
      <WorkflowEditor />
      <ChatPanel isOpen={isOpen} jobId={jobId} onClose={closeChat} />
    </MainLayout>
  )
}
