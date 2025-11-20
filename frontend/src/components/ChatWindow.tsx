'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send, Bot, User, ChevronDown, ChevronRight, LogOut, Menu } from 'lucide-react'; // Import icons
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import SQLDetailsPanel from '@/components/SQLDetailsPanel';
import CalculationDetailsPanel from '@/components/CalculationDetailsPanel';
import MathDisplay from '@/components/MathDisplay';
import ConversationTitle from '@/components/ConversationTitle';
import ChartDisplay from '@/components/ChartDisplay';
import { BackgroundLines } from "@/components/ui/background-lines";
import { useRouter } from 'next/navigation'; // Import useRouter

interface CustomerContext {
  customer_id?: string;
  first_name?: string;
  last_name?: string;
}

interface Message {
  message_id: string;
  role: string;
  content: string | null;
  tool_name?: string | null;
  tool_payload?: any;
  sql_details?: any;
  calculation_details?: any;
  chart_data?: any;
  created_at: string;
}

interface ChatWindowProps {
  conversationId: string;
  customerId?: string;
  sessionId?: string;
  isSidebarOpen?: boolean;
  toggleSidebar?: () => void;
  onConversationsRefresh?: () => void;
  onConversationCreated?: (conversationId: string) => void;
}

export default function ChatWindow({
  conversationId,
  customerId,
  sessionId,
  isSidebarOpen,
  toggleSidebar,
  onConversationsRefresh,
  onConversationCreated,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [title, setTitle] = useState('New Chat');
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null); // Ref for the textarea
  const [customerContext, setCustomerContext] = useState<CustomerContext | null>(null);
  const isStreamingRef = useRef(false); // Track if we're currently streaming
  const LIMIT = 30;
  const router = useRouter(); // Initialize useRouter

  const fetchMessages = async (reset = false) => {
    // Don't fetch messages if we're currently streaming (would interrupt real-time updates)
    if (isStreamingRef.current) {
      console.log('⏸️ Skipping fetchMessages - currently streaming');
      return;
    }

    if (reset) {
      setOffset(0);
      setHasMore(true);
    }

    const currentOffset = reset ? 0 : offset;
    setIsLoadingMore(!reset);

    try {
      const response = await fetch(
        `http://localhost:8000/api/conversations/${conversationId}/messages?limit=${LIMIT}&offset=${currentOffset}`
      );
      if (response.ok) {
        const data: Message[] = await response.json();
        console.log('📊 [Frontend] Fetched messages from DB:', data.map(m => ({ id: m.message_id, has_chart: !!m.chart_data })));
        // Parse JSON strings from database (with error handling)
        const parsedData = data.map((msg) => {
          try {
            const parsed_msg = {
              ...msg,
              sql_details: msg.sql_details
                ? typeof msg.sql_details === 'string'
                  ? JSON.parse(msg.sql_details)
                  : msg.sql_details
                : undefined,
              calculation_details: msg.calculation_details
                ? typeof msg.calculation_details === 'string'
                  ? JSON.parse(msg.calculation_details)
                  : msg.calculation_details
                : undefined,
              chart_data: msg.chart_data
                ? typeof msg.chart_data === 'string'
                  ? (() => {
                      const parsed = JSON.parse(msg.chart_data as string);
                      console.log('📊 [Frontend] Parsed chart_data from DB for message', msg.message_id, ':', parsed);
                      return parsed;
                    })()
                  : (() => {
                      console.log('📊 [Frontend] Chart_data already object for message', msg.message_id, ':', msg.chart_data);
                      return msg.chart_data;
                    })()
                : (() => {
                    console.log('📊 [Frontend] NO chart_data in DB for message:', msg.message_id);
                    return undefined;
                  })(),
              tool_payload: msg.tool_payload
                ? typeof msg.tool_payload === 'string'
                  ? JSON.parse(msg.tool_payload)
                  : msg.tool_payload
                : undefined,
            };
            console.log('📊 [Frontend] Returning parsed message:', parsed_msg.message_id, 'has chart_data:', !!parsed_msg.chart_data);
            return parsed_msg;
          } catch (e) {
            console.error('Failed to parse message JSON:', e);
            return msg; // Return original message if parsing fails
          }
        });
        // Remove assistant leading-echoes where assistant repeats the immediately preceding user content
        const stripLeadingUserEcho = (messagesArr: Message[]) => {
          const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          const result: Message[] = [];
          for (let i = 0; i < messagesArr.length; i++) {
            const m = messagesArr[i];
            if (m.role === 'assistant' && i > 0 && messagesArr[i - 1].role === 'user') {
              const userText = (messagesArr[i - 1].content || '').trim();
              if (userText && m.content) {
                try {
                  const assistantContent = (m.content || '').trim();
                  const lcAssistant = assistantContent.toLowerCase();
                  const lcUser = userText.toLowerCase();
                  
                  // Check if assistant message is exactly or nearly exactly the user message
                  if (lcAssistant === lcUser || 
                      lcAssistant.startsWith(lcUser + ' ') || 
                      lcAssistant.startsWith(lcUser + '\n') ||
                      lcAssistant.startsWith(lcUser + ':') ||
                      lcAssistant.startsWith(lcUser + ';')) {
                    // This is an echo - skip this message entirely
                    console.log('🚫 Skipping echo message:', assistantContent.slice(0, 50));
                    continue;
                  }
                  
                  const userTextEscaped = esc(userText);
                  // Allow a short prefix (e.g., 'growbe.' or similar) before the user's echoed text
                  const pattern = new RegExp('^\\s*(?:.{0,30}?)(?:' + userTextEscaped + ')[\\s:;\\-–—,.]*', 'i');
                  let newContent = assistantContent.replace(pattern, '').trim();
                  
                  // Fallback: lowercase substring search if regex didn't remove anything meaningful
                  if (newContent.length === assistantContent.length || newContent.length < 10) {
                    const pos = lcAssistant.indexOf(lcUser);
                    // Only remove if found near the start (first 50 chars) and there's content after
                    if (pos >= 0 && pos <= 50 && pos + lcUser.length < assistantContent.length) {
                      newContent = assistantContent.slice(pos + lcUser.length).trimStart();
                      // Also remove common separators that might follow
                      newContent = newContent.replace(/^[\s:;\-–—,.]+\s*/, '');
                    }
                  }
                  
                  // Only use cleaned version if it's meaningfully different and not empty
                  if (newContent.length > 0 && newContent !== assistantContent) {
                    result.push({ ...m, content: newContent });
                    continue;
                  }
                } catch (e) {
                  // if regex fails, just push original
                  console.warn('Echo detection failed in stripLeadingUserEcho:', e);
                }
              }
            }
            result.push(m);
          }
          return result;
        };
        const stripped = stripLeadingUserEcho(parsedData);
        const deduped = dedupeMessages(stripped);
        if (reset) {
          setMessages(deduped);
        } else {
          setMessages((prev) => [...deduped, ...prev]);
        }
        setHasMore(data.length === LIMIT);
        setOffset(currentOffset + data.length);
      }
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    } finally {
      setIsLoadingMore(false);
    }
  };

  const fetchConversation = async () => {
    try {
      const params = new URLSearchParams();
      if (customerId) params.append('customer_id', customerId);
      if (sessionId) params.append('session_id', sessionId);

      const response = await fetch(`http://localhost:8000/api/conversations?${params.toString()}`);
      if (response.ok) {
        const conversations = await response.json();
        const conv = conversations.find((c: any) => c.conversation_id === conversationId);
        if (conv) setTitle(conv.title || 'New Chat');
      }
    } catch (error) {
      console.error('Failed to fetch conversation:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    let currentConversationId = conversationId;

    // If we're on the greeting page (no conversationId), create a new conversation first
    if (!currentConversationId) {
      try {
        const createResponse = await fetch('http://localhost:8000/api/conversations/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: customerId,
          session_id: sessionId,
          scenario_type: customerId ? 'existing' : 'new',
        }),
        });

        if (!createResponse.ok) {
          throw new Error('Failed to create conversation');
        }

        const convData = await createResponse.json();
        currentConversationId = convData.conversation_id;

        // Notify parent that conversation was created
        if (onConversationCreated) {
          onConversationCreated(currentConversationId);
        }

        // Refresh the sidebar conversations list
        if (onConversationsRefresh) {
          onConversationsRefresh();
        }

      } catch (error) {
        console.error('Failed to create conversation:', error);
        setIsLoading(false);
        return;
      }
    }

    // 1. IMMEDIATELY show user message in UI (optimistic update)
    const tempUserMessageId = `temp-user-${Date.now()}`;
    const userMsg: Message = {
      message_id: tempUserMessageId,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    // 2. Build conversation history for streaming
    const history = messages
      .filter((m) => m.message_id !== tempUserMessageId) // Exclude temp message
      .map((msg) => ({
        role: msg.role,
        content: msg.content || '',
      }));
    history.push({ role: 'user', content: userMessage });

    // 3. Stream the response using /chat/stream (which now saves messages automatically)
    try {
      // Mark streaming early so any conversationId change doesn't trigger fetchMessages mid-stream
      isStreamingRef.current = true;

      const streamResponse = await fetch('http://localhost:8000/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          session_id: customerId || sessionId,
          user_type: customerId ? 'existing' : 'new',
          history: history.slice(-10), // Last 10 messages for context
          conversation_id: currentConversationId,
        }),
      });

      if (!streamResponse.ok || !streamResponse.body) {
        throw new Error('Failed to start streaming');
      }

      // Create placeholder assistant message
      const tempAssistantId = `temp-assistant-${Date.now()}`;
      const assistantMsg: Message = {
        message_id: tempAssistantId,
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // Stream the response
      const reader = streamResponse.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullContent = '';
      let sqlDetails: any = null;
      let calculationDetails: any = null;
      let chartData: any = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;

          const dataStr = trimmed.slice(5).trim();
          if (dataStr === '[DONE]') continue;

          try {
            const data = JSON.parse(dataStr);
            if (data.content) {
              const chunk = data.content;
              fullContent += chunk;
              
              // Always update the message with current content (for real-time streaming visibility)
              let displayContent = fullContent;
              
              // Remove leading user echo if present (for both streaming and final display)
              const lastUser = userMessage || '';
              if (lastUser.trim() && fullContent.length > 0) {
                try {
                  // Escape special regex characters in user message
                  const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                  const userTextEscaped = esc(lastUser.trim());
                  
                  // Try regex pattern first (allows prefix)
                  const pattern = new RegExp('^\\s*(?:.{0,30}?)(?:' + userTextEscaped + ')[\\s:;\-–—,.]*', 'i');
                  let cleaned = fullContent.replace(pattern, '').trimStart();
                  
                  // Fallback: lowercase substring search if regex didn't remove anything meaningful
                  if (cleaned.length === fullContent.length || cleaned.length < 10) {
                    const lcFull = fullContent.toLowerCase();
                    const lcUser = lastUser.trim().toLowerCase();
                    const pos = lcFull.indexOf(lcUser);
                    // Only remove if found near the start (first 50 chars) and there's content after
                    if (pos >= 0 && pos <= 50 && pos + lcUser.length < fullContent.length) {
                      cleaned = fullContent.slice(pos + lcUser.length).trimStart();
                      // Also remove common separators that might follow
                      cleaned = cleaned.replace(/^[\s:;\-–—,.]+\s*/, '');
                    }
                  }
                  
                  // Only use cleaned version if it's meaningfully different and not empty
                  if (cleaned.length > 0 && cleaned !== fullContent) {
                    displayContent = cleaned;
                  }
                } catch (e) {
                  // Regex failed, use original content
                  console.warn('Echo detection failed:', e);
                }
              }
              
              // Update message with cleaned content for real-time streaming
              setMessages((prev) =>
                prev.map((m) =>
                  m.message_id === tempAssistantId
                    ? { ...m, content: displayContent }
                    : m
                )
              );
            }
            if (data.sql_details) {
              sqlDetails = data.sql_details;
              setMessages((prev) =>
                prev.map((m) =>
                  m.message_id === tempAssistantId
                    ? { ...m, sql_details: sqlDetails }
                    : m
                )
              );
            }
            if (data.calculation_details) {
              calculationDetails = data.calculation_details;
              setMessages((prev) =>
                prev.map((m) =>
                  m.message_id === tempAssistantId
                    ? { ...m, calculation_details: calculationDetails }
                    : m
                )
              );
            }
            if (data.chart_data) {
              chartData = data.chart_data;
              console.log('📊 [Frontend] Received chart_data from stream:', chartData);
              console.log('   - Chart type:', chartData?.chart_type);
              console.log('   - Status:', chartData?.status);
              setMessages((prev) =>
                prev.map((m) =>
                  m.message_id === tempAssistantId
                    ? { ...m, chart_data: chartData }
                    : m
                )
              );
            }
            if (data.error) {
              console.error('Stream error from backend:', data.error);
              throw new Error(data.error);
            }
          } catch (e) {
            // Log parse errors but don't break the stream
            if (e instanceof Error && e.message !== dataStr) {
              console.warn('Failed to parse stream chunk:', e);
            }
          }
        }
      }

      // 4. After streaming completes, clean final content and mark streaming as done
      isStreamingRef.current = false;
      
      // Final echo cleanup on the complete content
      let finalContent = fullContent;
      if (userMessage.trim() && fullContent.length > 0) {
        try {
          const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          const userTextEscaped = esc(userMessage.trim());
          
          // Try regex pattern first
          const pattern = new RegExp('^\\s*(?:.{0,30}?)(?:' + userTextEscaped + ')[\\s:;\-–—,.]*', 'i');
          let cleaned = fullContent.replace(pattern, '').trimStart();
          
          // Fallback: lowercase substring search
          if (cleaned.length === fullContent.length || cleaned.length < 10) {
            const lcFull = fullContent.toLowerCase();
            const lcUser = userMessage.trim().toLowerCase();
            const pos = lcFull.indexOf(lcUser);
            if (pos >= 0 && pos <= 50 && pos + lcUser.length < fullContent.length) {
              cleaned = fullContent.slice(pos + lcUser.length).trimStart();
              cleaned = cleaned.replace(/^[\s:;\-–—,.]+\s*/, '');
            }
          }
          
          // Check if assistant message is just the user message (exact or near-exact match)
          const lcFinal = fullContent.toLowerCase().trim();
          const lcUserMsg = userMessage.toLowerCase().trim();
          if (lcFinal === lcUserMsg || lcFinal.startsWith(lcUserMsg + ' ') || lcFinal.startsWith(lcUserMsg + '\n')) {
            cleaned = fullContent.slice(userMessage.length).trimStart();
            cleaned = cleaned.replace(/^[\s:;\-–—,.\n]+\s*/, '');
          }
          
          if (cleaned.length > 0 && cleaned !== fullContent) {
            finalContent = cleaned;
            // Update the message with cleaned content
            setMessages((prev) =>
              prev.map((m) =>
                m.message_id === tempAssistantId
                  ? { ...m, content: finalContent }
                  : m
              )
            );
          }
        } catch (e) {
          console.warn('Final echo cleanup failed:', e);
        }
      }
      
      console.log(`✅ Stream completed. Full content length: ${fullContent.length} chars, cleaned: ${finalContent.length} chars`);
      if (!finalContent.trim()) {
        console.warn('⚠️ Stream completed but no content received after cleaning');
      }
      // If the component still doesn't have a conversationId prop (it may be new),
      // fetch messages using the locally-known currentConversationId to avoid 404s.
      if (!conversationId && currentConversationId) {
        try {
          const resp = await fetch(
            `http://localhost:8000/api/conversations/${currentConversationId}/messages?limit=${LIMIT}&offset=0`
          );
          if (resp.ok) {
            const data: Message[] = await resp.json();
            const parsedData = data.map((msg) => {
              try {
                return {
                  ...msg,
                  sql_details: msg.sql_details
                    ? typeof msg.sql_details === 'string'
                      ? JSON.parse(msg.sql_details)
                      : msg.sql_details
                    : null,
                  calculation_details: msg.calculation_details
                    ? typeof msg.calculation_details === 'string'
                      ? JSON.parse(msg.calculation_details)
                      : msg.calculation_details
                    : null,
                  chart_data: msg.chart_data
                    ? typeof msg.chart_data === 'string'
                      ? JSON.parse(msg.chart_data)
                      : msg.chart_data
                    : null,
                };
              } catch (e) {
                return msg;
              }
            });
            // Deduplicate trivial echoes between user and assistant
            const deduped = dedupeMessages(parsedData);
            // Replace optimistic messages with fetched messages
            console.log('Replacing optimistic messages with DB messages (preview):', parsedData.map(m=>({id:m.message_id, role:m.role, contentPreview: (m.content||'').slice(0,80)})));
            setMessages(parsedData);
            setHasMore(parsedData.length === LIMIT);
            setOffset(parsedData.length);
          }
        } catch (e) {
          console.error('Failed to refresh messages for new conversation:', e);
        }
      } else {
        // For existing conversations, wait a bit for DB to save, then refresh
        // This ensures we get the saved messages with proper IDs, but doesn't interrupt streaming
        setTimeout(async () => {
          if (!isStreamingRef.current) {
            await fetchMessages(true);
            await fetchConversation();
          }
        }, 500); // Small delay to let DB save complete
      }
    } catch (error) {
      console.error('Error sending message:', error);
      isStreamingRef.current = false; // Mark streaming as done even on error
      // Remove temp messages on error
      setMessages((prev) =>
        prev.filter(
          (m) => m.message_id !== tempUserMessageId && !m.message_id.startsWith('temp-assistant-')
        )
      );
      // Show error message
      const errorMsg: Message = {
        message_id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      // Ensure streaming flag is cleared
      isStreamingRef.current = false;
    }
  };

  useEffect(() => {
    if (conversationId) {
      fetchMessages(true);
      fetchConversation();
    } else {
      // Clear messages when switching to greeting page (no conversationId)
      setMessages([]);
      setTitle('New Chat');
    }
  }, [conversationId]);

  // Helper to remove assistant messages that simply echo the immediate preceding user message
  const dedupeMessages = (msgs: Message[]) => {
    const out: Message[] = [];
    for (const m of msgs) {
      if (
        m.role === 'assistant' &&
        out.length > 0 &&
        out[out.length - 1].role === 'user' &&
        (m.content || '').trim() === (out[out.length - 1].content || '').trim()
      ) {
        // skip assistant echo
        continue;
      }
      out.push(m);
    }
    return out;
  };

  // Fetch customer context when we have customerId (for greeting page)
  useEffect(() => {
    if (customerId && !customerContext) {
      fetchCustomerContext();
    }
  }, [customerId, customerContext]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = inputRef.current.scrollHeight + 'px';
    }
  }, [inputMessage]);

  const fetchCustomerContext = async () => {
    if (!customerId) return;
    try {
      const response = await fetch(`http://localhost:8000/customer/${customerId}/context`);
      if (response.ok) {
        const data = await response.json();
        setCustomerContext({ first_name: data.first_name, last_name: data.last_name });
      }
    } catch (error) {
      console.error('Failed to fetch customer context:', error);
    }
  };

  const handleSignOut = () => {
    // Clear session-related data (example: localStorage, cookies)
    localStorage.removeItem('session_id'); // Assuming session_id is stored here
    localStorage.removeItem('customer_id'); // Assuming customer_id is stored here
    // Redirect to landing page
    router.push('/');
  };

  const renderMessageSegments = (content: string | undefined) => {
    if (!content) return null;

    const parts = content.split(/(\$\$[\s\S]+?\$\$)/g);

    return parts.map((part, index) => {
      if (!part) return null;

      const isLatexBlock = part.startsWith('$$') && part.endsWith('$$');

      if (isLatexBlock) {
        const latex = part.slice(2, -2).trim();
        if (!latex) return null;
        return <MathDisplay key={`latex-${index}`} formula={latex} displayMode />;
      }

      return (
        <ReactMarkdown 
          key={`md-${index}`} 
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({node, ...props}) => (
              <a 
                {...props} 
                target="_blank" 
                rel="noopener noreferrer"
                className="font-bold text-blue-600 hover:text-blue-800 hover:underline"
              />
            ),
            img: ({node, ...props}) => {
              // Prevent broken image icons by not rendering images
              console.warn('🚫 [ChatWindow] Image tag detected and blocked:', props.src);
              return null; // Don't render images at all
            },
          }}
        >
          {part}
        </ReactMarkdown>
      );
    });
  };

  const ToolDropdown = ({ message }: { message: Message }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    if (!message.sql_details && !message.calculation_details && !message.tool_payload) {
      return null;
    }

    return (
      <div className="mt-2 border-t border-gray-200 pt-2">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          <span>
            {message.sql_details && 'SQL Query & Results'}
            {message.calculation_details && 'Calculation Details'}
            {message.tool_payload && !message.sql_details && !message.calculation_details && 'Tool Output'}
          </span>
        </button>

        {isExpanded && (
          <div className="mt-2 space-y-2">
            {message.sql_details && (
              <SQLDetailsPanel sqlDetails={message.sql_details} defaultCollapsed={false} />
            )}
            {message.calculation_details && (
              <CalculationDetailsPanel
                calculationDetails={message.calculation_details}
                defaultCollapsed={false}
              />
            )}
            {message.tool_payload && !message.sql_details && !message.calculation_details && (
              <div className="border border-gray-200 bg-white p-4 rounded">
                <pre className="text-xs overflow-auto">
                  {JSON.stringify(message.tool_payload, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`h-screen flex flex-col bg-gray-50 ${isSidebarOpen ? 'ml-80' : 'ml-20'} transition-all duration-300`}>
      {/* Header with Title and growbe. branding */}
      <div className="flex-shrink-0 p-4 border-b border-gray-300 bg-gray-100 flex items-center justify-between z-10">
        <div className="flex items-center flex-grow">
        <ConversationTitle
          conversationId={conversationId}
          title={title}
          onTitleUpdate={(newTitle) => setTitle(newTitle)}
        />
        </div>

        {/* growbe. branding on the right */}
        <div className="text-3xl font-bold text-gray-900">
          growbe.
        </div>
      </div>

      {/* Messages Area - Conditional rendering for initial state */}
      {messages.length === 0 ? (
        <>
          {/* Full-width BackgroundLines that ignores sidebar margin */}
          <div className={`absolute inset-0 ${isSidebarOpen ? 'left-80' : 'left-20'} top-0`} style={{ height: 'calc(100vh - 120px)' }}>
            <BackgroundLines className="flex items-center justify-center w-full h-full flex-col px-4">
              <div className="text-center z-20 relative">
                <h1 className="text-4xl font-bold text-gray-800 mb-4">
            Hello, {customerContext?.first_name || sessionId?.substring(0, 8) || 'there'}
          </h1>
                <p className="text-gray-600 text-xl">
                  What money move are we making today?
                </p>
              </div>
            </BackgroundLines>
        </div>

          {/* Invisible spacer to maintain layout */}
          <div className="flex-1" style={{ height: 'calc(100vh - 140px)' }} />
        </>
      ) : (
        <div className="overflow-y-auto p-4 space-y-4 pt-8" style={{ height: 'calc(100vh - 140px)' }}>
        {hasMore && messages.length >= LIMIT && (
          <div className="text-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => fetchMessages(false)}
              disabled={isLoadingMore}
            >
              {isLoadingMore ? 'Loading...' : 'Load earlier messages'}
            </Button>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.message_id}
            className={`flex gap-3 ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.role !== 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                <Bot className="h-5 w-5 text-blue-600" />
              </div>
            )}

            <div
              className={`max-w-[80%] p-4 transition-all duration-200 hover:shadow-md ${
                message.role === 'user'
                  ? 'bg-gray-100 text-gray-900 rounded-2xl shadow-sm border border-gray-200'
                  : 'bg-white border border-gray-200 text-gray-900 rounded-2xl shadow-sm'
              }`}
            >
              {message.role === 'user' ? (
                <div className="whitespace-pre-wrap">{message.content}</div>
              ) : (
                <>
                  <div className="prose prose-sm max-w-none">
                    {renderMessageSegments(message.content || '')}
                  </div>
                    {message.chart_data && <ChartDisplay chartData={message.chart_data} />}
                  <ToolDropdown message={message} />
                </>
              )}
              {/* Hidden timestamp - data preserved for ordering/analytics */}
              {/* <div
                className={`text-xs mt-2 ${
                  message.role === 'user' ? 'text-gray-600' : 'text-gray-500'
                }`}
              >
                {new Date(message.created_at).toLocaleTimeString()}
              </div> */}
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                <User className="h-5 w-5 text-gray-600" />
              </div>
            )}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>
      )}

      {/* Floating Input Area */}
      <div className="flex-shrink-0 p-4 pb-3">
        <div className="max-w-4xl mx-auto">
          <div className="relative bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200/50 p-1">
          <textarea
              ref={inputRef}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
              placeholder="Ask Growbe"
            disabled={isLoading}
              rows={2}
              className="w-full p-4 rounded-xl border-0 focus:outline-none resize-none overflow-hidden bg-transparent text-gray-800 placeholder-gray-500 text-base"
              style={{ minHeight: '60px', maxHeight: '120px' }}
          />
          </div>

          {/* Disclaimer */}
          <div className="text-center mt-2">
            <p className="text-xs text-gray-500">
              Growbe can make mistakes, so double check it!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}


