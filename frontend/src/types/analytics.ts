/**
 * Analytics Type Definitions
 * Types for quality assessment, patterns, calibration, and causal analysis
 */

export interface QualityScore {
  dimension: string;
  score: number;
  max_score: number;
  issues: string[];
  suggestions: string[];
}

export interface QualityAssessment {
  overall_quality: number;
  dimension_scores: Record<string, QualityScore>;
  strengths: string[];
  weaknesses: string[];
  improvement_priority: [string, number][];
  quality_grade: 'A' | 'B' | 'C' | 'D' | 'F';
  backfilled?: boolean;
  assessed_at?: string;
}

export interface Pattern {
  pattern_id: string;
  pattern_type: 'sequence' | 'decision_tree' | 'failure_mode';
  pattern_name: string;
  pattern_description: string;
  pattern_structure: Record<string, any>;
  success_rate: number;
  usage_count: number;
  applicable_domains: string[];
  example_capsule_ids: string[];
  confidence_impact?: number;
  created_at: string;
}

export interface PatternFilters {
  pattern_type?: string;
  min_success_rate?: number;
  domain?: string;
  limit?: number;
}

export interface CalibrationData {
  domain: string;
  confidence_bucket: number;
  predicted_count: number;
  actual_success_count: number;
  calibration_error: number;
  recommended_adjustment: number;
  success_rate: number;
}

export interface UncertaintyEstimate {
  point_estimate: number;
  confidence_interval: [number, number];
  credible_interval: [number, number];
  confidence_level: number;
  epistemic_uncertainty: number;
  aleatoric_uncertainty: number;
  total_uncertainty: number;
  risk_score: number;
  worst_case: number;
  best_case: number;
  variance: number;
  skewness: number;
  is_symmetric: boolean;
}

export interface OutcomeStats {
  total_outcomes: number;
  average_quality_score: number;
  outcomes_by_validation_method: Record<string, number>;
  total_patterns_discovered: number;
}

export interface Outcome {
  id: number;
  capsule_id: string;
  predicted_outcome?: string;
  actual_outcome: string;
  outcome_quality_score?: number;
  outcome_timestamp: string;
  validation_method?: string;
  validator_id?: string;
  notes?: string;
  created_at: string;
}

export interface CausalVariable {
  name: string;
  type: 'action' | 'condition' | 'outcome' | 'context';
  description: string;
  confidence: number;
}

export interface CausalEdge {
  source: string;
  target: string;
  type: 'direct_cause' | 'confounding' | 'mediating';
  strength: number;
  evidence_count: number;
}

export interface CausalGraph {
  variables: Record<string, CausalVariable>;
  edges: CausalEdge[];
  statistics: {
    num_variables: number;
    num_edges: number;
    root_causes: string[];
    terminal_effects: string[];
  };
}

export interface Strategy {
  strategy_id: string;
  strategy_name: string;
  strategy_description: string;
  success_rate: number;
  usage_count: number;
  applicable_domains: string[];
  applicable_problem_types: string[];
  example_capsule_ids: string[];
}

export interface StrategyRecommendation {
  strategy: Strategy;
  match_score: number;
  rationale: string;
  expected_confidence_boost: number;
  expected_success_probability: number;
}
