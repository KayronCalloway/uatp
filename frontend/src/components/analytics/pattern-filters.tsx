"use client"

import { useState } from "react"
import type { PatternFilters as PatternFiltersType } from "@/types/analytics"
import { Filter } from "lucide-react"

interface PatternFiltersProps {
  filters: PatternFiltersType
  onFiltersChange: (filters: PatternFiltersType) => void
}

const PATTERN_TYPES = [
  { value: "", label: "All Types" },
  { value: "sequence", label: "Sequence" },
  { value: "decision_tree", label: "Decision Tree" },
  { value: "failure_mode", label: "Failure Mode" },
]

const MIN_SUCCESS_RATES = [
  { value: "", label: "Any Success Rate" },
  { value: "0.5", label: "50%+" },
  { value: "0.6", label: "60%+" },
  { value: "0.7", label: "70%+" },
  { value: "0.8", label: "80%+" },
  { value: "0.9", label: "90%+" },
]

export function PatternFilters({
  filters,
  onFiltersChange,
}: PatternFiltersProps) {
  const [patternType, setPatternType] = useState(filters.pattern_type || "")
  const [minSuccessRate, setMinSuccessRate] = useState(
    filters.min_success_rate?.toString() || ""
  )

  const handlePatternTypeChange = (value: string) => {
    setPatternType(value)
    onFiltersChange({
      ...filters,
      pattern_type: value || undefined,
    })
  }

  const handleMinSuccessRateChange = (value: string) => {
    setMinSuccessRate(value)
    onFiltersChange({
      ...filters,
      min_success_rate: value ? parseFloat(value) : undefined,
    })
  }

  const handleReset = () => {
    setPatternType("")
    setMinSuccessRate("")
    onFiltersChange({ limit: filters.limit })
  }

  const hasActiveFilters = patternType || minSuccessRate

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-4">
        <Filter className="h-4 w-4 text-gray-400" />
        <span className="text-sm font-medium text-gray-700">Filters</span>
        {hasActiveFilters && (
          <button
            onClick={handleReset}
            className="ml-auto text-xs text-blue-600 hover:text-blue-700 font-medium"
          >
            Reset
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Pattern Type */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Pattern Type
          </label>
          <select
            value={patternType}
            onChange={(e) => handlePatternTypeChange(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {PATTERN_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Min Success Rate */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Minimum Success Rate
          </label>
          <select
            value={minSuccessRate}
            onChange={(e) => handleMinSuccessRateChange(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {MIN_SUCCESS_RATES.map((rate) => (
              <option key={rate.value} value={rate.value}>
                {rate.label}
              </option>
            ))}
          </select>
        </div>

        {/* Results count */}
        <div className="flex items-end">
          <div className="text-sm text-gray-600">
            {hasActiveFilters && (
              <span className="inline-flex items-center px-2 py-1 rounded-full bg-blue-50 text-blue-700 font-medium">
                {patternType && "Type"}{patternType && minSuccessRate && " + "}
                {minSuccessRate && "Success Rate"}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
