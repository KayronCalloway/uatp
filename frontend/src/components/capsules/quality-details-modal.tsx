"use client"

import { useQualityAssessment } from "@/hooks/useAnalytics"
import { Loader2, X, AlertCircle, Lightbulb, CheckCircle2, TrendingUp } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from "recharts"

interface QualityDetailsModalProps {
  capsuleId: string
  isOpen: boolean
  onClose: () => void
}

const DIMENSION_INFO = {
  completeness: {
    label: "Completeness",
    icon: "",
    description: "Are all necessary components present?",
    weight: 25,
  },
  coherence: {
    label: "Coherence",
    icon: "",
    description: "Does the reasoning flow logically?",
    weight: 20,
  },
  evidence_quality: {
    label: "Evidence Quality",
    icon: "",
    description: "How strong is the supporting evidence?",
    weight: 20,
  },
  logical_validity: {
    label: "Logical Validity",
    icon: "",
    description: "Are the logical inferences sound?",
    weight: 20,
  },
  bias_detection: {
    label: "Bias Detection",
    icon: "️",
    description: "Are potential biases identified?",
    weight: 10,
  },
  clarity: {
    label: "Clarity",
    icon: "",
    description: "Is the reasoning clear and understandable?",
    weight: 5,
  },
}

const GRADE_COLORS = {
  A: {
    text: "text-green-700",
    bg: "bg-green-50",
    border: "border-green-300",
    accent: "bg-green-500",
  },
  B: {
    text: "text-blue-700",
    bg: "bg-blue-50",
    border: "border-blue-300",
    accent: "bg-blue-500",
  },
  C: {
    text: "text-yellow-700",
    bg: "bg-yellow-50",
    border: "border-yellow-300",
    accent: "bg-yellow-500",
  },
  D: {
    text: "text-orange-700",
    bg: "bg-orange-50",
    border: "border-orange-300",
    accent: "bg-orange-500",
  },
  F: {
    text: "text-red-700",
    bg: "bg-red-50",
    border: "border-red-300",
    accent: "bg-red-500",
  },
}

export function QualityDetailsModal({
  capsuleId,
  isOpen,
  onClose,
}: QualityDetailsModalProps) {
  const { data: assessment, isLoading, error } = useQualityAssessment(capsuleId)

  if (!isOpen) return null

  // Modal overlay
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-white rounded-lg shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-lg hover:bg-gray-100 transition-colors"
          aria-label="Close modal"
        >
          <X className="h-5 w-5 text-gray-500" />
        </button>

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : error || !assessment ? (
          <div className="flex flex-col items-center justify-center py-20 px-6">
            <AlertCircle className="h-12 w-12 text-red-400 mb-4" />
            <p className="text-gray-600 text-center">
              Failed to load quality assessment
            </p>
          </div>
        ) : (
          <div className="p-8">
            {/* Header */}
            <QualityHeader assessment={assessment} />

            {/* Main content grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
              {/* Left column: Radar chart */}
              <QualityRadarChart assessment={assessment} />

              {/* Right column: Dimension scores */}
              <DimensionScores assessment={assessment} />
            </div>

            {/* Strengths and Weaknesses */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
              <StrengthsList strengths={assessment.strengths} />
              <WeaknessesList weaknesses={assessment.weaknesses} />
            </div>

            {/* Issues */}
            {Object.values(assessment.dimension_scores).some(
              (dim) => dim.issues.length > 0
            ) && <IssuesList assessment={assessment} />}

            {/* Improvement Suggestions */}
            <ImprovementSuggestions assessment={assessment} />
          </div>
        )}
      </div>
    </div>
  )
}

function QualityHeader({ assessment }: { assessment: any }) {
  const grade = assessment.quality_grade
  const colors = GRADE_COLORS[grade]
  const percentage = (assessment.overall_quality * 100).toFixed(0)

  return (
    <div className="flex items-center gap-6">
      {/* Grade badge */}
      <div
        className={cn(
          "flex flex-col items-center justify-center rounded-xl border-4 font-bold w-24 h-24",
          colors.bg,
          colors.border,
          colors.text
        )}
      >
        <span className="text-4xl font-extrabold">{grade}</span>
        <span className="text-xs font-semibold uppercase tracking-tight">
          Quality
        </span>
      </div>

      {/* Score details */}
      <div className="flex-1">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          Quality Assessment
        </h2>
        <div className="flex items-baseline gap-3">
          <span className="text-2xl font-bold text-gray-700">
            {percentage}%
          </span>
          <span className="text-sm text-gray-500">Overall Quality Score</span>
        </div>
      </div>
    </div>
  )
}

function QualityRadarChart({ assessment }: { assessment: any }) {
  // Prepare data for radar chart with error handling
  const radarData = Object.entries(assessment.dimension_scores || {})
    .map(([dimension, score]: [string, any]) => {
      if (!score || typeof score.score !== 'number' || typeof score.max_score !== 'number') {
        return null;
      }
      return {
        dimension: DIMENSION_INFO[dimension as keyof typeof DIMENSION_INFO]?.label || dimension,
        score: Math.min(100, Math.max(0, (score.score / score.max_score) * 100)),
        fullMark: 100,
      };
    })
    .filter(Boolean) as Array<{ dimension: string; score: number; fullMark: number }>;

  // If no valid data, show message
  if (radarData.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Dimension Overview
        </h3>
        <div className="flex items-center justify-center h-[300px] text-gray-500">
          No dimension data available
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-50 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Dimension Overview
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={radarData}>
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: "#6b7280", fontSize: 12 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: "#9ca3af", fontSize: 10 }}
          />
          <Radar
            name="Quality"
            dataKey="score"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.6}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

function DimensionScores({ assessment }: { assessment: any }) {
  const dimensionEntries = Object.entries(assessment.dimension_scores || {}).filter(
    ([_, score]: [string, any]) => score && typeof score.score === 'number' && typeof score.max_score === 'number'
  );

  if (dimensionEntries.length === 0) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Dimension Scores
        </h3>
        <div className="text-sm text-gray-500">No dimension scores available</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Dimension Scores
      </h3>
      {dimensionEntries.map(
        ([dimension, score]: [string, any]) => {
          const info = DIMENSION_INFO[dimension as keyof typeof DIMENSION_INFO]
          const percentage = Math.min(100, Math.max(0, (score.score / score.max_score) * 100))

          return (
            <div key={dimension} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{info?.icon || ""}</span>
                  <span className="text-sm font-medium text-gray-700">
                    {info?.label || dimension}
                  </span>
                  {info?.weight && (
                    <span className="text-xs text-gray-400">
                      ({info.weight}%)
                    </span>
                  )}
                </div>
                <span className="text-sm font-semibold text-gray-900">
                  {score.score.toFixed(1)} / {score.max_score}
                </span>
              </div>
              <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all",
                    percentage >= 90
                      ? "bg-green-500"
                      : percentage >= 75
                      ? "bg-blue-500"
                      : percentage >= 60
                      ? "bg-yellow-500"
                      : percentage >= 40
                      ? "bg-orange-500"
                      : "bg-red-500"
                  )}
                  style={{ width: `${percentage}%` }}
                />
              </div>
              {info?.description && (
                <p className="text-xs text-gray-500">{info.description}</p>
              )}
            </div>
          )
        }
      )}
    </div>
  )
}

function StrengthsList({ strengths }: { strengths: string[] }) {
  if (strengths.length === 0) return null

  return (
    <div className="bg-green-50 rounded-lg p-4 border border-green-200">
      <div className="flex items-center gap-2 mb-3">
        <CheckCircle2 className="h-5 w-5 text-green-600" />
        <h3 className="text-sm font-semibold text-green-900">Strengths</h3>
      </div>
      <ul className="space-y-2">
        {strengths.map((strength, index) => (
          <li key={index} className="text-sm text-green-800 flex items-start gap-2">
            <span className="text-green-600 mt-0.5">•</span>
            <span>{strength}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function WeaknessesList({ weaknesses }: { weaknesses: string[] }) {
  if (weaknesses.length === 0) return null

  return (
    <div className="bg-red-50 rounded-lg p-4 border border-red-200">
      <div className="flex items-center gap-2 mb-3">
        <AlertCircle className="h-5 w-5 text-red-600" />
        <h3 className="text-sm font-semibold text-red-900">Weaknesses</h3>
      </div>
      <ul className="space-y-2">
        {weaknesses.map((weakness, index) => (
          <li key={index} className="text-sm text-red-800 flex items-start gap-2">
            <span className="text-red-600 mt-0.5">•</span>
            <span>{weakness}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function IssuesList({ assessment }: { assessment: any }) {
  const allIssues = Object.entries(assessment.dimension_scores || {}).flatMap(
    ([dimension, score]: [string, any]) => {
      if (!score || !Array.isArray(score.issues)) return [];
      return score.issues.map((issue: string) => ({
        dimension: DIMENSION_INFO[dimension as keyof typeof DIMENSION_INFO]?.label || dimension,
        issue,
      }));
    }
  )

  if (allIssues.length === 0) return null

  return (
    <div className="mt-8 bg-red-50 rounded-lg p-6 border border-red-200">
      <div className="flex items-center gap-2 mb-4">
        <AlertCircle className="h-6 w-6 text-red-600" />
        <h3 className="text-lg font-semibold text-red-900">Issues Found</h3>
      </div>
      <ul className="space-y-3">
        {allIssues.map((item, index) => (
          <li key={index} className="flex items-start gap-3">
            <span className="flex-shrink-0 w-2 h-2 rounded-full bg-red-500 mt-2" />
            <div>
              <span className="text-xs font-semibold text-red-700 uppercase tracking-wide">
                {item.dimension}
              </span>
              <p className="text-sm text-red-800 mt-0.5">{item.issue}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

function ImprovementSuggestions({ assessment }: { assessment: any }) {
  // Collect all suggestions with their dimensions
  const allSuggestions = Object.entries(assessment.dimension_scores || {}).flatMap(
    ([dimension, score]: [string, any]) => {
      if (!score || !Array.isArray(score.suggestions)) return [];
      return score.suggestions.map((suggestion: string) => ({
        dimension: dimension as keyof typeof DIMENSION_INFO,
        dimensionLabel: DIMENSION_INFO[dimension as keyof typeof DIMENSION_INFO]?.label || dimension,
        suggestion,
      }));
    }
  )

  // Sort by improvement priority
  const priorityMap = new Map(assessment.improvement_priority || [])
  const sortedSuggestions = allSuggestions.sort((a, b) => {
    const priorityA = priorityMap.get(a.dimension) || 0
    const priorityB = priorityMap.get(b.dimension) || 0
    return priorityB - priorityA
  })

  if (sortedSuggestions.length === 0) {
    return (
      <div className="mt-8 bg-green-50 rounded-lg p-6 border border-green-200">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-6 w-6 text-green-600" />
          <p className="text-sm font-semibold text-green-900">
            No improvements needed - excellent quality!
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-8 bg-blue-50 rounded-lg p-6 border border-blue-200">
      <div className="flex items-center gap-2 mb-4">
        <Lightbulb className="h-6 w-6 text-blue-600" />
        <h3 className="text-lg font-semibold text-blue-900">
          Improvement Suggestions
        </h3>
        <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">
          Prioritized
        </span>
      </div>
      <ul className="space-y-3">
        {sortedSuggestions.map((item, index) => {
          const priority = priorityMap.get(item.dimension) || 0
          const isHighPriority = index < 3

          return (
            <li key={index} className="flex items-start gap-3">
              <span
                className={cn(
                  "flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold",
                  isHighPriority
                    ? "bg-blue-600 text-white"
                    : "bg-blue-200 text-blue-700"
                )}
              >
                {index + 1}
              </span>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-blue-700 uppercase tracking-wide">
                    {item.dimensionLabel}
                  </span>
                  {isHighPriority && (
                    <span className="flex items-center gap-1 text-xs text-blue-600">
                      <TrendingUp className="h-3 w-3" />
                      High Priority
                    </span>
                  )}
                </div>
                <p className="text-sm text-blue-800">{item.suggestion}</p>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
