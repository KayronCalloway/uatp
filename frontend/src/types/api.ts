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
  demo_mode?: boolean;  // Filter demo capsules (default: false to show only live data)
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
// Rich Data Types (Court-Admissible Format)
export interface DataSource {
  source: string;
  value: any;
  timestamp?: string;
  api_endpoint?: string;
  api_version?: string;
  query?: string;
  response_time_ms?: number;
  verification?: {
    cross_checked?: string[];
    values?: any[];
    consensus?: boolean;
  };
  audit_trail?: string;
}

export interface Alternative {
  option: string;
  score?: number;
  why_not_chosen: string;
  data?: Record<string, any>;
}

export interface RiskAssessment {
  probability_correct: number;
  probability_wrong: number;
  expected_value?: number;
  value_at_risk_95?: number;
  expected_loss_if_wrong?: number;
  expected_gain_if_correct?: number;
  key_risk_factors?: string[];
  safeguards?: string[];
  failure_modes?: Array<{
    scenario: string;
    probability: number;
    mitigation: string;
  }>;
  similar_decisions_count?: number;
  historical_accuracy?: number;
}

export interface EnhancedReasoningStep {
  step: number;
  action: string;
  confidence: number;
  reasoning?: string;
  plain_language?: string;
  data_sources?: DataSource[];
  alternatives_evaluated?: Alternative[];
  decision_criteria?: string[];
  confidence_basis?: string;
  uncertainty_factors?: string[];
  metadata?: Record<string, any>;
  // Backward compatibility
  thought?: string;
}

export interface PlainLanguageSummary {
  decision: string;
  why: string;
  key_factors: string[];
  what_if_different?: string;
  your_rights?: string;
  how_to_appeal?: string;
}

export interface Outcome {
  occurred: boolean;
  result: 'successful' | 'failed' | 'partial' | 'pending' | 'unknown';
  timestamp: string;
  ai_was_correct?: boolean;
  actual_vs_predicted?: string;
  financial_impact?: number;
  customer_satisfaction?: number;
  business_impact?: string;
  complications?: string[];
  lessons_learned?: string;
  notes?: string;
}

export interface AnyCapsule {
  id: string;
  capsule_id: string;
  type: string;
  content: string;
  metadata: Record<string, any>;
  timestamp: string;
  agent_id: string;
  payload?: {
    task?: string;
    decision?: string;
    reasoning_chain?: EnhancedReasoningStep[];
    confidence?: number;
    risk_assessment?: RiskAssessment;
    alternatives_considered?: Alternative[];
    plain_language_summary?: PlainLanguageSummary;
    outcome?: Outcome;
    [key: string]: any;
  };
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
