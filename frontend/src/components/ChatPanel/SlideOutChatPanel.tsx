// import React, {useEffect, useRef} from 'react'
// import {useChatStore} from '../../store/chatStore'
// import './SlideOutChatPanel.css'
// import ReactMarkdown from 'react-markdown'
//
// export function SlideOutChatPanel() {
//   const { isOpen, closeChat, messages, isLoading, input, setInput, sendMessage } = useChatStore()
//   const messagesEndRef = useRef<HTMLDivElement>(null)
//
//   // Auto-scroll to bottom on new messages
//   useEffect(() => {
//     messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
//   }, [messages, isLoading])
//
//   if (!isOpen) return null
//
//   const handleSend = (e: React.FormEvent) => {
//     e.preventDefault()
//     if (!input.trim()) return
//     sendMessage(input)
//   }
//
//   return (
//     <div className={`chat-panel-overlay ${isOpen ? 'open' : ''}`} onClick={closeChat}>
//       <div className={`chat-panel-drawer ${isOpen ? 'open' : ''}`} onClick={e => e.stopPropagation()}>
//
//         {/* Header */}
//         <div className="chat-panel-header">
//           <div className="chat-panel-header-title">
//             <span>✨</span>
//             <h3>Quant Assistant</h3>
//           </div>
//           <button className="chat-panel-close" onClick={closeChat} title="Close Panel">×</button>
//         </div>
//
//         {/* Message Area */}
//         <div className="chat-panel-messages">
//           {messages.length === 0 && !isLoading && (
//             <div className="chat-panel-empty">No messages yet.</div>
//           )}
//           {messages.map((msg, idx) => (
//             <div key={idx} className={`chat-bubble-container ${msg.role === 'user' ? 'user' : 'ai'}`}>
//               <div className="chat-bubble-label">{msg.role === 'user' ? 'You' : 'Quant Assistant'}</div>
//               <div className="chat-bubble-content">
//                 {msg.role === 'ai' ? (
//                   <ReactMarkdown>{msg.content}</ReactMarkdown>
//                 ) : (
//                   msg.content
//                 )}
//               </div>
//             </div>
//           ))}
//           {isLoading && (
//             <div className="chat-bubble-container ai">
//                <div className="chat-bubble-label">Quant Assistant</div>
//                <div className="chat-bubble-content">
//                   <div className="chat-typing-indicator">
//                     <span>.</span><span>.</span><span>.</span>
//                   </div>
//                </div>
//             </div>
//           )}
//           <div ref={messagesEndRef} />
//         </div>
//
//         {/* Input Area */}
//         <div className="chat-panel-input-container">
//           <form onSubmit={handleSend} className="chat-panel-input-form">
//             <input
//               type="text"
//               value={input}
//               onChange={e => setInput(e.target.value)}
//               placeholder="Ask a follow-up question..."
//               className="chat-panel-input"
//               disabled={isLoading}
//             />
//             <button type="submit" disabled={!input.trim() || isLoading} className="chat-panel-submit">
//               Send
//             </button>
//           </form>
//         </div>
//       </div>
//     </div>
//   )
// }
