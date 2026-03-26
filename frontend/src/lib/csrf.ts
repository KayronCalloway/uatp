/**
 * CSRF Token Management
 *
 * Handles fetching, storing, and sending CSRF tokens for cookie-authenticated requests.
 *
 * SECURITY:
 * - CSRF tokens protect against cross-site request forgery attacks
 * - Tokens are bound to user session (user_id) on the backend
 * - Must be sent via X-CSRF-Token header on all mutation requests (POST, PUT, DELETE)
 * - Token is refreshed on login/register and can be manually refreshed
 */

import { getApiBaseUrl } from './api-client';

// CSRF token storage (in-memory for security - not persisted)
let csrfToken: string | null = null;
let tokenExpiresAt: number | null = null;

/**
 * Get the current CSRF token from memory or cookie
 */
export function getCsrfToken(): string | null {
  // First check in-memory token
  if (csrfToken && tokenExpiresAt && Date.now() < tokenExpiresAt) {
    return csrfToken;
  }

  // Fall back to reading from cookie (set by backend)
  if (typeof document !== 'undefined') {
    const match = document.cookie.match(/csrf_token=([^;]+)/);
    if (match) {
      return match[1];
    }
  }

  return null;
}

/**
 * Store CSRF token in memory
 */
export function setCsrfToken(token: string, expiresIn: number = 3600): void {
  csrfToken = token;
  tokenExpiresAt = Date.now() + (expiresIn * 1000);
}

/**
 * Clear CSRF token (call on logout)
 */
export function clearCsrfToken(): void {
  csrfToken = null;
  tokenExpiresAt = null;
}

/**
 * Fetch a fresh CSRF token from the backend
 * Call this after login/register or when token expires
 */
export async function fetchCsrfToken(): Promise<string | null> {
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/api/v1/auth/csrf-token`,
      {
        method: 'GET',
        credentials: 'include', // Send cookies for session binding
      }
    );

    if (!response.ok) {
      console.warn('Failed to fetch CSRF token:', response.status);
      return null;
    }

    const data = await response.json();
    if (data.csrf_token) {
      setCsrfToken(data.csrf_token, data.expires_in || 3600);
      return data.csrf_token;
    }

    return null;
  } catch (error) {
    console.warn('Error fetching CSRF token:', error);
    return null;
  }
}

/**
 * Get CSRF token, fetching if necessary
 */
export async function ensureCsrfToken(): Promise<string | null> {
  const existing = getCsrfToken();
  if (existing) {
    return existing;
  }
  return fetchCsrfToken();
}

/**
 * Check if a request method requires CSRF protection
 */
export function requiresCsrf(method: string): boolean {
  const safeMethods = ['GET', 'HEAD', 'OPTIONS'];
  return !safeMethods.includes(method.toUpperCase());
}

/**
 * Add CSRF token to headers if needed
 */
export function addCsrfHeader(
  headers: Record<string, string>,
  method: string
): Record<string, string> {
  if (!requiresCsrf(method)) {
    return headers;
  }

  const token = getCsrfToken();
  if (token) {
    return {
      ...headers,
      'X-CSRF-Token': token,
    };
  }

  return headers;
}
