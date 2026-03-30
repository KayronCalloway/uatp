'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Shield,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Scale,
  FileCheck,
  Clock,
} from 'lucide-react';

interface Compliance {
  daubert_standard?: boolean;
  insurance_ready?: boolean;
  eu_ai_act_article_13?: boolean;
}

interface ComplianceStatusCardProps {
  dataRichness?: string;
  compliance?: Compliance;
  gatesPassed?: string[];
  blockers?: string[];
  hasSignature?: boolean;
  hasTrustedTimestamp?: boolean;
}

export function ComplianceStatusCard({
  dataRichness,
  compliance,
  gatesPassed = [],
  blockers = [],
  hasSignature,
  hasTrustedTimestamp,
}: ComplianceStatusCardProps) {
  const isCourtAdmissible = dataRichness === 'court_admissible';
  const isEnhanced = dataRichness === 'enhanced';

  return (
    <Card className={`border-2 ${
      isCourtAdmissible ? 'border-green-300 bg-green-50/30' :
      isEnhanced ? 'border-blue-300 bg-blue-50/30' :
      'border-gray-300'
    }`}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Scale className="h-5 w-5" />
            <span>Compliance Status</span>
          </div>
          <Badge
            variant="outline"
            className={`${
              isCourtAdmissible ? 'bg-green-100 text-green-800 border-green-300' :
              isEnhanced ? 'bg-blue-100 text-blue-800 border-blue-300' :
              'bg-gray-100 text-gray-800 border-gray-300'
            }`}
          >
            {dataRichness || 'standard'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Gates Status */}
        <div className="space-y-3">
          <div className="text-sm font-semibold text-gray-700">Verification Gates</div>

          <div className="grid grid-cols-2 gap-3">
            {/* Signature Gate */}
            <div className={`flex items-center gap-2 p-3 rounded-lg border ${
              hasSignature || gatesPassed.includes('signature_verified')
                ? 'bg-green-50 border-green-200'
                : 'bg-gray-50 border-gray-200'
            }`}>
              {hasSignature || gatesPassed.includes('signature_verified') ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <XCircle className="h-4 w-4 text-gray-400" />
              )}
              <div>
                <div className="text-xs font-medium text-gray-900">Signature</div>
                <div className="text-xs text-gray-600">
                  {hasSignature || gatesPassed.includes('signature_verified')
                    ? 'Verified'
                    : 'Not verified'}
                </div>
              </div>
            </div>

            {/* Timestamp Gate */}
            <div className={`flex items-center gap-2 p-3 rounded-lg border ${
              hasTrustedTimestamp || gatesPassed.includes('timestamp_verified')
                ? 'bg-green-50 border-green-200'
                : 'bg-gray-50 border-gray-200'
            }`}>
              {hasTrustedTimestamp || gatesPassed.includes('timestamp_verified') ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <XCircle className="h-4 w-4 text-gray-400" />
              )}
              <div>
                <div className="text-xs font-medium text-gray-900">Timestamp</div>
                <div className="text-xs text-gray-600">
                  {hasTrustedTimestamp || gatesPassed.includes('timestamp_verified')
                    ? 'RFC 3161 Verified'
                    : 'Local only'}
                </div>
              </div>
            </div>

            {/* Plain Language Gate */}
            <div className={`flex items-center gap-2 p-3 rounded-lg border ${
              gatesPassed.includes('plain_language_summary')
                ? 'bg-green-50 border-green-200'
                : 'bg-gray-50 border-gray-200'
            }`}>
              {gatesPassed.includes('plain_language_summary') ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <XCircle className="h-4 w-4 text-gray-400" />
              )}
              <div>
                <div className="text-xs font-medium text-gray-900">Plain Language</div>
                <div className="text-xs text-gray-600">
                  {gatesPassed.includes('plain_language_summary')
                    ? 'EU AI Act Art. 13'
                    : 'Not available'}
                </div>
              </div>
            </div>

            {/* Semantic Alignment Gate */}
            <div className={`flex items-center gap-2 p-3 rounded-lg border ${
              gatesPassed.includes('no_semantic_drift')
                ? 'bg-green-50 border-green-200'
                : 'bg-yellow-50 border-yellow-200'
            }`}>
              {gatesPassed.includes('no_semantic_drift') ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
              )}
              <div>
                <div className="text-xs font-medium text-gray-900">Semantic Alignment</div>
                <div className="text-xs text-gray-600">
                  {gatesPassed.includes('no_semantic_drift')
                    ? 'No drift detected'
                    : 'Unchecked'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Compliance Indicators */}
        {compliance && (
          <div className="space-y-3">
            <div className="text-sm font-semibold text-gray-700">Compliance Claims</div>
            <div className="space-y-2">
              {/* Daubert Standard */}
              <div className={`flex items-center justify-between p-3 rounded-lg ${
                compliance.daubert_standard ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'
              }`}>
                <div className="flex items-center gap-2">
                  <Scale className={`h-4 w-4 ${compliance.daubert_standard ? 'text-green-600' : 'text-gray-400'}`} />
                  <span className="text-sm font-medium">Daubert Standard</span>
                </div>
                <Badge variant="outline" className={
                  compliance.daubert_standard
                    ? 'bg-green-100 text-green-800 border-green-300'
                    : 'bg-gray-100 text-gray-600 border-gray-300'
                }>
                  {compliance.daubert_standard ? 'Compliant' : 'Not Claimed'}
                </Badge>
              </div>

              {/* Insurance Ready */}
              <div className={`flex items-center justify-between p-3 rounded-lg ${
                compliance.insurance_ready ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'
              }`}>
                <div className="flex items-center gap-2">
                  <Shield className={`h-4 w-4 ${compliance.insurance_ready ? 'text-green-600' : 'text-gray-400'}`} />
                  <span className="text-sm font-medium">Insurance Ready</span>
                </div>
                <Badge variant="outline" className={
                  compliance.insurance_ready
                    ? 'bg-green-100 text-green-800 border-green-300'
                    : 'bg-gray-100 text-gray-600 border-gray-300'
                }>
                  {compliance.insurance_ready ? 'Ready' : 'Not Ready'}
                </Badge>
              </div>

              {/* EU AI Act Article 13 */}
              <div className={`flex items-center justify-between p-3 rounded-lg ${
                compliance.eu_ai_act_article_13 ? 'bg-green-50 border border-green-200' : 'bg-gray-50 border border-gray-200'
              }`}>
                <div className="flex items-center gap-2">
                  <FileCheck className={`h-4 w-4 ${compliance.eu_ai_act_article_13 ? 'text-green-600' : 'text-gray-400'}`} />
                  <span className="text-sm font-medium">EU AI Act Art. 13</span>
                </div>
                <Badge variant="outline" className={
                  compliance.eu_ai_act_article_13
                    ? 'bg-green-100 text-green-800 border-green-300'
                    : 'bg-gray-100 text-gray-600 border-gray-300'
                }>
                  {compliance.eu_ai_act_article_13 ? 'Compliant' : 'Not Compliant'}
                </Badge>
              </div>
            </div>
          </div>
        )}

        {/* Blockers */}
        {blockers && blockers.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <span className="text-sm font-semibold text-yellow-900">Compliance Blockers</span>
            </div>
            <ul className="space-y-1">
              {blockers.map((blocker, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-yellow-800">
                  <span className="mt-1">-</span>
                  <span>{blocker}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Explanation */}
        <div className="text-xs text-gray-500 bg-gray-50 rounded p-3">
          <span className="font-semibold">Honest compliance:</span>{' '}
          Labels are only claimed when verification gates actually pass. Court-admissible
          requires cryptographic signature + trusted RFC 3161 timestamp. Insurance-ready
          requires historical accuracy data. This prevents &quot;theater&quot; compliance claims.
        </div>
      </CardContent>
    </Card>
  );
}
