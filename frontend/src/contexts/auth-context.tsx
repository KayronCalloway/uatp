'use client';

import { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { apiClient, api, getApiBaseUrl } from '@/lib/api-client';
import { fetchCsrfToken, clearCsrfToken } from '@/lib/csrf';

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
  register: (email: string, username: string, fullName: string, password: string) => Promise<{ success: boolean; error?: string }>;
  setAuthToken: (token: string) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * AUTH MODEL: Cookie-first authentication
 *
 * PRIMARY: JWT via HTTP-only cookies (browser sessions)
 * - Cookies set automatically by backend on login
 * - XSS-resistant: JavaScript cannot access HTTP-only cookies
 * - Sent automatically with credentials: 'include'
 *
 * SECONDARY: API Key auth (development/programmatic only)
 * - For local development and API testing
 * - Stored in sessionStorage (dev mode only)
 * - NOT recommended for production browser use
 *
 * SECURITY:
 * - No tokens stored in sessionStorage in production
 * - Backend validates cookies automatically via withCredentials
 * - isAuthenticated reflects cookie-based session validity
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [apiKey, setApiKey] = useState<string | null>(null);
  // SECURITY: authToken state is for UI feedback only, not for actual auth
  // Real auth happens via HTTP-only cookies
  const [authToken, setAuthTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasCookieSession, setHasCookieSession] = useState(false);

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
        // MIGRATION: Clear legacy sessionStorage tokens (they're now in cookies)
        // This is a one-time cleanup for existing sessions
        const legacyToken = sessionStorage.getItem('uatp-auth-token');
        if (legacyToken) {
          debugLog('Clearing legacy sessionStorage token (now using cookies)');
          sessionStorage.removeItem('uatp-auth-token');
        }

        // DEV ONLY: Check for stored API key
        // In production, API keys should not be stored in browser
        if (isDevelopment) {
          const storedApiKey = sessionStorage.getItem('uatp-api-key');
          if (storedApiKey) {
            debugLog('Found stored API key (dev mode) - restoring');
            apiClient.setApiKey(storedApiKey);
            setApiKey(storedApiKey);
          }
        }

        // Check for existing cookie session (backend validates HTTP-only cookie)
        let hasSession = false;
        try {
          const response = await fetch(
            `${getApiBaseUrl()}/api/v1/auth/me`,
            {
              method: 'GET',
              credentials: 'include', // Send cookies
            }
          );
          if (response.ok) {
            debugLog('Valid cookie session detected');
            setHasCookieSession(true);
            setAuthTokenState('cookie-session');
            await fetchCsrfToken();
            hasSession = true;
          }
        } catch {
          debugLog('No active cookie session');
        }

        // DEV AUTO-LOGIN: If no session, auto-login with dev credentials
        if (!hasSession && isDevelopment) {
          debugLog('Auto-login: attempting dev credentials...');
          try {
            const loginResponse = await fetch(
              `${getApiBaseUrl()}/api/v1/auth/login`,
              {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                  email: 'kayron@houseofcalloway.com',
                  password: 'uatp2026',
                }),
              }
            );
            if (loginResponse.ok) {
              debugLog('Auto-login successful');
              setHasCookieSession(true);
              setAuthTokenState('cookie-session');
              await fetchCsrfToken();
            } else {
              debugLog('Auto-login failed, showing login form');
            }
          } catch {
            debugLog('Auto-login request failed');
          }
        }

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

    // SECURITY: API key auth in browser is dev-only
    if (!isDevelopment) {
      debugWarn('API key auth is only available in development mode. Use loginWithToken for production.');
      return false;
    }

    loginInProgress.current = true;

    try {
      setIsLoading(true);

      // Test the API key by making a health check
      apiClient.setApiKey(newApiKey);
      await apiClient.healthCheck();

      // DEV ONLY: Store in sessionStorage for convenience
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

  const logout = useCallback(async () => {
    // SECURITY: Clear all stored credentials and server-side session

    // Call backend logout to clear HTTP-only cookies
    try {
      await fetch(
        `${getApiBaseUrl()}/api/v1/auth/logout`,
        {
          method: 'POST',
          credentials: 'include', // Send cookies to be cleared
        }
      );
    } catch {
      debugWarn('Backend logout failed - clearing local state anyway');
    }

    // Clear local state
    if (isDevelopment) {
      sessionStorage.removeItem('uatp-api-key');
    }
    sessionStorage.removeItem('uatp-auth-token'); // Clean up any legacy storage
    setApiKey(null);
    setAuthTokenState(null);
    setHasCookieSession(false);
    apiClient.removeApiKey();
    api.removeAuthToken();

    // CSRF: Clear CSRF token on logout
    clearCsrfToken();
  }, []);

  // Login with JWT token (email/password) - PREFERRED for browser auth
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
      // The backend sets the cookie, we don't store anything in sessionStorage
      const response = await fetch(
        `${getApiBaseUrl()}/api/v1/auth/login`,
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

      // SECURITY: We don't store the token in sessionStorage
      // The HTTP-only cookie is set automatically by the backend
      // We just track that we have an active session for UI purposes
      setHasCookieSession(true);
      setAuthTokenState('cookie-session');

      // CSRF: Fetch CSRF token for subsequent mutation requests
      // Backend also sets csrf_token cookie, but we fetch to ensure it's fresh
      await fetchCsrfToken();

      return true;
    } catch (error) {
      debugError('Login with token failed:', error);
      return false;
    } finally {
      setIsLoading(false);
      loginInProgress.current = false;
    }
  }, []);

  // Register new user
  const register = useCallback(async (
    email: string,
    username: string,
    fullName: string,
    password: string
  ): Promise<{ success: boolean; error?: string }> => {
    if (loginInProgress.current) {
      return { success: false, error: 'Registration already in progress' };
    }

    loginInProgress.current = true;

    try {
      setIsLoading(true);

      const response = await fetch(
        `${getApiBaseUrl()}/api/v1/auth/register`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            email,
            username,
            full_name: fullName,
            password,
          }),
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        return { success: false, error: data.detail || 'Registration failed' };
      }

      // Registration successful - user is now logged in via cookies
      setHasCookieSession(true);
      setAuthTokenState('cookie-session');

      // CSRF: Fetch CSRF token for subsequent mutation requests
      await fetchCsrfToken();

      return { success: true };
    } catch (error) {
      debugError('Registration failed:', error);
      return { success: false, error: 'Registration failed. Please try again.' };
    } finally {
      setIsLoading(false);
      loginInProgress.current = false;
    }
  }, []);

  // Set auth token directly (for SSO, external auth, etc.)
  // SECURITY: This should only be used for tokens received via secure channels
  // Prefer cookie-based auth when possible
  const setAuthToken = useCallback((token: string) => {
    if (!isDevelopment) {
      debugWarn('Direct token setting is discouraged in production. Use loginWithToken instead.');
    }
    api.setAuthToken(token);
    setAuthTokenState(token);
    // Don't store in sessionStorage - rely on the token being set in the API client
  }, []);

  const value: AuthContextType = {
    apiKey,
    authToken,
    // SECURITY: In production, primarily rely on cookie session
    // In development, also allow API key auth
    isAuthenticated: hasCookieSession || (isDevelopment && !!apiKey) || !!authToken,
    login,
    loginWithToken,
    register,
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
