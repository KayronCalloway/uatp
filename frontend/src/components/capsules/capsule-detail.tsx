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
  RefreshCw,
  CheckSquare
} from 'lucide-react';
import { formatDate, getCapsuleTypeColor, truncateText } from '@/lib/utils';
import { AnyCapsule, GetCapsuleQuery } from '@/types/api';
import { OutcomeRecorder } from './outcome-recorder';
import { QualityBadge } from '@/components/capsules/quality-badge';
import { QualityDetailsModal } from '@/components/capsules/quality-details-modal';
import { DataSourcesCard } from '@/components/capsules/DataSourcesCard';
import { RiskAssessmentCard } from '@/components/capsules/RiskAssessmentCard';
import { AlternativesCard } from '@/components/capsules/AlternativesCard';
import { PlainLanguageCard } from '@/components/capsules/PlainLanguageCard';
import { OutcomeCard } from '@/components/capsules/OutcomeCard';

interface CapsuleDetailProps {
  capsuleId: string;
  onBack?: () => void;
}

export function CapsuleDetail({ capsuleId, onBack }: CapsuleDetailProps) {
  const [includeRaw, setIncludeRaw] = useState(false);
  const [showRawData, setShowRawData] = useState(false);
  const [showOutcomeRecorder, setShowOutcomeRecorder] = useState(false);
  const [showQualityModal, setShowQualityModal] = useState(false);

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
                variant={showOutcomeRecorder ? "default" : "outline"}
                size="sm"
                onClick={() => setShowOutcomeRecorder(!showOutcomeRecorder)}
              >
                <CheckSquare className="h-4 w-4 mr-2" />
                {showOutcomeRecorder ? 'Hide Outcome' : 'Record Outcome'}
              </Button>
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
          <div className="flex items-center justify-between">
            <CardTitle>Basic Information</CardTitle>
            <QualityBadge
              capsuleId={capsule.capsule_id || capsule.id}
              size="md"
              onClick={() => setShowQualityModal(true)}
            />
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Core Metadata Grid */}
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

          {/* Confidence & Uncertainty */}
          {(capsule.confidence !== undefined || capsule.payload?.confidence !== undefined) && (
            <div className="border-t pt-4">
              <label className="text-sm font-medium text-gray-500 mb-2 block">
                Confidence & Uncertainty
              </label>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-blue-900">
                      {((capsule.confidence || capsule.payload?.confidence || 0) * 100).toFixed(1)}%
                    </span>
                    <span className="text-sm text-blue-700">Overall Confidence</span>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    (capsule.confidence || capsule.payload?.confidence || 0) >= 0.9
                      ? 'bg-green-100 text-green-700'
                      : (capsule.confidence || capsule.payload?.confidence || 0) >= 0.7
                      ? 'bg-blue-100 text-blue-700'
                      : (capsule.confidence || capsule.payload?.confidence || 0) >= 0.5
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-red-100 text-red-700'
                  }`}>
                    {(capsule.confidence || capsule.payload?.confidence || 0) >= 0.9 ? 'High' :
                     (capsule.confidence || capsule.payload?.confidence || 0) >= 0.7 ? 'Good' :
                     (capsule.confidence || capsule.payload?.confidence || 0) >= 0.5 ? 'Moderate' : 'Low'}
                  </div>
                </div>

                {/* Confidence bar */}
                <div className="relative h-2 bg-blue-100 rounded-full overflow-hidden mb-3">
                  <div
                    className="h-full bg-blue-600 rounded-full transition-all"
                    style={{ width: `${(capsule.confidence || capsule.payload?.confidence || 0) * 100}%` }}
                  />
                </div>

                {/* Uncertainty breakdown - Only show if actual values exist */}
                {(() => {
                  const epistemicUncertainty = capsule.epistemic_uncertainty ?? capsule.payload?.uncertainty_analysis?.epistemic_uncertainty;
                  const aleatoricUncertainty = capsule.aleatoric_uncertainty ?? capsule.payload?.uncertainty_analysis?.aleatoric_uncertainty;
                  const totalUncertainty = capsule.total_uncertainty ?? capsule.payload?.uncertainty_analysis?.total_uncertainty;
                  const riskScore = capsule.risk_score ?? capsule.payload?.uncertainty_analysis?.risk_score;

                  return (epistemicUncertainty !== undefined || aleatoricUncertainty !== undefined) ? (
                    <div className="space-y-2">
                      <div className="grid grid-cols-2 gap-3 text-xs">
                        {epistemicUncertainty !== undefined && (
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-purple-500" />
                            <span className="text-gray-600">
                              <span className="font-medium text-gray-700">Epistemic:</span>{' '}
                              {(epistemicUncertainty * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                        {aleatoricUncertainty !== undefined && (
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-teal-500" />
                            <span className="text-gray-600">
                              <span className="font-medium text-gray-700">Aleatoric:</span>{' '}
                              {(aleatoricUncertainty * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                        {totalUncertainty !== undefined && (
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-orange-500" />
                            <span className="text-gray-600">
                              <span className="font-medium text-gray-700">Total:</span>{' '}
                              {(totalUncertainty * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                        {riskScore !== undefined && (
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-red-500" />
                            <span className="text-gray-600">
                              <span className="font-medium text-gray-700">Risk:</span>{' '}
                              {(riskScore * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                      </div>
                      {/* Confidence Interval if available */}
                      {capsule.payload?.uncertainty_analysis?.confidence_interval && (
                        <div className="text-xs text-gray-600">
                          <span className="font-medium text-gray-700">95% CI:</span>{' '}
                          [{(capsule.payload.uncertainty_analysis.confidence_interval[0] * 100).toFixed(1)}%,{' '}
                          {(capsule.payload.uncertainty_analysis.confidence_interval[1] * 100).toFixed(1)}%]
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-xs text-gray-500 italic">
                      Uncertainty breakdown: Available after backend analysis
                    </div>
                  );
                })()}
              </div>
            </div>
          )}

          {/* Domain & Problem Context */}
          {(capsule.payload?.session_metadata?.problem_domain || capsule.payload?.session_metadata?.problem_type) && (
            <div className="border-t pt-4">
              <label className="text-sm font-medium text-gray-500 mb-2 block">
                Context
              </label>
              <div className="flex flex-wrap gap-2">
                {capsule.payload?.session_metadata?.problem_domain && (
                  <div className="inline-flex items-center gap-2 px-3 py-2 bg-purple-50 border border-purple-200 rounded-lg">
                    <Database className="h-4 w-4 text-purple-600" />
                    <div>
                      <div className="text-xs text-purple-600 font-medium">Domain</div>
                      <div className="text-sm text-purple-900 font-semibold">
                        {capsule.payload.session_metadata.problem_domain}
                      </div>
                    </div>
                  </div>
                )}
                {capsule.payload?.session_metadata?.problem_type && (
                  <div className="inline-flex items-center gap-2 px-3 py-2 bg-green-50 border border-green-200 rounded-lg">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <div>
                      <div className="text-xs text-green-600 font-medium">Problem Type</div>
                      <div className="text-sm text-green-900 font-semibold">
                        {capsule.payload.session_metadata.problem_type}
                      </div>
                    </div>
                  </div>
                )}
                {capsule.payload?.session_metadata?.user_expertise && (
                  <div className="inline-flex items-center gap-2 px-3 py-2 bg-indigo-50 border border-indigo-200 rounded-lg">
                    <User className="h-4 w-4 text-indigo-600" />
                    <div>
                      <div className="text-xs text-indigo-600 font-medium">Expertise</div>
                      <div className="text-sm text-indigo-900 font-semibold">
                        {capsule.payload.session_metadata.user_expertise}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Capsule Chain Navigation */}
          {capsule.previous_capsule_id && (
            <div className="border-t pt-4">
              <label className="text-sm font-medium text-gray-500 mb-2 block">
                Capsule Chain
              </label>
              <div className="flex items-center gap-2 text-sm">
                <button
                  onClick={() => window.location.href = `/capsules/${capsule.previous_capsule_id}`}
                  className="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg transition-colors"
                >
                  <ArrowLeft className="h-3 w-3" />
                  <span className="font-mono text-xs">
                    {capsule.previous_capsule_id.slice(0, 8)}...
                  </span>
                  <span className="text-gray-600">Previous</span>
                </button>
                <div className="flex-1 flex items-center justify-center">
                  <div className="h-0.5 w-full bg-gray-300" />
                </div>
                <div className="px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg">
                  <span className="text-blue-700 font-semibold text-xs">Current</span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Verification Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Shield className="h-5 w-5" />
              <span>Cryptographic Verification</span>
            </CardTitle>
            {verificationData && !verificationLoading && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                disabled={isLoading}
              >
                <RefreshCw className={`h-3 w-3 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Re-verify
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {verificationLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-center space-y-3">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-sm text-gray-600">Verifying cryptographic signature...</p>
              </div>
            </div>
          ) : verificationData ? (
            <>
              {/* Visual Status Indicator */}
              <div className={`rounded-lg p-6 border-2 ${
                verificationData.verified
                  ? 'bg-green-50 border-green-300'
                  : 'bg-red-50 border-red-300'
              }`}>
                <div className="flex items-start gap-4">
                  <div className={`flex-shrink-0 w-16 h-16 rounded-full flex items-center justify-center ${
                    verificationData.verified ? 'bg-green-100' : 'bg-red-100'
                  }`}>
                    {verificationData.verified ? (
                      <CheckCircle className="h-8 w-8 text-green-600" />
                    ) : (
                      <XCircle className="h-8 w-8 text-red-600" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className={`text-xl font-bold ${
                        verificationData.verified ? 'text-green-900' : 'text-red-900'
                      }`}>
                        {verificationData.verified ? 'Cryptographically Verified' : 'Verification Failed'}
                      </h3>
                      {verificationData.from_cache && (
                        <span className="px-2 py-0.5 text-xs font-semibold bg-blue-100 text-blue-700 rounded">
                          Cached Result
                        </span>
                      )}
                    </div>
                    <p className={`text-sm ${
                      verificationData.verified ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {verificationData.verified
                        ? 'This capsule\'s signature and hash have been cryptographically verified. The content has not been tampered with since creation.'
                        : 'This capsule failed cryptographic verification. The signature does not match or the content may have been modified.'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Verification Error Details */}
              {verificationData.verification_error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="text-sm font-semibold text-red-900 mb-1">Verification Error</h4>
                      <p className="text-sm text-red-700">{verificationData.verification_error}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Verification Details Grid */}
              {verificationData.verified && (
                <div className="border-t pt-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Verification Details</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Signature Status */}
                    {capsule.signature && (
                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <CheckCircle className="h-4 w-4 text-green-600" />
                          <span className="text-xs font-semibold text-gray-600 uppercase">Signature</span>
                        </div>
                        <p className="text-xs font-mono text-gray-900 break-all">
                          {capsule.signature.slice(0, 32)}...
                        </p>
                      </div>
                    )}

                    {/* Signer Information */}
                    {capsule.verification?.signer && (
                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <User className="h-4 w-4 text-blue-600" />
                          <span className="text-xs font-semibold text-gray-600 uppercase">Signer</span>
                        </div>
                        <p className="text-xs text-gray-900">{capsule.verification.signer}</p>
                      </div>
                    )}

                    {/* Verify Key Status */}
                    {verificationData.metadata_has_verify_key !== null && (
                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <Shield className="h-4 w-4 text-purple-600" />
                          <span className="text-xs font-semibold text-gray-600 uppercase">Verify Key</span>
                        </div>
                        <p className="text-xs text-gray-900">
                          {verificationData.metadata_has_verify_key ? 'Present in metadata' : 'Not in metadata'}
                        </p>
                      </div>
                    )}

                    {/* Verification Timestamp */}
                    {capsule.timestamp && (
                      <div className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <Clock className="h-4 w-4 text-orange-600" />
                          <span className="text-xs font-semibold text-gray-600 uppercase">Created</span>
                        </div>
                        <p className="text-xs text-gray-900">{formatDate(capsule.timestamp)}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Trust Score (if available) */}
              {capsule.trust_score !== undefined && (
                <div className="border-t pt-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Trust Metrics</h4>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-blue-700 font-medium">Trust Score</span>
                      <span className="text-2xl font-bold text-blue-900">
                        {(capsule.trust_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="relative h-2 bg-blue-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-600 rounded-full transition-all"
                        style={{ width: `${capsule.trust_score * 100}%` }}
                      />
                    </div>
                    <p className="text-xs text-blue-700 mt-2">
                      Based on agent reputation, verification history, and content quality
                    </p>
                  </div>
                </div>
              )}

              {/* Additional Messages */}
              {verificationData.message && (
                <div className="text-xs text-gray-600 bg-gray-50 rounded p-3">
                  <span className="font-medium">Note:</span> {verificationData.message}
                </div>
              )}
            </>
          ) : capsule.verification?.message ? (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-yellow-900 mb-1">Verification Unavailable</h4>
                  <p className="text-sm text-yellow-700">{capsule.verification.message}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
              <Shield className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <h4 className="text-sm font-semibold text-gray-900 mb-1">Verification Data Not Available</h4>
              <p className="text-xs text-gray-600">
                Cryptographic verification data could not be retrieved for this capsule
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reasoning Process */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Database className="h-5 w-5" />
            <span>Reasoning Process</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* SEE: At-a-glance summary if reasoning steps exist */}
          {(capsule.payload?.reasoning_steps?.length > 0 || capsule.reasoning_trace?.reasoning_steps?.length > 0) && (
            <div className="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Total Steps */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="text-xs text-blue-600 font-medium mb-1">Total Steps</div>
                <div className="text-2xl font-bold text-blue-900">
                  {(capsule.payload?.reasoning_steps || capsule.reasoning_trace?.reasoning_steps || []).length}
                </div>
              </div>

              {/* Critical Path Strength */}
              {capsule.payload?.critical_path_analysis?.critical_path_strength !== undefined && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                  <div className="text-xs text-orange-600 font-medium mb-1">Path Strength</div>
                  <div className="text-2xl font-bold text-orange-900">
                    {(capsule.payload.critical_path_analysis.critical_path_strength * 100).toFixed(0)}%
                  </div>
                </div>
              )}

              {/* Average Step Confidence */}
              {(() => {
                const steps = capsule.payload?.reasoning_steps || capsule.reasoning_trace?.reasoning_steps || [];
                const confidences = steps
                  .map((s: any) => s.confidence)
                  .filter((c: any) => c !== undefined && c !== null);
                const avgConfidence = confidences.length > 0
                  ? confidences.reduce((a: number, b: number) => a + b, 0) / confidences.length
                  : null;
                return avgConfidence !== null ? (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <div className="text-xs text-green-600 font-medium mb-1">Avg Confidence</div>
                    <div className="text-2xl font-bold text-green-900">
                      {(avgConfidence * 100).toFixed(0)}%
                    </div>
                  </div>
                ) : null;
              })()}

              {/* Critical Steps Count */}
              {capsule.payload?.critical_path_analysis?.critical_steps?.length > 0 && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                  <div className="text-xs text-purple-600 font-medium mb-1">Critical Steps</div>
                  <div className="text-2xl font-bold text-purple-900">
                    {capsule.payload.critical_path_analysis.critical_steps.length}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="bg-gray-50 p-4 rounded-lg">
            {(capsule.content || capsule.payload?.content) ? (
              <pre className="text-sm whitespace-pre-wrap">{capsule.content || capsule.payload?.content}</pre>
            ) : (capsule.payload?.reasoning_steps?.length > 0 || capsule.reasoning_trace?.reasoning_steps?.length > 0) ? (
              <div className="space-y-6">
                {(capsule.payload?.reasoning_steps || capsule.reasoning_trace?.reasoning_steps || []).map((step: any, index: number) => {
                  const isCritical = capsule.payload?.critical_path_analysis?.critical_steps?.includes(step.step_id || index + 1);
                  const isBottleneck = capsule.payload?.critical_path_analysis?.bottleneck_steps?.includes(step.step_id || index + 1);
                  const isDecisionPoint = capsule.payload?.critical_path_analysis?.key_decision_points?.includes(step.step_id || index + 1);
                  const hasConfidence = step.confidence !== undefined && step.confidence !== null;

                  return (
                    <div key={index} className={`relative rounded-lg border-2 overflow-hidden ${
                      isCritical
                        ? 'border-orange-400 bg-orange-50/30'
                        : 'border-gray-200 bg-white'
                    }`}>
                      {/* Step Header Bar */}
                      <div className={`px-4 py-3 border-b ${
                        isCritical ? 'bg-orange-100 border-orange-200' : 'bg-gray-50 border-gray-200'
                      }`}>
                        <div className="flex items-center justify-between">
                          {/* Left: Step number and type */}
                          <div className="flex items-center gap-3">
                            <div className={`flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${
                              isCritical
                                ? 'bg-orange-500 text-white'
                                : 'bg-blue-500 text-white'
                            }`}>
                              {step.step_id || index + 1}
                            </div>
                            <div>
                              <div className="text-sm font-semibold text-gray-900">
                                {step.operation || 'Reasoning Step'}
                              </div>
                              {step.confidence_basis && (
                                <div className="text-xs text-gray-600 mt-0.5">
                                  {step.confidence_basis}
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Right: Status badges */}
                          <div className="flex items-center gap-2">
                            {isCritical && (
                              <span className="px-2 py-1 bg-orange-200 text-orange-800 rounded text-xs font-semibold">
                                🎯 Critical Path
                              </span>
                            )}
                            {isBottleneck && (
                              <span className="px-2 py-1 bg-red-200 text-red-800 rounded text-xs font-semibold">
                                ⚠️ Bottleneck
                              </span>
                            )}
                            {isDecisionPoint && (
                              <span className="px-2 py-1 bg-purple-200 text-purple-800 rounded text-xs font-semibold">
                                🔀 Decision Point
                              </span>
                            )}
                            {hasConfidence && (
                              <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                                step.confidence >= 0.9 ? 'bg-green-100 text-green-800' :
                                step.confidence >= 0.7 ? 'bg-blue-100 text-blue-800' :
                                step.confidence >= 0.5 ? 'bg-yellow-100 text-yellow-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {(step.confidence * 100).toFixed(0)}%
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Step Content */}
                      <div className="p-4 space-y-3">
                        {/* Main Reasoning */}
                        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                          <pre className="text-sm whitespace-pre-wrap text-gray-800 leading-relaxed">
                            {typeof step === 'string' ? step : step.reasoning}
                          </pre>
                        </div>

                        {/* Confidence Explanation - Only if exists */}
                        {step.measurements?.confidence_explanation && (
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm font-semibold text-blue-900">💡 Confidence Analysis</span>
                            </div>
                            <div className="space-y-2">
                              {/* Boosting factors */}
                              {step.measurements.confidence_explanation.boosting_factors?.length > 0 && (
                                <div>
                                  <div className="text-xs font-semibold text-green-700 mb-1">✓ Boosting Factors</div>
                                  <ul className="text-xs text-green-600 space-y-0.5">
                                    {step.measurements.confidence_explanation.boosting_factors.map((factor: string, i: number) => (
                                      <li key={i} className="flex items-start gap-1">
                                        <span className="mt-0.5">•</span>
                                        <span>{factor}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Limiting factors */}
                              {step.measurements.confidence_explanation.limiting_factors?.length > 0 && (
                                <div>
                                  <div className="text-xs font-semibold text-red-700 mb-1">⚠ Limiting Factors</div>
                                  <ul className="text-xs text-red-600 space-y-0.5">
                                    {step.measurements.confidence_explanation.limiting_factors.map((factor: string, i: number) => (
                                      <li key={i} className="flex items-start gap-1">
                                        <span className="mt-0.5">•</span>
                                        <span>{factor}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Improvement suggestions */}
                              {step.measurements.confidence_explanation.improvement_suggestions?.length > 0 && (
                                <div>
                                  <div className="text-xs font-semibold text-blue-700 mb-1">💬 Improvement Suggestions</div>
                                  <ul className="text-xs text-blue-600 space-y-0.5">
                                    {step.measurements.confidence_explanation.improvement_suggestions.map((suggestion: string, i: number) => (
                                      <li key={i} className="flex items-start gap-1">
                                        <span className="mt-0.5">•</span>
                                        <span>{suggestion}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Grid for secondary information - only if data exists */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {/* Uncertainty sources */}
                          {step.uncertainty_sources && step.uncertainty_sources.length > 0 && (
                            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                              <div className="flex items-center gap-1 mb-2">
                                <AlertCircle className="h-4 w-4 text-yellow-600" />
                                <span className="text-xs font-semibold text-yellow-900">Uncertainty Sources</span>
                              </div>
                              <ul className="text-xs text-yellow-700 space-y-1">
                                {step.uncertainty_sources.map((source: string, i: number) => (
                                  <li key={i} className="flex items-start gap-1">
                                    <span className="mt-0.5">•</span>
                                    <span>{source}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Alternatives considered */}
                          {step.alternatives_considered && step.alternatives_considered.length > 0 && (
                            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                              <div className="flex items-center gap-1 mb-2">
                                <CheckCircle className="h-4 w-4 text-purple-600" />
                                <span className="text-xs font-semibold text-purple-900">Alternatives Considered</span>
                              </div>
                              <ul className="text-xs text-purple-700 space-y-1">
                                {step.alternatives_considered.map((alt: string, i: number) => (
                                  <li key={i} className="flex items-start gap-1">
                                    <span className="mt-0.5">•</span>
                                    <span>{alt}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>

                        {/* Measurements - collapsed by default, only if exists */}
                        {step.measurements && Object.keys(step.measurements).filter(k => k !== 'confidence_explanation').length > 0 && (
                          <details className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                            <summary className="text-xs font-semibold text-gray-700 cursor-pointer flex items-center gap-2">
                              <Database className="h-3 w-3" />
                              Additional Measurements ({Object.keys(step.measurements).filter(k => k !== 'confidence_explanation').length})
                            </summary>
                            <div className="mt-2 space-y-1 pl-5">
                              {Object.entries(step.measurements)
                                .filter(([key]) => key !== 'confidence_explanation')
                                .map(([key, value]: [string, any]) => (
                                  <div key={key} className="text-xs text-gray-700">
                                    <span className="font-medium">{key.replace(/_/g, ' ')}:</span>{' '}
                                    <span className="text-gray-600">{JSON.stringify(value)}</span>
                                  </div>
                                ))}
                            </div>
                          </details>
                        )}

                        {/* Footer: Attribution and Dependencies */}
                        {(step.attribution_sources?.length > 0 || step.depends_on_steps?.length > 0) && (
                          <div className="pt-2 border-t border-gray-200 space-y-1">
                            {step.attribution_sources && step.attribution_sources.length > 0 && (
                              <div className="text-xs text-gray-600">
                                <span className="font-medium">Attribution:</span> {step.attribution_sources.join(', ')}
                              </div>
                            )}
                            {step.depends_on_steps && step.depends_on_steps.length > 0 && (
                              <div className="text-xs text-gray-600">
                                <span className="font-medium">Depends on:</span> Steps {step.depends_on_steps.join(', ')}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}

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

                {/* NEW: Critical Path Analysis Summary */}
                {capsule.payload?.critical_path_analysis && (
                  <div className="mt-6 bg-orange-50 border border-orange-200 rounded-lg p-4">
                    <div className="text-sm font-medium text-orange-900 mb-3">🎯 Critical Path Analysis</div>

                    <div className="grid grid-cols-2 gap-4 text-sm mb-3">
                      <div>
                        <span className="text-gray-600">Critical Steps:</span>
                        <span className="ml-2 font-medium text-gray-900">
                          {capsule.payload.critical_path_analysis.critical_steps?.join(', ') || 'All steps'}
                        </span>
                      </div>

                      <div>
                        <span className="text-gray-600">Path Strength:</span>
                        <span className="ml-2 font-medium text-gray-900">
                          {(capsule.payload.critical_path_analysis.critical_path_strength * 100).toFixed(1)}%
                        </span>
                      </div>

                      <div>
                        <span className="text-gray-600">Dependency Depth:</span>
                        <span className="ml-2 font-medium text-gray-900">
                          {capsule.payload.critical_path_analysis.dependency_depth} levels
                        </span>
                      </div>

                      {capsule.payload.critical_path_analysis.peripheral_steps?.length > 0 && (
                        <div>
                          <span className="text-gray-600">Peripheral Steps:</span>
                          <span className="ml-2 font-medium text-gray-900">
                            {capsule.payload.critical_path_analysis.peripheral_steps.length}
                          </span>
                        </div>
                      )}
                    </div>

                    {capsule.payload.critical_path_analysis.weakest_link && (
                      <div className="bg-red-50 border border-red-200 rounded p-2 mt-2">
                        <div className="text-xs font-medium text-red-800">⚠️ Weakest Link:</div>
                        <div className="text-xs text-red-700 mt-1">
                          Step {capsule.payload.critical_path_analysis.weakest_link.step_id}
                          {' '}({(capsule.payload.critical_path_analysis.weakest_link.confidence * 100).toFixed(1)}% confidence)
                        </div>
                        <div className="text-xs text-red-600 mt-1 italic">
                          "{capsule.payload.critical_path_analysis.weakest_link.reasoning}"
                        </div>
                      </div>
                    )}

                    {capsule.payload.critical_path_analysis.key_decision_points?.length > 0 && (
                      <div className="text-xs text-gray-600 mt-2">
                        <strong>Decision Points:</strong> Steps {capsule.payload.critical_path_analysis.key_decision_points.join(', ')}
                      </div>
                    )}
                  </div>
                )}

                {/* NEW: Improvement Recommendations */}
                {capsule.payload?.improvement_recommendations && capsule.payload.improvement_recommendations.length > 0 && (
                  <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="text-sm font-medium text-blue-900 mb-2">💡 Improvement Recommendations</div>
                    <ul className="space-y-1 text-xs text-blue-800">
                      {capsule.payload.improvement_recommendations.map((rec: string, i: number) => (
                        <li key={i} className="flex items-start">
                          <span className="mr-2">•</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-gray-500 text-sm">No content available</div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Rich Data Components - Court-Admissible Format */}

      {/* Data Sources - Provenance Tracking */}
      {capsule.payload?.reasoning_chain?.some((step: any) => step.data_sources?.length > 0) && (
        <DataSourcesCard
          dataSources={
            capsule.payload.reasoning_chain
              .flatMap((step: any) => step.data_sources || [])
              .filter(Boolean)
          }
        />
      )}

      {/* Risk Assessment - Insurance-Ready */}
      {capsule.payload?.risk_assessment && (
        <RiskAssessmentCard riskAssessment={capsule.payload.risk_assessment} />
      )}

      {/* Alternatives Considered - Decision Methodology */}
      {capsule.payload?.alternatives_considered?.length > 0 && (
        <AlternativesCard alternatives={capsule.payload.alternatives_considered} />
      )}

      {/* Plain Language Summary - EU AI Act Article 13 */}
      {capsule.payload?.plain_language_summary && (
        <PlainLanguageCard summary={capsule.payload.plain_language_summary} />
      )}

      {/* Outcome - Ground Truth */}
      {capsule.payload?.outcome && (
        <OutcomeCard outcome={capsule.payload.outcome} />
      )}

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Database className="h-5 w-5" />
            <span>Session Context & Metadata</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* SEE: Quick overview of what metadata is available */}
          {capsule.payload?.session_metadata && (
            <div className="mb-4 flex flex-wrap gap-2">
              {capsule.payload.session_metadata.user_goal && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                  <CheckCircle className="h-3 w-3" />
                  User Goal
                </span>
              )}
              {capsule.payload.session_metadata.success_criteria && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                  <CheckCircle className="h-3 w-3" />
                  Success Criteria
                </span>
              )}
              {capsule.payload.session_metadata.constraints && Object.keys(capsule.payload.session_metadata.constraints).length > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs font-medium">
                  <AlertCircle className="h-3 w-3" />
                  Constraints
                </span>
              )}
              {capsule.payload.session_metadata.risks_identified && capsule.payload.session_metadata.risks_identified.length > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">
                  <AlertCircle className="h-3 w-3" />
                  Risks
                </span>
              )}
              {(capsule.payload.session_metadata.files_involved?.length > 0 || capsule.payload.session_metadata.tools_used?.length > 0) && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium">
                  <Database className="h-3 w-3" />
                  Context Data
                </span>
              )}
            </div>
          )}

          <div className="bg-gray-50 p-4 rounded-lg">
            {capsule.payload ? (
              <div className="space-y-4">
                {/* UNDERSTAND: Enhanced Context Display */}
                {capsule.payload.session_metadata && (
                  <div className="space-y-4">
                    {/* Primary Goal & Outcome Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* User Goal */}
                      {capsule.payload.session_metadata.user_goal && (
                        <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                              <span className="text-white text-lg">🎯</span>
                            </div>
                            <div className="text-sm font-bold text-blue-900">User Goal</div>
                          </div>
                          <div className="text-sm text-blue-800 leading-relaxed">{capsule.payload.session_metadata.user_goal}</div>
                        </div>
                      )}

                      {/* Expected Outcome */}
                      {capsule.payload.session_metadata.expected_outcome && (
                        <div className="bg-indigo-50 border-2 border-indigo-200 rounded-lg p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center">
                              <span className="text-white text-lg">🎬</span>
                            </div>
                            <div className="text-sm font-bold text-indigo-900">Expected Outcome</div>
                          </div>
                          <div className="text-sm text-indigo-800 leading-relaxed">{capsule.payload.session_metadata.expected_outcome}</div>
                        </div>
                      )}
                    </div>

                    {/* Success Criteria - Full Width */}
                    {capsule.payload.session_metadata.success_criteria && (
                      <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircle className="h-5 w-5 text-green-600" />
                          <div className="text-sm font-bold text-green-900">Success Criteria</div>
                        </div>
                        <div className="text-sm text-green-800 leading-relaxed">{capsule.payload.session_metadata.success_criteria}</div>
                      </div>
                    )}

                    {/* Constraints & Risks Grid */}
                    {(capsule.payload.session_metadata.constraints && Object.keys(capsule.payload.session_metadata.constraints).length > 0) ||
                     (capsule.payload.session_metadata.risks_identified && capsule.payload.session_metadata.risks_identified.length > 0) ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Constraints */}
                        {capsule.payload.session_metadata.constraints && Object.keys(capsule.payload.session_metadata.constraints).length > 0 && (
                          <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <AlertCircle className="h-5 w-5 text-yellow-600" />
                              <div className="text-sm font-bold text-yellow-900">Constraints</div>
                            </div>
                            <div className="space-y-2">
                              {Object.entries(capsule.payload.session_metadata.constraints).map(([key, value]: [string, any]) => (
                                <div key={key} className="flex items-start gap-2 text-sm">
                                  <span className="text-yellow-600 mt-0.5">•</span>
                                  <div className="text-yellow-800">
                                    <span className="font-semibold">{key.replace(/_/g, ' ')}:</span>{' '}
                                    <span>{String(value)}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Risks Identified */}
                        {capsule.payload.session_metadata.risks_identified && capsule.payload.session_metadata.risks_identified.length > 0 && (
                          <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-3">
                              <AlertCircle className="h-5 w-5 text-red-600" />
                              <div className="text-sm font-bold text-red-900">Risks Identified</div>
                            </div>
                            <ul className="space-y-2">
                              {capsule.payload.session_metadata.risks_identified.map((risk: string, i: number) => (
                                <li key={i} className="flex items-start gap-2 text-sm">
                                  <span className="text-red-600 mt-0.5">•</span>
                                  <span className="text-red-800">{risk}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ) : null}

                    {/* Context Information: Files & Tools */}
                    {(capsule.payload.session_metadata.files_involved?.length > 0 || capsule.payload.session_metadata.tools_used?.length > 0) && (
                      <div className="bg-gray-50 border-2 border-gray-200 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-3">
                          <Database className="h-5 w-5 text-gray-600" />
                          <div className="text-sm font-bold text-gray-900">Technical Context</div>
                        </div>

                        <div className="space-y-3">
                          {capsule.payload.session_metadata.files_involved?.length > 0 && (
                            <div>
                              <div className="text-xs font-semibold text-gray-700 mb-2">Files Involved ({capsule.payload.session_metadata.files_involved.length})</div>
                              <div className="flex flex-wrap gap-2">
                                {capsule.payload.session_metadata.files_involved.map((file: string, i: number) => (
                                  <span key={i} className="inline-flex items-center gap-1 bg-white border border-gray-300 px-2 py-1 rounded text-xs font-mono text-gray-700">
                                    <Database className="h-3 w-3" />
                                    {file}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {capsule.payload.session_metadata.tools_used?.length > 0 && (
                            <div>
                              <div className="text-xs font-semibold text-gray-700 mb-2">Tools Used ({capsule.payload.session_metadata.tools_used.length})</div>
                              <div className="flex flex-wrap gap-2">
                                {capsule.payload.session_metadata.tools_used.map((tool: string, i: number) => (
                                  <span key={i} className="inline-flex items-center gap-1 bg-blue-100 border border-blue-300 px-2 py-1 rounded text-xs font-medium text-blue-800">
                                    <CheckCircle className="h-3 w-3" />
                                    {tool}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Original Session Metadata (collapsed view) */}
                    <details className="text-xs">
                      <summary className="cursor-pointer text-gray-600 hover:text-gray-900 font-medium">
                        View Raw Session Metadata
                      </summary>
                      <pre className="mt-2 overflow-x-auto bg-white p-2 rounded border">
                        {JSON.stringify(capsule.payload.session_metadata, null, 2)}
                      </pre>
                    </details>
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

      {/* Outcome Recorder */}
      {showOutcomeRecorder && (
        <OutcomeRecorder
          capsuleId={capsule.capsule_id || capsule.id}
          predictedOutcome={
            capsule.payload?.predicted_outcome ||
            capsule.payload?.session_metadata?.expected_outcome
          }
          onSuccess={() => {
            setShowOutcomeRecorder(false);
            refetch();
          }}
          onCancel={() => setShowOutcomeRecorder(false)}
        />
      )}

      {/* Quality Details Modal */}
      <QualityDetailsModal
        capsuleId={capsule.capsule_id || capsule.id}
        isOpen={showQualityModal}
        onClose={() => setShowQualityModal(false)}
      />
    </div>
  );
}
