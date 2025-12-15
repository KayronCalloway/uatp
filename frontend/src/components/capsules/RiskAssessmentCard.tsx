'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { TrendingUp, Shield, AlertTriangle, Activity, TrendingDown } from 'lucide-react';
import { RiskAssessment } from '@/types/api';

interface RiskAssessmentCardProps {
  riskAssessment: RiskAssessment;
}

export function RiskAssessmentCard({ riskAssessment }: RiskAssessmentCardProps) {
  if (!riskAssessment) {
    return null;
  }

  const {
    probability_correct,
    probability_wrong,
    expected_value,
    value_at_risk_95,
    expected_loss_if_wrong,
    expected_gain_if_correct,
    key_risk_factors,
    safeguards,
    failure_modes,
    similar_decisions_count,
    historical_accuracy
  } = riskAssessment;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-purple-600" />
          Risk Assessment
          <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded ml-auto">
            Insurance-Ready
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Probability Metrics */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center justify-between">
                <span className="text-sm text-green-700 font-medium">
                  Probability Correct
                </span>
                <TrendingUp className="w-4 h-4 text-green-600" />
              </div>
              <div className="mt-2 text-2xl font-bold text-green-800">
                {(probability_correct * 100).toFixed(1)}%
              </div>
            </div>

            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center justify-between">
                <span className="text-sm text-red-700 font-medium">
                  Probability Wrong
                </span>
                <TrendingDown className="w-4 h-4 text-red-600" />
              </div>
              <div className="mt-2 text-2xl font-bold text-red-800">
                {(probability_wrong * 100).toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Financial Impact */}
          {(expected_value !== undefined || value_at_risk_95 !== undefined) && (
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-900">Financial Impact</h4>
              <div className="grid grid-cols-2 gap-4">
                {expected_value !== undefined && (
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded">
                    <span className="text-sm text-gray-700">Expected Value:</span>
                    <span className={`font-bold ${expected_value >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {expected_value >= 0 ? '+' : ''}${expected_value.toLocaleString()}
                    </span>
                  </div>
                )}

                {value_at_risk_95 !== undefined && (
                  <div className="flex justify-between items-center p-3 bg-orange-50 rounded">
                    <span className="text-sm text-gray-700">VaR (95%):</span>
                    <span className="font-bold text-orange-600">
                      -${Math.abs(value_at_risk_95).toLocaleString()}
                    </span>
                  </div>
                )}

                {expected_gain_if_correct !== undefined && (
                  <div className="flex justify-between items-center p-3 bg-green-50 rounded">
                    <span className="text-sm text-gray-700">If Correct:</span>
                    <span className="font-bold text-green-600">
                      +${expected_gain_if_correct.toLocaleString()}
                    </span>
                  </div>
                )}

                {expected_loss_if_wrong !== undefined && (
                  <div className="flex justify-between items-center p-3 bg-red-50 rounded">
                    <span className="text-sm text-gray-700">If Wrong:</span>
                    <span className="font-bold text-red-600">
                      -${Math.abs(expected_loss_if_wrong).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Key Risk Factors */}
          {key_risk_factors && key_risk_factors.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-orange-600" />
                Key Risk Factors
              </h4>
              <ul className="space-y-2">
                {key_risk_factors.map((factor, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="text-orange-500 mt-1">▸</span>
                    <span className="text-gray-700">{factor}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Safeguards */}
          {safeguards && safeguards.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <Shield className="w-4 h-4 text-green-600" />
                Safeguards in Place
              </h4>
              <div className="grid gap-2">
                {safeguards.map((safeguard, i) => (
                  <div key={i} className="flex items-start gap-2 p-3 bg-green-50 rounded-lg border border-green-200">
                    <Shield className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-800">{safeguard}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Failure Modes */}
          {failure_modes && failure_modes.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-900">Failure Mode Analysis</h4>
              <div className="space-y-3">
                {failure_modes.map((mode, i) => (
                  <div key={i} className="p-4 border rounded-lg space-y-2 bg-gray-50">
                    <div className="flex items-start justify-between">
                      <span className="font-medium text-gray-900">{mode.scenario}</span>
                      <span className="text-sm font-semibold text-orange-600">
                        {(mode.probability * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="text-sm text-gray-700">
                      <span className="font-medium text-green-700">Mitigation:</span> {mode.mitigation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Historical Context */}
          {(similar_decisions_count !== undefined || historical_accuracy !== undefined) && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-blue-600" />
                <h4 className="font-semibold text-blue-900">Historical Context</h4>
              </div>
              <div className="space-y-2">
                {similar_decisions_count !== undefined && (
                  <div className="flex justify-between text-sm">
                    <span className="text-blue-700">Similar Decisions:</span>
                    <span className="font-semibold text-blue-900">
                      {similar_decisions_count.toLocaleString()}
                    </span>
                  </div>
                )}
                {historical_accuracy !== undefined && (
                  <div className="flex justify-between text-sm">
                    <span className="text-blue-700">Historical Accuracy:</span>
                    <span className="font-semibold text-blue-900">
                      {(historical_accuracy * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Insurance Note */}
          <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
            <div className="flex items-start gap-2">
              <Shield className="w-4 h-4 text-purple-600 mt-0.5" />
              <div className="text-sm text-purple-800">
                <span className="font-semibold">Insurance Ready:</span> This risk assessment
                includes quantitative probabilities, financial impacts, and safeguards -
                enabling accurate insurance premium calculation.
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
