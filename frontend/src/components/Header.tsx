'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { Home, Sparkles, Plus, User, LogOut } from 'lucide-react';
import { useStreamingContext } from '@/contexts/StreamingContext';
import { useAuth } from '@/contexts/AuthContext';

export default function Header() {
  const pathname = usePathname();
  const isChatPage = pathname === '/chat';
  const streamingContext = useStreamingContext();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    // Redirect to home page
    window.location.href = '/';
  };

  return (
    <header className="bg-gray-900 shadow-sm border-b border-gray-700 fixed top-0 left-0 right-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-12">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5 text-yellow-400" />
            <h1 className="text-lg font-semibold text-white">
              Ava
            </h1>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Chat-specific controls */}
            {isChatPage && (
              <>
                {/* New Chat Button - Subtle dark style */}
                <Link 
                  href="/lead-capture"
                  className="flex items-center space-x-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white text-xs font-medium rounded transition-colors border border-gray-700"
                  title="Start a new conversation"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>New Chat</span>
                </Link>

                {/* Streaming Toggle - only show if context is available */}
                {streamingContext && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-300">Normal</span>
                    <button
                      onClick={() => streamingContext.setIsStreaming(!streamingContext.isStreaming)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        streamingContext.isStreaming ? 'bg-blue-600' : 'bg-gray-600'
                      }`}
                      title={streamingContext.isStreaming ? 'Switch to Normal Mode' : 'Switch to Streaming Mode'}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          streamingContext.isStreaming ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                    <span className="text-sm text-gray-300">Stream</span>
                  </div>
                )}
                
                <Link 
                  href="/"
                  className="text-gray-400 hover:text-white transition-colors"
                  title="Back to Home"
                >
                  <Home className="h-5 w-5" />
                </Link>
              </>
            )}
            
            {/* Authentication buttons */}
            {user ? (
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 text-gray-300">
                  <User className="h-4 w-4" />
                  <span className="text-sm">{user.email}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1 px-3 py-1 text-sm text-gray-300 hover:text-white transition-colors"
                  title="Logout"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Link
                  href="/"
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors rounded"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
