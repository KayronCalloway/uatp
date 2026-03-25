'use client';

/**
 * DEPRECATED: This file exists for backwards compatibility only.
 *
 * It re-exports from the proper auth-context.tsx which has real authentication.
 * All new code should import directly from '@/contexts/auth-context'.
 *
 * SECURITY: The previous implementation was an authentication bypass that
 * always returned isAuthenticated: true. This has been fixed.
 *
 * TODO: Migrate all imports from auth-context-simple to auth-context
 * and delete this file.
 */

// Re-export everything from the real auth context
export { AuthProvider, useAuth } from './auth-context';
