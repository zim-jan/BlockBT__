import React, {useEffect, useRef, useState} from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {useChat} from '../../hooks/useChat';
import {AlertCircle, ChevronDown, ChevronRight, FileText, Loader2, RefreshCw, Send, X} from 'lucide-react';

interface ChatPanelProps {
  jobId: number | null;
  isOpen: boolean;
  onClose: () => void;
}

function PromptAccordion({ content }: { content: string }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="w-full bg-surface-container border border-outline-variant/30 rounded-lg overflow-hidden my-2 text-xs">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-3 py-2 bg-surface-container-high hover:bg-surface-bright flex items-center justify-between text-on-surface-variant font-label transition-colors"
      >
        <div className="flex items-center gap-2">
          <FileText className="w-3.5 h-3.5 text-primary" />
          <span className="font-semibold text-on-surface">Initial Strategy Payload & Context</span>
        </div>
        {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
      {expanded && (
        <div className="p-3 bg-surface-container-lowest border-t border-outline-variant/20 font-mono text-[11px] text-on-surface-variant overflow-x-auto max-h-64 whitespace-pre-wrap">
          {content}
        </div>
      )}
    </div>
  );
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ jobId, isOpen, onClose }) => {
  const { messages, isLoadingHistory, isSending, error, fetchHistory, analyzeInitial, sendMessage } = useChat(jobId);
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

  const handleRetry = () => {
    analyzeInitial();
  };

  const isInitialPrompt = (msgContent: string) => {
    return msgContent.includes('--- KEY METRICS ---') || msgContent.includes('senior quantitative analyst');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-[420px] bg-surface-container-low shadow-2xl border-l border-outline-variant/30 flex flex-col z-[9999] transform transition-transform duration-300 translate-x-0 font-body text-on-surface dark">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b border-outline-variant/20 bg-surface-container">
        <div>
          <h2 className="text-base font-bold font-headline text-on-surface">AI Results Analysis</h2>
          <p className="font-label text-xs text-on-surface-variant">Local Ollama Quant Assistant</p>
        </div>
        <button
          onClick={onClose}
          className="text-on-surface-variant hover:text-on-surface focus:outline-none transition-colors p-1 rounded-md hover:bg-surface-container-high"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-background">
        {(isLoadingHistory && !hasInitialized) ? (
          <div className="flex flex-col justify-center items-center h-full text-on-surface-variant space-y-2">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <span className="font-label text-xs">Analyzing initial report...</span>
          </div>
        ) : error ? (
          <div className="flex flex-col justify-center items-center h-full p-4 text-center space-y-4">
            <div className="p-3 bg-error/10 text-error rounded-full border border-error/20">
              <AlertCircle className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h3 className="font-headline text-sm font-bold text-on-surface">Analysis Failed</h3>
              <p className="font-label text-xs text-on-surface-variant max-w-xs">{error}</p>
            </div>
            <button
              onClick={handleRetry}
              className="px-3 py-2 bg-primary text-on-primary text-xs font-semibold uppercase tracking-wider rounded transition-colors flex items-center gap-1.5 hover:bg-primary/90"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry Analysis
            </button>
          </div>
        ) : (
          messages.map((msg, index) => {
            if (msg.role === 'user' && isInitialPrompt(msg.content)) {
              return <PromptAccordion key={msg.id || index} content={msg.content} />;
            }

            return (
              <div
                key={msg.id || index}
                className={`flex flex-col ${
                  msg.role === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                <div
                  className={`max-w-[90%] rounded-lg p-3 text-xs leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-primary/20 text-on-surface border border-primary/30 rounded-br-none font-medium'
                      : 'bg-surface-container border border-outline-variant/20 text-on-surface rounded-bl-none prose prose-invert prose-xs max-w-none'
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
            );
          })
        )}

        {isSending && (
          <div className="flex items-start">
            <div className="bg-surface-container text-on-surface-variant border border-outline-variant/20 rounded-lg rounded-bl-none p-3 max-w-[85%] flex items-center text-xs">
               <Loader2 className="w-4 h-4 animate-spin mr-2 text-primary" />
               <span>Generating response...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-outline-variant/20 bg-surface-container">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about the strategy results..."
            disabled={isSending || isLoadingHistory}
            className="flex-1 px-3 py-2 bg-surface-container-low border border-outline-variant/40 text-on-surface text-xs focus:outline-none focus:border-primary disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputMessage.trim() || isSending || isLoadingHistory}
            className="p-2 bg-primary text-on-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
