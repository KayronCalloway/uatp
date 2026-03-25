'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

/**
 * SECURITY: Creator/Admin privileges context
 *
 * IMPORTANT: All privileges MUST come from the backend JWT token.
 * The frontend NEVER determines authorization - it only reflects
 * what the backend has authorized via the JWT claims.
 *
 * Flow:
 * 1. User logs in via auth-context
 * 2. Backend returns JWT with 'scopes' or 'roles' claim
 * 3. This context reads privileges from the verified JWT
 * 4. UI conditionally renders based on these privileges
 *
 * NEVER:
 * - Store privileges in localStorage
 * - Hardcode creator keys or IDs
 * - Auto-enable privileges based on health checks
 * - Trust any client-side privilege escalation
 */

interface CreatorPrivileges {
  adminAccess: boolean;
  bulkOperations: boolean;
  systemDebug: boolean;
  rawDataAccess: boolean;
  advancedTools: boolean;
}

interface CreatorState {
  isCreator: boolean;
  creatorId: string | null;
  privileges: CreatorPrivileges;
}

interface CreatorContextValue {
  state: CreatorState;
  refreshPrivileges: () => Promise<void>;
}

const NO_PRIVILEGES: CreatorPrivileges = {
  adminAccess: false,
  bulkOperations: false,
  systemDebug: false,
  rawDataAccess: false,
  advancedTools: false,
};

const initialState: CreatorState = {
  isCreator: false,
  creatorId: null,
  privileges: NO_PRIVILEGES,
};

const CreatorContext = createContext<CreatorContextValue>({
  state: initialState,
  refreshPrivileges: async () => {},
});

/**
 * Map JWT scopes/roles to privilege flags
 * SECURITY: This mapping should match backend authorization logic
 */
function mapScopesToPrivileges(scopes: string[]): CreatorPrivileges {
  const scopeSet = new Set(scopes.map(s => s.toLowerCase()));

  return {
    // Only 'admin' scope grants admin access
    adminAccess: scopeSet.has('admin'),
    // Bulk operations require explicit scope
    bulkOperations: scopeSet.has('admin') || scopeSet.has('bulk'),
    // Debug access is admin-only
    systemDebug: scopeSet.has('admin') || scopeSet.has('debug'),
    // Raw data access requires explicit scope
    rawDataAccess: scopeSet.has('admin') || scopeSet.has('raw_data'),
    // Advanced tools require creator or admin scope
    advancedTools: scopeSet.has('admin') || scopeSet.has('creator') || scopeSet.has('advanced'),
  };
}

/**
 * Decode JWT payload (without verification - that's the backend's job)
 * SECURITY: We only decode to read claims, NOT to verify authenticity
 */
function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const payload = parts[1];
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

export function CreatorProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<CreatorState>(initialState);

  const refreshPrivileges = useCallback(async () => {
    // Get auth token from sessionStorage (set by auth-context)
    const token = sessionStorage.getItem('uatp-auth-token');

    if (!token) {
      // No token = no privileges
      setState(initialState);
      return;
    }

    // Decode JWT to read claims
    const payload = decodeJwtPayload(token);

    if (!payload) {
      setState(initialState);
      return;
    }

    // Check token expiration
    const exp = payload.exp as number | undefined;
    if (exp && Date.now() >= exp * 1000) {
      // Token expired - clear privileges
      setState(initialState);
      return;
    }

    // Extract user info and scopes from JWT claims
    const userId = (payload.sub || payload.user_id) as string | undefined;
    const scopes = (payload.scopes || payload.roles || []) as string[];

    // Map scopes to privileges
    const privileges = mapScopesToPrivileges(scopes);

    // Determine if user has any elevated privileges
    const isCreator = Object.values(privileges).some(v => v);

    setState({
      isCreator,
      creatorId: userId || null,
      privileges,
    });
  }, []);

  // Refresh privileges on mount and when storage changes
  useEffect(() => {
    refreshPrivileges();

    // Listen for storage changes (e.g., login/logout in another tab)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'uatp-auth-token') {
        refreshPrivileges();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [refreshPrivileges]);

  return (
    <CreatorContext.Provider value={{ state, refreshPrivileges }}>
      {children}
    </CreatorContext.Provider>
  );
}

export function useCreator() {
  const context = useContext(CreatorContext);
  if (!context) {
    throw new Error('useCreator must be used within a CreatorProvider');
  }
  return context;
}

export function useIsCreator() {
  const { state } = useCreator();
  return state.isCreator;
}

export function useCreatorPrivileges() {
  const { state } = useCreator();
  return state.privileges;
}
