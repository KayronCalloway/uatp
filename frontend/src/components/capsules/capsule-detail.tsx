'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  ArrowLeft, 
  Shield, 
  Clock, 
  User, 
  Database, 
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  AlertCircle,
  Copy,
  RefreshCw
} from 'lucide-react';
import { formatDate, getCapsuleTypeColor, truncateText } from '@/lib/utils';
import { AnyCapsule, GetCapsuleQuery } from '@/types/api';

interface CapsuleDetailProps {
  capsuleId: string;
  onBack?: () => void;
}

export function CapsuleDetail({ capsuleId, onBack }: CapsuleDetailProps) {
  const [includeRaw, setIncludeRaw] = useState(false);
  const [showRawData, setShowRawData] = useState(false);

  const queryParams: GetCapsuleQuery = {
    include_raw: includeRaw,
  };

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['capsule', capsuleId, queryParams],
    queryFn: () => api.getCapsule(capsuleId, queryParams),
    enabled: !!capsuleId,
  });

  const { data: verificationData, isLoading: verificationLoading } = useQuery({
    queryKey: ['capsule-verification', capsuleId],
    queryFn: () => api.verifyCapsule(capsuleId),
    enabled: !!capsuleId,
  });

  const capsule = data?.capsule;
  const rawData = data?.raw_data;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (error) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="flex items-center justify-center text-red-600">
            <p>Error loading capsule: {error.message}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!capsule) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="text-center text-gray-500">
            Capsule not found
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {onBack && (
                <Button variant="ghost" size="sm" onClick={onBack}>
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              )}
              <div>
                <CardTitle className="flex items-center space-x-2">
                  <Database className="h-5 w-5" />
                  <span>Capsule Details</span>
                </CardTitle>
                <p className="text-sm text-gray-500 mt-1">
                  {truncateText(capsule.capsule_id || capsule.id, 40)}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIncludeRaw(!includeRaw)}
              >
                {includeRaw ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
                {includeRaw ? 'Hide Raw' : 'Show Raw'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Basic Info */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Type</label>
              <div className="mt-1">
                <span className={`px-2 py-1 text-sm font-medium rounded-full ${getCapsuleTypeColor(capsule.type)}`}>
                  {capsule.type}
                </span>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">ID</label>
              <div className="mt-1 flex items-center space-x-2">
                <span className="text-sm font-mono">{capsule.capsule_id || capsule.id}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(capsule.capsule_id || capsule.id)}
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Agent</label>
              <div className="mt-1 flex items-center space-x-2">
                <User className="h-4 w-4 text-gray-400" />
                <span className="text-sm">{capsule.agent_id || capsule.payload?.agent_id || 'Unknown'}</span>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Timestamp</label>
              <div className="mt-1 flex items-center space-x-2">
                <Clock className="h-4 w-4 text-gray-400" />
                <span className="text-sm">{formatDate(capsule.timestamp)}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Verification Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>Verification Status</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {verificationLoading ? (
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span className="text-sm">Verifying...</span>
            </div>
          ) : verificationData ? (
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                {verificationData.verified ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-600" />
                )}
                <span className={`text-sm font-medium ${verificationData.verified ? 'text-green-600' : 'text-red-600'}`}>
                  {verificationData.verified ? 'Verified' : 'Not Verified'}
                </span>
                {verificationData.from_cache && (
                  <span className="text-xs text-gray-500">(cached)</span>
                )}
              </div>

              {verificationData.verification_error && (
                <div className="flex items-start space-x-2 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>{verificationData.verification_error}</span>
                </div>
              )}

              {verificationData.message && (
                <div className="text-sm text-gray-600">
                  {verificationData.message}
                </div>
              )}

              {verificationData.metadata_has_verify_key !== null && (
                <div className="text-sm text-gray-600">
                  Metadata has verify key: {verificationData.metadata_has_verify_key ? 'Yes' : 'No'}
                </div>
              )}
            </div>
          ) : capsule.verification?.message ? (
            <div className="text-sm text-gray-600">
              {capsule.verification.message}
            </div>
          ) : (
            <div className="text-sm text-gray-500">
              Verification data not available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Content */}
      <Card>
        <CardHeader>
          <CardTitle>Content</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 p-4 rounded-lg">
            {(capsule.content || capsule.payload?.content) ? (
              <pre className="text-sm whitespace-pre-wrap">{capsule.content || capsule.payload?.content}</pre>
            ) : (capsule.payload?.reasoning_steps?.length > 0 || capsule.reasoning_trace?.reasoning_steps?.length > 0) ? (
              <div className="space-y-4">
                {(capsule.payload?.reasoning_steps || capsule.reasoning_trace?.reasoning_steps || []).map((step: any, index: number) => (
                  <div key={index} className="border-l-4 border-blue-500 pl-4 space-y-2">
                    {/* Step header with confidence */}
                    <div className="text-xs text-gray-500">
                      <div className="flex items-center justify-between">
                        <span>
                          Step {step.step_id || index + 1}: {step.operation || 'reasoning'}
                        </span>
                        {step.confidence !== undefined && step.confidence !== null && (
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            step.confidence >= 0.9 ? 'bg-green-100 text-green-800' :
                            step.confidence >= 0.7 ? 'bg-blue-100 text-blue-800' :
                            step.confidence >= 0.5 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {(step.confidence * 100).toFixed(1)}% confidence
                          </span>
                        )}
                      </div>
                      {step.confidence_basis && (
                        <div className="mt-1 text-xs text-gray-600">
                          <span className="font-medium">Basis:</span> {step.confidence_basis}
                        </div>
                      )}
                    </div>

                    {/* Step reasoning */}
                    <pre className="text-sm whitespace-pre-wrap">{typeof step === 'string' ? step : step.reasoning}</pre>

                    {/* Uncertainty sources */}
                    {step.uncertainty_sources && step.uncertainty_sources.length > 0 && (
                      <div className="bg-yellow-50 border border-yellow-200 rounded p-2">
                        <div className="text-xs font-medium text-yellow-800 mb-1">⚠️ Uncertainty Sources:</div>
                        <ul className="text-xs text-yellow-700 list-disc list-inside">
                          {step.uncertainty_sources.map((source: string, i: number) => (
                            <li key={i}>{source}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Measurements */}
                    {step.measurements && Object.keys(step.measurements).length > 0 && (
                      <div className="bg-blue-50 border border-blue-200 rounded p-2">
                        <div className="text-xs font-medium text-blue-800 mb-1">📊 Measurements:</div>
                        <div className="space-y-1">
                          {Object.entries(step.measurements).map(([key, value]: [string, any]) => (
                            <div key={key} className="text-xs text-blue-700">
                              <span className="font-medium">{key}:</span> {JSON.stringify(value)}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Alternatives considered */}
                    {step.alternatives_considered && step.alternatives_considered.length > 0 && (
                      <div className="bg-purple-50 border border-purple-200 rounded p-2">
                        <div className="text-xs font-medium text-purple-800 mb-1">🔀 Alternatives Considered:</div>
                        <ul className="text-xs text-purple-700 list-disc list-inside">
                          {step.alternatives_considered.map((alt: string, i: number) => (
                            <li key={i}>{alt}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Attribution */}
                    {step.attribution_sources && step.attribution_sources.length > 0 && (
                      <div className="text-xs text-gray-600">
                        <strong>Attribution:</strong> {step.attribution_sources.join(', ')}
                      </div>
                    )}

                    {/* Dependencies */}
                    {step.depends_on_steps && step.depends_on_steps.length > 0 && (
                      <div className="text-xs text-gray-500">
                        <strong>Depends on steps:</strong> {step.depends_on_steps.join(', ')}
                      </div>
                    )}
                  </div>
                ))}

                {/* Overall confidence methodology */}
                {(capsule.reasoning_trace?.confidence_methodology || capsule.payload?.confidence_methodology) && (
                  <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="text-sm font-medium text-gray-700 mb-2">📈 Confidence Computation Method</div>
                    {(() => {
                      const methodology = capsule.reasoning_trace?.confidence_methodology || capsule.payload?.confidence_methodology;
                      return (
                        <div className="space-y-2">
                          <div className="text-sm text-gray-600">
                            <span className="font-medium">Method:</span>{' '}
                            <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">
                              {methodology.method.replace(/_/g, ' ')}
                            </span>
                          </div>
                          {methodology.critical_path_steps && methodology.critical_path_steps.length > 0 && (
                            <div className="text-sm text-gray-600">
                              <span className="font-medium">Critical Path Steps:</span> {methodology.critical_path_steps.join(', ')}
                            </div>
                          )}
                          {methodology.explanation && (
                            <div className="text-sm text-gray-600 italic">
                              {methodology.explanation}
                            </div>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-gray-500 text-sm">No content available</div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 p-4 rounded-lg">
            {capsule.payload ? (
              <div className="space-y-4">
                {/* Display session metadata if available */}
                {capsule.payload.session_metadata && (
                  <div>
                    <div className="text-sm font-medium text-gray-700 mb-2">Session Metadata:</div>
                    <pre className="text-xs overflow-x-auto">
                      {JSON.stringify(capsule.payload.session_metadata, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Display other payload fields */}
                {Object.entries(capsule.payload).filter(([key]) =>
                  !['reasoning_steps', 'content', 'session_metadata'].includes(key)
                ).length > 0 && (
                  <div className="border-t pt-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">Additional Payload Data:</div>
                    <div className="space-y-2">
                      {Object.entries(capsule.payload).filter(([key]) =>
                        !['reasoning_steps', 'content', 'session_metadata'].includes(key)
                      ).map(([key, value]) => (
                        <div key={key} className="text-xs">
                          <span className="font-medium text-gray-600">{key}:</span>{' '}
                          <span className="text-gray-800">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (capsule.metadata || capsule.payload?.metadata) ? (
              <pre className="text-sm overflow-x-auto">
                {JSON.stringify(capsule.metadata || capsule.payload?.metadata, null, 2)}
              </pre>
            ) : capsule.reasoning_trace?.reasoning_steps?.[0]?.metadata ? (
              <div className="space-y-3">
                <pre className="text-sm overflow-x-auto">
                  {JSON.stringify(capsule.reasoning_trace.reasoning_steps[0].metadata, null, 2)}
                </pre>
                {capsule.reasoning_trace.reasoning_steps[0].metadata.economic_attribution && (
                  <div className="border-t pt-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">💰 Economic Attribution:</div>
                    {Object.entries(capsule.reasoning_trace.reasoning_steps[0].metadata.economic_attribution).map(([key, value]: [string, any]) => (
                      <div key={key} className="text-xs text-gray-600">
                        • {key.replace('_', ' ')}: {value.weight * 100}% (${value.value})
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-gray-500 text-sm">No metadata available</div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Raw Data */}
      {includeRaw && rawData && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Raw Data</CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowRawData(!showRawData)}
              >
                {showRawData ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
                {showRawData ? 'Hide' : 'Show'}
              </Button>
            </div>
          </CardHeader>
          {showRawData && (
            <CardContent>
              <div className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                <pre className="text-xs">
                  {JSON.stringify(rawData, null, 2)}
                </pre>
              </div>
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
}