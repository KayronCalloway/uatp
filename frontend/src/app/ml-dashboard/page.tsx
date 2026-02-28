"use client"

import { useMLDashboard, useRecentOutcomes } from "@/hooks/useAnalytics"
import {
  Loader2,
  Brain,
  Target,
  History,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  XCircle,
  TrendingUp,
  Activity,
} from "lucide-react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  ReferenceLine,
} from "recharts"
import Link from "next/link"

export default function MLDashboardPage() {
  const { data, isLoading, error, refetch } = useMLDashboard()
  const { data: recentOutcomes } = useRecentOutcomes(5)

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading ML Dashboard...</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-800">Failed to load ML dashboard data</p>
            <p className="text-sm text-red-600 mt-2">{String(error)}</p>
          </div>
        </div>
      </div>
    )
  }

  const { calibration, outcomes, historical_accuracy, learning_loop } = data

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Brain className="h-8 w-8 text-purple-600" />
              <h1 className="text-3xl font-bold text-gray-900">
                ML Learning Dashboard
              </h1>
            </div>
            <p className="text-gray-600">
              Monitor confidence calibration, outcome tracking, and historical accuracy learning
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>

        {/* Learning Loop Status */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-600" />
              Learning Loop Status
            </h2>
            <StatusBadge status={learning_loop.status} />
          </div>
          <p className="text-gray-600 mb-4">{learning_loop.description}</p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ComponentStatus
              name="Calibration"
              active={learning_loop.components.calibration}
              description="Platt scaling for confidence adjustment"
            />
            <ComponentStatus
              name="Outcome Tracking"
              active={learning_loop.components.outcome_tracking}
              description="Automatic outcome inference from follow-ups"
            />
            <ComponentStatus
              name="Historical Accuracy"
              active={learning_loop.components.historical_accuracy}
              description="Learning from similar past capsules"
            />
          </div>

          {/* Learning Loop Diagram */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Learning Loop Flow</h3>
            <div className="flex items-center justify-center gap-2 text-sm flex-wrap">
              <FlowStep label="Capsule Created" icon="1" />
              <FlowArrow />
              <FlowStep label="Historical Accuracy" icon="2" active={learning_loop.components.historical_accuracy} />
              <FlowArrow />
              <FlowStep label="Calibration" icon="3" active={learning_loop.components.calibration} />
              <FlowArrow />
              <FlowStep label="Final Confidence" icon="4" />
              <FlowArrow />
              <FlowStep label="Outcome Inferred" icon="5" active={learning_loop.components.outcome_tracking} />
              <FlowArrow />
              <FlowStep label="Updates Calibration" icon="6" />
            </div>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Calibration Section */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
              <TrendingUp className="h-5 w-5 text-green-600" />
              Confidence Calibration
            </h2>

            {calibration.status === "available" && calibration.global_metrics ? (
              <>
                {/* Metrics Summary */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <MetricBox
                    label="Brier Score"
                    value={calibration.global_metrics.brier_score.toFixed(4)}
                    description="Lower is better"
                    good={calibration.global_metrics.brier_score < 0.1}
                  />
                  <MetricBox
                    label="Calibration Error"
                    value={`${(calibration.global_metrics.calibration_error * 100).toFixed(1)}%`}
                    description="Lower is better"
                    good={calibration.global_metrics.calibration_error < 0.1}
                  />
                  <MetricBox
                    label="Sample Size"
                    value={calibration.global_metrics.sample_size.toString()}
                    description="Outcomes tracked"
                  />
                  <MetricBox
                    label="Log Loss"
                    value={calibration.global_metrics.log_loss?.toFixed(4) || "N/A"}
                    description="Lower is better"
                  />
                </div>

                {/* Reliability Diagram */}
                {calibration.reliability_data.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-3">
                      Reliability Diagram
                    </h3>
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart
                        data={calibration.reliability_data}
                        margin={{ top: 20, right: 20, left: 20, bottom: 40 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="bucket"
                          tick={{ fontSize: 12 }}
                          tickFormatter={(value) => `${(parseFloat(value) * 100).toFixed(0)}%`}
                        />
                        <YAxis
                          domain={[0, 1]}
                          tick={{ fontSize: 12 }}
                          tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                        />
                        <Tooltip
                          formatter={(value: number) => [`${(value * 100).toFixed(0)}%`, "Actual Rate"]}
                          labelFormatter={(label) => `Predicted: ${(parseFloat(label) * 100).toFixed(0)}%`}
                        />
                        <Legend wrapperStyle={{ paddingTop: 10 }} />
                        <Bar
                          dataKey="actual"
                          name="Actual Success Rate"
                          fill="#3b82f6"
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                    <p className="text-xs text-gray-500 mt-1 text-center">
                      Bars should match predicted % for perfect calibration (e.g., 80% predicted = 80% actual)
                    </p>
                  </div>
                )}

                {/* Recommendations */}
                {calibration.recommendations.length > 0 && (
                  <div className="mt-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">
                      Recommendations
                    </h3>
                    <ul className="space-y-1">
                      {calibration.recommendations.map((rec, i) => (
                        <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                          <span className="text-blue-500 mt-0.5">•</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                <p>{calibration.error || "Calibration data not available"}</p>
              </div>
            )}
          </div>

          {/* Outcomes Section */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
              <Target className="h-5 w-5 text-blue-600" />
              Outcome Tracking
            </h2>

            {outcomes.status === "available" ? (
              <>
                {/* Stats Summary */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <MetricBox
                    label="Total Outcomes"
                    value={outcomes.total_with_outcomes.toString()}
                    description="Capsules with outcomes"
                  />
                  <MetricBox
                    label="Pending"
                    value={outcomes.pending_count.toString()}
                    description="Awaiting follow-up"
                  />
                  <MetricBox
                    label="Success Rate"
                    value={outcomes.success_rate !== undefined && outcomes.success_rate !== null
                      ? `${(outcomes.success_rate * 100).toFixed(0)}%`
                      : "N/A"
                    }
                    description="Successful outcomes"
                    good={outcomes.success_rate !== undefined && outcomes.success_rate > 0.7}
                  />
                  <MetricBox
                    label="Partial"
                    value={outcomes.by_status.partial?.toString() || "0"}
                    description="Partial outcomes"
                  />
                </div>

                {/* Outcome Pie Chart */}
                {outcomes.by_status_data.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-3">
                      Outcomes by Status
                    </h3>
                    <ResponsiveContainer width="100%" height={200}>
                      <PieChart>
                        <Pie
                          data={outcomes.by_status_data}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, value }) => `${name}: ${value}`}
                          outerRadius={70}
                          fill="#8884d8"
                          dataKey="count"
                          nameKey="status"
                        >
                          {outcomes.by_status_data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Recent Outcomes */}
                {recentOutcomes?.outcomes && recentOutcomes.outcomes.length > 0 && (
                  <div className="mt-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">
                      Recent Outcomes
                    </h3>
                    <div className="space-y-2">
                      {recentOutcomes.outcomes.slice(0, 3).map((outcome: any) => (
                        <div
                          key={outcome.capsule_id}
                          className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded"
                        >
                          <Link
                            href={`/capsules/${outcome.capsule_id}`}
                            className="text-blue-600 hover:underline truncate max-w-[180px]"
                          >
                            {outcome.capsule_id.slice(0, 20)}...
                          </Link>
                          <OutcomeBadge status={outcome.status} />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                <p>{outcomes.error || "Outcome data not available"}</p>
              </div>
            )}
          </div>
        </div>

        {/* Historical Accuracy Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
            <History className="h-5 w-5 text-purple-600" />
            Historical Accuracy Learning
          </h2>

          {historical_accuracy.status === "available" ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Stats */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  Data Summary
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <MetricBox
                    label="Total Capsules"
                    value={historical_accuracy.total_capsules.toString()}
                    description="In database"
                  />
                  <MetricBox
                    label="With Embeddings"
                    value={historical_accuracy.capsules_with_embeddings.toString()}
                    description="Can be compared"
                  />
                  <MetricBox
                    label="With Outcomes"
                    value={historical_accuracy.capsules_with_outcomes.toString()}
                    description="For accuracy calculation"
                  />
                  <MetricBox
                    label="Historical Weight"
                    value={`${(historical_accuracy.historical_weight * 100).toFixed(0)}%`}
                    description="Influence on confidence"
                  />
                </div>
              </div>

              {/* Configuration */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  Configuration
                </h3>
                <div className="space-y-3">
                  <ConfigItem
                    label="Similarity Threshold"
                    value={historical_accuracy.similarity_threshold}
                    description="Minimum cosine similarity"
                  />
                  <ConfigItem
                    label="Max Similar Capsules"
                    value={historical_accuracy.max_similar_capsules}
                    description="Top N considered"
                  />
                  <ConfigItem
                    label="Min Sample Size"
                    value={historical_accuracy.min_sample_size}
                    description="Required for adjustment"
                  />
                </div>

                {/* Outcome Distribution */}
                {Object.keys(historical_accuracy.outcome_distribution).length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-xs font-medium text-gray-500 mb-2">
                      Outcome Distribution
                    </h4>
                    <div className="flex gap-2">
                      {Object.entries(historical_accuracy.outcome_distribution).map(([status, count]) => (
                        <span
                          key={status}
                          className={`px-2 py-1 text-xs rounded ${
                            status === "success" ? "bg-green-100 text-green-800" :
                            status === "partial" ? "bg-amber-100 text-amber-800" :
                            "bg-red-100 text-red-800"
                          }`}
                        >
                          {status}: {count}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="h-8 w-8 mx-auto mb-2" />
              <p>{historical_accuracy.error || "Historical accuracy data not available"}</p>
            </div>
          )}
        </div>

        {/* Navigation Links */}
        <div className="mt-8 flex gap-4">
          <Link
            href="/analytics/outcomes"
            className="text-blue-600 hover:underline text-sm"
          >
            View Detailed Outcomes →
          </Link>
          <Link
            href="/analytics/patterns"
            className="text-blue-600 hover:underline text-sm"
          >
            View Patterns →
          </Link>
        </div>
      </div>
    </div>
  )
}

// Helper Components

function StatusBadge({ status }: { status: string }) {
  const styles = {
    healthy: "bg-green-100 text-green-800",
    partial: "bg-amber-100 text-amber-800",
    unavailable: "bg-red-100 text-red-800",
  }[status] || "bg-gray-100 text-gray-800"

  const icons = {
    healthy: <CheckCircle className="h-4 w-4" />,
    partial: <AlertCircle className="h-4 w-4" />,
    unavailable: <XCircle className="h-4 w-4" />,
  }

  return (
    <span className={`flex items-center gap-1 px-3 py-1 text-sm font-medium rounded-full ${styles}`}>
      {icons[status as keyof typeof icons]}
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

function ComponentStatus({
  name,
  active,
  description,
}: {
  name: string
  active: boolean
  description: string
}) {
  return (
    <div className={`p-4 rounded-lg border ${active ? "bg-green-50 border-green-200" : "bg-gray-50 border-gray-200"}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium text-gray-900">{name}</span>
        {active ? (
          <CheckCircle className="h-5 w-5 text-green-600" />
        ) : (
          <XCircle className="h-5 w-5 text-gray-400" />
        )}
      </div>
      <p className="text-xs text-gray-600">{description}</p>
    </div>
  )
}

function FlowStep({
  label,
  icon,
  active = true,
}: {
  label: string
  icon: string
  active?: boolean
}) {
  return (
    <div className={`flex flex-col items-center ${active ? "" : "opacity-50"}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
        active ? "bg-blue-600 text-white" : "bg-gray-300 text-gray-600"
      }`}>
        {icon}
      </div>
      <span className="text-xs mt-1 text-center max-w-[80px]">{label}</span>
    </div>
  )
}

function FlowArrow() {
  return <span className="text-gray-400">→</span>
}

function MetricBox({
  label,
  value,
  description,
  good,
}: {
  label: string
  value: string
  description: string
  good?: boolean
}) {
  return (
    <div className="p-3 bg-gray-50 rounded-lg">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-xl font-bold ${good === true ? "text-green-600" : good === false ? "text-amber-600" : "text-gray-900"}`}>
        {value}
      </div>
      <div className="text-xs text-gray-400">{description}</div>
    </div>
  )
}

function ConfigItem({
  label,
  value,
  description,
}: {
  label: string
  value: number
  description: string
}) {
  return (
    <div className="flex items-center justify-between text-sm">
      <div>
        <span className="text-gray-900">{label}</span>
        <span className="text-xs text-gray-500 ml-2">({description})</span>
      </div>
      <span className="font-mono text-gray-700">{value}</span>
    </div>
  )
}

function OutcomeBadge({ status }: { status: string }) {
  const styles = {
    success: "bg-green-100 text-green-800",
    partial: "bg-amber-100 text-amber-800",
    failure: "bg-red-100 text-red-800",
  }[status] || "bg-gray-100 text-gray-800"

  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded ${styles}`}>
      {status}
    </span>
  )
}
