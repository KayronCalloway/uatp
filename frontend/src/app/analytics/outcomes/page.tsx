"use client"

import { useOutcomeStats, usePendingOutcomes } from "@/hooks/useAnalytics"
import { Loader2, Target, TrendingUp, CheckCircle, Clock } from "lucide-react"
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts"
import Link from "next/link"

const VALIDATION_METHOD_COLORS: Record<string, string> = {
  user_feedback: "#3b82f6", // blue
  automated_test: "#10b981", // green
  peer_review: "#8b5cf6", // purple
  outcome_measurement: "#f59e0b", // amber
  manual_verification: "#ef4444", // red
}

export default function OutcomesPage() {
  const { data: stats, isLoading: statsLoading, error: statsError } = useOutcomeStats()
  const { data: pending, isLoading: pendingLoading } = usePendingOutcomes(10)

  if (statsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  if (statsError || !stats) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-800">Failed to load outcome statistics</p>
          </div>
        </div>
      </div>
    )
  }

  // Prepare pie chart data
  const validationMethodData = Object.entries(stats.outcomes_by_validation_method).map(
    ([method, count]) => ({
      name: method.split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" "),
      value: count,
      color: VALIDATION_METHOD_COLORS[method] || "#6b7280",
    })
  )

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Target className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">
              Outcome Tracking
            </h1>
          </div>
          <p className="text-gray-600">
            Monitor validated outcomes and quality metrics
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            label="Total Outcomes"
            value={stats.total_outcomes}
            icon={<Target className="h-6 w-6" />}
            color="blue"
          />
          <MetricCard
            label="Average Quality"
            value={`${(stats.average_quality_score * 100).toFixed(0)}%`}
            icon={<CheckCircle className="h-6 w-6" />}
            color="green"
          />
          <MetricCard
            label="Patterns Discovered"
            value={stats.total_patterns_discovered}
            icon={<TrendingUp className="h-6 w-6" />}
            color="purple"
          />
          <MetricCard
            label="Pending Validation"
            value={pending?.total || 0}
            icon={<Clock className="h-6 w-6" />}
            color="amber"
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Validation Methods Pie Chart */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Outcomes by Validation Method
            </h3>
            {validationMethodData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={validationMethodData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name}: ${((percent || 0) * 100).toFixed(0)}%`
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {validationMethodData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-gray-500">
                No validation data available
              </div>
            )}
          </div>

          {/* Quality Score Gauge */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Average Quality Score
            </h3>
            <div className="flex items-center justify-center h-[300px]">
              <QualityGauge score={stats.average_quality_score} />
            </div>
          </div>
        </div>

        {/* Pending Outcomes */}
        {pending && pending.pending_capsules.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Pending Validation
              </h3>
              <span className="text-sm text-gray-500">
                {pending.total} capsule{pending.total !== 1 ? "s" : ""} awaiting outcome validation
              </span>
            </div>
            <div className="space-y-3">
              {pending.pending_capsules.slice(0, 5).map((capsule: any) => (
                <Link
                  key={capsule.capsule_id}
                  href={`/capsules/${capsule.capsule_id}`}
                  className="block p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 mb-1">
                        {capsule.query || "Untitled"}
                      </p>
                      <p className="text-sm text-gray-600 line-clamp-1">
                        {capsule.conclusion || "No conclusion"}
                      </p>
                    </div>
                    <div className="ml-4 text-xs text-gray-500">
                      {capsule.domain && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                          {capsule.domain}
                        </span>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
              {pending.total > 5 && (
                <div className="text-center pt-2">
                  <span className="text-sm text-gray-500">
                    + {pending.total - 5} more pending
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function MetricCard({
  label,
  value,
  icon,
  color,
}: {
  label: string
  value: string | number
  icon: React.ReactNode
  color: "blue" | "green" | "purple" | "amber"
}) {
  const colorClasses = {
    blue: "text-blue-600 bg-blue-50",
    green: "text-green-600 bg-green-50",
    purple: "text-purple-600 bg-purple-50",
    amber: "text-amber-600 bg-amber-50",
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-gray-500">{label}</span>
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>{icon}</div>
      </div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  )
}

function QualityGauge({ score }: { score: number }) {
  const percentage = (score * 100).toFixed(0)
  const angle = (score * 180) - 90 // -90 to 90 degrees

  // Determine color based on score
  let color = "#ef4444" // red
  if (score >= 0.8) color = "#10b981" // green
  else if (score >= 0.6) color = "#3b82f6" // blue
  else if (score >= 0.4) color = "#f59e0b" // amber

  return (
    <div className="relative w-64 h-32">
      {/* Background arc */}
      <svg viewBox="0 0 200 100" className="w-full h-full">
        <path
          d="M 10 90 A 80 80 0 0 1 190 90"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="20"
          strokeLinecap="round"
        />
        {/* Colored arc */}
        <path
          d="M 10 90 A 80 80 0 0 1 190 90"
          fill="none"
          stroke={color}
          strokeWidth="20"
          strokeLinecap="round"
          strokeDasharray={`${score * 283} 283`}
        />
        {/* Needle */}
        <line
          x1="100"
          y1="90"
          x2="100"
          y2="30"
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
          transform={`rotate(${angle} 100 90)`}
        />
        <circle cx="100" cy="90" r="5" fill={color} />
      </svg>

      {/* Score text */}
      <div className="absolute inset-0 flex items-end justify-center pb-2">
        <div className="text-center">
          <div className="text-4xl font-bold text-gray-900">{percentage}</div>
          <div className="text-sm text-gray-500">Quality Score</div>
        </div>
      </div>
    </div>
  )
}
