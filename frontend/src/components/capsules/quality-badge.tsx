"use client"

import { useQualityAssessment } from "@/hooks/useAnalytics"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface QualityBadgeProps {
  capsuleId: string
  size?: "sm" | "md" | "lg"
  showLabel?: boolean
  onClick?: () => void
  className?: string
}

const GRADE_COLORS = {
  A: {
    text: "text-green-700",
    bg: "bg-green-50",
    border: "border-green-300",
    ring: "ring-green-200",
  },
  B: {
    text: "text-blue-700",
    bg: "bg-blue-50",
    border: "border-blue-300",
    ring: "ring-blue-200",
  },
  C: {
    text: "text-yellow-700",
    bg: "bg-yellow-50",
    border: "border-yellow-300",
    ring: "ring-yellow-200",
  },
  D: {
    text: "text-orange-700",
    bg: "bg-orange-50",
    border: "border-orange-300",
    ring: "ring-orange-200",
  },
  F: {
    text: "text-red-700",
    bg: "bg-red-50",
    border: "border-red-300",
    ring: "ring-red-200",
  },
}

const SIZE_CLASSES = {
  sm: {
    container: "w-12 h-12",
    grade: "text-lg",
    label: "text-[10px]",
  },
  md: {
    container: "w-16 h-16",
    grade: "text-2xl",
    label: "text-xs",
  },
  lg: {
    container: "w-20 h-20",
    grade: "text-3xl",
    label: "text-sm",
  },
}

export function QualityBadge({
  capsuleId,
  size = "md",
  showLabel = true,
  onClick,
  className,
}: QualityBadgeProps) {
  const { data: assessment, isLoading, error } = useQualityAssessment(capsuleId)

  if (isLoading) {
    return (
      <div
        className={cn(
          "flex items-center justify-center rounded-lg border-2 border-gray-200 bg-gray-50",
          SIZE_CLASSES[size].container,
          className
        )}
      >
        <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
      </div>
    )
  }

  if (error || !assessment) {
    return (
      <div
        className={cn(
          "flex items-center justify-center rounded-lg border-2 border-gray-200 bg-gray-50",
          SIZE_CLASSES[size].container,
          className
        )}
        title="Quality assessment unavailable"
      >
        <span className="text-gray-400 text-sm">?</span>
      </div>
    )
  }

  const grade = assessment.quality_grade
  const colors = GRADE_COLORS[grade]
  const sizeClasses = SIZE_CLASSES[size]

  // Pulse animation for low grades
  const shouldPulse = grade === "D" || grade === "F"

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border-2 font-bold cursor-pointer transition-all",
        "hover:scale-105 hover:shadow-md",
        colors.bg,
        colors.border,
        colors.text,
        sizeClasses.container,
        shouldPulse && "animate-pulse",
        onClick && "hover:ring-4",
        onClick && colors.ring,
        className
      )}
      onClick={(e) => {
        e.stopPropagation()
        onClick?.()
      }}
      title={`Quality: ${(assessment.overall_quality * 100).toFixed(0)}% (Click for details)`}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.stopPropagation()
          onClick?.()
        }
      }}
    >
      <span className={cn("font-extrabold", sizeClasses.grade)}>{grade}</span>
      {showLabel && (
        <span className={cn("font-semibold uppercase tracking-tight", sizeClasses.label)}>
          Quality
        </span>
      )}
    </div>
  )
}

// Inline variant for displaying in lists
export function QualityBadgeInline({
  capsuleId,
  onClick,
}: {
  capsuleId: string
  onClick?: () => void
}) {
  const { data: assessment, isLoading } = useQualityAssessment(capsuleId)

  if (isLoading) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-gray-100 text-gray-600 text-xs font-medium">
        <Loader2 className="h-3 w-3 animate-spin" />
        <span>Quality</span>
      </span>
    )
  }

  if (!assessment) {
    return null
  }

  const grade = assessment.quality_grade
  const colors = GRADE_COLORS[grade]

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold cursor-pointer",
        "hover:ring-2 transition-all",
        colors.bg,
        colors.text,
        colors.border,
        "border",
        onClick && colors.ring
      )}
      onClick={(e) => {
        e.stopPropagation()
        onClick?.()
      }}
      title={`Quality: ${(assessment.overall_quality * 100).toFixed(0)}%`}
    >
      <span className="font-extrabold">{grade}</span>
      <span className="font-normal">Quality</span>
    </span>
  )
}
