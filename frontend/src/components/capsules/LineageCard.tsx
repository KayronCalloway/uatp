'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { GitBranch, Layers, History, Zap, ArrowRight, Package } from 'lucide-react';
import { Lineage } from '@/types/api';

interface LineageCardProps {
  lineage: Lineage;
}

export function LineageCard({ lineage }: LineageCardProps) {
  if (!lineage) {
    return null;
  }

  const {
    generation,
    parent_capsules,
    derivation_method,
    transformation_log
  } = lineage;

  const getDerivationIcon = (method: string) => {
    switch (method.toLowerCase()) {
      case 'direct_creation':
        return <Package className="w-4 h-4" />;
      case 'remix':
      case 'fork':
        return <GitBranch className="w-4 h-4" />;
      case 'merge':
        return <Layers className="w-4 h-4" />;
      default:
        return <Zap className="w-4 h-4" />;
    }
  };

  const getDerivationColor = (method: string) => {
    switch (method.toLowerCase()) {
      case 'direct_creation':
        return 'bg-green-50 border-green-200 text-green-700';
      case 'remix':
        return 'bg-purple-50 border-purple-200 text-purple-700';
      case 'fork':
        return 'bg-blue-50 border-blue-200 text-blue-700';
      case 'merge':
        return 'bg-orange-50 border-orange-200 text-orange-700';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-700';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-purple-600" />
          Provenance & Lineage
          <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded ml-auto">
            UATP v7.0
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Generation & Derivation Method */}
          <div className="grid grid-cols-2 gap-4">
            {/* Generation Badge */}
            <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Layers className="w-4 h-4 text-indigo-600" />
                <span className="text-sm font-medium text-indigo-700">Generation</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-indigo-900">{generation}</span>
                <span className="text-sm text-indigo-600">
                  {generation === 1 ? 'Original' : `${generation}th derived`}
                </span>
              </div>
            </div>

            {/* Derivation Method */}
            <div className={`p-4 border rounded-lg ${getDerivationColor(derivation_method)}`}>
              <div className="flex items-center gap-2 mb-2">
                {getDerivationIcon(derivation_method)}
                <span className="text-sm font-medium">Derivation Method</span>
              </div>
              <div className="text-lg font-bold capitalize">
                {derivation_method.replace(/_/g, ' ')}
              </div>
            </div>
          </div>

          {/* Parent Capsules */}
          {parent_capsules && parent_capsules.length > 0 ? (
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-purple-600" />
                Parent Capsules ({parent_capsules.length})
              </h4>
              <div className="space-y-2">
                {parent_capsules.map((parentId, i) => (
                  <div
                    key={i}
                    className="p-3 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors cursor-pointer"
                    onClick={() => window.location.href = `/capsules/${parentId}`}
                  >
                    <div className="flex items-center gap-2">
                      <ArrowRight className="w-4 h-4 text-purple-600 flex-shrink-0" />
                      <span className="text-sm font-mono text-gray-800 flex-1">
                        {parentId}
                      </span>
                      <span className="text-xs text-purple-600 font-medium">
                        View parent
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2">
                <Package className="w-4 h-4 text-green-600" />
                <div className="text-sm">
                  <span className="font-semibold text-green-900">Original Creation</span>
                  <span className="text-green-700"> - This is a first-generation capsule with no parent capsules</span>
                </div>
              </div>
            </div>
          )}

          {/* Transformation Log */}
          {transformation_log && transformation_log.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <History className="w-4 h-4 text-blue-600" />
                Transformation History ({transformation_log.length})
              </h4>
              <div className="space-y-2">
                {transformation_log.map((entry, i) => (
                  <div
                    key={i}
                    className="relative pl-6 pb-4 border-l-2 border-blue-200 last:pb-0"
                  >
                    {/* Timeline dot */}
                    <div className="absolute left-0 top-0 -translate-x-[9px] w-4 h-4 rounded-full bg-blue-500 border-2 border-white" />

                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="flex items-start justify-between mb-1">
                        <span className="text-sm font-semibold text-blue-900">
                          {entry.operation}
                        </span>
                        <span className="text-xs text-blue-600">
                          {new Date(entry.timestamp).toLocaleString()}
                        </span>
                      </div>
                      {entry.description && (
                        <p className="text-sm text-blue-700">{entry.description}</p>
                      )}
                    </div>
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
