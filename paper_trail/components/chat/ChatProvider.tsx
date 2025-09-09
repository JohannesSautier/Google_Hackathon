'use client';

import React, { createContext, useContext } from 'react';
import ChatWidget from './ChatWidget';
import { useChatContext } from '@/lib/hooks/useChatContext';

interface ChatContextType {
  context: any;
  updateContext: (newContext: any) => void;
  clearContext: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}

interface ChatProviderProps {
  children: React.ReactNode;
}

export default function ChatProvider({ children }: ChatProviderProps) {
  const chatContext = useChatContext();

  return (
    <ChatContext.Provider value={chatContext}>
      {children}
      <ChatWidget context={chatContext.context} />
    </ChatContext.Provider>
  );
}
