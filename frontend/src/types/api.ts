// API Types - Generated from backend schemas
export interface ErrorResponse {
  error: string;
  details?: string;
}

export interface CapsuleListResponse {
  capsules: AnyCapsule[];
}

export interface CompressedCapsuleListResponse {
  capsules: Record<string, any>[];
}

export interface ListCapsulesQuery {
  page?: number;
  per_page?: number;
  compress?: boolean;
}

export interface GetCapsuleQuery {
  include_raw?: boolean;
}

export interface CapsuleDetailResponse {
  capsule: AnyCapsule;
  raw_data?: Record<string, any>;
}

export interface CapsuleStatsResponse {
  total_capsules: number;
  types: Record<string, number>;
  unique_agents: number;
}

export interface VerificationResponse {
  capsule_id: string;
  verified: boolean;
  from_cache?: boolean;
  metadata_has_verify_key?: boolean;
  verification_error?: string;
  error?: string;
}

export interface HealthCheckResponse {
  status: string;
  timestamp: string;
  version: string;
  engine: Record<string, any>;
  features: Record<string, boolean>;
}

export interface IndexResponse {
  service: string;
  version: string;
  documentation: string;
}

export interface AIGenerateRequest {
  prompt: string;
  model?: string;
  max_tokens?: number;
  temperature?: number;
}

export interface AIGenerateResponse {
  status: string;
  generated_text: string;
}

export interface ChainSeal {
  seal_id: string;
  chain_id: string;
  chain_state_hash: string;
  signer_id: string;
  timestamp: string;
  note: string;
  version: string;
  signature: string;
  verify_key: string;
}

export interface ChainSealListResponse {
  seals: ChainSeal[];
}

export interface SealChainRequest {
  chain_id: string;
  note?: string;
}

export interface SealChainResponse {
  status: string;
  seal: ChainSeal;
}

export interface VerifySealQuery {
  verify_key: string;
  seal_id?: string;
}

export interface VerifySealResponse {
  verified: boolean;
  chain_id: string;
  seal_id?: string;
  signer_id?: string;
  timestamp?: string;
  chain_unchanged?: boolean;
  note?: string;
  error?: string;
}

// Capsule types - will need to be expanded based on actual capsule schemas
export interface AnyCapsule {
  id: string;
  capsule_id: string;
  type: string;
  content: string;
  metadata: Record<string, any>;
  timestamp: string;
  agent_id: string;
  [key: string]: any;
}

// Trust and reasoning types
export interface TrustMetrics {
  agent_id: string;
  trust_score: number;
  reputation: number;
  violations: number;
  last_updated: string;
}

export interface ReasoningAnalysisRequest {
  capsule_id?: string;
  trace_data?: Record<string, any>;
  analysis_type?: string;
}

export interface ReasoningAnalysisResponse {
  analysis: Record<string, any>;
  insights: string[];
  confidence: number;
  timestamp: string;
}

export interface ValidationResponse {
  valid: boolean;
  errors: string[];
  warnings: string[];
  confidence: number;
}