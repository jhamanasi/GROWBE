'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

export interface UserAuth {
  email: string;
  securityQuestions: {
    question1: {
      selectedQuestion: string;
      answer: string;
    };
    question2: {
      selectedQuestion: string;
      answer: string;
    };
  };
  createdAt: string;
  lastLogin: string;
}

interface AuthContextType {
  user: UserAuth | null;
  isLoading: boolean;
  login: (userData: Omit<UserAuth, 'createdAt' | 'lastLogin'>) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserAuth | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load user from localStorage on mount
  useEffect(() => {
    try {
      const storedUser = localStorage.getItem('userAuth');
      if (storedUser) {
        const userData = JSON.parse(storedUser);
        // Update lastLogin when loading from storage
        const updatedUserData = {
          ...userData,
          lastLogin: new Date().toISOString(),
        };
        setUser(updatedUserData);
        localStorage.setItem('userAuth', JSON.stringify(updatedUserData));
      }
    } catch (error) {
      console.error('Error loading user from localStorage:', error);
      localStorage.removeItem('userAuth');
    }
    setIsLoading(false);
  }, []);

  const login = useCallback((userData: Omit<UserAuth, 'createdAt' | 'lastLogin'>) => {
    const now = new Date().toISOString();
    const fullUserData: UserAuth = {
      ...userData,
      createdAt: now,
      lastLogin: now,
    };
    
    setUser(fullUserData);
    localStorage.setItem('userAuth', JSON.stringify(fullUserData));
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('userAuth');
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
