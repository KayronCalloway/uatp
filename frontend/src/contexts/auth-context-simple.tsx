'use client';

import { createContext, useContext, useState } from 'react';

interface AuthContextType {
  apiKey: string | null;
  isAuthenticated: boolean;
  login: (apiKey: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [apiKey] = useState<string>('no-auth-required');
  const [isLoading] = useState(false); // Never loading

  const login = async (newApiKey: string): Promise<boolean> => {
    return true; // Always successful for now
  };

  const logout = () => {
    // No-op for now
  };

  const value: AuthContextType = {
    apiKey,
    isAuthenticated: true, // Always authenticated
    login,
    logout,
    isLoading: false, // Never loading
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