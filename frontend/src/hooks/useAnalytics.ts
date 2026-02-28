/**
 * Analytics Hooks
 * React Query hooks for fetching analytics data
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { analyticsAPI } from '@/lib/analytics-api';
import { api } from '@/lib/api-client';
import { calculateQualityFromCapsule } from '@/lib/quality-calculator';
import type { PatternFilters } from '@/types/analytics';

// ============================================================================
// Patterns
// ============================================================================

export function usePatterns(filters?: PatternFilters) {
  return useQuery({
    queryKey: ['patterns', filters],
    queryFn: () => analyticsAPI.getPatterns(filters),
  });
}

export function usePattern(patternId: string) {
  return useQuery({
    queryKey: ['pattern', patternId],
    queryFn: () => analyticsAPI.getPattern(patternId),
    enabled: !!patternId,
  });
}

// ============================================================================
// Calibration
// ============================================================================

export function useCalibrationData(domain?: string) {
  return useQuery({
    queryKey: ['calibration', domain],
    queryFn: () => analyticsAPI.getCalibrationData(domain),
  });
}

export function useUpdateCalibration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: analyticsAPI.updateCalibration,
    onSuccess: () => {
      // Invalidate calibration queries to refetch
      queryClient.invalidateQueries({ queryKey: ['calibration'] });
    },
  });
}

// ============================================================================
// Outcomes
// ============================================================================

export function useOutcomeStats() {
  return useQuery({
    queryKey: ['outcome-stats'],
    queryFn: analyticsAPI.getOutcomeStats,
  });
}

export function useOutcomesForCapsule(capsuleId: string) {
  return useQuery({
    queryKey: ['outcomes', capsuleId],
    queryFn: () => analyticsAPI.getOutcomesForCapsule(capsuleId),
    enabled: !!capsuleId,
  });
}

export function usePendingOutcomes(limit: number = 50) {
  return useQuery({
    queryKey: ['pending-outcomes', limit],
    queryFn: () => analyticsAPI.getPendingOutcomes(limit),
  });
}

export function useCreateOutcome() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: analyticsAPI.createOutcome,
    onSuccess: (_, variables) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['outcomes', variables.capsule_id] });
      queryClient.invalidateQueries({ queryKey: ['outcome-stats'] });
      queryClient.invalidateQueries({ queryKey: ['pending-outcomes'] });
    },
  });
}

// ============================================================================
// Quality Assessment
// ============================================================================

export function useQualityAssessment(capsuleId: string) {
  return useQuery({
    queryKey: ['quality', capsuleId],
    queryFn: async () => {
      // Try to fetch from backend endpoint first
      try {
        return await analyticsAPI.getQualityAssessment(capsuleId);
      } catch (error) {
        // Backend endpoint doesn't exist yet, calculate from capsule data
        const capsuleData = await api.getCapsule(capsuleId, {});
        if (!capsuleData?.capsule) {
          throw new Error('Capsule not found');
        }
        return calculateQualityFromCapsule(capsuleData.capsule);
      }
    },
    enabled: !!capsuleId,
  });
}

// ============================================================================
// Strategies
// ============================================================================

export function useStrategies(domain?: string) {
  return useQuery({
    queryKey: ['strategies', domain],
    queryFn: () => analyticsAPI.getStrategies(domain),
  });
}

export function useStrategyRecommendations(context: {
  domain?: string;
  problem_type?: string;
  context_elements?: string[];
}) {
  return useQuery({
    queryKey: ['strategy-recommendations', context],
    queryFn: () => analyticsAPI.getStrategyRecommendations(context),
    enabled: !!(context.domain || context.problem_type),
  });
}

// ============================================================================
// Causal Analysis
// ============================================================================

export function useCausalGraph(capsuleIds: string[]) {
  return useQuery({
    queryKey: ['causal-graph', capsuleIds],
    queryFn: () => analyticsAPI.getCausalGraph(capsuleIds),
    enabled: capsuleIds.length > 0,
  });
}

export function useRootCauses(outcomeVariable: string, capsuleIds: string[]) {
  return useQuery({
    queryKey: ['root-causes', outcomeVariable, capsuleIds],
    queryFn: () => analyticsAPI.getRootCauses(outcomeVariable, capsuleIds),
    enabled: !!outcomeVariable && capsuleIds.length > 0,
  });
}

// ============================================================================
// Analytics Summary
// ============================================================================

export function useAnalyticsSummary() {
  return useQuery({
    queryKey: ['analytics-summary'],
    queryFn: analyticsAPI.getAnalyticsSummary,
  });
}

// ============================================================================
// ML Dashboard
// ============================================================================

export function useMLDashboard() {
  return useQuery({
    queryKey: ['ml-dashboard'],
    queryFn: analyticsAPI.getMLDashboard,
  });
}

export function useCalibrationTable() {
  return useQuery({
    queryKey: ['calibration-table'],
    queryFn: analyticsAPI.getCalibrationTable,
  });
}

export function useRecentOutcomes(limit: number = 10) {
  return useQuery({
    queryKey: ['recent-outcomes', limit],
    queryFn: () => analyticsAPI.getRecentOutcomes(limit),
  });
}

export function useTestCalibration(confidence: number | null) {
  return useQuery({
    queryKey: ['test-calibration', confidence],
    queryFn: () => analyticsAPI.testCalibration(confidence!),
    enabled: confidence !== null && confidence >= 0 && confidence <= 1,
  });
}
