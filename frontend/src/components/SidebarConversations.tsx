'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Plus, MessageSquare, Clock, Menu, LogOut, ChevronDown, ChevronUp } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface Conversation {
  conversation_id: string;
  title: string;
  preview: string;
  last_message_at: string | null;
  message_count: number;
  scenario_type: string;
}

interface SidebarConversationsProps {
  customerId?: string;
  sessionId?: string;
  onConversationSelect: (conversationId: string) => void;
  activeConversationId?: string;
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
  onConversationsRefresh?: () => void;
  refreshTrigger?: number;
}

export default function SidebarConversations({
  customerId,
  sessionId,
  onConversationSelect,
  activeConversationId,
  isSidebarOpen,
  toggleSidebar,
  onConversationsRefresh,
  refreshTrigger,
}: SidebarConversationsProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [isChatsExpanded, setIsChatsExpanded] = useState(true);
  const router = useRouter();

  const fetchConversations = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (customerId) params.append('customer_id', customerId);
      if (sessionId && !customerId) params.append('session_id', sessionId);

      const response = await fetch(`http://localhost:8000/api/conversations?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        setConversations(data);
        // Don't call onConversationsRefresh here to avoid loops
        // This callback should only be called when conversations are created/modified externally
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = async () => {
    setIsCreating(true);
    try {
      const params = new URLSearchParams();
      if (customerId) params.set('customerId', customerId);
      if (sessionId) params.set('sessionId', sessionId);
      router.push(`/conversations?${params.toString()}`);
      onConversationSelect(''); // Explicitly set active conversation to null to show greeting
    } catch (error) {
      console.error('Error starting new chat:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('customerId');
    localStorage.removeItem('sessionId');
    router.push('/');
  };

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  useEffect(() => {
    if (customerId || sessionId) {
      fetchConversations();
    }
  }, [customerId, sessionId, refreshTrigger]); 

  // REMOVED: The automatic conversation selection logic that was causing infinite loops.
  // The greeting page is now the default state when activeConversationId is null.
  // Users can manually select conversations from the sidebar or start new ones.


  return (
    <div
      className={`h-full bg-gray-100 border-r border-gray-300 flex flex-col fixed left-0 top-0 z-40
        ${isSidebarOpen ? 'w-80' : 'w-20'}
        transition-all duration-300`}
    >
      {/* Collapsed State Content */}
      {!isSidebarOpen ? (
        <>
          {/* Top: Expand Button */}
          <div className="p-4 border-b border-gray-300">
            <Button
              onClick={toggleSidebar}
              variant="ghost"
              size="icon"
              className="w-full text-gray-700 hover:bg-gray-200 h-12"
              title="Expand sidebar"
            >
              <Menu className="h-6 w-6" />
            </Button>
          </div>

          {/* Middle: New Chat Button */}
          <div className="p-4">
        <Button
          onClick={handleNewChat}
          disabled={isCreating}
              variant="ghost"
              size="icon"
              className="w-full text-gray-700 hover:bg-gray-200 h-12"
              title="New chat"
        >
              <Plus className="h-6 w-6" />
            </Button>
          </div>

          {/* Bottom: Logout (positioned at bottom) */}
          <div className="mt-auto p-4">
            <Button
              onClick={handleLogout}
              variant="ghost"
              size="icon"
              className="w-full text-gray-700 hover:bg-gray-200 h-12"
              title="Logout"
            >
              <LogOut className="h-6 w-6" />
            </Button>
          </div>
        </>
        ) : (
        /* Expanded State Content */
        <>
          {/* Top Hamburger Button */}
          <div className="p-3 flex justify-start">
          <Button
              onClick={toggleSidebar}
            variant="ghost"
            size="icon"
              className="text-gray-700 hover:bg-gray-200"
              title="Collapse sidebar"
          >
            <Menu className="h-6 w-6" />
        </Button>
          </div>

          {/* New Chat Button */}
          <div className="p-4 border-b border-gray-300">
            <Button
              onClick={handleNewChat}
              disabled={isCreating}
              className="w-full bg-gray-100 hover:bg-gray-200 text-gray-900 border border-gray-200 flex items-center justify-center space-x-2 shadow-sm h-12"
            >
              <Plus className="h-5 w-5" />
              <span className="text-base font-medium">New Chat</span>
            </Button>
          </div>

          {/* Collapsible Chats Section */}
          <div className="flex-1 flex flex-col min-h-0">
            {/* Chats Header */}
            <div className="p-4 border-b border-gray-300">
              <Button
                onClick={() => setIsChatsExpanded(!isChatsExpanded)}
                variant="ghost"
                className="w-full text-left text-gray-700 hover:bg-gray-200 flex items-center justify-between p-2"
              >
                <span className="text-base font-medium">
                  Chats ({conversations.length})
                </span>
                {isChatsExpanded ?
                  <ChevronUp className="h-5 w-5" /> :
                  <ChevronDown className="h-5 w-5" />
                }
              </Button>
      </div>

            {/* Chats List */}
            {isChatsExpanded && (
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
                  <div className="p-4 text-center text-gray-600 text-base">
                    Loading conversations...
                  </div>
        ) : conversations.length === 0 ? (
                  <div className="p-4 text-center text-gray-600 text-base">
            No conversations yet. Start a new chat!
          </div>
        ) : (
          <div className="p-2">
            {conversations.map((conv) => (
              <button
                key={conv.conversation_id}
                onClick={() => onConversationSelect(conv.conversation_id)}
                        className={`w-full text-left p-4 rounded-lg mb-2 transition-colors border ${
                  activeConversationId === conv.conversation_id
                            ? 'bg-gray-200 text-gray-900 border-gray-300 shadow-sm'
                            : 'bg-gray-100 text-gray-900 border-gray-200 hover:bg-gray-200'
                }`}
              >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="text-base font-medium truncate flex-1">
                    {conv.title || 'New Chat'}
                  </h3>
                </div>
                        <div className="flex items-center text-sm text-gray-900">
                          <Clock className="h-4 w-4 mr-2" />
                  {formatTimestamp(conv.last_message_at)}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
      )}
          </div>

          {/* Logout at bottom */}
          <div className="p-4 border-t border-gray-300">
            <Button
              onClick={handleLogout}
              variant="ghost"
              className="w-full text-gray-700 hover:bg-gray-200 flex items-center justify-center space-x-2 h-12"
            >
              <LogOut className="h-5 w-5" />
              <span className="text-base font-medium">Logout</span>
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

