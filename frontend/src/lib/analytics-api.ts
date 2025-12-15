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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
  return fetchAPI<OutcomeStats>('/outcomes/stats');
}

export async function getOutcomesForCapsule(capsuleId: string) {
  return fetchAPI<{ outcomes: Outcome[]; total: number }>(`/outcomes/${capsuleId}`);
}

export async function getPendingOutcomes(limit: number = 50) {
  return fetchAPI<{ pending_capsules: any[]; total: number }>(
    `/outcomes/pending?limit=${limit}`
  );
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
};
