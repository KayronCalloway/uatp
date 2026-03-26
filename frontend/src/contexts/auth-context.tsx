'use client';

import { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { apiClient, api } from '@/lib/api-client';

// SECURITY: Only log in development mode
const isDevelopment = process.env.NODE_ENV === 'development';
const debugLog = (...args: unknown[]) => {
  if (isDevelopment) {
    console.log(...args);
  }
};
const debugWarn = (...args: unknown[]) => {
  if (isDevelopment) {
    console.warn(...args);
  }
};
const debugError = (...args: unknown[]) => {
  if (isDevelopment) {
    console.error(...args);
  }
};

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

/**
 * SECURITY NOTES:
 * - JWT tokens stored in sessionStorage (cleared on tab close)
 * - API keys stored in sessionStorage, NOT localStorage (reduces XSS risk window)
 * - All sensitive data cleared on logout
 * - For maximum security, consider HTTP-only cookies instead
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [authToken, setAuthTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // SECURITY: Prevent race conditions with refs
  const isInitialized = useRef(false);
  const loginInProgress = useRef(false);

  useEffect(() => {
    // Prevent double-initialization (React StrictMode in dev)
    if (isInitialized.current) return;
    isInitialized.current = true;

    const initAuth = async () => {
      debugLog('Initializing auth...');

      try {
        // Check for stored JWT token (sessionStorage for security)
        const storedToken = sessionStorage.getItem('uatp-auth-token');
        if (storedToken) {
          debugLog('Found stored auth token - restoring session');
          api.setAuthToken(storedToken);
          setAuthTokenState(storedToken);
        }

        // Check for stored API key (sessionStorage for security)
        const storedApiKey = sessionStorage.getItem('uatp-api-key');
        if (storedApiKey) {
          debugLog('Found stored API key - restoring');
          apiClient.setApiKey(storedApiKey);
          setApiKey(storedApiKey);
        }

        // Quick health check with short timeout (non-blocking)
        setTimeout(async () => {
          try {
            await apiClient.healthCheck();
            debugLog('Background health check passed - backend accessible');
          } catch {
            debugWarn('Background health check failed - some features may be unavailable');
          }
        }, 100);

      } catch (error) {
        debugError('Auth initialization error:', error);
      }

      debugLog('Auth initialization complete');
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = useCallback(async (newApiKey: string): Promise<boolean> => {
    // Prevent concurrent login attempts
    if (loginInProgress.current) {
      debugWarn('Login already in progress, ignoring duplicate request');
      return false;
    }

    loginInProgress.current = true;

    try {
      setIsLoading(true);

      // Test the API key by making a health check
      apiClient.setApiKey(newApiKey);
      await apiClient.healthCheck();

      // SECURITY: Store in sessionStorage (not localStorage) to limit XSS exposure
      sessionStorage.setItem('uatp-api-key', newApiKey);
      setApiKey(newApiKey);

      return true;
    } catch {
      // If failed, remove the API key
      apiClient.removeApiKey();
      sessionStorage.removeItem('uatp-api-key');
      setApiKey(null);

      return false;
    } finally {
      setIsLoading(false);
      loginInProgress.current = false;
    }
  }, []);

  const logout = () => {
    // SECURITY: Clear all stored credentials
    sessionStorage.removeItem('uatp-api-key');
    sessionStorage.removeItem('uatp-auth-token');
    setApiKey(null);
    setAuthTokenState(null);
    apiClient.removeApiKey();
    api.removeAuthToken();
  };

  // Login with JWT token (email/password)
  const loginWithToken = useCallback(async (email: string, password: string): Promise<boolean> => {
    // Prevent concurrent login attempts
    if (loginInProgress.current) {
      debugWarn('Login already in progress, ignoring duplicate request');
      return false;
    }

    loginInProgress.current = true;

    try {
      setIsLoading(true);

      // Call auth login endpoint
      // SECURITY: credentials: 'include' enables HTTP-only cookie auth
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_UATP_API_URL || 'http://localhost:8000'}/api/v1/auth/login`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include', // Enable cookie auth
          body: JSON.stringify({ email, password }),
        }
      );

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();

      // Set token in API client and state (backwards compatibility)
      // NOTE: HTTP-only cookies are now set automatically by backend
      // sessionStorage is kept for backwards compatibility but cookies are preferred
      api.setAuthToken(data.access_token);
      sessionStorage.setItem('uatp-auth-token', data.access_token);
      setAuthTokenState(data.access_token);

      return true;
    } catch (error) {
      debugError('Login with token failed:', error);
      return false;
    } finally {
      setIsLoading(false);
      loginInProgress.current = false;
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
