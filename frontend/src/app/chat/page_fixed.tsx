'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send, Bot, User, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import SQLDetailsPanel from '@/components/SQLDetailsPanel'
import InlineSQLChart from '@/components/InlineSQLChart'
import SuggestionCards from '@/components/SuggestionCards'
import LeadProgressCompact from '@/components/LeadProgressCompact'
// Authentication removed - no longer needed
import { StreamingProvider, useStreamingContext } from '@/contexts/StreamingContext'

interface ChartConfig {
  type: string;
  title: string;
  x_axis: string;
  y_axis: string;
  eligible: boolean;
  series_columns?: string[];
}

interface Suggestion {
  title: string;
  description: string;
  question: string;
  icon: string;
}

interface LeadContext {
  id: number;
  name: string;
  email: string;
  phone: string;
  looking_for: string;
  budget_range?: string;
  timeline?: string;
  session_id: string;
}

interface SQLDetails {
  query: string;
  result_count: number;
  columns: string[];
  rows: any[];
  total_rows: number;
  execution_time?: string;
  truncated?: boolean;
  chart_config?: ChartConfig;
}

interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: number  // Changed to number (timestamp)
  sqlDetails?: SQLDetails
}

export default function ChatPage() {
  return (
    <StreamingProvider>
      <ChatPageContent />
    </StreamingProvider>
  );
}

function ChatPageContent() {
  const streamingContext = useStreamingContext();
  const isStreaming = streamingContext?.isStreaming ?? true;
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('sessionId');
  
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // Lead context state
  const [leadContext, setLeadContext] = useState<LeadContext | null>(null)
  const [isLoadingLead, setIsLoadingLead] = useState(false)
  
  // Suggestion system state
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(true)
  const [showSuggestions, setShowSuggestions] = useState(true)

  // Load lead context from session ID
  useEffect(() => {
    if (sessionId) {
      loadLeadContext(sessionId);
    }
  }, [sessionId]);

  // Load suggestions when component mounts
  useEffect(() => {
    loadSuggestions();
  }, []);

  const loadLeadContext = async (sessionId: string) => {
    setIsLoadingLead(true);
    try {
      const response = await fetch(`http://localhost:9000/leads/session/${sessionId}`);
      if (response.ok) {
        const lead = await response.json();
        setLeadContext(lead);
        console.log('Lead context loaded:', lead);
        
        // Send personalized greeting message from Ava
        await sendPersonalizedGreeting(lead);
      } else {
        console.error('Failed to load lead context');
      }
    } catch (error) {
      console.error('Error loading lead context:', error);
    } finally {
      setIsLoadingLead(false);
    }
  };

  const sendPersonalizedGreeting = async (lead: LeadContext) => {
    // Create personalized greeting message
    const greetingMessage: Message = {
      id: 'greeting-' + Date.now(),
      content: `Hi ${lead.name}! I'm so excited to help you find your perfect property! 🏠

I see you're looking to **${lead.looking_for.toLowerCase()}**${lead.budget_range ? ` with a budget around **${lead.budget_range}**` : ''}${lead.timeline ? ` and you're planning to move **${lead.timeline}**` : ''}. That's fantastic!

Let me ask you a few questions to better understand what you're looking for:

**What area or neighborhood are you most interested in?** I'd love to help you explore some great options!`,
      isUser: false,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, greetingMessage]);
    setShowSuggestions(false); // Hide suggestions since Ava is now chatting
  };

         const loadSuggestions = async () => {
           setIsLoadingSuggestions(true);
           try {
             // Add timeout to prevent hanging
             const controller = new AbortController();
             const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
             
             const response = await fetch('http://localhost:9000/suggestions', {
               method: 'POST',
               headers: {
                 'Content-Type': 'application/json',
               },
               body: JSON.stringify({}),
               signal: controller.signal
             });
             
             clearTimeout(timeoutId);
             
             if (response.ok) {
               const data = await response.json();
               console.log('Suggestions loaded:', data.suggestions?.length || 0);
               setSuggestions(data.suggestions || []);
             } else {
               console.error('Suggestions API error:', response.status, response.statusText);
               throw new Error(`HTTP ${response.status}`);
             }
           } catch (error) {
             console.error('Failed to load suggestions:', error);
             // Generate new fallback suggestions each time
             const fallbackSuggestions = [
               {
                 title: "Find Properties",
                 description: "Search for homes and apartments",
                 question: "Help me find properties in my budget",
                 icon: "🏠"
               },
               {
                 title: "Market Trends",
                 description: "Get current real estate market data",
                 question: "What are the current market trends?",
                 icon: "📊"
               },
               {
                 title: "Mortgage Calculator",
                 description: "Calculate monthly payments",
                 question: "Calculate my mortgage payment",
                 icon: "💰"
               },
               {
                 title: "Real Estate Help",
                 description: "Get assistance with buying or selling",
                 question: "How can you help me with real estate?",
                 icon: "🤝"
               }
             ];
             
             // Shuffle the suggestions to provide variety
             const shuffled = fallbackSuggestions.sort(() => Math.random() - 0.5);
             setSuggestions(shuffled);
           } finally {
             setIsLoadingSuggestions(false);
           }
         };

  const handleSuggestionClick = (question: string) => {
    setInputMessage(question);
    setShowSuggestions(false);
    // Auto-send the question
    setTimeout(() => {
      sendMessageWithText(question);
    }, 100);
  };

         const sendMessageWithText = async (messageText: string) => {
           if (!messageText.trim() || isLoading) return;

           const userMessage: Message = {
             id: Date.now().toString(),
             content: messageText,
             isUser: true,
             timestamp: Date.now()
           }

           setMessages(prev => [...prev, userMessage])
           setInputMessage('')
           
           // Reset textarea height
           const textarea = document.querySelector('textarea') as HTMLTextAreaElement;
           if (textarea) {
             textarea.style.height = '48px';
           }
           
           setIsLoading(true)

           if (isStreaming) {
             await sendStreamingMessage(messageText)
           } else {
             await sendNormalMessage(messageText)
           }
         };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;
    setShowSuggestions(false); // Hide suggestions when user starts chatting
    await sendMessageWithText(inputMessage);
  }

  const sendNormalMessage = async (message: string) => {
    try {
      const response = await fetch('http://localhost:9000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message,
          session_id: sessionId // Include session ID for lead context
        }),
      })

      if (response.ok) {
        const data = await response.json()
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: data.response,
          isUser: false,
          timestamp: Date.now(),
          sqlDetails: data.sql_details || undefined
        }
        setMessages(prev => [...prev, botMessage])
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: 'Sorry, I encountered an error. Please try again.',
          isUser: false,
          timestamp: Date.now()
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I couldn\'t connect to the server. Please try again.',
        isUser: false,
        timestamp: Date.now()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const sendStreamingMessage = async (message: string) => {
    // Create an empty bot message for streaming
    const botMessageId = (Date.now() + 1).toString()
    const botMessage: Message = {
      id: botMessageId,
      content: '',
      isUser: false,
      timestamp: Date.now()
    }
    
    setMessages(prev => [...prev, botMessage])
    setStreamingMessageId(botMessageId)

    try {
      const response = await fetch('http://localhost:9000/chat-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message,
          session_id: sessionId // Include session ID for lead context
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (reader) {
        let buffer = ''
        
        while (true) {
          const { done, value } = await reader.read()
          
          if (done) break
          
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // Keep incomplete line in buffer
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const eventData = JSON.parse(line.slice(6))
                
                if (eventData.type === 'data') {
                  // Append text chunk to the streaming message
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, content: msg.content + eventData.content }
                      : msg
                  ))
                } else if (eventData.type === 'tool') {
                  // Add tool usage indicator
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, content: msg.content + '\n\n' + eventData.content + '\n\n' }
                      : msg
                  ))
                } else if (eventData.type === 'sql_details') {
                  // Add SQL details to the message
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, sqlDetails: eventData.content }
                      : msg
                  ))
                } else if (eventData.type === 'error') {
                  // Handle error
                  setMessages(prev => prev.map(msg => 
                    msg.id === botMessageId 
                      ? { ...msg, content: eventData.content }
                      : msg
                  ))
                  break
                } else if (eventData.type === 'complete') {
                  // Streaming complete
                  break
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e)
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error)
      setMessages(prev => prev.map(msg => 
        msg.id === botMessageId 
          ? { ...msg, content: 'Sorry, I couldn\'t connect to the server. Please try again.' }
          : msg
      ))
    } finally {
      setIsLoading(false)
      setStreamingMessageId(null)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <>
      {/* Main chat container with proper spacing for fixed header */}
      <div className="pt-12 h-screen bg-gray-100 flex items-center justify-center p-4">
        <div className="w-full max-w-[1000px] bg-white shadow-xl flex flex-col overflow-hidden rounded-lg" style={{ height: 'calc(100vh - 6rem)' }}>

          {/* Lead Progress - Show when we have session ID */}
          {sessionId && (
            <div className="border-b border-gray-200 bg-blue-50 p-3">
              <LeadProgressCompact sessionId={sessionId} />
            </div>
          )}

          {/* Chat Messages */}
          <div className="flex-1 overflow-hidden bg-white">
            <div className="h-full flex flex-col">
              <div className="flex-1 overflow-y-auto px-6">
                {/* Show suggestions when no messages and user hasn't started chatting */}
                {showSuggestions && messages.length === 0 && (
                  <div className="pt-8">
                    <SuggestionCards
                      suggestions={suggestions}
                      onSuggestionClick={handleSuggestionClick}
                      isLoading={isLoadingSuggestions}
                      userName={leadContext?.name || 'there'}
                      leadContext={leadContext}
                    />
                  </div>
                )}
      
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className="border-b border-gray-200 py-6 px-2"
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        {message.isUser ? (
                          <User className="h-6 w-6 text-gray-600" />
                        ) : (
                          <Sparkles className="h-4 w-4 text-blue-600" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="font-semibold text-sm text-gray-900">
                            {message.isUser ? 'You' : 'Ava'}
                          </span>
                          <span className="text-xs text-gray-400">
                            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <div className="text-sm text-gray-700 leading-relaxed">
                          {message.isUser ? (
                            <div className="whitespace-pre-wrap">{message.content}</div>
                          ) : (
                            <div className="max-w-none">
                              <ReactMarkdown 
                                remarkPlugins={[remarkGfm]}
                                components={{
                                  // Custom styling for headings
                                  h1: ({ children }) => (
                                    <h1 className="text-lg font-bold text-gray-900 mt-4 mb-3 first:mt-0">
                                      {children}
                                    </h1>
                                  ),
                                  h2: ({ children }) => (
                                    <h2 className="text-base font-bold text-gray-900 mt-4 mb-2 first:mt-0">
                                      {children}
                                    </h2>
                                  ),
                                  h3: ({ children }) => (
                                    <h3 className="text-sm font-semibold text-gray-900 mt-3 mb-2 first:mt-0">
                                      {children}
                                    </h3>
                                  ),
                                  h4: ({ children }) => (
                                    <h4 className="text-sm font-semibold text-gray-900 mt-3 mb-1 first:mt-0">
                                      {children}
                                    </h4>
                                  ),
                                  h5: ({ children }) => (
                                    <h5 className="text-xs font-semibold text-gray-900 mt-2 mb-1 first:mt-0">
                                      {children}
                                    </h5>
                                  ),
                                  h6: ({ children }) => (
                                    <h6 className="text-xs font-medium text-gray-700 mt-2 mb-1 first:mt-0">
                                      {children}
                                    </h6>
                                  ),
                                  // Custom styling for paragraphs
                                  p: ({ children }) => (
                                    <p className="text-gray-700 mb-3 leading-relaxed">
                                      {children}
                                    </p>
                                  ),
                                  // Custom styling for unordered lists
                                  ul: ({ children }) => (
                                    <ul className="list-disc list-inside text-gray-700 mb-3 space-y-1 ml-4">
                                      {children}
                                    </ul>
                                  ),
                                  // Custom styling for ordered lists
                                  ol: ({ children }) => (
                                    <ol className="list-decimal list-inside text-gray-700 mb-3 space-y-1 ml-4">
                                      {children}
                                    </ol>
                                  ),
                                  // Custom styling for list items
                                  li: ({ children }) => (
                                    <li className="text-gray-700">
                                      {children}
                                    </li>
                                  ),
                                  // Custom styling for code blocks
                                  pre: ({ children }) => (
                                    <pre className="bg-gray-900 text-gray-100 p-4 rounded overflow-x-auto text-sm mb-4">
                                      {children}
                                    </pre>
                                  ),
                                  // Custom styling for inline code
                                  code: ({ children, className }) => {
                                    const isInline = !className?.includes('language-');
                                    if (isInline) {
                                      return (
                                        <code className="bg-blue-50 text-blue-600 px-1 py-0.5 rounded text-sm font-mono">
                                          {children}
                                        </code>
                                      );
                                    }
                                    return <code className={className}>{children}</code>;
                                  },
                                  // Custom styling for blockquotes
                                  blockquote: ({ children }) => (
                                    <blockquote className="border-l-4 border-blue-500 bg-blue-50 p-4 my-4 italic">
                                      {children}
                                    </blockquote>
                                  ),
                                  // Custom styling for strong/bold text
                                  strong: ({ children }) => (
                                    <strong className="font-semibold text-gray-900">
                                      {children}
                                    </strong>
                                  ),
                                  // Custom styling for emphasis/italic text
                                  em: ({ children }) => (
                                    <em className="italic text-gray-700">
                                      {children}
                                    </em>
                                  ),
                                  // Custom styling for tables
                                  table: ({ children }) => (
                                    <div className="overflow-x-auto my-4">
                                      <table className="min-w-full border-collapse border border-gray-300">
                                        {children}
                                      </table>
                                    </div>
                                  ),
                                  th: ({ children }) => (
                                    <th className="border border-gray-300 bg-gray-100 px-4 py-2 text-left font-semibold">
                                      {children}
                                    </th>
                                  ),
                                  td: ({ children }) => (
                                    <td className="border border-gray-300 px-4 py-2">
                                      {children}
                                    </td>
                                  ),
                                }}
                              >
                                {message.content}
                              </ReactMarkdown>
                              
                              {/* Inline Chart - show chart if available */}
                              {message.sqlDetails?.chart_config && (
                                <InlineSQLChart
                                  chartConfig={message.sqlDetails.chart_config}
                                  sqlData={{
                                    rows: message.sqlDetails.rows,
                                    columns: message.sqlDetails.columns
                                  }}
                                />
                              )}
                              
                              {/* SQL Details Panel */}
                              {message.sqlDetails && (
                                <div className="mt-4">
                                  <SQLDetailsPanel 
                                    sqlDetails={message.sqlDetails}
                                    defaultCollapsed={true}
                                  />
                                </div>
                              )}
                              
                              {/* Streaming indicator */}
                              {streamingMessageId === message.id && (
                                <div className="flex items-center space-x-1 mt-2">
                                  <div className="w-1 h-1 bg-blue-500 rounded-full animate-pulse"></div>
                                  <div className="w-1 h-1 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.1s' }}></div>
                                  <div className="w-1 h-1 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                                  <span className="text-xs text-blue-500 ml-2">streaming...</span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {isLoading && !isStreaming && (
                  <div className="border-b border-gray-200 py-6 px-2">
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        <Sparkles className="h-4 w-4 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="font-semibold text-sm text-gray-900">Ava</span>
                        </div>
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t border-gray-200 bg-white px-6 py-4 flex-shrink-0">
                <div className="flex items-end space-x-3">
                  <div className="flex-1 relative">
                    <textarea
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          sendMessage()
                        }
                      }}
                      placeholder="Type your message... (Shift+Enter for new line)"
                      className="w-full min-h-[48px] max-h-[120px] px-4 py-3 text-base border-0 outline-none focus:outline-none focus:ring-0 resize-none overflow-y-auto bg-white"
                      disabled={isLoading}
                      rows={1}
                      style={{
                        height: 'auto',
                        minHeight: '48px',
                        maxHeight: '120px'
                      }}
                      onInput={(e) => {
                        const target = e.target as HTMLTextAreaElement;
                        target.style.height = 'auto';
                        target.style.height = Math.min(target.scrollHeight, 120) + 'px';
                      }}
                    />
                  </div>
                  <Button
                    onClick={sendMessage}
                    disabled={!inputMessage.trim() || isLoading}
                    className="h-12 w-12 bg-black hover:bg-gray-800 rounded-full flex-shrink-0"
                  >
                    {isLoading ? (
                      <div className="w-4 h-4 border-2 border-gray-400 border-t-white rounded-full animate-spin" />
                    ) : (
                      <Send className="h-5 w-5" />
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
