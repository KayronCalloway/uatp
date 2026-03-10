/**
 * React Hook for Capsule Encryption
 * ==================================
 *
 * Provides encryption/decryption capabilities for capsule payloads.
 * Manages the user's encryption key in memory only (never persisted).
 *
 * Usage:
 *   const { encryptPayload, decryptPayload, isReady, error } = useCapsuleEncryption();
 *
 *   // Encrypt before creating capsule
 *   const encrypted = await encryptPayload(myPayload);
 *   api.createEncryptedCapsule({ ...capsuleData, ...encrypted });
 *
 *   // Decrypt when viewing capsule
 *   const decrypted = await decryptPayload(capsule.encrypted_payload, capsule.encryption_metadata);
 */

import { useState, useEffect, useCallback } from 'react';
import {
  importKey,
  encryptPayload as encrypt,
  decryptPayload as decrypt,
  EncryptionMetadata,
  EncryptedPayload,
  isEncrypted,
} from '@/lib/capsule-encryption';
import { api } from '@/lib/api-client';

interface UseCapsuleEncryptionResult {
  /** Whether the encryption key is loaded and ready */
  isReady: boolean;
  /** Error if key loading failed */
  error: Error | null;
  /** Encrypt a payload for storage */
  encryptPayload: (payload: object) => Promise<EncryptedPayload>;
  /** Decrypt an encrypted payload */
  decryptPayload: <T = object>(ciphertext: string, metadata: EncryptionMetadata) => Promise<T>;
  /** Check if a capsule has encrypted payload */
  isEncrypted: typeof isEncrypted;
  /** Reload the encryption key */
  reloadKey: () => Promise<void>;
}

export function useCapsuleEncryption(): UseCapsuleEncryptionResult {
  const [cryptoKey, setCryptoKey] = useState<CryptoKey | null>(null);
  const [keyId, setKeyId] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadKey = useCallback(async () => {
    try {
      setError(null);

      // Check if we have an auth token
      if (!api.hasAuthToken()) {
        // No auth token - user not logged in
        setIsReady(false);
        return;
      }

      // Fetch encryption key from backend
      const response = await api.getMyEncryptionKey();
      const key = await importKey(response.key);

      setCryptoKey(key);
      setKeyId(response.key_id);
      setIsReady(true);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load encryption key'));
      setIsReady(false);
    }
  }, []);

  // Load key on mount and when auth changes
  useEffect(() => {
    loadKey();
  }, [loadKey]);

  const encryptPayload = useCallback(
    async (payload: object): Promise<EncryptedPayload> => {
      if (!cryptoKey) {
        throw new Error('Encryption key not loaded');
      }
      return encrypt(payload, cryptoKey, keyId || undefined);
    },
    [cryptoKey, keyId]
  );

  const decryptPayload = useCallback(
    async <T = object>(ciphertext: string, metadata: EncryptionMetadata): Promise<T> => {
      if (!cryptoKey) {
        throw new Error('Encryption key not loaded');
      }
      return decrypt<T>(ciphertext, metadata.iv, cryptoKey);
    },
    [cryptoKey]
  );

  return {
    isReady,
    error,
    encryptPayload,
    decryptPayload,
    isEncrypted,
    reloadKey: loadKey,
  };
}

export default useCapsuleEncryption;
