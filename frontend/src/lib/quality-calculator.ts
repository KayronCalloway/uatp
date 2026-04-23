/**
 * Quality Assessment Calculator
 * Calculates quality scores from capsule data using uncertainty, trust, and reasoning metrics
 */

import type { QualityAssessment, QualityScore } from '@/types/analytics'
import type { AnyCapsule } from '@/types/api'

interface UncertaintyAnalysis {
  epistemic_uncertainty?: number
  aleatoric_uncertainty?: number
  total_uncertainty?: number
  risk_score?: number
  confidence_interval?: [number, number]
}

interface CriticalPathAnalysis {
  critical_steps?: any[]
  bottlenecks?: any[]
  decision_points?: any[]
  estimated_impact?: number
}

/**
 * Calculate quality assessment from capsule data
 */
export function calculateQualityFromCapsule(capsule: AnyCapsule): QualityAssessment {
  const payload = (capsule.payload || capsule.metadata || {}) as Record<string, any>
  const verification = capsule.verification || {}
  const reasoning_steps = (payload.reasoning_steps || []) as any[]

  // Extract metadata
  const uncertainty: UncertaintyAnalysis = payload.uncertainty_analysis || {}
  const criticalPath: CriticalPathAnalysis = payload.critical_path_analysis || {}
  const trustScore = verification.trust_score || capsule.trust_score || 0.7
  const improvementRecs = payload.improvement_recommendations || []

  // Calculate dimension scores
  const completeness = calculateCompleteness(reasoning_steps, payload, criticalPath)
  const coherence = calculateCoherence(reasoning_steps, trustScore)
  const evidenceQuality = calculateEvidenceQuality(reasoning_steps, trustScore)
  const logicalValidity = calculateLogicalValidity(uncertainty, trustScore)
  const biasDetection = calculateBiasDetection(improvementRecs, payload)
  const clarity = calculateClarity(reasoning_steps, payload)

  const dimensionScores: Record<string, QualityScore> = {
    completeness,
    coherence,
    evidence_quality: evidenceQuality,
    logical_validity: logicalValidity,
    bias_detection: biasDetection,
    clarity,
  }

  // Calculate weighted overall quality
  const weights = {
    completeness: 0.25,
    coherence: 0.20,
    evidence_quality: 0.20,
    logical_validity: 0.20,
    bias_detection: 0.10,
    clarity: 0.05,
  }

  const overallQuality = Object.entries(dimensionScores).reduce(
    (sum, [dimension, score]) => {
      const weight = weights[dimension as keyof typeof weights] || 0
      const normalizedScore = score.score / score.max_score
      return sum + normalizedScore * weight
    },
    0
  )

  // Convert to grade
  const qualityGrade = scoreToGrade(overallQuality)

  // Identify strengths and weaknesses
  const { strengths, weaknesses } = identifyStrengthsWeaknesses(dimensionScores)

  // Calculate improvement priorities
  const improvementPriority = calculateImprovementPriority(dimensionScores, weights)

  return {
    overall_quality: overallQuality,
    quality_grade: qualityGrade,
    dimension_scores: dimensionScores,
    strengths,
    weaknesses,
    improvement_priority: improvementPriority,
  }
}

/**
 * Calculate completeness score based on reasoning structure
 */
function calculateCompleteness(
  reasoningSteps: any[],
  payload: any,
  criticalPath: CriticalPathAnalysis
): QualityScore {
  const issues: string[] = []
  const suggestions: string[] = []

  let score = 10

  // Check for reasoning steps
  if (reasoningSteps.length === 0) {
    score -= 4
    issues.push('No reasoning steps provided')
    suggestions.push('Include step-by-step reasoning trace')
  } else if (reasoningSteps.length < 3) {
    score -= 2
    issues.push('Very brief reasoning (less than 3 steps)')
    suggestions.push('Provide more detailed reasoning steps')
  }

  // Check for final answer/conclusion
  if (!payload.final_answer && !payload.conclusion && !payload.response) {
    score -= 2
    issues.push('Missing final answer or conclusion')
    suggestions.push('Include explicit final answer')
  }

  // Check for critical path analysis
  if (!criticalPath.critical_steps || criticalPath.critical_steps.length === 0) {
    score -= 1
    suggestions.push('Add critical path analysis')
  }

  // Check for improvement recommendations
  if (!payload.improvement_recommendations || payload.improvement_recommendations.length === 0) {
    score -= 1
    suggestions.push('Include improvement recommendations')
  }

  return {
    dimension: 'completeness',
    score: Math.max(0, score),
    max_score: 10,
    issues,
    suggestions,
  }
}

/**
 * Calculate coherence based on reasoning flow and trust
 */
function calculateCoherence(reasoningSteps: any[], trustScore: number): QualityScore {
  const issues: string[] = []
  const suggestions: string[] = []

  let score = 10

  // Base score on trust (trust reflects overall consistency)
  if (trustScore < 0.5) {
    score -= 4
    issues.push('Low trust score indicates inconsistencies')
  } else if (trustScore < 0.7) {
    score -= 2
    issues.push('Moderate trust score')
  }

  // Check reasoning step coherence (if steps have confidence)
  if (reasoningSteps.length > 0) {
    const confidences = reasoningSteps
      .map((step) => step.confidence)
      .filter((c) => typeof c === 'number')

    if (confidences.length > 1) {
      // Check for large confidence drops (incoherence indicator)
      for (let i = 1; i < confidences.length; i++) {
        if (confidences[i - 1] - confidences[i] > 0.3) {
          score -= 1
          issues.push('Large confidence drop between reasoning steps')
          break
        }
      }
    }
  }

  if (score < 8) {
    suggestions.push('Review reasoning flow for consistency')
  }

  return {
    dimension: 'coherence',
    score: Math.max(0, score),
    max_score: 10,
    issues,
    suggestions,
  }
}

/**
 * Calculate evidence quality based on reasoning steps and trust
 */
function calculateEvidenceQuality(reasoningSteps: any[], trustScore: number): QualityScore {
  const issues: string[] = []
  const suggestions: string[] = []

  let score = 10

  // Base score on trust
  if (trustScore < 0.6) {
    score -= 3
    issues.push('Low trust score affects evidence credibility')
  }

  // Check if reasoning steps have evidence/support
  if (reasoningSteps.length > 0) {
    const stepsWithEvidence = reasoningSteps.filter(
      (step) =>
        step.evidence || step.support || step.references || (step.reasoning && step.reasoning.length > 50)
    )

    const evidenceRatio = stepsWithEvidence.length / reasoningSteps.length

    if (evidenceRatio < 0.3) {
      score -= 3
      issues.push('Few reasoning steps include supporting evidence')
      suggestions.push('Provide more supporting evidence for claims')
    } else if (evidenceRatio < 0.6) {
      score -= 1
      suggestions.push('Consider adding more supporting evidence')
    }
  }

  return {
    dimension: 'evidence_quality',
    score: Math.max(0, score),
    max_score: 10,
    issues,
    suggestions,
  }
}

/**
 * Calculate logical validity based on uncertainty and trust
 */
function calculateLogicalValidity(uncertainty: UncertaintyAnalysis, trustScore: number): QualityScore {
  const issues: string[] = []
  const suggestions: string[] = []

  let score = 10

  // High uncertainty indicates potential logical issues
  if (uncertainty.total_uncertainty !== undefined) {
    if (uncertainty.total_uncertainty > 0.5) {
      score -= 2
      issues.push('High total uncertainty')
      suggestions.push('Reduce epistemic uncertainty through additional evidence')
    } else if (uncertainty.total_uncertainty > 0.3) {
      score -= 1
    }
  }

  // High epistemic uncertainty specifically indicates knowledge gaps
  if (uncertainty.epistemic_uncertainty !== undefined && uncertainty.epistemic_uncertainty > 0.4) {
    issues.push('High epistemic uncertainty (knowledge gaps)')
  }

  // Risk score indicates potential logical flaws
  if (uncertainty.risk_score !== undefined && uncertainty.risk_score > 0.5) {
    score -= 1
    issues.push('Elevated risk score')
  }

  // Trust score reflects logical soundness
  if (trustScore < 0.7) {
    score -= 1
  }

  return {
    dimension: 'logical_validity',
    score: Math.max(0, score),
    max_score: 10,
    issues,
    suggestions,
  }
}

/**
 * Calculate bias detection - looks for signs of balanced vs. biased reasoning
 */
function calculateBiasDetection(improvementRecs: any[], payload: any): QualityScore {
  const issues: string[] = []
  const suggestions: string[] = []

  let score = 10

  // Look for indicators of GOOD bias awareness (positive signs)
  const hasAlternatives = payload.alternatives || payload.alternative_approaches
  const hasUncertaintyAnalysis = payload.uncertainty_analysis
  const hasCaveats = JSON.stringify(payload).match(/however|although|but|caveat|limitation|trade-?off/gi)
  const hasQualifiers = JSON.stringify(payload).match(/might|may|could|possibly|potentially|likely/gi)

  // Check reasoning steps for balanced thinking
  const reasoningSteps = payload.reasoning_steps || []
  const hasMultiplePerspectives = reasoningSteps.some((step: any) => {
    const content = JSON.stringify(step).toLowerCase()
    return content.includes('alternative') ||
           content.includes('another approach') ||
           content.includes('different perspective') ||
           content.includes('trade-off') ||
           content.includes('pros and cons')
  })

  // Look for signs of UNEXAMINED assumptions (negative signs)
  const hasStrongAssertions = JSON.stringify(payload).match(/obviously|clearly|certainly|undoubtedly|always|never/gi)
  const strongAssertionCount = hasStrongAssertions ? hasStrongAssertions.length : 0

  // Check for one-sided reasoning
  const hasOnlyOneApproach = reasoningSteps.length > 0 && !hasMultiplePerspectives && !hasAlternatives

  // Scoring logic: Start neutral, adjust based on evidence

  // POSITIVE indicators (show bias awareness)
  let positiveScore = 0
  if (hasAlternatives) positiveScore += 2
  if (hasMultiplePerspectives) positiveScore += 2
  if (hasCaveats && hasCaveats.length >= 2) positiveScore += 1
  if (hasQualifiers && hasQualifiers.length >= 3) positiveScore += 1
  if (hasUncertaintyAnalysis) positiveScore += 1

  // NEGATIVE indicators (show potential bias)
  let negativeScore = 0
  if (strongAssertionCount > 5) {
    negativeScore += 2
    issues.push('Many strong assertions without caveats')
    suggestions.push('Qualify strong claims with evidence or acknowledge limitations')
  }
  if (hasOnlyOneApproach && reasoningSteps.length > 3) {
    negativeScore += 2
    issues.push('Single approach considered without exploring alternatives')
    suggestions.push('Consider alternative approaches or perspectives')
  }

  // Final score: 8 base (neutral) + positives - negatives
  score = 8 + positiveScore - negativeScore
  score = Math.min(10, Math.max(0, score))

  // Add suggestions if score is low
  if (score < 7 && !hasAlternatives) {
    suggestions.push('Explicitly consider alternative viewpoints or approaches')
  }
  if (score < 7 && strongAssertionCount > 3) {
    suggestions.push('Use more qualified language to acknowledge uncertainty')
  }

  return {
    dimension: 'bias_detection',
    score: Math.max(0, score),
    max_score: 10,
    issues,
    suggestions,
  }
}

/**
 * Calculate clarity based on reasoning steps
 */
function calculateClarity(reasoningSteps: any[], payload: any): QualityScore {
  const issues: string[] = []
  const suggestions: string[] = []

  let score = 10

  // Check reasoning step descriptions
  if (reasoningSteps.length > 0) {
    const stepsWithDescriptions = reasoningSteps.filter(
      (step) => step.reasoning && step.reasoning.length > 20
    )

    if (stepsWithDescriptions.length === 0) {
      score -= 3
      issues.push('Reasoning steps lack clear descriptions')
      suggestions.push('Add clearer descriptions to reasoning steps')
    } else if (stepsWithDescriptions.length < reasoningSteps.length / 2) {
      score -= 1
      suggestions.push('Some steps could be clearer')
    }
  }

  return {
    dimension: 'clarity',
    score: Math.max(0, score),
    max_score: 10,
    issues,
    suggestions,
  }
}

/**
 * Convert numeric score (0-1) to letter grade
 */
function scoreToGrade(score: number): 'A' | 'B' | 'C' | 'D' | 'F' {
  if (score >= 0.9) return 'A'
  if (score >= 0.8) return 'B'
  if (score >= 0.7) return 'C'
  if (score >= 0.6) return 'D'
  return 'F'
}

/**
 * Identify strengths and weaknesses from dimension scores
 */
function identifyStrengthsWeaknesses(
  dimensionScores: Record<string, QualityScore>
): {
  strengths: string[]
  weaknesses: string[]
} {
  const strengths: string[] = []
  const weaknesses: string[] = []

  const dimensionNames = {
    completeness: 'Completeness',
    coherence: 'Coherence',
    evidence_quality: 'Evidence Quality',
    logical_validity: 'Logical Validity',
    bias_detection: 'Bias Detection',
    clarity: 'Clarity',
  }

  Object.entries(dimensionScores).forEach(([dimension, score]) => {
    const percentage = (score.score / score.max_score) * 100
    const name = dimensionNames[dimension as keyof typeof dimensionNames] || dimension

    if (percentage >= 90) {
      strengths.push(`Strong ${name.toLowerCase()} (${percentage.toFixed(0)}%)`)
    } else if (percentage < 70) {
      weaknesses.push(`Weak ${name.toLowerCase()} (${percentage.toFixed(0)}%)`)
    }
  })

  return { strengths, weaknesses }
}

/**
 * Calculate improvement priorities based on dimension scores and weights
 */
function calculateImprovementPriority(
  dimensionScores: Record<string, QualityScore>,
  weights: Record<string, number>
): [string, number][] {
  const priorities: [string, number][] = Object.entries(dimensionScores)
    .map(([dimension, score]) => {
      const normalizedScore = score.score / score.max_score
      const weight = weights[dimension as keyof typeof weights] || 0
      // Priority = impact (weight) * improvement potential (1 - score)
      const priority = weight * (1 - normalizedScore)
      return [dimension, priority] as [string, number]
    })
    .sort((a, b) => b[1] - a[1]) // Sort by priority descending

  return priorities
}
