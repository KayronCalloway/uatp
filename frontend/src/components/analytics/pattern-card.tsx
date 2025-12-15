"use client"

import { useState } from "react"
import type { Pattern } from "@/types/analytics"
import { cn } from "@/lib/utils"
import {
  GitBranch,
  TrendingUp,
  Users,
  Tag,
  ChevronDown,
  ChevronUp,
  ExternalLink,
} from "lucide-react"
import Link from "next/link"

interface PatternCardProps {
  pattern: Pattern
}

const PATTERN_TYPE_CONFIG = {
  sequence: {
    label: "Sequence",
    color: "text-blue-600 bg-blue-50 border-blue-200",
    icon: GitBranch,
  },
  decision_tree: {
    label: "Decision Tree",
    color: "text-indigo-600 bg-indigo-50 border-indigo-200",
    icon: GitBranch,
  },
  failure_mode: {
    label: "Failure Mode",
    color: "text-red-600 bg-red-50 border-red-200",
    icon: GitBranch,
  },
}

export function PatternCard({ pattern }: PatternCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const typeConfig = PATTERN_TYPE_CONFIG[pattern.pattern_type]
  const successPercentage = (pattern.success_rate * 100).toFixed(0)
  const TypeIcon = typeConfig.icon

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:border-gray-300 transition-colors">
      {/* Main content */}
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={cn(
                  "inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold border",
                  typeConfig.color
                )}
              >
                <TypeIcon className="h-3 w-3" />
                {typeConfig.label}
              </span>
              {pattern.confidence_impact && pattern.confidence_impact > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold bg-green-50 text-green-700 border border-green-200">
                  <TrendingUp className="h-3 w-3" />
                  +{(pattern.confidence_impact * 100).toFixed(0)}% confidence
                </span>
              )}
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {pattern.pattern_name}
            </h3>
            <p className="text-sm text-gray-600">{pattern.pattern_description}</p>
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex-shrink-0 p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? (
              <ChevronUp className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronDown className="h-5 w-5 text-gray-400" />
            )}
          </button>
        </div>

        {/* Metrics */}
        <div className="flex items-center gap-6 mb-4">
          {/* Success Rate */}
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-600">Success Rate:</span>
            <span
              className={cn(
                "text-sm font-bold",
                pattern.success_rate >= 0.8
                  ? "text-green-600"
                  : pattern.success_rate >= 0.6
                  ? "text-blue-600"
                  : "text-yellow-600"
              )}
            >
              {successPercentage}%
            </span>
          </div>

          {/* Usage Count */}
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-gray-400" />
            <span className="text-sm text-gray-600">Used:</span>
            <span className="text-sm font-semibold text-gray-900">
              {pattern.usage_count} {pattern.usage_count === 1 ? "time" : "times"}
            </span>
          </div>
        </div>

        {/* Success Rate Bar */}
        <div className="mb-4">
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full transition-all",
                pattern.success_rate >= 0.8
                  ? "bg-green-500"
                  : pattern.success_rate >= 0.6
                  ? "bg-blue-500"
                  : "bg-yellow-500"
              )}
              style={{ width: `${pattern.success_rate * 100}%` }}
            />
          </div>
        </div>

        {/* Domains */}
        {pattern.applicable_domains.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <Tag className="h-3 w-3 text-gray-400" />
            <span className="text-xs text-gray-500">Domains:</span>
            {pattern.applicable_domains.map((domain) => (
              <span
                key={domain}
                className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700"
              >
                {domain}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-gray-200 bg-gray-50 p-6">
          <div className="space-y-4">
            {/* Pattern Structure */}
            {pattern.pattern_structure && (
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">
                  Pattern Structure
                </h4>
                <pre className="text-xs bg-white border border-gray-200 rounded p-3 overflow-x-auto">
                  {JSON.stringify(pattern.pattern_structure, null, 2)}
                </pre>
              </div>
            )}

            {/* Example Capsules */}
            {pattern.example_capsule_ids.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">
                  Example Capsules
                </h4>
                <div className="flex flex-wrap gap-2">
                  {pattern.example_capsule_ids.slice(0, 5).map((capsuleId) => (
                    <Link
                      key={capsuleId}
                      href={`/capsules/${capsuleId}`}
                      className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-white border border-gray-200 hover:border-blue-300 hover:bg-blue-50 text-sm text-gray-700 hover:text-blue-700 transition-colors"
                    >
                      <span className="font-mono text-xs">
                        {capsuleId.slice(0, 8)}...
                      </span>
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  ))}
                  {pattern.example_capsule_ids.length > 5 && (
                    <span className="inline-flex items-center px-3 py-1 rounded-lg bg-gray-100 text-sm text-gray-600">
                      +{pattern.example_capsule_ids.length - 5} more
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>Created: {new Date(pattern.created_at).toLocaleDateString()}</span>
              <span>ID: {pattern.pattern_id.slice(0, 16)}...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
