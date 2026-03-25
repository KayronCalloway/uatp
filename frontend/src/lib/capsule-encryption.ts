/**
 * Capsule Encryption Utilities
 * ============================
 *
 * Client-side encryption for capsule payloads using AES-256-GCM.
 * Enables privacy-first model where:
 * - Users encrypt payloads before sending to server
 * - Only the user who created a capsule can decrypt its contents
 * - Server and admins see only encrypted blobs
 *
 * Security:
 * - Uses Web Crypto API (browser-native, FIPS-compliant)
 * - AES-256-GCM provides authenticated encryption
 * - 96-bit random IV per encryption (never reused)
 * - Key should be stored in memory only (not localStorage)
 */

/**
 * Encryption metadata stored with encrypted payload
 */
export interface EncryptionMetadata {
  iv: string; // Base64-encoded IV
  algorithm: string; // Always "AES-256-GCM"
  key_id?: string; // Optional key identifier
}

/**
 * Result of encrypting a payload
 */
export interface EncryptedPayload {
  ciphertext: string; // Base64-encoded ciphertext with auth tag
  metadata: EncryptionMetadata;
}

/**
 * Import a raw key from Base64 for use with Web Crypto API
 *
 * @param keyBase64 - Base64-encoded AES-256 key (from /user-keys/my-encryption-key)
 * @returns CryptoKey for use with encrypt/decrypt
 */
export async function importKey(keyBase64: string): Promise<CryptoKey> {
  const keyBytes = Uint8Array.from(atob(keyBase64), (c) => c.charCodeAt(0));

  if (keyBytes.length !== 32) {
    throw new Error(`Invalid key length: expected 32 bytes, got ${keyBytes.length}`);
  }

  return await crypto.subtle.importKey(
    'raw',
    keyBytes,
    { name: 'AES-GCM', length: 256 },
    false, // not extractable
    ['encrypt', 'decrypt']
  );
}

/**
 * Encrypt a capsule payload using AES-256-GCM
 *
 * @param payload - The payload object to encrypt
 * @param key - CryptoKey from importKey()
 * @param keyId - Optional key identifier for tracking
 * @returns Encrypted payload with metadata
 */
export async function encryptPayload(
  payload: object,
  key: CryptoKey,
  keyId?: string
): Promise<EncryptedPayload> {
  // Generate random 96-bit IV (12 bytes, optimal for GCM)
  const iv = crypto.getRandomValues(new Uint8Array(12));

  // Serialize payload to JSON
  const plaintext = new TextEncoder().encode(JSON.stringify(payload));

  // Encrypt with AES-256-GCM
  const ciphertext = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    plaintext
  );

  // Convert to Base64 for transport
  const ciphertextBytes = new Uint8Array(ciphertext);
  const ciphertextBase64 = btoa(
    Array.from(ciphertextBytes).map(b => String.fromCharCode(b)).join('')
  );
  const ivBase64 = btoa(
    Array.from(iv).map(b => String.fromCharCode(b)).join('')
  );

  return {
    ciphertext: ciphertextBase64,
    metadata: {
      iv: ivBase64,
      algorithm: 'AES-256-GCM',
      key_id: keyId,
    },
  };
}

/**
 * Decrypt a capsule payload using AES-256-GCM
 *
 * @param ciphertext - Base64-encoded ciphertext
 * @param iv - Base64-encoded IV from encryption metadata
 * @param key - CryptoKey from importKey()
 * @returns Decrypted payload object
 */
export async function decryptPayload<T = object>(
  ciphertext: string,
  iv: string,
  key: CryptoKey
): Promise<T> {
  // Decode from Base64
  const ciphertextBytes = Uint8Array.from(atob(ciphertext), (c) =>
    c.charCodeAt(0)
  );
  const ivBytes = Uint8Array.from(atob(iv), (c) => c.charCodeAt(0));

  // Decrypt with AES-256-GCM
  const plaintext = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: ivBytes },
    key,
    ciphertextBytes
  );

  // Parse JSON payload
  const decoded = new TextDecoder().decode(plaintext);
  try {
    return JSON.parse(decoded) as T;
  } catch {
    throw new Error('Failed to parse decrypted payload as JSON');
  }
}

/**
 * Convenience wrapper for encrypting and decrypting with metadata
 */
export async function decryptWithMetadata<T = object>(
  encryptedPayload: string,
  metadata: EncryptionMetadata,
  key: CryptoKey
): Promise<T> {
  return decryptPayload<T>(encryptedPayload, metadata.iv, key);
}

/**
 * Check if a capsule has encrypted payload
 */
export function isEncrypted(capsule: {
  encrypted_payload?: string;
  encryption_metadata?: EncryptionMetadata;
}): boolean {
  return !!(capsule.encrypted_payload && capsule.encryption_metadata);
}

/**
 * Key cache manager for storing keys in memory only
 * Keys are never persisted to localStorage or sessionStorage
 */
class KeyCache {
  private keys: Map<string, CryptoKey> = new Map();

  async getOrImport(keyId: string, keyBase64: string): Promise<CryptoKey> {
    if (this.keys.has(keyId)) {
      return this.keys.get(keyId)!;
    }

    const key = await importKey(keyBase64);
    this.keys.set(keyId, key);
    return key;
  }

  clear(): void {
    this.keys.clear();
  }

  has(keyId: string): boolean {
    return this.keys.has(keyId);
  }
}

// Global key cache instance
export const keyCache = new KeyCache();

/**
 * Example usage:
 *
 * // 1. Get encryption key from backend
 * const response = await api.get('/user-keys/my-encryption-key');
 * const { key, key_id } = response.data;
 *
 * // 2. Import key for use
 * const cryptoKey = await importKey(key);
 *
 * // 3. Encrypt payload before creating capsule
 * const payload = { reasoning_steps: [...], conclusion: '...' };
 * const encrypted = await encryptPayload(payload, cryptoKey, key_id);
 *
 * // 4. Create capsule with encrypted payload
 * await api.post('/capsules', {
 *   type: 'reasoning_trace',
 *   encrypted_payload: encrypted.ciphertext,
 *   encryption_metadata: encrypted.metadata,
 *   payload: {}, // Empty or minimal metadata only
 * });
 *
 * // 5. Decrypt payload when viewing capsule
 * const capsule = await api.get('/capsules/abc123');
 * if (isEncrypted(capsule)) {
 *   const decrypted = await decryptWithMetadata(
 *     capsule.encrypted_payload,
 *     capsule.encryption_metadata,
 *     cryptoKey
 *   );
 * }
 */
