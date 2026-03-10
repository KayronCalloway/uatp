"use client"

import { PatternCard } from "@/components/analytics/pattern-card"
import type { Pattern } from "@/types/analytics"

interface PatternListProps {
  patterns: Pattern[]
}

export function PatternList({ patterns }: PatternListProps) {
  // Sort patterns by success rate (highest first)
  const sortedPatterns = [...patterns].sort(
    (a, b) => b.success_rate - a.success_rate
  )

  return (
    <div className="space-y-4">
      {sortedPatterns.map((pattern) => (
        <PatternCard key={pattern.pattern_id} pattern={pattern} />
      ))}
    </div>
  )
}
