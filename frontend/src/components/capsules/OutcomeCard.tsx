'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Activity, CheckCircle, XCircle, DollarSign, Star, FileText, Clock } from 'lucide-react';
import { Outcome } from '@/types/api';
import { formatDate } from '@/lib/utils';

interface OutcomeCardProps {
  outcome: Outcome;
}

export function OutcomeCard({ outcome }: OutcomeCardProps) {
  if (!outcome) {
    return null;
  }

  const getResultColor = (result: string) => {
    switch (result) {
      case 'successful':
        return 'green';
      case 'failed':
        return 'red';
      case 'partial':
        return 'yellow';
      case 'pending':
        return 'blue';
      default:
        return 'gray';
    }
  };

  const color = getResultColor(outcome.result);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-emerald-600" />
          Actual Outcome (Ground Truth)
          <span className={`text-xs bg-${color}-100 text-${color}-800 px-2 py-1 rounded ml-auto capitalize`}>
            {outcome.result}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Main Status */}
          <div className={`p-4 bg-${color}-50 rounded-lg border-2 border-${color}-200`}>
            <div className="flex items-center gap-3 mb-3">
              {outcome.result === 'successful' ? (
                <CheckCircle className="w-8 h-8 text-green-600" />
              ) : outcome.result === 'failed' ? (
                <XCircle className="w-8 h-8 text-red-600" />
              ) : (
                <Activity className="w-8 h-8 text-gray-600" />
              )}
              <div>
                <div className={`text-lg font-bold text-${color}-900 capitalize`}>
                  {outcome.result}
                </div>
                <div className="text-sm text-gray-600 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Recorded: {formatDate(outcome.timestamp)}
                </div>
              </div>
            </div>

            {outcome.occurred !== undefined && (
              <div className="text-sm">
                <span className="text-gray-700">Event Occurred:</span>
                <span className={`ml-2 font-semibold ${outcome.occurred ? 'text-green-700' : 'text-red-700'}`}>
                  {outcome.occurred ? 'Yes' : 'No'}
                </span>
              </div>
            )}
          </div>

          {/* AI Accuracy */}
          {outcome.ai_was_correct !== undefined && (
            <div className={`p-4 rounded-lg border-2 ${
              outcome.ai_was_correct
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {outcome.ai_was_correct ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600" />
                  )}
                  <span className="font-semibold text-gray-900">
                    AI Prediction Accuracy
                  </span>
                </div>
                <span className={`text-lg font-bold ${
                  outcome.ai_was_correct ? 'text-green-700' : 'text-red-700'
                }`}>
                  {outcome.ai_was_correct ? 'Correct ✓' : 'Incorrect ✗'}
                </span>
              </div>
              {outcome.actual_vs_predicted && (
                <div className="mt-2 text-sm text-gray-700">
                  {outcome.actual_vs_predicted}
                </div>
              )}
            </div>
          )}

          {/* Financial Impact */}
          {outcome.financial_impact !== undefined && (
            <div className={`p-4 rounded-lg border ${
              outcome.financial_impact >= 0
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <DollarSign className={`w-5 h-5 ${
                    outcome.financial_impact >= 0 ? 'text-green-600' : 'text-red-600'
                  }`} />
                  <span className="font-semibold text-gray-900">Financial Impact</span>
                </div>
                <span className={`text-xl font-bold ${
                  outcome.financial_impact >= 0 ? 'text-green-700' : 'text-red-700'
                }`}>
                  {outcome.financial_impact >= 0 ? '+' : ''}
                  ${Math.abs(outcome.financial_impact).toLocaleString()}
                </span>
              </div>
            </div>
          )}

          {/* Customer Satisfaction */}
          {outcome.customer_satisfaction !== undefined && (
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Star className="w-5 h-5 text-blue-600" />
                  <span className="font-semibold text-gray-900">Customer Satisfaction</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex gap-0.5">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`w-4 h-4 ${
                          star <= outcome.customer_satisfaction!
                            ? 'fill-yellow-400 text-yellow-400'
                            : 'text-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                  <span className="text-lg font-bold text-blue-700">
                    {outcome.customer_satisfaction.toFixed(1)}/5
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Business Impact */}
          {outcome.business_impact && (
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <h4 className="font-semibold text-gray-900 mb-2">Business Impact</h4>
              <p className="text-gray-800 leading-relaxed">
                {outcome.business_impact}
              </p>
            </div>
          )}

          {/* Complications */}
          {outcome.complications && outcome.complications.length > 0 && (
            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <h4 className="font-semibold text-orange-900 mb-3">Complications</h4>
              <ul className="space-y-2">
                {outcome.complications.map((complication, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="text-orange-500 mt-1">⚠</span>
                    <span className="text-gray-800">{complication}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Lessons Learned */}
          {outcome.lessons_learned && (
            <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
              <h4 className="font-semibold text-indigo-900 mb-2">Lessons Learned</h4>
              <p className="text-gray-800 leading-relaxed">
                {outcome.lessons_learned}
              </p>
            </div>
          )}

          {/* Notes */}
          {outcome.notes && (
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-4 h-4 text-gray-600" />
                <h4 className="font-semibold text-gray-900">Additional Notes</h4>
              </div>
              <p className="text-gray-700 text-sm leading-relaxed">
                {outcome.notes}
              </p>
            </div>
          )}

          {/* ML Training Note */}
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
            <div className="flex items-start gap-2">
              <Activity className="w-4 h-4 text-emerald-600 mt-0.5" />
              <div className="text-sm text-emerald-800">
                <span className="font-semibold">Ground Truth Recorded:</span> This outcome
                data enables ML model improvement, insurance claim validation, and risk
                model calibration.
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
