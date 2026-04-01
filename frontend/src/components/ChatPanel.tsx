import React, {useEffect, useRef, useState} from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {useChat} from '../hooks/useChat';
import {Loader2, Send, X} from 'lucide-react';

interface ChatPanelProps {
  jobId: number | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ jobId, isOpen, onClose }) => {
  const { messages, isLoadingHistory, isSending, fetchHistory, analyzeInitial, sendMessage } = useChat(jobId);
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [hasInitialized, setHasInitialized] = useState(false);

  useEffect(() => {
    if (isOpen && jobId && !hasInitialized) {
      const initChat = async () => {
        const history = await fetchHistory();
        if (history.length === 0) {
          await analyzeInitial();
        }
        setHasInitialized(true);
      };
      initChat();
    }
  }, [isOpen, jobId, fetchHistory, analyzeInitial, hasInitialized]);

  // Reset initialization when job ID changes or panel closes
  useEffect(() => {
    if (!isOpen || !jobId) {
       setHasInitialized(false);
    }
  }, [isOpen, jobId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isSending || isLoadingHistory) return;
    sendMessage(inputMessage);
    setInputMessage('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-[400px] bg-white shadow-2xl border-l border-gray-200 flex flex-col z-50 transform transition-transform duration-300 translate-x-0">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-800">AI Results Analysis</h2>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 focus:outline-none transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {(isLoadingHistory && !hasInitialized) ? (
          <div className="flex flex-col justify-center items-center h-full text-gray-500">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-2" />
            <span>Analyzing initial report...</span>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={msg.id || index}
              className={`flex flex-col ${
                msg.role === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              <div
                className={`max-w-[85%] rounded-lg p-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-100 text-blue-900 rounded-br-none'
                    : 'bg-gray-800 text-gray-100 rounded-bl-none prose prose-invert prose-sm'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  <p className="whitespace-pre-wrap m-0">{msg.content}</p>
                )}
              </div>
            </div>
          ))
        )}

        {isSending && (
          <div className="flex items-start">
            <div className="bg-gray-800 text-gray-100 rounded-lg rounded-bl-none p-3 max-w-[85%] flex items-center">
               <Loader2 className="w-4 h-4 animate-spin mr-2" />
               <span className="text-sm">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <form onSubmit={handleSendMessage} className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about the results..."
            disabled={isSending || isLoadingHistory}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || isSending || isLoadingHistory}
            className="p-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};
