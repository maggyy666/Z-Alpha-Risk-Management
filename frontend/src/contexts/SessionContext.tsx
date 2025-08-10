import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiService from '../services/api';

interface SessionData {
  username: string;
  email: string;
  logged_in: boolean;
}

interface SessionContextType {
  session: SessionData | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  setCurrentUser: (username: string) => void;
  setDefaultSession: () => void;
  getCurrentUsername: () => string;
  refreshPortfolioData: () => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const useSession = () => {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

interface SessionProviderProps {
  children: ReactNode;
}

export const SessionProvider: React.FC<SessionProviderProps> = ({ children }) => {
  const [session, setSession] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize session from localStorage or URL parameters
  useEffect(() => {
    // First check URL parameters for session data
    const urlParams = new URLSearchParams(window.location.search);
    const sessionParam = urlParams.get('session');
    
    if (sessionParam) {
      try {
        const sessionData = JSON.parse(decodeURIComponent(sessionParam));
        console.log('SessionContext - session from URL:', sessionData);
        setSession(sessionData);
        // Save to localStorage for future use
        localStorage.setItem('zalpha_session', JSON.stringify(sessionData));
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
        setLoading(false);
        return;
      } catch (error) {
        console.error('Error parsing session from URL:', error);
      }
    }

    // Fallback to localStorage
    const savedSession = localStorage.getItem('zalpha_session');
    console.log('SessionContext - savedSession from localStorage:', savedSession);
    
    if (savedSession) {
      try {
        const sessionData = JSON.parse(savedSession);
        console.log('SessionContext - parsed sessionData:', sessionData);
        setSession(sessionData);
      } catch (error) {
        console.error('Error parsing saved session:', error);
        // No fallback - user needs to login
        setSession(null);
      }
    } else {
      console.log('SessionContext - no saved session found');
      // No session - user needs to login
      setSession(null);
    }
    setLoading(false);
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await apiService.login({ username, password });
      if (response.success) {
        const sessionData = {
          username: response.username || username,
          email: username.includes('@') ? username : `${username}@zalpha.com`,
          logged_in: true
        };
        setSession(sessionData);
        localStorage.setItem('zalpha_session', JSON.stringify(sessionData));
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = () => {
    setSession(null);
    localStorage.removeItem('zalpha_session');
    window.location.href = 'http://localhost:3001';
  };

  const setCurrentUser = (username: string) => {
    const sessionData = {
      username,
      email: username === 'admin' ? 'admin@zalpha.com' : 'user@external-zalpha.com',
      logged_in: true
    };
    setSession(sessionData);
    localStorage.setItem('zalpha_session', JSON.stringify(sessionData));
  };

  // For development/testing - set default session
  const setDefaultSession = () => {
    const sessionData = {
      username: 'admin',
      email: 'admin@zalpha.com',
      logged_in: true
    };
    setSession(sessionData);
    localStorage.setItem('zalpha_session', JSON.stringify(sessionData));
  };

  const getCurrentUsername = () => {
    return session?.username || 'admin';
  };

  const refreshPortfolioData = () => {
    // Force a page reload to refresh all portfolio data
    // This is a fallback - individual components should handle their own refresh
    window.location.reload();
  };

  const value = {
    session,
    loading,
    login,
    logout,
    setCurrentUser,
    setDefaultSession,
    getCurrentUsername,
    refreshPortfolioData
  };

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  );
};
