import {create} from 'zustand';

interface ChatState {
  isOpen: boolean;
  jobId: number | null;
  openChat: (jobId: number) => void;
  closeChat: () => void;
}

// We simplify the global store to just handle the open/close state and the active jobId.
// The actual chat messages and API interactions are handled by the useChat hook locally in the ChatPanel.
export const useChatStore = create<ChatState>((set) => ({
  isOpen: false,
  jobId: null,

  openChat: (jobId: number) => {
    set({ isOpen: true, jobId });
  },

  closeChat: () => {
    set({ isOpen: false });
  },
}));
