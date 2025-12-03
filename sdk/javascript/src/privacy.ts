/**
 * UATP JavaScript/TypeScript SDK - Privacy Engine Module
 * 
 * Provides zero-knowledge proof generation and privacy-preserving functionality.
 */

import CryptoJS from 'crypto-js';
import { Timestamp } from './types';

export interface ZKProof {
  proofId: string;
  proofType: 'attribution' | 'identity' | 'ownership' | 'computation';
  statement: string; // What is being proven
  proofData: Record<string, any>;
  verificationKey: string;
  creatorId: string;
  validityPeriod: number; // seconds
  createdAt: Timestamp;
  readonly isValid: boolean;
}

export interface PrivacyPolicy {
  anonymizeUserId: boolean;
  hideContent: boolean;
  encryptMetadata: boolean;
  zeroKnowledgeProofs: boolean;
  retentionPeriodDays: number;
  sharingPermissions: string[];
}

export interface CreateProofOptions {
  data: Record<string, any>;
  proofType?: 'attribution' | 'identity' | 'ownership' | 'computation';
  statement?: string;
  validityHours?: number;
}

export interface AnonymizeDataOptions {
  data: Record<string, any>;
  anonymizationLevel?: 'minimal' | 'standard' | 'maximum';
}

export interface EncryptDataOptions {
  data: Record<string, any>;
  encryptionKey?: string;
}

/**
 * Handles privacy-preserving operations for UATP.
 */
export class PrivacyEngine {
  private client: any;
  private proofCache: Map<string, ZKProof> = new Map();
  private privacyPolicies: Map<string, PrivacyPolicy> = new Map();

  constructor(client: any) {
    this.client = client;
  }

  /**
   * Create a zero-knowledge proof for privacy-preserving operations.
   */
  async createProof(options: CreateProofOptions): Promise<ZKProof> {
    const {
      data,
      proofType = 'attribution',
      statement,
      validityHours = 24
    } = options;

    const finalStatement = statement || `Proof of ${proofType} without revealing sensitive data`;

    // Generate proof components
    const proofId = `zkp_${this.generateRandomHex(16)}`;
    const verificationKey = this.generateVerificationKey(data, proofType);

    // Create proof request
    const proofRequest = {
      proofType,
      statement: finalStatement,
      dataHash: CryptoJS.SHA256(JSON.stringify(data)).toString(),
      validityHours,
      timestamp: new Date().toISOString()
    };

    try {
      // Submit to UATP privacy service
      const response = await this.client.request('POST', '/api/v1/privacy/create-proof', proofRequest);
      const result = response.data;

      // Create ZK proof object
      const zkProof: ZKProof = {
        proofId,
        proofType,
        statement: finalStatement,
        proofData: result.proofData || {},
        verificationKey,
        creatorId: result.creatorId || 'anonymous',
        validityPeriod: validityHours * 3600,
        createdAt: new Date().toISOString(),

        get isValid(): boolean {
          const now = Date.now();
          const created = new Date(this.createdAt).getTime();
          const expiry = created + (this.validityPeriod * 1000);
          return now < expiry;
        }
      };

      // Cache the proof
      this.proofCache.set(proofId, zkProof);

      this.client.emit('proof_created', { proofId, proofType });
      return zkProof;

    } catch (error) {
      console.error('ZK proof creation failed:', error);

      // Create fallback proof
      const fallbackProof: ZKProof = {
        proofId,
        proofType,
        statement: finalStatement,
        proofData: {
          method: 'local_commitment',
          commitment: CryptoJS.SHA256(JSON.stringify(data)).toString(),
          nonce: this.generateRandomHex(32)
        },
        verificationKey,
        creatorId: 'local_user',
        validityPeriod: validityHours * 3600,
        createdAt: new Date().toISOString(),

        get isValid(): boolean {
          const now = Date.now();
          const created = new Date(this.createdAt).getTime();
          const expiry = created + (this.validityPeriod * 1000);
          return now < expiry;
        }
      };

      this.proofCache.set(proofId, fallbackProof);
      return fallbackProof;
    }
  }

  private generateVerificationKey(data: Record<string, any>, proofType: string): string {
    const keyMaterial = `${proofType}:${JSON.stringify(data)}:${this.generateRandomHex(16)}`;
    return CryptoJS.SHA256(keyMaterial).toString();
  }

  private generateRandomHex(length: number): string {
    const chars = '0123456789abcdef';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars[Math.floor(Math.random() * chars.length)];
    }
    return result;
  }

  /**
   * Verify a zero-knowledge proof.
   */
  async verifyProof(proof: ZKProof | string): Promise<any> {
    let proofObj: ZKProof;
    let proofId: string;

    if (typeof proof === 'string') {
      proofId = proof;
      const cachedProof = this.proofCache.get(proofId);
      if (!cachedProof) {
        const fetchedProof = await this.getProof(proofId);
        if (!fetchedProof) {
          return { verified: false, error: 'Proof not found' };
        }
        proofObj = fetchedProof;
      } else {
        proofObj = cachedProof;
      }
    } else {
      proofObj = proof;
      proofId = proof.proofId;
    }

    const verificationRequest = {
      proofId,
      proofType: proofObj.proofType,
      verificationKey: proofObj.verificationKey,
      timestamp: new Date().toISOString()
    };

    try {
      const response = await this.client.request('POST', '/api/v1/privacy/verify-proof', verificationRequest);
      const result = response.data;

      // Check local validity as well
      const isLocallyValid = proofObj.isValid;

      const verificationResult = {
        verified: (result.verified || false) && isLocallyValid,
        proofId,
        proofType: proofObj.proofType,
        statement: proofObj.statement,
        validityRemaining: Math.max(0, proofObj.validityPeriod - 
          ((Date.now() - new Date(proofObj.createdAt).getTime()) / 1000)),
        verificationTimestamp: new Date().toISOString(),
        details: result.details || {}
      };

      this.client.emit('proof_verified', { proofId, verified: verificationResult.verified });
      return verificationResult;

    } catch (error) {
      console.error(`Proof verification failed for ${proofId}:`, error);
      return {
        verified: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        proofId
      };
    }
  }

  /**
   * Retrieve a proof by ID.
   */
  async getProof(proofId: string): Promise<ZKProof | null> {
    // Check cache first
    if (this.proofCache.has(proofId)) {
      return this.proofCache.get(proofId)!;
    }

    try {
      const response = await this.client.request('GET', `/api/v1/privacy/proofs/${proofId}`);
      const data = response.data;

      const proof: ZKProof = {
        proofId: data.proofId,
        proofType: data.proofType,
        statement: data.statement,
        proofData: data.proofData,
        verificationKey: data.verificationKey,
        creatorId: data.creatorId,
        validityPeriod: data.validityPeriod,
        createdAt: data.createdAt,

        get isValid(): boolean {
          const now = Date.now();
          const created = new Date(this.createdAt).getTime();
          const expiry = created + (this.validityPeriod * 1000);
          return now < expiry;
        }
      };

      // Cache the proof
      this.proofCache.set(proofId, proof);
      return proof;

    } catch (error) {
      console.error(`Failed to get proof ${proofId}:`, error);
      return null;
    }
  }

  /**
   * Anonymize sensitive data while preserving utility.
   */
  async anonymizeData(options: AnonymizeDataOptions): Promise<any> {
    const { data, anonymizationLevel = 'standard' } = options;

    const anonymizationRequest = {
      data,
      level: anonymizationLevel,
      timestamp: new Date().toISOString()
    };

    try {
      const response = await this.client.request('POST', '/api/v1/privacy/anonymize', anonymizationRequest);
      
      this.client.emit('data_anonymized', { level: anonymizationLevel });
      return response.data.anonymizedData || {};

    } catch (error) {
      console.error('Data anonymization failed:', error);

      // Fallback local anonymization
      return this.localAnonymize(data, anonymizationLevel);
    }
  }

  private localAnonymize(data: Record<string, any>, level: string): Record<string, any> {
    const anonymized = { ...data };

    // Fields to anonymize based on level
    const sensitiveFields: Record<string, string[]> = {
      minimal: ['userId', 'email'],
      standard: ['userId', 'email', 'username', 'fullName', 'ipAddress'],
      maximum: ['userId', 'email', 'username', 'fullName', 'ipAddress', 
               'location', 'deviceId', 'sessionId']
    };

    const fieldsToAnonymize = sensitiveFields[level] || sensitiveFields.standard;

    for (const field of fieldsToAnonymize) {
      if (field in anonymized) {
        if (['userId', 'email', 'username'].includes(field)) {
          // Hash with salt
          const salt = this.generateRandomHex(16);
          anonymized[field] = CryptoJS.SHA256(
            `${anonymized[field]}${salt}`
          ).toString().substring(0, 16);
        } else {
          // Remove completely
          anonymized[field] = '[REDACTED]';
        }
      }
    }

    return anonymized;
  }

  /**
   * Create or update privacy policy for a user.
   */
  async createPrivacyPolicy(userId: string, policy: PrivacyPolicy): Promise<boolean> {
    const policyRequest = {
      userId,
      policy: {
        anonymizeUserId: policy.anonymizeUserId,
        hideContent: policy.hideContent,
        encryptMetadata: policy.encryptMetadata,
        zeroKnowledgeProofs: policy.zeroKnowledgeProofs,
        retentionPeriodDays: policy.retentionPeriodDays,
        sharingPermissions: policy.sharingPermissions
      },
      timestamp: new Date().toISOString()
    };

    try {
      await this.client.request('PUT', `/api/v1/privacy/policies/${userId}`, policyRequest);

      // Cache the policy
      this.privacyPolicies.set(userId, policy);

      this.client.emit('privacy_policy_updated', { userId });
      return true;

    } catch (error) {
      console.error(`Failed to update privacy policy for ${userId}:`, error);
      return false;
    }
  }

  /**
   * Get privacy policy for a user.
   */
  async getPrivacyPolicy(userId: string): Promise<PrivacyPolicy | null> {
    // Check cache first
    if (this.privacyPolicies.has(userId)) {
      return this.privacyPolicies.get(userId)!;
    }

    try {
      const response = await this.client.request('GET', `/api/v1/privacy/policies/${userId}`);
      const data = response.data;
      const policyData = data.policy;

      const policy: PrivacyPolicy = {
        anonymizeUserId: policyData.anonymizeUserId,
        hideContent: policyData.hideContent,
        encryptMetadata: policyData.encryptMetadata,
        zeroKnowledgeProofs: policyData.zeroKnowledgeProofs,
        retentionPeriodDays: policyData.retentionPeriodDays,
        sharingPermissions: policyData.sharingPermissions
      };

      // Cache the policy
      this.privacyPolicies.set(userId, policy);
      return policy;

    } catch (error) {
      console.error(`Failed to get privacy policy for ${userId}:`, error);
      return null;
    }
  }

  /**
   * Encrypt sensitive data for secure storage.
   */
  async encryptSensitiveData(options: EncryptDataOptions): Promise<any> {
    const { data, encryptionKey } = options;
    const key = encryptionKey || this.generateRandomHex(32);

    const encryptionRequest = {
      data,
      keyHint: CryptoJS.SHA256(key).toString().substring(0, 16),
      timestamp: new Date().toISOString()
    };

    try {
      const response = await this.client.request('POST', '/api/v1/privacy/encrypt', encryptionRequest, {
        headers: { 'X-Encryption-Key': key }
      });

      this.client.emit('data_encrypted', {});
      return response.data;

    } catch (error) {
      console.error('Data encryption failed:', error);

      // Fallback local encryption (simplified)
      const encryptedData: Record<string, any> = {};
      
      for (const [dataKey, value] of Object.entries(data)) {
        if (typeof value === 'string' && ['content', 'prompt', 'response'].includes(dataKey)) {
          // Simple encryption using CryptoJS
          const encrypted = CryptoJS.AES.encrypt(value, key).toString();
          encryptedData[dataKey] = encrypted;
        } else {
          encryptedData[dataKey] = value;
        }
      }

      return {
        encryptedData,
        encryptionMethod: 'local_fallback',
        keyHint: CryptoJS.SHA256(key).toString().substring(0, 16)
      };
    }
  }

  /**
   * Clear all cached privacy data.
   */
  clearCache(): void {
    this.proofCache.clear();
    this.privacyPolicies.clear();
    this.client.emit('privacy_cache_cleared', {});
  }
}