'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Users, DollarSign, Share2, Award, Clock } from 'lucide-react';
import { Attribution } from '@/types/api';
import { isValidCapsuleId } from '@/lib/validation';

interface AttributionCardProps {
  attribution: Attribution;
}

export function AttributionCard({ attribution }: AttributionCardProps) {
  const router = useRouter();

  /**
   * SECURITY: Safe navigation to another capsule.
   * Validates the capsule ID before navigation to prevent open redirect attacks.
   */
  const navigateToCapsule = useCallback((capsuleId: string) => {
    if (!isValidCapsuleId(capsuleId)) {
      console.warn('Invalid capsule ID for navigation');
      return;
    }
    router.push(`/capsules/${capsuleId}`);
  }, [router]);

  if (!attribution || !attribution.contributors || attribution.contributors.length === 0) {
    return null;
  }

  const {
    contributors,
    weights,
    upstream_capsules,
    compensation_rules
  } = attribution;

  // Sort contributors by weight (descending)
  const sortedContributors = [...contributors].sort((a, b) => b.weight - a.weight);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5 text-blue-600" />
          Economic Attribution
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded ml-auto">
            UATP v7.4
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Contributors */}
          <div className="space-y-3">
            <h4 className="font-semibold text-gray-900 flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-600" />
              Contributors ({contributors.length})
            </h4>
            <div className="space-y-2">
              {sortedContributors.map((contributor, i) => (
                <div
                  key={i}
                  className="p-4 border rounded-lg bg-gradient-to-r from-blue-50 to-white"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Award className="w-4 h-4 text-blue-600" />
                        <span className="font-medium text-gray-900">
                          {contributor.agent_id}
                        </span>
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-semibold">
                          {contributor.role}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-gray-600 mt-1">
                        <Clock className="w-3 h-3" />
                        {new Date(contributor.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-blue-600">
                        {(contributor.weight * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">contribution</div>
                    </div>
                  </div>

                  {/* Weight bar */}
                  <div className="relative h-2 bg-blue-100 rounded-full overflow-hidden mt-2">
                    <div
                      className="h-full bg-blue-600 rounded-full transition-all"
                      style={{ width: `${contributor.weight * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Economic Weights Summary */}
          {weights && Object.keys(weights).length > 0 && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <DollarSign className="w-4 h-4 text-green-600" />
                <h4 className="font-semibold text-green-900">Economic Distribution</h4>
              </div>
              <div className="space-y-2">
                {Object.entries(weights).map(([agentId, weight]) => (
                  <div key={agentId} className="flex justify-between items-center text-sm">
                    <span className="text-green-700 font-medium">{agentId}:</span>
                    <span className="font-bold text-green-900">
                      {((weight as number) * 100).toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Compensation Rules */}
          {compensation_rules && (
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <DollarSign className="w-4 h-4 text-purple-600" />
                <h4 className="font-semibold text-purple-900">Compensation Rules</h4>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-purple-700">Distribution Model:</span>
                  <span className="font-semibold text-purple-900 capitalize">
                    {compensation_rules.distribution_model.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-purple-700">Minimum Threshold:</span>
                  <span className="font-semibold text-purple-900">
                    {(compensation_rules.minimum_contribution_threshold * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Upstream Capsules */}
          {upstream_capsules && upstream_capsules.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <Share2 className="w-4 h-4 text-orange-600" />
                Upstream Capsules ({upstream_capsules.length})
              </h4>
              <div className="space-y-2">
                {upstream_capsules.map((capsuleId, i) => (
                  <div
                    key={i}
                    className="p-3 bg-orange-50 border border-orange-200 rounded-lg hover:bg-orange-100 transition-colors cursor-pointer"
                    onClick={() => navigateToCapsule(capsuleId)}
                    onKeyDown={(e) => e.key === 'Enter' && navigateToCapsule(capsuleId)}
                    role="button"
                    tabIndex={0}
                  >
                    <span className="text-sm font-mono text-gray-800">{capsuleId}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
