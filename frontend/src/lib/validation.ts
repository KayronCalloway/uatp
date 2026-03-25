/**
 * Input Validation Utilities
 *
 * SECURITY: These functions validate user input before use in navigation,
 * API calls, or other sensitive operations to prevent injection attacks.
 */

/**
 * Validates a capsule ID to ensure it only contains safe characters.
 * Prevents open redirect and path traversal attacks.
 *
 * Valid capsule IDs contain only:
 * - Alphanumeric characters (a-z, A-Z, 0-9)
 * - Hyphens (-) and underscores (_)
 * - Colons (:) for namespaced IDs
 *
 * @param id - The capsule ID to validate
 * @returns true if the ID is valid, false otherwise
 */
export function isValidCapsuleId(id: string | undefined | null): boolean {
  if (!id || typeof id !== 'string') {
    return false;
  }

  // Max length check to prevent DoS
  if (id.length > 256) {
    return false;
  }

  // Only allow safe characters: alphanumeric, hyphens, underscores, colons
  // No slashes, dots (path traversal), or special URL characters
  const safePattern = /^[a-zA-Z0-9_:-]+$/;
  return safePattern.test(id);
}

/**
 * Sanitizes a string for safe display in error messages.
 * Truncates and removes potentially dangerous characters.
 *
 * @param input - The string to sanitize
 * @param maxLength - Maximum length of output (default: 50)
 * @returns Sanitized string safe for display
 */
export function sanitizeForDisplay(
  input: string | undefined | null,
  maxLength: number = 50
): string {
  if (!input || typeof input !== 'string') {
    return '[invalid]';
  }

  // Remove any HTML/script tags and control characters
  const cleaned = input
    .replace(/<[^>]*>/g, '')
    .replace(/[\x00-\x1f\x7f]/g, '');

  if (cleaned.length > maxLength) {
    return cleaned.slice(0, maxLength) + '...';
  }

  return cleaned;
}

/**
 * Validates a URL to ensure it's a safe internal path.
 * Prevents open redirect attacks.
 *
 * @param url - The URL or path to validate
 * @returns true if the URL is a safe internal path
 */
export function isValidInternalPath(url: string | undefined | null): boolean {
  if (!url || typeof url !== 'string') {
    return false;
  }

  // Must start with / (relative path)
  if (!url.startsWith('/')) {
    return false;
  }

  // Cannot contain protocol indicators (prevents javascript:, data:, etc.)
  if (url.includes(':')) {
    return false;
  }

  // Cannot have double slashes (prevents //evil.com)
  if (url.includes('//')) {
    return false;
  }

  // Cannot have path traversal
  if (url.includes('..')) {
    return false;
  }

  return true;
}
