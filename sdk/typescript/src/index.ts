/**
 * UATP TypeScript SDK
 *
 * Cryptographic audit trails for AI decisions.
 *
 * @example
 * ```typescript
 * import { UATP } from 'uatp';
 *
 * const client = new UATP();
 *
 * const result = await client.certify({
 *   task: 'Loan decision',
 *   decision: 'Approved for $50,000',
 *   reasoning: [
 *     { step: 1, thought: 'Credit score excellent', confidence: 0.95 }
 *   ]
 * });
 *
 * console.log(result.signature); // Ed25519 signature
 * ```
 *
 * @packageDocumentation
 */

export { UATP } from './client';

export {
  deriveKeyPair,
  deriveDevicePassphrase,
  createSignedCapsule,
  verifyCapsule,
  hashContent,
  sign,
  verify,
  canonicalize,
  bytesToHex,
  hexToBytes,
} from './crypto';

export type {
  UATPConfig,
  CertifyOptions,
  SignedCapsule,
  CapsuleContent,
  CapsuleProof,
  VerificationResult,
  ReasoningStep,
  DataSource,
  KeyPair,
} from './types';
