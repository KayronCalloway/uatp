/**
 * UATP TypeScript SDK - Type Definitions
 */

export interface ReasoningStep {
  step: number;
  thought: string;
  confidence: number;
  action?: string;
  data_sources?: DataSource[];
  reasoning?: string;
  plain_language?: string;
}

export interface DataSource {
  source: string;
  value: unknown;
  timestamp?: string;
  api_endpoint?: string;
}

export interface CertifyOptions {
  /** Description of the task */
  task: string;
  /** The AI's final decision */
  decision: string;
  /** List of reasoning steps */
  reasoning: ReasoningStep[];
  /** Optional passphrase for key encryption (recommended for production) */
  passphrase?: string;
  /** If true, derive passphrase from browser/device info (default: true) */
  deviceBound?: boolean;
  /** Overall confidence score (0-1). Auto-calculated if not provided */
  confidence?: number;
  /** Additional metadata to attach */
  metadata?: Record<string, unknown>;
  /** Request RFC 3161 timestamp from server (default: true) */
  requestTimestamp?: boolean;
  /** Store capsule on UATP server (default: false) */
  storeOnServer?: boolean;
}

export interface SignedCapsule {
  /** Unique capsule identifier */
  capsuleId: string;
  /** Ed25519 signature (hex) */
  signature: string;
  /** Public key for verification (hex) */
  publicKey: string;
  /** SHA-256 hash of content (hex) */
  contentHash: string;
  /** ISO timestamp of signing */
  timestamp: string;
  /** Original content that was signed */
  content: CapsuleContent;
  /** RFC 3161 timestamp token (if requested) */
  timestampToken?: string;
  /** Timestamp authority used */
  timestampTsa?: string;
  /** Whether stored on server */
  serverStored?: boolean;
  /** URL to verify on server */
  proofUrl?: string;
}

export interface CapsuleContent {
  task: string;
  decision: string;
  reasoning_chain: ReasoningStep[];
  confidence: number;
  metadata: Record<string, unknown>;
}

export interface CapsuleProof {
  capsuleId: string;
  capsuleType: string;
  status: string;
  timestamp: Date;
  payload: Record<string, unknown>;
  rawData: Record<string, unknown>;
}

export interface VerificationResult {
  valid: boolean;
  signatureValid: boolean;
  hashValid: boolean;
  timestampValid?: boolean;
  errors?: string[];
}

export interface UATPConfig {
  /** API key for authenticated requests */
  apiKey?: string;
  /** Base URL of UATP server (default: http://localhost:8000) */
  baseUrl?: string;
  /** Request timeout in milliseconds (default: 30000) */
  timeout?: number;
}

export interface KeyPair {
  privateKey: Uint8Array;
  publicKey: Uint8Array;
}
