'use client';

import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { apiClient, api } from '@/lib/api-client';

interface AuthContextType {
  apiKey: string | null;
  authToken: string | null;
  isAuthenticated: boolean;
  login: (apiKey: string) => Promise<boolean>;
  loginWithToken: (email: string, password: string) => Promise<boolean>;
  setAuthToken: (token: string) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [authToken, setAuthTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      console.log('Initializing auth...');

      try {
        // Check for stored JWT token (sessionStorage for security)
        const storedToken = sessionStorage.getItem('uatp-auth-token');
        if (storedToken) {
          console.log('Found stored auth token - restoring session');
          api.setAuthToken(storedToken);
          setAuthTokenState(storedToken);
        }

        // Since the backend doesn't require authentication for some endpoints, set a default state
        console.log('Setting default API key');
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
    sessionStorage.removeItem('uatp-auth-token');
    setApiKey(null);
    setAuthTokenState(null);
    apiClient.removeApiKey();
    api.removeAuthToken();
  };

  // Login with JWT token (email/password)
  const loginWithToken = useCallback(async (email: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);

      // Call auth login endpoint
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_UATP_API_URL || 'http://localhost:8000'}/auth/login`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        }
      );

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();

      // Set token in API client and state
      api.setAuthToken(data.access_token);
      sessionStorage.setItem('uatp-auth-token', data.access_token);
      setAuthTokenState(data.access_token);

      return true;
    } catch (error) {
      console.error('Login with token failed:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Set auth token directly (for SSO, external auth, etc.)
  const setAuthToken = useCallback((token: string) => {
    api.setAuthToken(token);
    sessionStorage.setItem('uatp-auth-token', token);
    setAuthTokenState(token);
  }, []);

  const value: AuthContextType = {
    apiKey,
    authToken,
    isAuthenticated: !!apiKey || !!authToken,
    login,
    loginWithToken,
    setAuthToken,
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
