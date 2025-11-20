'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import ConversationsLayout from '@/components/ConversationsLayout';

export default function ConversationsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const customerId = searchParams.get('customerId');
  const sessionId = searchParams.get('sessionId');
  const conversationIdParam = searchParams.get('conversationId');

  // State to trigger sidebar refresh
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Explicitly set to null if the parameter is an empty string
  const processedConversationIdParam = (conversationIdParam === '' || conversationIdParam === null)
    ? null
    : conversationIdParam;


  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    processedConversationIdParam
  );



  const handleConversationSelect = (conversationId: string) => {
    // Convert empty string to null for greeting page
    const normalizedConversationId = (conversationId === '' || conversationId === null) ? null : conversationId;
    setActiveConversationId(normalizedConversationId);
    const params = new URLSearchParams();
    if (customerId) params.set('customerId', customerId);
    if (sessionId) params.set('sessionId', sessionId);
    // Only add conversationId if it's not empty/null
    if (normalizedConversationId && normalizedConversationId.trim() !== '') {
      params.set('conversationId', normalizedConversationId);
    }
    router.push(`/conversations?${params.toString()}`);
  };

  const handleConversationsRefresh = () => {
    // Trigger sidebar to refresh conversations
    setRefreshTrigger(prev => prev + 1);
  };

  const handleConversationCreated = (conversationId: string) => {
    // Update the active conversation when a new one is created
    setActiveConversationId(conversationId);
    // Update URL
    const params = new URLSearchParams();
    if (customerId) params.set('customerId', customerId);
    if (sessionId) params.set('sessionId', sessionId);
    params.set('conversationId', conversationId);
    router.push(`/conversations?${params.toString()}`);
  };

  useEffect(() => {
    if (processedConversationIdParam) {
      setActiveConversationId(processedConversationIdParam);
    } else {
      setActiveConversationId(null);
    }
  }, [processedConversationIdParam]);

  if (!customerId && !sessionId) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">No user session found</h1>
          <p className="text-gray-600 mb-4">
            Please log in or create a new account to start conversations.
          </p>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <ConversationsLayout
        customerId={customerId || undefined}
        sessionId={sessionId || undefined}
      activeConversationId={activeConversationId || undefined}
        onConversationSelect={handleConversationSelect}
        onConversationsRefresh={handleConversationsRefresh}
        refreshTrigger={refreshTrigger}
        onConversationCreated={handleConversationCreated}
    />
  );
}

