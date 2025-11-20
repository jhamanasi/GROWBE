'use client';

import { useState } from 'react';
import SidebarConversations from '@/components/SidebarConversations';
import ChatWindow from '@/components/ChatWindow';

interface ConversationsLayoutProps {
  customerId?: string;
  sessionId?: string;
  activeConversationId?: string;
  onConversationSelect: (conversationId: string) => void;
  onConversationsRefresh?: () => void;
  refreshTrigger?: number;
  onConversationCreated?: (conversationId: string) => void;
}

export default function ConversationsLayout({
  customerId,
  sessionId,
  activeConversationId,
  onConversationSelect,
  onConversationsRefresh,
  refreshTrigger,
  onConversationCreated,
}: ConversationsLayoutProps) {
  // Initialize isSidebarOpen to false so it's collapsed by default
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="h-screen flex">
      {/* Sidebar - Always rendered, just collapsed */}
      <SidebarConversations
        customerId={customerId}
        sessionId={sessionId}
        onConversationSelect={onConversationSelect}
        activeConversationId={activeConversationId}
        isSidebarOpen={isSidebarOpen}
        toggleSidebar={toggleSidebar}
        onConversationsRefresh={onConversationsRefresh}
        refreshTrigger={refreshTrigger}
      />

      {/* Chat window area - margin handled by ChatWindow component */}
      <div className="flex-1 flex flex-col">
        <ChatWindow
          conversationId={activeConversationId || ''}
          customerId={customerId}
          sessionId={sessionId}
          isSidebarOpen={isSidebarOpen}
          toggleSidebar={toggleSidebar}
          onConversationsRefresh={onConversationsRefresh}
          onConversationCreated={onConversationCreated}
        />
      </div>
    </div>
  );
}
