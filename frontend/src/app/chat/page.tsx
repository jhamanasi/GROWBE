'use client'

import { useState, useRef, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { useSearchParams, useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send, Bot, User, Sparkles, DollarSign, ArrowLeft } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import 'katex/dist/katex.min.css'
import SQLDetailsPanel from '@/components/SQLDetailsPanel'
import CalculationDetailsPanel from '@/components/CalculationDetailsPanel'
import MathDisplay from '@/components/MathDisplay'
// Removed popup interactive components to reduce latency and simplify UX
// import InlineSQLChart from '@/components/InlineSQLChart'
// import InteractivePrompts from '@/components/InteractivePrompts'
import SuggestionCards from '@/components/SuggestionCards'
import { StreamingProvider, useStreamingContext } from '@/contexts/StreamingContext'

interface ChartConfig {
  type: string;
  title: string;
  x_axis: string;
  y_axis: string;
  eligible: boolean;
  series_columns?: string[];
}

interface CustomerContext {
  customer_id: string;
  first_name: string;
  last_name: string;
  base_salary_annual?: number;
  persona_type?: string;
  assessment?: {
    primary_goal?: string;
    debt_status?: string;
    employment_status?: string;
    timeline?: string;
    risk_tolerance?: string;
  };
}

interface SQLDetails {
  query: string;
  result_count: number;
  columns: string[];
  rows: Record<string, unknown>[];
  total_rows: number;
  execution_time?: string;
  truncated?: boolean;
  chart_config?: ChartConfig;
}

interface CalculationStep {
  title: string;
  description: string;
  latex: string;
  display: boolean;
}

interface CalculationDetails {
  scenario_type: string;
  calculation_steps?: CalculationStep[];
  latex_formulas?: string[];
  tool_name?: string;
}

interface InteractiveComponent {
  type: string;
  config: Record<string, unknown>;
  field_name?: string;
}

interface Message {
  id: string
  content: string
  isUser: boolean
  timestamp: number
  sqlDetails?: SQLDetails
  calculationDetails?: CalculationDetails
  interactiveComponent?: InteractiveComponent
  guidance?: string
}

interface Suggestion {
  title: string;
  description: string;
  question: string;
  icon: string;
}

const CHAT_HISTORY_STORAGE_KEY = 'finagent_chat_history'
const MAX_MESSAGE_LENGTH = 4000
const STREAM_POLL_INTERVAL = 250
const SUGGESTION_LIMIT = 6
const MAX_HISTORY_MESSAGES = 40

const renderMessageSegments = (content: string | undefined) => {
  if (!content) return null

  const parts = content.split(/(\$\$[\s\S]+?\$\$)/g)

  return parts.map((part, index) => {
    if (!part) return null

    const isLatexBlock = part.startsWith('$$') && part.endsWith('$$')

    if (isLatexBlock) {
      const latex = part.slice(2, -2).trim()
      if (!latex) return null
      return <MathDisplay key={`latex-${index}`} formula={latex} displayMode />
    }

    return (
      <ReactMarkdown key={`md-${index}`} remarkPlugins={[remarkGfm]}>
        {part}
      </ReactMarkdown>
    )
  })
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
  const router = useRouter();
  const customerId = searchParams.get('customerId');
  const userType = searchParams.get('userType'); // 'existing' or 'new'
  
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const greetingSentRef = useRef(false)
  const initializingRef = useRef(false)
  
  // Customer context state
  const [customerContext, setCustomerContext] = useState<CustomerContext | null>(null)
  const [isLoadingCustomer, setIsLoadingCustomer] = useState(false)

  // NEW: Redirect to the new persistent conversations UI with sidebar
  useEffect(() => {
    const params = new URLSearchParams(Array.from(searchParams.entries()));
    const query = params.toString();
    router.replace(`/conversations${query ? `?${query}` : ''}`);
  }, []);

  // Interactive components disabled

  // Suggestions state
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false)

  // Load customer context from customer ID
  useEffect(() => {
    if (customerId) {
      initializeChat(customerId, userType);
    }
  }, [customerId, userType]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const initializeChat = async (customerId: string, userType: string | null) => {
    if (initializingRef.current) return;
    initializingRef.current = true;

    try {
      setIsLoadingCustomer(true);
      
      // Load customer context
      if (userType === 'existing') {
        const response = await fetch(`http://localhost:8000/customer/${customerId}/context`);
        if (response.ok) {
          const context = await response.json();
          setCustomerContext(context.context);
        }
      } else if (userType === 'new') {
        // For new users, we might not have full context yet
        setCustomerContext({ customer_id: customerId, first_name: '', last_name: '' });
      }

      // Load suggestions
      await loadSuggestions();

      // Send initial greeting if not already sent
      if (!greetingSentRef.current) {
        greetingSentRef.current = true;
        if (userType === 'existing') {
          // Show immediate greeting while agent generates personalized response
          const firstName = customerContext?.first_name || 'there';
          const immediateGreeting = `Hi ${firstName}! I'm Growbe, your AI financial advisor. I'm reviewing your financial profile to provide personalized insights...`;
          addMessage(immediateGreeting, false);
          
          // Then ask the agent to generate a personalized greeting using customer context
          setTimeout(async () => {
            await streamAgentMessage(
              'Greet the user by first name and briefly summarize their financial profile in 1-2 sentences. Then suggest one or two relevant next steps.'
            );
          }, 100); // Small delay to let immediate greeting show first
        } else {
          const greetingMessage = `Welcome! I'm Growbe, your AI financial advisor. I've created your financial profile based on your assessment. Let's start working on your financial goals!`;
          addMessage(greetingMessage, false);
        }
      }
    } catch (error) {
      console.error('Error initializing chat:', error);
    } finally {
      setIsLoadingCustomer(false);
      initializingRef.current = false;
    }
  };

  // Stream an assistant-initiated message without adding a user bubble
  const streamAgentMessage = async (prompt: string) => {
    try {
      // Build conversation history from messages
      const history = messages.map(msg => ({
        role: msg.isUser ? 'user' : 'assistant',
        content: msg.content
      }))
      
      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: prompt,
          session_id: customerId,
          user_type: userType,
          history: history  // Include conversation history
        })
      });

      if (!response.ok || !response.body) {
        addMessage('Sorry, I encountered an error. Please try again.', false);
        return;
      }

      // Create a placeholder assistant message and stream into it
      const agentMessageId = addMessage('', false);
      setStreamingMessageId(agentMessageId);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith('data:')) continue;
          const dataStr = line.slice(5).trim();
          if (dataStr === '[DONE]') {
            continue;
          }
          try {
            const data = JSON.parse(dataStr);
            if (data?.content) {
              setMessages(prev => prev.map(m => m.id === agentMessageId ? { ...m, content: (m.content || '') + data.content } : m));
            }
            if (data?.sql_details) {
              setMessages(prev => prev.map(m => m.id === agentMessageId ? { ...m, sqlDetails: data.sql_details } : m));
            }
            if (data?.calculation_details) {
              setMessages(prev => prev.map(m => m.id === agentMessageId ? { ...m, calculationDetails: data.calculation_details } : m));
            }
          } catch {}
        }
      }

      if (buffer) {
        const line = buffer.trim();
        if (line.startsWith('data:')) {
          const dataStr = line.slice(5).trim();
          if (dataStr !== '[DONE]') {
            try {
              const data = JSON.parse(dataStr);
              if (data?.content) {
                setMessages(prev => prev.map(m => m.id === agentMessageId ? { ...m, content: (m.content || '') + data.content } : m));
              }
              if (data?.sql_details) {
                setMessages(prev => prev.map(m => m.id === agentMessageId ? { ...m, sqlDetails: data.sql_details } : m));
              }
              if (data?.calculation_details) {
                setMessages(prev => prev.map(m => m.id === agentMessageId ? { ...m, calculationDetails: data.calculation_details } : m));
              }
            } catch {}
          }
        }
      }

      setStreamingMessageId(null);
    } catch (error) {
      console.error('Error streaming agent message:', error);
      addMessage('Sorry, I encountered an error. Please try again.', false);
    }
  };

  const loadSuggestions = async () => {
    try {
      setIsLoadingSuggestions(true);
      const response = await fetch('http://localhost:8000/suggestions');
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions);
      }
    } catch (error) {
      console.error('Error loading suggestions:', error);
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  const addMessage = (content: string, isUser: boolean, sqlDetails?: SQLDetails, calculationDetails?: CalculationDetails, interactiveComponent?: InteractiveComponent, guidance?: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      content,
      isUser,
      timestamp: Date.now(),
      sqlDetails,
      calculationDetails,
      interactiveComponent,
      guidance
    }
    setMessages(prev => [...prev, newMessage])
    return newMessage.id
  }

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return

    const userMessageId = addMessage(message, true)
    setInputMessage('')
    setIsLoading(true)

    try {
      // Build conversation history from messages (exclude current message)
      const history = messages.map(msg => ({
        role: msg.isUser ? 'user' : 'assistant',
        content: msg.content
      }))
      
      // Streamed chat: connect to /chat/stream and append chunks as they arrive
      const response = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          session_id: customerId,
          user_type: userType,
          history: history  // Include conversation history
        })
      })

      if (!response.ok || !response.body) {
        addMessage('Sorry, I encountered an error. Please try again.', false)
      } else {
        // Create a placeholder assistant message and stream into it
        const agentMessageId = addMessage('', false)
        setStreamingMessageId(agentMessageId)
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { value, done } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          const parts = buffer.split('\n\n')
          // Keep the last partial chunk in buffer
          buffer = parts.pop() || ''

          for (const part of parts) {
            const line = part.trim()
            if (!line.startsWith('data:')) continue
            const dataStr = line.slice(5).trim()
            if (dataStr === '[DONE]') {
              continue
            }
            try {
              const data = JSON.parse(dataStr)
              if (data?.content) {
                setMessages(prev => prev.map(m => m.id === agentMessageId ? { ...m, content: (m.content || '') + data.content } : m))
              }
              if (data?.sql_details) {
                setMessages(prev => prev.map(m => m.id === agentMessageId ? { ...m, sqlDetails: data.sql_details } : m))
              }
              if (data?.calculation_details) {
                setMessages(prev => prev.map(m => m.id === agentMessageId ? { ...m, calculationDetails: data.calculation_details } : m))
              }
            } catch (e) {
              // ignore malformed chunks
            }
          }
        }
        // Flush any remaining buffer chunk
        if (buffer) {
          const line = buffer.trim()
          if (line.startsWith('data:')) {
            const dataStr = line.slice(5).trim()
            if (dataStr !== '[DONE]') {
              try {
                const data = JSON.parse(dataStr)
                if (data?.content) {
                  setMessages(prev => prev.map(m => m.id === agentMessageId ? { ...m, content: (m.content || '') + data.content } : m))
                }
                if (data?.sql_details) {
                  setMessages(prev => prev.map(m => m.id === agentMessageId ? { ...m, sqlDetails: data.sql_details } : m))
                }
                if (data?.calculation_details) {
                  setMessages(prev => prev.map(m => m.id === agentMessageId ? { ...m, calculationDetails: data.calculation_details } : m))
                }
              } catch {}
            }
          }
        }
        setStreamingMessageId(null)
      }
    } catch (error) {
      console.error('Error sending message:', error)
      addMessage('Sorry, I encountered an error. Please try again.', false)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestionClick = (question: string) => {
    handleSendMessage(question)
  }

  // Interactive responses removed

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  // Show loading state while initializing
  if (isLoadingCustomer) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your financial profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      {/* Fixed Header */}
      <div className="flex-shrink-0 bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-blue-600 rounded-lg flex items-center justify-center">
                <DollarSign className="h-5 w-5 text-white" />
              </div>
              <div>
              <h1 className="text-lg font-bold text-gray-900">Growbe</h1>
              <p className="text-sm text-gray-600">Chat with Growbe</p>
              <div className="text-xs text-green-600 font-medium">✓ Sticky Input Active</div>
              </div>
            </div>
            <Link href="/">
              <Button variant="outline" size="sm" className="flex items-center space-x-2">
                <ArrowLeft className="h-4 w-4" />
                <span>Back to Home</span>
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Messages - Fixed height calculation */}
      <div className="flex-1 overflow-y-auto" style={{ height: 'calc(100vh - 120px)' }}>
        <div className="max-w-4xl mx-auto px-4 py-6">
          {messages.length === 0 && !isLoadingSuggestions ? (
            <SuggestionCards
              suggestions={suggestions}
              onSuggestionClick={handleSuggestionClick}
              isLoading={isLoadingSuggestions}
              userName={customerContext?.first_name}
              customerContext={customerContext}
            />
          ) : (
            <div className="space-y-6">
              {messages.map((message) => {
                return (
                  <div key={message.id} className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`flex max-w-3xl ${message.isUser ? 'flex-row-reverse' : 'flex-row'} items-start space-x-3`}>
                      {/* Avatar */}
                      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                        message.isUser 
                          ? 'bg-blue-600' 
                          : 'bg-gradient-to-r from-green-500 to-blue-600'
                      }`}>
                        {message.isUser ? (
                          <User className="h-4 w-4 text-white" />
                        ) : (
                          <Bot className="h-4 w-4 text-white" />
                        )}
                      </div>

                      {/* Message Content */}
                      <div className={`flex-1 ${message.isUser ? 'text-right' : 'text-left'}`}>
                        <div className={`inline-block p-4 rounded-2xl ${
                          message.isUser 
                            ? 'bg-blue-600 text-white' 
                            : 'bg-white border border-gray-200 text-gray-900'
                        }`}>
                          <div className="prose prose-sm max-w-none">
                            {renderMessageSegments(message.content)}
                          </div>
                          
                        {/* Guidance removed to reduce extra UI latency */}
                        </div>

                        {/* Interactive components disabled */}

                        {/* SQL Details */}
                        {message.sqlDetails && (
                          <div className="mt-3">
                            <SQLDetailsPanel sqlDetails={message.sqlDetails} />
                          </div>
                        )}

                        {/* Calculation Details */}
                        {message.calculationDetails && (
                          <div className="mt-3">
                            <CalculationDetailsPanel calculationDetails={message.calculationDetails} />
                          </div>
                        )}

                        {/* Timestamp */}
                        <div className={`text-xs text-gray-500 mt-1 ${message.isUser ? 'text-right' : 'text-left'}`}>
                          {formatTimestamp(message.timestamp)}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}

              {/* Loading indicator */}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-blue-600 rounded-full flex items-center justify-center">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                    <div className="bg-white border border-gray-200 rounded-2xl p-4">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Fixed Input at Bottom */}
      <div className="flex-shrink-0 bg-white border-t shadow-lg bg-gradient-to-r from-green-50 to-blue-50">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex space-x-3">
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage(inputMessage)}
              placeholder="Ask Growbe about your finances..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button
              onClick={() => handleSendMessage(inputMessage)}
              disabled={isLoading || !inputMessage.trim()}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}