'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

interface StreamingContextType {
  isStreaming: boolean;
  setIsStreaming: (streaming: boolean) => void;
}

const StreamingContext = createContext<StreamingContextType | undefined>(undefined);

export function StreamingProvider({ children }: { children: ReactNode }) {
  const [isStreaming, setIsStreaming] = useState(true);

  return (
    <StreamingContext.Provider value={{ isStreaming, setIsStreaming }}>
      {children}
    </StreamingContext.Provider>
  );
}

export function useStreamingContext() {
  const context = useContext(StreamingContext);
  return context; // Return undefined if not in provider
}
