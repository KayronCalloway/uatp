"use client"

import { useState } from "react"
import { usePatterns } from "@/hooks/useAnalytics"
import { PatternFilters } from "@/components/analytics/pattern-filters"
import { PatternList } from "@/components/analytics/pattern-list"
import { Loader2, TrendingUp, BookOpen } from "lucide-react"
import type { PatternFilters as PatternFiltersType } from "@/types/analytics"

export default function PatternsPage() {
  const [filters, setFilters] = useState<PatternFiltersType>({
    limit: 50,
  })

  const { data, isLoading, error } = usePatterns(filters)

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">
              Reasoning Patterns
            </h1>
          </div>
          <p className="text-gray-600">
            Discover successful reasoning patterns learned from validated capsules
          </p>
        </div>

        {/* Stats summary */}
        {data && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <StatCard
              label="Total Patterns"
              value={data.total}
              icon={<BookOpen className="h-5 w-5" />}
            />
            <StatCard
              label="Avg Success Rate"
              value={
                data.patterns.length > 0
                  ? `${(
                      data.patterns.reduce((sum, p) => sum + p.success_rate, 0) /
                      data.patterns.length *
                      100
                    ).toFixed(0)}%`
                  : "N/A"
              }
              icon={<TrendingUp className="h-5 w-5" />}
            />
            <StatCard
              label="Total Applications"
              value={data.patterns.reduce((sum, p) => sum + p.usage_count, 0)}
              icon={<BookOpen className="h-5 w-5" />}
            />
          </div>
        )}

        {/* Filters */}
        <div className="mb-6">
          <PatternFilters filters={filters} onFiltersChange={setFilters} />
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-800">
              Failed to load patterns: {error.message}
            </p>
          </div>
        ) : !data || data.patterns.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No patterns found
            </h3>
            <p className="text-gray-600">
              Patterns will appear here as capsules are validated and analyzed
            </p>
          </div>
        ) : (
          <PatternList patterns={data.patterns} />
        )}
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  icon,
}: {
  label: string
  value: string | number
  icon: React.ReactNode
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-500">{label}</span>
        <div className="text-gray-400">{icon}</div>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  )
}
