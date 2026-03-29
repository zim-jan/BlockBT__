--- frontend/src/App.tsx
+++ frontend/src/App.tsx
@@ -2,12 +2,10 @@
 import './App.css'
 import { WorkflowEditor } from './flows/WorkflowEditor'
 import { MainLayout } from './components/Layout/MainLayout'
 import { SlideOutChatPanel } from './components/ChatPanel/SlideOutChatPanel'
-import { useEffect } from 'react'
-import { useChatStore } from './store/chatStore'

 interface HealthResponse {
   status: string
 }

 function App() {
@@ -22,14 +20,6 @@
     refetchInterval: 10_000,
   })

-  // For Playwright Testing
-  const openChat = useChatStore(state => state.openChat)
-  useEffect(() => {
-    const handleForceOpen = () => openChat(1);
-    window.addEventListener('force-open-chat', handleForceOpen);
-    return () => window.removeEventListener('force-open-chat', handleForceOpen);
-  }, [openChat])
-
   return (
     <MainLayout>
       {/* Absolute positioned health indicator over the flow canvas */}
