--- frontend/src/App.tsx
+++ frontend/src/App.tsx
@@ -2,6 +2,7 @@
 import './App.css'
 import { WorkflowEditor } from './flows/WorkflowEditor'
 import { MainLayout } from './components/Layout/MainLayout'
+import { SlideOutChatPanel } from './components/ChatPanel/SlideOutChatPanel'

 interface HealthResponse {
   status: string
@@ -25,6 +26,7 @@
           {isLoading ? '⏳ Connecting...' : isError ? '🔴 API Offline' : `🟢 API ${health?.status}`}
       </div>
       <WorkflowEditor />
+      <SlideOutChatPanel />
     </MainLayout>
   )
 }
