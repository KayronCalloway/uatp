/**
 * UATP TypeScript SDK - Cryptographic Operations
 *
 * Zero-Trust Architecture:
 * - Private keys NEVER leave your device
 * - All signing happens locally using Ed25519
 * - Keys are derived from passphrase using PBKDF2 (480,000 iterations)
 */

import * as ed from '@noble/ed25519';
import { sha256 } from '@noble/hashes/sha256';
import { pbkdf2 } from '@noble/hashes/pbkdf2';
import { bytesToHex, hexToBytes } from '@noble/hashes/utils';
import type { KeyPair, CapsuleContent, SignedCapsule } from './types';

// Use synchronous SHA-512 for ed25519
ed.etc.sha512Sync = (...m) => {
  const { sha512 } = require('@noble/hashes/sha512');
  return sha512(ed.etc.concatBytes(...m));
};

const PBKDF2_ITERATIONS = 480_000;
const SALT_PREFIX = 'uatp-v1-key-derivation';

/**
 * Derive an Ed25519 key pair from a passphrase.
 * Uses PBKDF2-HMAC-SHA256 with 480,000 iterations.
 */
export function deriveKeyPair(passphrase: string): KeyPair {
  const salt = new TextEncoder().encode(SALT_PREFIX);
  const passphraseBytes = new TextEncoder().encode(passphrase);

  // Derive 32 bytes for Ed25519 seed
  const seed = pbkdf2(sha256, passphraseBytes, salt, {
    c: PBKDF2_ITERATIONS,
    dkLen: 32,
  });

  // Generate key pair from seed
  const privateKey = seed;
  const publicKey = ed.getPublicKey(privateKey);

  return { privateKey, publicKey };
}

/**
 * Generate a device-bound passphrase.
 *
 * SECURITY BOUNDARY: This is a CONVENIENCE feature, not a security feature.
 * For production, use an explicit passphrase.
 */
export function deriveDevicePassphrase(): string {
  // In browser, use available entropy sources
  const factors: string[] = [];

  if (typeof window !== 'undefined') {
    factors.push(window.navigator.userAgent);
    factors.push(window.navigator.language);
    factors.push(String(window.screen.width));
    factors.push(String(window.screen.height));
    factors.push(window.location.hostname);
  } else if (typeof process !== 'undefined') {
    // Node.js environment
    factors.push(process.platform);
    factors.push(process.arch);
    factors.push(process.env.USER || process.env.USERNAME || '');
    factors.push(require('os').hostname());
  }

  const combined = factors.join(':');
  const hash = sha256(new TextEncoder().encode(combined));
  return `device_${bytesToHex(hash).slice(0, 32)}`;
}

/**
 * Canonicalize content for signing.
 * Ensures deterministic JSON serialization.
 */
export function canonicalize(obj: unknown): string {
  return JSON.stringify(obj, Object.keys(obj as object).sort());
}

/**
 * Hash content using SHA-256.
 */
export function hashContent(content: CapsuleContent): string {
  const canonical = canonicalize(content);
  const hash = sha256(new TextEncoder().encode(canonical));
  return bytesToHex(hash);
}

/**
 * Sign content with Ed25519.
 */
export function sign(content: CapsuleContent, privateKey: Uint8Array): string {
  const canonical = canonicalize(content);
  const messageBytes = new TextEncoder().encode(canonical);
  const signature = ed.sign(messageBytes, privateKey);
  return bytesToHex(signature);
}

/**
 * Verify an Ed25519 signature.
 */
export function verify(
  content: CapsuleContent,
  signature: string,
  publicKey: string
): boolean {
  try {
    const canonical = canonicalize(content);
    const messageBytes = new TextEncoder().encode(canonical);
    const signatureBytes = hexToBytes(signature);
    const publicKeyBytes = hexToBytes(publicKey);
    return ed.verify(signatureBytes, messageBytes, publicKeyBytes);
  } catch {
    return false;
  }
}

/**
 * Generate a unique capsule ID.
 */
export function generateCapsuleId(): string {
  const timestamp = Date.now().toString(36);
  const randomBytes = new Uint8Array(8);

  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    crypto.getRandomValues(randomBytes);
  } else {
    // Node.js fallback
    const { randomBytes: nodeRandom } = require('crypto');
    const buf = nodeRandom(8);
    randomBytes.set(buf);
  }

  const random = bytesToHex(randomBytes).slice(0, 8);
  return `cap_${timestamp}_${random}`;
}

/**
 * Create a signed capsule.
 */
export function createSignedCapsule(
  content: CapsuleContent,
  keyPair: KeyPair
): SignedCapsule {
  const capsuleId = generateCapsuleId();
  const contentHash = hashContent(content);
  const signature = sign(content, keyPair.privateKey);
  const publicKey = bytesToHex(keyPair.publicKey);
  const timestamp = new Date().toISOString();

  return {
    capsuleId,
    signature,
    publicKey,
    contentHash,
    timestamp,
    content,
  };
}

/**
 * Verify a signed capsule locally.
 * No server required - pure cryptographic verification.
 */
export function verifyCapsule(capsule: SignedCapsule): {
  valid: boolean;
  signatureValid: boolean;
  hashValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  // Verify hash
  const computedHash = hashContent(capsule.content);
  const hashValid = computedHash === capsule.contentHash;
  if (!hashValid) {
    errors.push('Content hash mismatch - capsule may have been tampered with');
  }

  // Verify signature
  const signatureValid = verify(
    capsule.content,
    capsule.signature,
    capsule.publicKey
  );
  if (!signatureValid) {
    errors.push('Signature verification failed');
  }

  return {
    valid: hashValid && signatureValid,
    signatureValid,
    hashValid,
    errors,
  };
}

export { bytesToHex, hexToBytes };
