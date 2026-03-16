'use client';

import { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { GitBranch, Layers, History, Zap, ArrowRight, ArrowLeft, Package, ChevronDown, ChevronUp, Loader2, Network } from 'lucide-react';
import { Lineage } from '@/types/api';
import { api } from '@/lib/api-client';

interface LineageCardProps {
  lineage: Lineage;
  capsuleId?: string;  // Optional: enables live lineage fetching
}

interface LiveLineageData {
  ancestors: string[];
  descendants: string[];
  lineagePath: string[];
  loading: boolean;
  error: string | null;
}

export function LineageCard({ lineage, capsuleId }: LineageCardProps) {
  const [liveData, setLiveData] = useState<LiveLineageData>({
    ancestors: [],
    descendants: [],
    lineagePath: [],
    loading: false,
    error: null,
  });
  const [showAncestors, setShowAncestors] = useState(true);
  const [showDescendants, setShowDescendants] = useState(true);
  const [showLineagePath, setShowLineagePath] = useState(false);

  // Fetch live lineage data when capsuleId is provided
  useEffect(() => {
    if (!capsuleId) return;

    const fetchLineageData = async () => {
      setLiveData(prev => ({ ...prev, loading: true, error: null }));

      try {
        const [ancestorsRes, descendantsRes, lineageRes] = await Promise.all([
          api.getCapsuleAncestors(capsuleId, 10).catch(() => ({ ancestors: [] })),
          api.getCapsuleDescendants(capsuleId, 10).catch(() => ({ descendants: [] })),
          api.getCapsuleLineage(capsuleId).catch(() => ({ lineage: [] })),
        ]);

        setLiveData({
          ancestors: ancestorsRes.ancestors || [],
          descendants: descendantsRes.descendants || [],
          lineagePath: lineageRes.lineage || [],
          loading: false,
          error: null,
        });
      } catch (err) {
        setLiveData(prev => ({
          ...prev,
          loading: false,
          error: 'Failed to fetch lineage data',
        }));
      }
    };

    fetchLineageData();
  }, [capsuleId]);

  if (!lineage && !capsuleId) {
    return null;
  }

  const {
    generation = 1,
    parent_capsules = [],
    derivation_method = 'direct_creation',
    transformation_log = []
  } = lineage || {};

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

  const navigateToCapsule = (id: string) => {
    window.location.href = `/capsules/${id}`;
  };

  const hasLiveData = liveData.ancestors.length > 0 || liveData.descendants.length > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-purple-600" />
          Provenance & Lineage
          {liveData.loading && <Loader2 className="w-4 h-4 animate-spin text-purple-400" />}
          <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded ml-auto">
            UATP v7.4
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

          {/* Live Lineage Path */}
          {liveData.lineagePath.length > 1 && (
            <div className="space-y-3">
              <button
                onClick={() => setShowLineagePath(!showLineagePath)}
                className="w-full flex items-center justify-between text-left"
              >
                <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                  <Network className="w-4 h-4 text-indigo-600" />
                  Lineage Path ({liveData.lineagePath.length} capsules)
                </h4>
                {showLineagePath ? (
                  <ChevronUp className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                )}
              </button>

              {showLineagePath && (
                <div className="flex flex-wrap items-center gap-2 p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
                  {liveData.lineagePath.map((id, i) => (
                    <div key={id} className="flex items-center gap-2">
                      <button
                        onClick={() => navigateToCapsule(id)}
                        className={`px-2 py-1 text-xs font-mono rounded transition-colors ${
                          id === capsuleId
                            ? 'bg-indigo-600 text-white'
                            : 'bg-white border border-indigo-300 text-indigo-700 hover:bg-indigo-100'
                        }`}
                      >
                        {id.length > 12 ? `${id.slice(0, 6)}...${id.slice(-4)}` : id}
                      </button>
                      {i < liveData.lineagePath.length - 1 && (
                        <ArrowRight className="w-3 h-3 text-indigo-400" />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Live Ancestors (from API) */}
          {capsuleId && (
            <div className="space-y-3">
              <button
                onClick={() => setShowAncestors(!showAncestors)}
                className="w-full flex items-center justify-between text-left"
              >
                <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                  <ArrowLeft className="w-4 h-4 text-amber-600" />
                  Ancestors ({liveData.ancestors.length})
                  {liveData.loading && <Loader2 className="w-3 h-3 animate-spin" />}
                </h4>
                {showAncestors ? (
                  <ChevronUp className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                )}
              </button>

              {showAncestors && (
                <>
                  {liveData.ancestors.length > 0 ? (
                    <div className="space-y-2">
                      {liveData.ancestors.map((ancestorId, i) => (
                        <div
                          key={i}
                          className="p-3 bg-amber-50 border border-amber-200 rounded-lg hover:bg-amber-100 transition-colors cursor-pointer"
                          onClick={() => navigateToCapsule(ancestorId)}
                        >
                          <div className="flex items-center gap-2">
                            <ArrowLeft className="w-4 h-4 text-amber-600 flex-shrink-0" />
                            <span className="text-sm font-mono text-gray-800 flex-1">
                              {ancestorId}
                            </span>
                            <span className="text-xs text-amber-600 font-medium">
                              Gen -{i + 1}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
                      {liveData.loading ? 'Loading ancestors...' : 'No ancestors found (genesis capsule)'}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Live Descendants (from API) */}
          {capsuleId && (
            <div className="space-y-3">
              <button
                onClick={() => setShowDescendants(!showDescendants)}
                className="w-full flex items-center justify-between text-left"
              >
                <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                  <ArrowRight className="w-4 h-4 text-emerald-600" />
                  Descendants ({liveData.descendants.length})
                  {liveData.loading && <Loader2 className="w-3 h-3 animate-spin" />}
                </h4>
                {showDescendants ? (
                  <ChevronUp className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                )}
              </button>

              {showDescendants && (
                <>
                  {liveData.descendants.length > 0 ? (
                    <div className="space-y-2">
                      {liveData.descendants.map((descendantId, i) => (
                        <div
                          key={i}
                          className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors cursor-pointer"
                          onClick={() => navigateToCapsule(descendantId)}
                        >
                          <div className="flex items-center gap-2">
                            <ArrowRight className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                            <span className="text-sm font-mono text-gray-800 flex-1">
                              {descendantId}
                            </span>
                            <span className="text-xs text-emerald-600 font-medium">
                              Gen +{i + 1}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600">
                      {liveData.loading ? 'Loading descendants...' : 'No descendants yet'}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Parent Capsules (from payload) */}
          {parent_capsules && parent_capsules.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-purple-600" />
                Parent Capsules ({parent_capsules.length})
                <span className="text-xs text-gray-500 font-normal">(from payload)</span>
              </h4>
              <div className="space-y-2">
                {parent_capsules.map((parentId, i) => (
                  <div
                    key={i}
                    className="p-3 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors cursor-pointer"
                    onClick={() => navigateToCapsule(parentId)}
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
          )}

          {/* Original Creation Badge (when no parents and no ancestors) */}
          {(!parent_capsules || parent_capsules.length === 0) &&
           liveData.ancestors.length === 0 &&
           !liveData.loading && (
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

          {/* Error Display */}
          {liveData.error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {liveData.error}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
