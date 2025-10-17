'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, User, RefreshCw, Minimize2, Maximize2, X, MessageCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import SQLDetailsPanel from '@/components/SQLDetailsPanel';

interface Schema {
  id: string;
  name: string;
  tables: any[];
  relationships: any[];
}

interface SQLDetails {
  query: string;
  result_count: number;
  columns: string[];
  rows: any[];
  total_rows: number;
  execution_time?: string;
  truncated?: boolean;
}

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: number;
  sqlDetails?: SQLDetails;
}

interface SchemaChatbotProps {
  schema: Schema;
  onSchemaUpdate: () => void;
}

export default function SchemaChatbot({ schema, onSchemaUpdate }: SchemaChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const [useStreaming, setUseStreaming] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Floating widget state
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: 'welcome',
        content: `# Welcome to Schema Builder! 🏗️

I'm your SQLite schema assistant. I can help you:

## **Table Operations**
- Create, rename, or delete tables
- Add, modify, or remove columns
- Set up primary keys and constraints

## **Relationships**
- Create foreign key relationships
- Link tables together
- Remove relationships

## **Schema Management**
- Generate SQL CREATE statements
- Validate schema consistency
- Export your schema

## **Example Commands**
- *"Create a users table with id, email, and name"*
- *"Add a created_at datetime column to users"*
- *"Create an orders table and link it to users"*
- *"Generate SQL for the entire schema"*

**Current Schema:** ${schema.name}  
**Tables:** ${schema.tables.length} | **Relationships:** ${schema.relationships.length}

What would you like to build? 🚀`,
        isUser: false,
        timestamp: Date.now()
      }]);
    }
  }, [schema.name, schema.tables.length, schema.relationships.length]);


  const sendMessage = async () => {
    if (!input.trim() || isLoading || isStreaming) return;

    if (useStreaming) {
      await sendStreamingMessage();
    } else {
      await sendNormalMessage();
    }
  };

  const sendNormalMessage = async () => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content: input.trim(),
      isUser: true,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:9000/schema-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          schema_id: schema.id,
          message: userMessage.content
        })
      });

      if (!response.ok) throw new Error('Failed to get response');
      
      const data = await response.json();
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response,
        isUser: false,
        timestamp: Date.now(),
        sqlDetails: data.sql_details || undefined
      };

      setMessages(prev => [...prev, botMessage]);
      
      // Refresh schema after AI response
      setTimeout(() => {
        onSchemaUpdate();
      }, 500);
      
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        isUser: false,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const sendStreamingMessage = async () => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content: input.trim(),
      isUser: true,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);

    // Create initial bot message
    const botMessageId = (Date.now() + 1).toString();
    const initialBotMessage: Message = {
      id: botMessageId,
      content: '',
      isUser: false,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, initialBotMessage]);
    setStreamingMessageId(botMessageId);

    try {
      const response = await fetch('http://localhost:9000/schema-chat-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          schema_id: schema.id,
          message: userMessage.content
        })
      });

      if (!response.ok) throw new Error('Failed to get streaming response');

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      let buffer = '';
      let shouldRefreshSchema = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += new TextDecoder().decode(value);
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'data' && data.content) {
                setMessages(prev => prev.map(msg => 
                  msg.id === botMessageId 
                    ? { ...msg, content: msg.content + data.content }
                    : msg
                ));
              } else if (data.type === 'tool') {
                shouldRefreshSchema = true;
                setMessages(prev => prev.map(msg => 
                  msg.id === botMessageId 
                    ? { ...msg, content: msg.content + '\n\n' + data.content + '\n\n' }
                    : msg
                ));
              } else if (data.type === 'sql_details') {
                // Add SQL details to the message
                setMessages(prev => prev.map(msg => 
                  msg.id === botMessageId 
                    ? { ...msg, sqlDetails: data.content }
                    : msg
                ));
              } else if (data.type === 'complete') {
                // Streaming complete
                break;
              } else if (data.type === 'error') {
                setMessages(prev => prev.map(msg => 
                  msg.id === botMessageId 
                    ? { ...msg, content: `Error: ${data.content}` }
                    : msg
                ));
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }

      // Refresh schema if tools were used
      if (shouldRefreshSchema) {
        setTimeout(() => {
          onSchemaUpdate();
        }, 500);
      }

    } catch (error) {
      setMessages(prev => prev.map(msg => 
        msg.id === botMessageId 
          ? { ...msg, content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}` }
          : msg
      ));
    } finally {
      setIsStreaming(false);
      setStreamingMessageId(null);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // If collapsed, show only the floating button
  if (isCollapsed) {
    return (
      <div
        className="fixed bottom-4 right-4 z-50 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg cursor-pointer transition-colors"
        onClick={() => setIsCollapsed(false)}
      >
        <MessageCircle className="h-6 w-6" />
      </div>
    );
  }

  return (
    <div
      className="fixed bottom-4 right-4 z-40 bg-white border border-gray-300 rounded-lg shadow-xl flex flex-col w-96"
      style={{
        height: isMinimized ? 'auto' : 'calc(100vh - 2rem)',
        maxHeight: isMinimized ? 'auto' : 'calc(100vh - 2rem)',
      }}
    >
      {/* Header */}
      <div
        className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between rounded-t-lg"
      >
        <div className="flex items-center space-x-2">
          <Sparkles className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-medium text-gray-700">Schema Assistant</span>
          <span className="text-xs text-gray-400">•</span>
          <span className="text-xs text-gray-500">{schema.name}</span>
        </div>
        
        <div className="flex items-center space-x-1">
          {/* Streaming Toggle */}
          <div className="flex items-center space-x-1 text-xs mr-2">
            <span className={useStreaming ? 'text-blue-500' : 'text-gray-400'}>Stream</span>
            <button
              onClick={() => setUseStreaming(!useStreaming)}
              className={`w-4 h-2 rounded-full transition-colors ${
                useStreaming ? 'bg-blue-500' : 'bg-gray-300'
              }`}
            >
              <div
                className={`w-1.5 h-1.5 bg-white rounded-full transition-transform ${
                  useStreaming ? 'translate-x-2.5' : 'translate-x-0.5'
                }`}
              />
            </button>
            <span className={!useStreaming ? 'text-blue-500' : 'text-gray-400'}>Normal</span>
          </div>

          {/* Control buttons */}
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
            title={isMinimized ? "Expand" : "Minimize"}
          >
            {isMinimized ? <Maximize2 className="h-3 w-3" /> : <Minimize2 className="h-3 w-3" />}
          </button>
          <button
            onClick={() => setIsCollapsed(true)}
            className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
            title="Collapse"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      </div>

      {/* Chat content - hidden when minimized */}
      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {messages.map((message) => (
              <div key={message.id} className="flex space-x-2">
                {/* Avatar */}
                <div className="flex-shrink-0">
                  {message.isUser ? (
                    <div className="w-6 h-6 bg-gray-600 rounded-full flex items-center justify-center">
                      <User className="h-3 w-3 text-white" />
                    </div>
                  ) : (
                    <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                      <Sparkles className="h-3 w-3 text-white" />
                    </div>
                  )}
                </div>

                {/* Message Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-xs font-medium text-gray-900">
                      {message.isUser ? 'You' : 'Assistant'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                    {/* Streaming indicator */}
                    {isStreaming && streamingMessageId === message.id && (
                      <div className="flex items-center space-x-1">
                        <div className="w-1 h-1 bg-blue-600 rounded-full animate-pulse"></div>
                        <div className="w-1 h-1 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-1 h-1 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                      </div>
                    )}
                  </div>
                  
                  {message.isUser ? (
                    <div className="bg-gray-100 text-gray-900 px-3 py-2 rounded max-w-xs text-sm">
                      {message.content}
                    </div>
                  ) : (
                    <div className="max-w-none text-xs">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          h1: ({ children }) => <h1 className="text-lg font-bold text-gray-900 mt-3 mb-2 first:mt-0">{children}</h1>,
                          h2: ({ children }) => <h2 className="text-base font-bold text-gray-900 mt-3 mb-2 first:mt-0">{children}</h2>,
                          h3: ({ children }) => <h3 className="text-sm font-bold text-gray-900 mt-2 mb-1 first:mt-0">{children}</h3>,
                          h4: ({ children }) => <h4 className="text-xs font-bold text-gray-900 mt-2 mb-1 first:mt-0">{children}</h4>,
                          h5: ({ children }) => <h5 className="text-xs font-bold text-gray-900 mt-2 mb-1 first:mt-0">{children}</h5>,
                          h6: ({ children }) => <h6 className="text-xs font-bold text-gray-900 mt-2 mb-1 first:mt-0">{children}</h6>,
                          p: ({ children }) => <p className="text-gray-700 mb-2 last:mb-0 text-xs">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc list-inside text-gray-700 mb-2 space-y-0.5 text-xs">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal list-inside text-gray-700 mb-2 space-y-0.5 text-xs">{children}</ol>,
                          li: ({ children }) => <li className="text-gray-700 text-xs">{children}</li>,
                          code: ({ children }) => <code className="bg-blue-50 text-blue-600 px-1 py-0.5 rounded text-xs">{children}</code>,
                          pre: ({ children }) => <pre className="bg-gray-900 text-gray-100 p-2 rounded text-xs overflow-x-auto mb-2">{children}</pre>,
                          blockquote: ({ children }) => <blockquote className="border-l-2 border-blue-500 bg-blue-50 pl-2 py-1 text-gray-700 mb-2 text-xs">{children}</blockquote>,
                          strong: ({ children }) => <strong className="font-bold text-gray-900">{children}</strong>,
                          em: ({ children }) => <em className="italic text-gray-700">{children}</em>,
                          table: ({ children }) => <table className="border-collapse border border-gray-300 text-xs mb-2">{children}</table>,
                          th: ({ children }) => <th className="border border-gray-300 px-1 py-0.5 bg-gray-100 font-bold text-gray-900 text-xs">{children}</th>,
                          td: ({ children }) => <td className="border border-gray-300 px-1 py-0.5 text-gray-700 text-xs">{children}</td>,
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                      
                      {/* SQL Details Panel */}
                      {message.sqlDetails && (
                        <div className="mt-2">
                          <SQLDetailsPanel 
                            sqlDetails={message.sqlDetails}
                            defaultCollapsed={true}
                            className="text-xs"
                          />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Loading indicator for normal mode */}
            {isLoading && !isStreaming && (
              <div className="flex space-x-2">
                <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                  <Sparkles className="h-3 w-3 text-white" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-xs font-medium text-gray-900">Assistant</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce"></div>
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-3 bg-white rounded-b-lg">
            <div className="flex space-x-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about your schema..."
                className="flex-1 border border-gray-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 rounded"
                disabled={isLoading || isStreaming}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading || isStreaming}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-3 py-1.5 rounded flex items-center"
              >
                {isLoading || isStreaming ? (
                  <RefreshCw className="h-3 w-3 animate-spin" />
                ) : (
                  <Send className="h-3 w-3" />
                )}
              </button>
            </div>
          </div>
        </>
      )}

    </div>
  );
}