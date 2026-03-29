--- frontend/src/flows/nodes/PortfolioNode.tsx
+++ frontend/src/flows/nodes/PortfolioNode.tsx
@@ -1,5 +1,6 @@
 import { Handle, Position } from 'reactflow'
 import type { PortfolioNodeData } from '../../types'
+import { useChatStore } from '../../store/chatStore'

 interface Props {
   data: PortfolioNodeData
@@ -21,6 +22,7 @@

 export function PortfolioNode({ data }: Props) {
   const { jobStatus, metrics, error } = data
+  const openChat = useChatStore(state => state.openChat)

   const isPending = jobStatus === 'PENDING'
   const isRunning = jobStatus === 'RUNNING'
@@ -69,9 +71,15 @@
               value={metrics.final_capital != null ? `$${metrics.final_capital.toLocaleString('en-US', { maximumFractionDigits: 0 })}` : '—'}
             />
             <div className="rf-action-row" style={{ marginTop: '1rem', display: 'flex', justifyContent: 'center' }}>
-              <button disabled title="Integration pending via MCP" style={{ padding: '0.5rem 1rem', cursor: 'not-allowed', opacity: 0.6, backgroundColor: '#333', color: '#fff', border: '1px solid #555', borderRadius: '4px' }}>
+              <button
+                onClick={() => {
+                  if (data.jobId) openChat(data.jobId);
+                }}
+                title="Analyze via AI"
+                style={{ padding: '0.5rem 1rem', cursor: 'pointer', backgroundColor: '#81ecff', color: '#003840', border: '1px solid #00d4ec', borderRadius: '4px', fontWeight: 'bold' }}
+              >
                 Analyze Results via AI (MCP)
               </button>
             </div>
