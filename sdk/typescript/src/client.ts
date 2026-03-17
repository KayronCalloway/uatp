/**
 * UATP TypeScript SDK - Client
 *
 * Zero-Trust Architecture:
 * - Private keys NEVER leave your device
 * - All signing happens locally using Ed25519
 * - Only content hash sent to server for RFC 3161 timestamping
 * - Capsules can be verified independently without UATP
 */

import type {
  UATPConfig,
  CertifyOptions,
  SignedCapsule,
  CapsuleProof,
  VerificationResult,
  ReasoningStep,
  CapsuleContent,
} from './types';

import {
  deriveKeyPair,
  deriveDevicePassphrase,
  createSignedCapsule,
  verifyCapsule,
} from './crypto';

const DEFAULT_BASE_URL = 'http://localhost:8000';
const DEFAULT_TIMEOUT = 30000;
const SDK_VERSION = '0.1.0';

export class UATP {
  private apiKey?: string;
  private baseUrl: string;
  private timeout: number;

  /**
   * Initialize UATP client.
   *
   * @example
   * ```typescript
   * // Local development
   * const client = new UATP();
   *
   * // Production
   * const client = new UATP({
   *   apiKey: 'your-api-key',
   *   baseUrl: 'https://api.uatp.io'
   * });
   * ```
   */
  constructor(config: UATPConfig = {}) {
    this.apiKey = config.apiKey;
    this.baseUrl = (config.baseUrl || DEFAULT_BASE_URL).replace(/\/$/, '');
    this.timeout = config.timeout || DEFAULT_TIMEOUT;

    if (this.baseUrl === DEFAULT_BASE_URL) {
      console.warn('UATP client using localhost - set baseUrl for production');
    }
  }

  /**
   * Create a cryptographically certified capsule for an AI decision.
   *
   * ZERO-TRUST: Private key NEVER leaves your device.
   * - All signing happens locally using Ed25519
   * - Only the content hash is sent to UATP for timestamping
   * - Capsules can be verified independently without UATP
   *
   * @example
   * ```typescript
   * const result = await client.certify({
   *   task: 'Loan decision',
   *   decision: 'Approved for $50,000 at 5.2% APR',
   *   reasoning: [
   *     { step: 1, thought: 'Credit score 720 (excellent)', confidence: 0.95 },
   *     { step: 2, thought: 'Debt-to-income 0.28 (acceptable)', confidence: 0.90 }
   *   ]
   * });
   *
   * console.log(result.capsuleId);
   * console.log(result.signature);
   * ```
   */
  async certify(options: CertifyOptions): Promise<SignedCapsule> {
    const {
      task,
      decision,
      reasoning,
      passphrase,
      deviceBound = true,
      confidence,
      metadata = {},
      requestTimestamp = true,
      storeOnServer = false,
    } = options;

    // Validate inputs
    if (!task || typeof task !== 'string') {
      throw new Error('task must be a non-empty string');
    }
    if (!decision || typeof decision !== 'string') {
      throw new Error('decision must be a non-empty string');
    }
    if (!reasoning || !Array.isArray(reasoning) || reasoning.length === 0) {
      throw new Error('reasoning must be a non-empty array');
    }

    // Determine passphrase
    let signingPassphrase: string;
    if (passphrase) {
      if (passphrase.length < 8) {
        throw new Error('passphrase must be at least 8 characters');
      }
      signingPassphrase = passphrase;
    } else if (deviceBound) {
      console.warn(
        'Using device-bound passphrase (DEVELOPMENT ONLY). ' +
          'For production, provide an explicit passphrase.'
      );
      signingPassphrase = deriveDevicePassphrase();
    } else {
      throw new Error('Either provide a passphrase or set deviceBound=true');
    }

    // Calculate confidence if not provided
    const calculatedConfidence =
      confidence ??
      reasoning.reduce((sum, step) => sum + (step.confidence || 0.5), 0) /
        reasoning.length;

    // Create content for signing
    const content: CapsuleContent = {
      task,
      decision,
      reasoning_chain: reasoning,
      confidence: calculatedConfidence,
      metadata: {
        ...metadata,
        timestamp: new Date().toISOString(),
        sdk_version: SDK_VERSION,
        signing_mode: 'local',
      },
    };

    // Derive key pair from passphrase
    const keyPair = deriveKeyPair(signingPassphrase);

    // Sign locally - private key NEVER leaves device
    const signed = createSignedCapsule(content, keyPair);

    // Request RFC 3161 timestamp if desired
    if (requestTimestamp) {
      try {
        const response = await this.fetch('/timestamp', {
          method: 'POST',
          body: JSON.stringify({ hash: signed.contentHash }),
        });

        if (response.ok) {
          const tsData = await response.json();
          signed.timestampToken = tsData.rfc3161;
          signed.timestampTsa = tsData.tsa;
        }
      } catch (error) {
        console.warn(
          'Could not obtain timestamp. Capsule is still valid, just without external timestamp.',
          error
        );
      }
    }

    // Store on server if requested
    if (storeOnServer) {
      try {
        const capsuleData = {
          ...signed,
          type: 'reasoning_trace',
          payload: content,
        };

        const response = await this.fetch('/capsules/store', {
          method: 'POST',
          body: JSON.stringify(capsuleData),
        });

        if (response.ok) {
          signed.serverStored = true;
          signed.proofUrl = `${this.baseUrl}/capsules/${signed.capsuleId}/verify`;
        }
      } catch (error) {
        console.warn('Could not store on server. Capsule is still valid locally.', error);
        signed.serverStored = false;
      }
    }

    return signed;
  }

  /**
   * Retrieve full cryptographic proof for a capsule.
   *
   * @example
   * ```typescript
   * const proof = await client.getProof('cap_abc123');
   * console.log(proof.payload.task);
   * ```
   */
  async getProof(capsuleId: string): Promise<CapsuleProof> {
    const response = await this.fetch(`/capsules/${capsuleId}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Capsule ${capsuleId} not found`);
      }
      throw new Error(`Failed to retrieve proof: ${response.status}`);
    }

    const data = await response.json();
    const capsule = data.capsule || data;

    return {
      capsuleId: capsule.capsule_id || capsule.id || capsuleId,
      capsuleType: capsule.type || capsule.capsule_type || 'unknown',
      status: capsule.status || 'unknown',
      timestamp: new Date(capsule.timestamp),
      payload: capsule.payload || {},
      rawData: data,
    };
  }

  /**
   * List capsules from the server.
   *
   * @example
   * ```typescript
   * const capsules = await client.listCapsules(10);
   * for (const cap of capsules) {
   *   console.log(cap.capsuleId, cap.status);
   * }
   * ```
   */
  async listCapsules(limit = 10): Promise<CapsuleProof[]> {
    const response = await this.fetch(`/capsules?demo_mode=false&per_page=${limit}`);

    if (!response.ok) {
      throw new Error(`Failed to list capsules: ${response.status}`);
    }

    const data = await response.json();

    return (data.capsules || []).slice(0, limit).map((item: Record<string, unknown>) => ({
      capsuleId: item.capsule_id as string,
      capsuleType: (item.type as string) || 'unknown',
      status: (item.status as string) || 'unknown',
      timestamp: new Date(item.timestamp as string),
      payload: (item.payload as Record<string, unknown>) || {},
      rawData: item,
    }));
  }

  /**
   * Verify a capsule locally without server.
   *
   * This can be done by anyone - no UATP infrastructure required.
   * Only uses cryptographic data embedded in the capsule.
   *
   * @example
   * ```typescript
   * const result = client.verifyLocal(capsule);
   * if (result.valid) {
   *   console.log('Capsule is authentic!');
   * }
   * ```
   */
  verifyLocal(capsule: SignedCapsule): VerificationResult {
    return verifyCapsule(capsule);
  }

  /**
   * Record the actual outcome of an AI decision (ground truth).
   *
   * @example
   * ```typescript
   * await client.recordOutcome('cap_abc123', {
   *   result: 'successful',
   *   aiWasCorrect: true,
   *   financialImpact: 2500,
   *   notes: 'Loan fully paid on time'
   * });
   * ```
   */
  async recordOutcome(
    capsuleId: string,
    outcome: {
      result?: string;
      aiWasCorrect?: boolean;
      financialImpact?: number;
      customerSatisfaction?: number;
      notes?: string;
    }
  ): Promise<boolean> {
    const params = new URLSearchParams();
    if (outcome.result) params.set('outcome_status', outcome.result);
    if (outcome.notes) params.set('notes', outcome.notes);
    if (outcome.customerSatisfaction) {
      params.set('rating', String(outcome.customerSatisfaction));
    }

    const response = await this.fetch(
      `/capsules/${capsuleId}/outcome?${params.toString()}`,
      { method: 'POST' }
    );

    if (response.status === 401) {
      throw new Error('Authentication required. Outcome tracking requires a valid API key.');
    }

    if (response.status === 404) {
      throw new Error(`Capsule ${capsuleId} not found`);
    }

    if (!response.ok) {
      throw new Error(`Failed to record outcome: ${response.status}`);
    }

    return true;
  }

  /**
   * Internal fetch wrapper with timeout and headers.
   */
  private async fetch(path: string, options: RequestInit = {}): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': `uatp-typescript-sdk/${SDK_VERSION}`,
          ...(this.apiKey ? { Authorization: `Bearer ${this.apiKey}` } : {}),
          ...options.headers,
        },
      });

      return response;
    } finally {
      clearTimeout(timeoutId);
    }
  }
}
