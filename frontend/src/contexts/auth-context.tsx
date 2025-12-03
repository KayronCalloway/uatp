'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';

interface AuthContextType {
  apiKey: string | null;
  isAuthenticated: boolean;
  login: (apiKey: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      console.log('Initializing auth...');
      
      try {
        // Since the backend doesn't require authentication, just set a default state
        console.log('No authentication required - proceeding to app');
        setApiKey('no-auth-required');
        localStorage.setItem('uatp-api-key', 'no-auth-required');
        
        // Quick health check with short timeout (non-blocking)
        setTimeout(async () => {
          try {
            await apiClient.healthCheck();
            console.log('Background health check passed - backend accessible');
          } catch (error) {
            console.warn('Background health check failed - using mock data mode');
          }
        }, 100);
        
      } catch (error) {
        console.error('Auth initialization error:', error);
        setApiKey('no-auth-required');
        localStorage.setItem('uatp-api-key', 'no-auth-required');
      }
      
      console.log('Auth initialization complete');
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (newApiKey: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      
      // Test the API key by making a health check
      apiClient.setApiKey(newApiKey);
      await apiClient.healthCheck();
      
      // If successful, store the API key
      localStorage.setItem('uatp-api-key', newApiKey);
      setApiKey(newApiKey);
      
      return true;
    } catch (error) {
      // If failed, remove the API key
      apiClient.removeApiKey();
      localStorage.removeItem('uatp-api-key');
      setApiKey(null);
      
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('uatp-api-key');
    setApiKey(null);
    apiClient.removeApiKey();
  };

  const value: AuthContextType = {
    apiKey,
    isAuthenticated: !!apiKey,
    login,
    logout,
    isLoading,
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