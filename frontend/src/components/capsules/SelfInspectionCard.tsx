'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  AlertTriangle,
  CheckCircle,
  AlertCircle,
  Info,
  Shield,
} from 'lucide-react';

interface Contradiction {
  category: string;
  severity: 'critical' | 'warning' | 'info';
  description: string;
  recommendation: string;
}

interface SelfInspection {
  contradictions_found: number;
  critical_count?: number;
  warning_count?: number;
  info_count?: number;
  status?: string;
  issues?: Contradiction[];
}

interface SelfInspectionCardProps {
  selfInspection: SelfInspection;
}

export function SelfInspectionCard({ selfInspection }: SelfInspectionCardProps) {
  const hasIssues = selfInspection.contradictions_found > 0;
  const hasCritical = (selfInspection.critical_count || 0) > 0;

  return (
    <Card className={`border-2 ${
      hasCritical ? 'border-red-300 bg-red-50/30' :
      hasIssues ? 'border-yellow-300 bg-yellow-50/30' :
      'border-green-300 bg-green-50/30'
    }`}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>Self-Inspection Results</span>
          </div>
          <Badge
            variant="outline"
            className={`${
              hasCritical ? 'bg-red-100 text-red-800 border-red-300' :
              hasIssues ? 'bg-yellow-100 text-yellow-800 border-yellow-300' :
              'bg-green-100 text-green-800 border-green-300'
            }`}
          >
            {hasCritical ? 'Critical Issues' :
             hasIssues ? 'Warnings Found' :
             'Clean'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-3">
          <div className="bg-white rounded-lg p-3 border">
            <div className="text-xs text-gray-600 mb-1">Total Issues</div>
            <div className="text-2xl font-bold text-gray-900">
              {selfInspection.contradictions_found}
            </div>
          </div>
          <div className="bg-red-50 rounded-lg p-3 border border-red-200">
            <div className="text-xs text-red-600 mb-1">Critical</div>
            <div className="text-2xl font-bold text-red-900">
              {selfInspection.critical_count || 0}
            </div>
          </div>
          <div className="bg-yellow-50 rounded-lg p-3 border border-yellow-200">
            <div className="text-xs text-yellow-600 mb-1">Warnings</div>
            <div className="text-2xl font-bold text-yellow-900">
              {selfInspection.warning_count || 0}
            </div>
          </div>
          <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
            <div className="text-xs text-blue-600 mb-1">Info</div>
            <div className="text-2xl font-bold text-blue-900">
              {selfInspection.info_count || 0}
            </div>
          </div>
        </div>

        {/* Issues List */}
        {selfInspection.issues && selfInspection.issues.length > 0 && (
          <div className="space-y-3">
            <div className="text-sm font-semibold text-gray-700">Detected Issues</div>
            {selfInspection.issues.map((issue, index) => (
              <div
                key={index}
                className={`rounded-lg p-4 border-l-4 ${
                  issue.severity === 'critical'
                    ? 'bg-red-50 border-red-500'
                    : issue.severity === 'warning'
                    ? 'bg-yellow-50 border-yellow-500'
                    : 'bg-blue-50 border-blue-500'
                }`}
              >
                <div className="flex items-start gap-3">
                  {issue.severity === 'critical' ? (
                    <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                  ) : issue.severity === 'warning' ? (
                    <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                  ) : (
                    <Info className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-bold uppercase ${
                        issue.severity === 'critical' ? 'text-red-700' :
                        issue.severity === 'warning' ? 'text-yellow-700' :
                        'text-blue-700'
                      }`}>
                        {issue.category.replace(/_/g, ' ')}
                      </span>
                      <Badge
                        variant="outline"
                        className={`text-xs ${
                          issue.severity === 'critical' ? 'border-red-300 text-red-700' :
                          issue.severity === 'warning' ? 'border-yellow-300 text-yellow-700' :
                          'border-blue-300 text-blue-700'
                        }`}
                      >
                        {issue.severity}
                      </Badge>
                    </div>
                    <p className={`text-sm mb-2 ${
                      issue.severity === 'critical' ? 'text-red-800' :
                      issue.severity === 'warning' ? 'text-yellow-800' :
                      'text-blue-800'
                    }`}>
                      {issue.description}
                    </p>
                    <div className={`text-xs ${
                      issue.severity === 'critical' ? 'text-red-600' :
                      issue.severity === 'warning' ? 'text-yellow-600' :
                      'text-blue-600'
                    }`}>
                      <span className="font-semibold">Recommendation:</span> {issue.recommendation}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Clean Status Message */}
        {selfInspection.status === 'clean' && (
          <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-lg p-4">
            <CheckCircle className="h-6 w-6 text-green-600" />
            <div>
              <div className="text-sm font-semibold text-green-900">No Contradictions Detected</div>
              <div className="text-xs text-green-700">
                This capsule passed all self-inspection checks.
              </div>
            </div>
          </div>
        )}

        {/* What This Means */}
        <div className="text-xs text-gray-500 bg-gray-50 rounded p-3">
          <span className="font-semibold">What is self-inspection?</span>{' '}
          The system checks its own output for contradictions: semantic drift (summary doesn&apos;t
          address the question), quality mismatches (perfect scores with failing grades),
          confidence-evidence gaps (high confidence without evidence), and unearned labels
          (claiming court-admissible without proper verification).
        </div>
      </CardContent>
    </Card>
  );
}
