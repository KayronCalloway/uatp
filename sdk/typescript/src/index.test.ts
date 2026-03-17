import { describe, it, expect } from 'vitest';
import {
  UATP,
  deriveKeyPair,
  hashContent,
  sign,
  verify,
  createSignedCapsule,
  verifyCapsule,
} from './index';

describe('UATP SDK', () => {
  describe('Key Derivation', () => {
    it('should derive deterministic key pairs from passphrase', () => {
      const keyPair1 = deriveKeyPair('test-passphrase');
      const keyPair2 = deriveKeyPair('test-passphrase');

      expect(keyPair1.publicKey).toEqual(keyPair2.publicKey);
      expect(keyPair1.privateKey).toEqual(keyPair2.privateKey);
    });

    it('should derive different keys from different passphrases', () => {
      const keyPair1 = deriveKeyPair('passphrase-1');
      const keyPair2 = deriveKeyPair('passphrase-2');

      expect(keyPair1.publicKey).not.toEqual(keyPair2.publicKey);
    });
  });

  describe('Signing and Verification', () => {
    const testContent = {
      task: 'Test task',
      decision: 'Test decision',
      reasoning_chain: [
        { step: 1, thought: 'Test thought', confidence: 0.9 },
      ],
      confidence: 0.9,
      metadata: { timestamp: '2024-01-01T00:00:00Z' },
    };

    it('should sign and verify content', () => {
      const keyPair = deriveKeyPair('test-passphrase');
      const signature = sign(testContent, keyPair.privateKey);

      const isValid = verify(
        testContent,
        signature,
        Buffer.from(keyPair.publicKey).toString('hex')
      );

      expect(isValid).toBe(true);
    });

    it('should fail verification with wrong public key', () => {
      const keyPair1 = deriveKeyPair('passphrase-1');
      const keyPair2 = deriveKeyPair('passphrase-2');

      const signature = sign(testContent, keyPair1.privateKey);

      const isValid = verify(
        testContent,
        signature,
        Buffer.from(keyPair2.publicKey).toString('hex')
      );

      expect(isValid).toBe(false);
    });
  });

  describe('Capsule Creation', () => {
    it('should create a signed capsule', () => {
      const keyPair = deriveKeyPair('test-passphrase');
      const content = {
        task: 'Test task',
        decision: 'Test decision',
        reasoning_chain: [
          { step: 1, thought: 'Test thought', confidence: 0.9 },
        ],
        confidence: 0.9,
        metadata: {},
      };

      const capsule = createSignedCapsule(content, keyPair);

      expect(capsule.capsuleId).toMatch(/^cap_/);
      expect(capsule.signature).toBeTruthy();
      expect(capsule.publicKey).toBeTruthy();
      expect(capsule.contentHash).toBeTruthy();
    });

    it('should verify a created capsule', () => {
      const keyPair = deriveKeyPair('test-passphrase');
      const content = {
        task: 'Test task',
        decision: 'Test decision',
        reasoning_chain: [
          { step: 1, thought: 'Test thought', confidence: 0.9 },
        ],
        confidence: 0.9,
        metadata: {},
      };

      const capsule = createSignedCapsule(content, keyPair);
      const result = verifyCapsule(capsule);

      expect(result.valid).toBe(true);
      expect(result.signatureValid).toBe(true);
      expect(result.hashValid).toBe(true);
    });
  });

  describe('UATP Client', () => {
    it('should create a client instance', () => {
      const client = new UATP({ baseUrl: 'http://localhost:8000' });
      expect(client).toBeInstanceOf(UATP);
    });
  });
});
