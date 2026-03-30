import { useState, useCallback } from 'react';
import { api } from '../services/api';
import type { components } from '../services/api.d';

type ChatMessage = components['schemas']['ChatMessageResponse'];

export function useChat(jobId: number | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const fetchHistory = useCallback(async () => {
    if (!jobId) return [];
    setIsLoadingHistory(true);
    try {
      const history = await api.results.getChat(jobId);
      setMessages(history);
      return history;
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
      return [];
    } finally {
      setIsLoadingHistory(false);
    }
  }, [jobId]);

  const analyzeInitial = useCallback(async () => {
    if (!jobId) return;
    setIsLoadingHistory(true);
    try {
      await api.results.analyze(jobId);
      await fetchHistory();
    } catch (error) {
      console.error('Failed to analyze initial report:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  }, [jobId, fetchHistory]);

  const sendMessage = useCallback(async (content: string) => {
    if (!jobId || !content.trim()) return;

    const tempUserMessage: ChatMessage = {
      id: Date.now(),
      job_id: jobId,
      role: 'user',
      content: content.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, tempUserMessage]);
    setIsSending(true);

    try {
      await api.results.sendChat(jobId, { content: content.trim() });
      await fetchHistory();
    } catch (error) {
      console.error('Failed to send chat message:', error);
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMessage.id));
    } finally {
      setIsSending(false);
    }
  }, [jobId, fetchHistory]);

  return {
    messages,
    isLoadingHistory,
    isSending,
    fetchHistory,
    analyzeInitial,
    sendMessage,
  };
}
