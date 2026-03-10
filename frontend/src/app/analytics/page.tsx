"use client"

import { useAnalyticsSummary, usePatterns, useOutcomeStats } from "@/hooks/useAnalytics"
import { Loader2, TrendingUp, Target, BarChart3, Zap, ArrowRight } from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"

export default function AnalyticsOverviewPage() {
  const { data: summary, isLoading: summaryLoading } = useAnalyticsSummary()
  const { data: patterns, isLoading: patternsLoading } = usePatterns({ limit: 5 })
  const { data: outcomes, isLoading: outcomesLoading } = useOutcomeStats()

  if (summaryLoading && patternsLoading && outcomesLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  return (
    <div className="py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Intelligence Dashboard
          </h2>
          <p className="text-gray-600">
            Overview of learned patterns, outcomes, and quality metrics
          </p>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            label="Total Capsules"
            value={summary?.total_capsules || 0}
            change="+12% this week"
            icon={<Zap className="h-6 w-6" />}
            color="blue"
            href="/capsules"
          />
          <MetricCard
            label="Validated Outcomes"
            value={outcomes?.total_outcomes || summary?.total_outcomes || 0}
            change="Latest insights"
            icon={<Target className="h-6 w-6" />}
            color="green"
            href="/analytics/outcomes"
          />
          <MetricCard
            label="Patterns Discovered"
            value={patterns?.total || summary?.total_patterns || 0}
            change="High success rates"
            icon={<TrendingUp className="h-6 w-6" />}
            color="purple"
            href="/analytics/patterns"
          />
          <MetricCard
            label="Average Quality"
            value={
              outcomes?.average_quality_score
                ? `${(outcomes.average_quality_score * 100).toFixed(0)}%`
                : summary?.average_quality
                ? `${(summary.average_quality * 100).toFixed(0)}%`
                : "N/A"
            }
            change="Quality trending up"
            icon={<BarChart3 className="h-6 w-6" />}
            color="amber"
            href="/analytics/calibration"
          />
        </div>

        {/* Quick Access Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Top Patterns */}
          <QuickAccessCard
            title="Top Performing Patterns"
            description="Most successful reasoning patterns"
            href="/analytics/patterns"
            icon={<TrendingUp className="h-5 w-5" />}
          >
            {patternsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : patterns && patterns.patterns.length > 0 ? (
              <div className="space-y-3">
                {patterns.patterns.slice(0, 3).map((pattern) => (
                  <div
                    key={pattern.pattern_id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 text-sm">
                        {pattern.pattern_name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {pattern.pattern_type.replace("_", " ")} • Used {pattern.usage_count} times
                      </p>
                    </div>
                    <div className="ml-4">
                      <span
                        className={cn(
                          "px-2 py-1 rounded text-xs font-semibold",
                          pattern.success_rate >= 0.8
                            ? "bg-green-100 text-green-700"
                            : pattern.success_rate >= 0.6
                            ? "bg-blue-100 text-blue-700"
                            : "bg-yellow-100 text-yellow-700"
                        )}
                      >
                        {(pattern.success_rate * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 py-4">No patterns discovered yet</p>
            )}
          </QuickAccessCard>

          {/* System Health */}
          <QuickAccessCard
            title="System Intelligence Health"
            description="Key performance indicators"
            href="/analytics/calibration"
            icon={<BarChart3 className="h-5 w-5" />}
          >
            <div className="space-y-4">
              <HealthIndicator
                label="Calibration Quality"
                value={summary?.calibration_ece ? `ECE: ${summary.calibration_ece.toFixed(3)}` : "N/A"}
                status={
                  summary?.calibration_ece
                    ? summary.calibration_ece < 0.1
                      ? "good"
                      : summary.calibration_ece < 0.2
                      ? "fair"
                      : "poor"
                    : "unknown"
                }
              />
              <HealthIndicator
                label="Outcome Coverage"
                value={
                  outcomes?.total_outcomes
                    ? `${outcomes.total_outcomes} validated`
                    : "0 validated"
                }
                status={
                  outcomes?.total_outcomes
                    ? outcomes.total_outcomes > 100
                      ? "good"
                      : outcomes.total_outcomes > 50
                      ? "fair"
                      : "poor"
                    : "unknown"
                }
              />
              <HealthIndicator
                label="Pattern Learning"
                value={
                  patterns?.total
                    ? `${patterns.total} patterns`
                    : "0 patterns"
                }
                status={
                  patterns?.total
                    ? patterns.total > 10
                      ? "good"
                      : patterns.total > 5
                      ? "fair"
                      : "poor"
                    : "unknown"
                }
              />
              <HealthIndicator
                label="Strategies Learned"
                value={summary?.strategies_learned ? `${summary.strategies_learned} strategies` : "N/A"}
                status={
                  summary?.strategies_learned
                    ? summary.strategies_learned > 5
                      ? "good"
                      : summary.strategies_learned > 2
                      ? "fair"
                      : "poor"
                    : "unknown"
                }
              />
            </div>
          </QuickAccessCard>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard
            title="Causal Analysis"
            description="Explore causal relationships between variables"
            href="/analytics/causal"
            icon={<TrendingUp className="h-6 w-6 text-indigo-600" />}
            badge="Advanced"
            badgeColor="indigo"
          />
          <FeatureCard
            title="Quality Trends"
            description="Track quality improvements over time"
            href="/analytics/quality"
            icon={<BarChart3 className="h-6 w-6 text-green-600" />}
            badge="Coming Soon"
            badgeColor="green"
          />
          <FeatureCard
            title="Strategy Library"
            description="Browse proven reasoning strategies"
            href="/analytics/strategies"
            icon={<Target className="h-6 w-6 text-purple-600" />}
            badge="Coming Soon"
            badgeColor="purple"
          />
        </div>
      </div>
    </div>
  )
}

function MetricCard({
  label,
  value,
  change,
  icon,
  color,
  href,
}: {
  label: string
  value: string | number
  change: string
  icon: React.ReactNode
  color: "blue" | "green" | "purple" | "amber"
  href: string
}) {
  const colorClasses = {
    blue: "text-blue-600 bg-blue-50",
    green: "text-green-600 bg-green-50",
    purple: "text-purple-600 bg-purple-50",
    amber: "text-amber-600 bg-amber-50",
  }

  return (
    <Link
      href={href}
      className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-300 hover:shadow-md transition-all"
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-gray-500">{label}</span>
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>{icon}</div>
      </div>
      <p className="text-3xl font-bold text-gray-900 mb-1">{value}</p>
      <p className="text-xs text-gray-500">{change}</p>
    </Link>
  )
}

function QuickAccessCard({
  title,
  description,
  href,
  icon,
  children,
}: {
  title: string
  description: string
  href: string
  icon: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="text-blue-600">{icon}</div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <p className="text-sm text-gray-500">{description}</p>
          </div>
        </div>
        <Link
          href={href}
          className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          View All
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
      {children}
    </div>
  )
}

function HealthIndicator({
  label,
  value,
  status,
}: {
  label: string
  value: string
  status: "good" | "fair" | "poor" | "unknown"
}) {
  const statusColors = {
    good: "bg-green-500",
    fair: "bg-yellow-500",
    poor: "bg-red-500",
    unknown: "bg-gray-300",
  }

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-3">
        <div className={`w-2 h-2 rounded-full ${statusColors[status]}`} />
        <span className="text-sm font-medium text-gray-700">{label}</span>
      </div>
      <span className="text-sm text-gray-600">{value}</span>
    </div>
  )
}

function FeatureCard({
  title,
  description,
  href,
  icon,
  badge,
  badgeColor,
}: {
  title: string
  description: string
  href: string
  icon: React.ReactNode
  badge?: string
  badgeColor?: string
}) {
  const badgeColorClasses = {
    indigo: "bg-indigo-100 text-indigo-700",
    green: "bg-green-100 text-green-700",
    purple: "bg-purple-100 text-purple-700",
  }

  return (
    <Link
      href={href}
      className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-300 hover:shadow-md transition-all"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
        {badge && (
          <span
            className={`px-2 py-1 rounded text-xs font-semibold ${
              badgeColorClasses[badgeColor as keyof typeof badgeColorClasses] ||
              "bg-gray-100 text-gray-700"
            }`}
          >
            {badge}
          </span>
        )}
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </Link>
  )
}
