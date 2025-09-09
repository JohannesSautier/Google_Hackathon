'use client';

import React from 'react';
import Link from 'next/link';
import { ChatBubbleLeftRightIcon as ChatIcon } from '@heroicons/react/24/outline';
import { useChat } from '@/components/chat/ChatProvider';

export default function Header() {
  return (
    <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md z-50 border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg"></div>
            <span className="text-xl font-bold text-gray-900">PaperTrail</span>
          </Link>
          <div className="flex items-center space-x-4">
            <Link href="/dashboard" className="text-gray-600 hover:text-gray-900 text-sm font-medium transition">
              Dashboard
            </Link>
            <Link href="/timeline" className="text-gray-600 hover:text-gray-900 text-sm font-medium transition">
              Timeline
            </Link>
            <ChatButton />
            <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition">
              Get Started
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

function ChatButton() {
  const { context } = useChat();
  
  return (
    <button 
      className="flex items-center space-x-2 text-gray-600 hover:text-blue-600 transition-colors"
      title="Chat with AI Assistant"
    >
      <ChatIcon className="w-5 h-5" />
      <span className="text-sm font-medium hidden sm:inline">AI Chat</span>
    </button>
  );
}
