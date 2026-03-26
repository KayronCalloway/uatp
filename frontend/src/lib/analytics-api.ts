/**
 * Analytics API Client
 * Functions for fetching analytics data from backend
 */

import type {
  QualityAssessment,
  Pattern,
  PatternFilters,
  CalibrationData,
  OutcomeStats,
  Outcome,
  CausalGraph,
  Strategy,
  StrategyRecommendation,
} from '@/types/analytics';
import { getApiBaseUrl } from './api-client';

// SECURITY: Use getApiBaseUrl which enforces config in production
const API_BASE = getApiBaseUrl();

// Generic fetch wrapper with error handling
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `API Error: ${response.statusText}`);
  }

  return response.json();
}

// ============================================================================
// Quality Assessment
// ============================================================================

export async function getQualityAssessment(capsuleId: string): Promise<QualityAssessment> {
  // Note: Backend endpoint would need to be created for this
  // For now, this would call a quality assessment endpoint
  return fetchAPI<QualityAssessment>(`/api/quality/${capsuleId}`);
}

// ============================================================================
// Patterns
// ============================================================================

export async function getPatterns(filters?: PatternFilters) {
  const params = new URLSearchParams();

  if (filters?.pattern_type) params.append('pattern_type', filters.pattern_type);
  if (filters?.min_success_rate !== undefined) {
    params.append('min_success_rate', filters.min_success_rate.toString());
  }
  if (filters?.limit) params.append('limit', filters.limit.toString());

  const queryString = params.toString();
  const endpoint = `/outcomes/patterns${queryString ? `?${queryString}` : ''}`;

  return fetchAPI<{ patterns: Pattern[]; total: number }>(endpoint);
}

export async function getPattern(patternId: string): Promise<Pattern> {
  return fetchAPI<Pattern>(`/outcomes/patterns/${patternId}`);
}

// ============================================================================
// Calibration
// ============================================================================

export async function getCalibrationData(domain?: string) {
  const params = new URLSearchParams();
  if (domain) params.append('domain', domain);

  const queryString = params.toString();
  const endpoint = `/outcomes/calibration/data${queryString ? `?${queryString}` : ''}`;

  return fetchAPI<{ calibration_data: CalibrationData[]; total: number }>(endpoint);
}

export async function updateCalibration() {
  return fetchAPI<{
    message: string;
    updated: number;
    total_outcomes_processed: number;
  }>('/outcomes/calibration/update', {
    method: 'POST',
  });
}

// ============================================================================
// Outcomes
// ============================================================================

export async function getOutcomeStats(): Promise<OutcomeStats> {
  // Try ML dashboard endpoint first (has richer data), fall back to capsules endpoint
  try {
    const mlData = await fetchAPI<any>('/ml/outcomes/stats');
    // Transform ML dashboard format to expected OutcomeStats format
    return {
      total_outcomes: mlData.total_with_outcomes || 0,
      average_quality_score: mlData.success_rate || 0,
      total_patterns_discovered: 0,
      outcomes_by_validation_method: mlData.by_status || {},
    };
  } catch {
    // Fall back to capsules endpoint
    const data = await fetchAPI<any>('/capsules/outcomes/stats');
    return {
      total_outcomes: data.total_tracked || 0,
      average_quality_score: (data.success_rate_percent || 0) / 100,
      total_patterns_discovered: 0,
      outcomes_by_validation_method: data.outcome_counts || {},
    };
  }
}

export async function getOutcomesForCapsule(capsuleId: string) {
  return fetchAPI<{ outcomes: Outcome[]; total: number }>(`/outcomes/${capsuleId}`);
}

export async function getPendingOutcomes(limit: number = 50) {
  // Use capsules endpoint with outcome_status filter
  try {
    const data = await fetchAPI<any>(`/capsules?outcome_status=pending&limit=${limit}`);
    return {
      pending_capsules: data.capsules || [],
      total: data.total || 0,
    };
  } catch {
    // Return empty if endpoint not available
    return {
      pending_capsules: [],
      total: 0,
    };
  }
}

export async function createOutcome(outcome: {
  capsule_id: string;
  predicted_outcome?: string;
  actual_outcome: string;
  outcome_quality_score?: number;
  validation_method?: string;
  validator_id?: string;
  notes?: string;
}) {
  return fetchAPI<Outcome>('/outcomes', {
    method: 'POST',
    body: JSON.stringify(outcome),
  });
}

// ============================================================================
// Causal Analysis
// ============================================================================

export async function getCausalGraph(capsuleIds: string[]): Promise<CausalGraph> {
  // Note: Backend endpoint would need to be created for this
  // This would build a causal graph from specified capsules
  return fetchAPI<CausalGraph>('/api/causal/graph', {
    method: 'POST',
    body: JSON.stringify({ capsule_ids: capsuleIds }),
  });
}

export async function getRootCauses(outcomeVariable: string, capsuleIds: string[]) {
  return fetchAPI<{ root_causes: any[]; confidence: number }>('/api/causal/root-causes', {
    method: 'POST',
    body: JSON.stringify({
      outcome_variable: outcomeVariable,
      capsule_ids: capsuleIds,
    }),
  });
}

export async function predictIntervention(
  interventionVar: string,
  interventionValue: any,
  outcomeVar: string,
  capsuleIds: string[]
) {
  return fetchAPI<{
    average_effect: number;
    confidence_interval: [number, number];
    description: string;
  }>('/api/causal/intervention', {
    method: 'POST',
    body: JSON.stringify({
      intervention_var: interventionVar,
      intervention_value: interventionValue,
      outcome_var: outcomeVar,
      capsule_ids: capsuleIds,
    }),
  });
}

// ============================================================================
// Strategies
// ============================================================================

export async function getStrategies(domain?: string) {
  const params = new URLSearchParams();
  if (domain) params.append('domain', domain);

  const queryString = params.toString();
  const endpoint = `/api/strategies${queryString ? `?${queryString}` : ''}`;

  return fetchAPI<{ strategies: Strategy[]; total: number }>(endpoint);
}

export async function getStrategyRecommendations(context: {
  domain?: string;
  problem_type?: string;
  context_elements?: string[];
}) {
  return fetchAPI<{ recommendations: StrategyRecommendation[] }>(
    '/api/strategies/recommend',
    {
      method: 'POST',
      body: JSON.stringify(context),
    }
  );
}

// ============================================================================
// Uncertainty
// ============================================================================

export async function getUncertaintyEstimate(
  confidence: number,
  sampleSize: number = 10
) {
  return fetchAPI<any>('/api/uncertainty/estimate', {
    method: 'POST',
    body: JSON.stringify({
      confidence,
      sample_size: sampleSize,
    }),
  });
}

// ============================================================================
// Analytics Summary
// ============================================================================

export async function getAnalyticsSummary() {
  // Aggregate endpoint that returns overview of all analytics
  return fetchAPI<{
    total_capsules: number;
    total_outcomes: number;
    total_patterns: number;
    average_quality: number;
    calibration_ece: number;
    strategies_learned: number;
  }>('/api/analytics/summary');
}

// ============================================================================
// ML Dashboard
// ============================================================================

export interface MLDashboardData {
  calibration: {
    status: string;
    global_metrics?: {
      sample_size: number;
      brier_score: number;
      calibration_error: number;
      log_loss?: number;
      reliability_diagram?: Record<string, number>;
    };
    domains?: Record<string, any>;
    reliability_data: Array<{
      predicted: number;
      actual: number;
      bucket: string;
    }>;
    recommendations: string[];
    drift_alerts: string[];
    error?: string;
  };
  outcomes: {
    status: string;
    total_with_outcomes: number;
    by_status: Record<string, number>;
    by_status_data: Array<{
      status: string;
      count: number;
      color: string;
    }>;
    pending_count: number;
    success_rate?: number;
    error?: string;
  };
  historical_accuracy: {
    status: string;
    total_capsules: number;
    capsules_with_outcomes: number;
    capsules_with_embeddings: number;
    outcome_distribution: Record<string, number>;
    similarity_threshold: number;
    max_similar_capsules: number;
    min_sample_size: number;
    historical_weight: number;
    error?: string;
  };
  learning_loop: {
    status: string;
    components: Record<string, boolean>;
    healthy_count: number;
    total_components: number;
    description: string;
  };
}

export async function getMLDashboard(): Promise<MLDashboardData> {
  return fetchAPI<MLDashboardData>('/ml/dashboard');
}

export async function getCalibrationTable(): Promise<{ table: string; format: string; error?: string }> {
  return fetchAPI('/ml/calibration/table');
}

export async function getRecentOutcomes(limit: number = 10) {
  return fetchAPI<{ outcomes: any[]; total: number; error?: string }>(
    `/ml/outcomes/recent?limit=${limit}`
  );
}

export async function testCalibration(confidence: number) {
  return fetchAPI<{
    raw_confidence: number;
    calibrated_confidence: number;
    adjustment: number;
    calibration_status: string;
    sample_size: number;
    error?: string;
  }>(`/ml/calibration/test?confidence=${confidence}`, {
    method: 'POST',
  });
}

export const analyticsAPI = {
  // Quality
  getQualityAssessment,

  // Patterns
  getPatterns,
  getPattern,

  // Calibration
  getCalibrationData,
  updateCalibration,

  // Outcomes
  getOutcomeStats,
  getOutcomesForCapsule,
  getPendingOutcomes,
  createOutcome,

  // Causal
  getCausalGraph,
  getRootCauses,
  predictIntervention,

  // Strategies
  getStrategies,
  getStrategyRecommendations,

  // Uncertainty
  getUncertaintyEstimate,

  // Summary
  getAnalyticsSummary,

  // ML Dashboard
  getMLDashboard,
  getCalibrationTable,
  getRecentOutcomes,
  testCalibration,
};
