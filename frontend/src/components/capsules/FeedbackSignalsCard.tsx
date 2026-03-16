'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  MessageSquare,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  Zap,
} from 'lucide-react';

interface FeedbackSignals {
  correction_count: number;
  requery_count: number;
  refinement_count: number;
  acceptance_count: number;
  abandonment_detected: boolean;
  correction_rate: number;
  acceptance_rate: number;
  net_sentiment: number;
  inferred_reward: number;
}

interface FeedbackSignalsCardProps {
  feedbackSignals: FeedbackSignals;
}

export function FeedbackSignalsCard({ feedbackSignals }: FeedbackSignalsCardProps) {
  const {
    correction_count,
    requery_count,
    refinement_count,
    acceptance_count,
    abandonment_detected,
    correction_rate,
    acceptance_rate,
    net_sentiment,
    inferred_reward,
  } = feedbackSignals;

  // Determine overall quality based on inferred reward
  const getQualityLevel = (reward: number) => {
    if (reward >= 0.8) return { label: 'Excellent', color: 'bg-green-500', textColor: 'text-green-700' };
    if (reward >= 0.6) return { label: 'Good', color: 'bg-blue-500', textColor: 'text-blue-700' };
    if (reward >= 0.4) return { label: 'Mixed', color: 'bg-yellow-500', textColor: 'text-yellow-700' };
    return { label: 'Needs Improvement', color: 'bg-red-500', textColor: 'text-red-700' };
  };

  const quality = getQualityLevel(inferred_reward);

  // Calculate total positive and negative signals
  const positiveSignals = acceptance_count + refinement_count;
  const negativeSignals = correction_count + requery_count + (abandonment_detected ? 1 : 0);
  const totalSignals = positiveSignals + negativeSignals;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <MessageSquare className="h-5 w-5" />
            <span>Conversation Feedback</span>
          </CardTitle>
          <Badge
            variant="outline"
            className={`${quality.textColor} border-current`}
          >
            {quality.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Main Reward Score */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-blue-600" />
              <span className="text-sm font-semibold text-blue-900">Response Quality Score</span>
            </div>
            <span className="text-3xl font-bold text-blue-900">
              {(inferred_reward * 100).toFixed(0)}%
            </span>
          </div>

          {/* Progress bar */}
          <div className="relative h-3 bg-blue-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${quality.color}`}
              style={{ width: `${inferred_reward * 100}%` }}
            />
          </div>

          <p className="text-xs text-blue-700 mt-2">
            Based on implicit user feedback signals from the conversation
          </p>
        </div>

        {/* Signal Counts Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {/* Acceptance */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-xs font-medium text-green-700">Accepted</span>
            </div>
            <div className="text-2xl font-bold text-green-900">{acceptance_count}</div>
          </div>

          {/* Refinement */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="h-4 w-4 text-blue-600" />
              <span className="text-xs font-medium text-blue-700">Refined</span>
            </div>
            <div className="text-2xl font-bold text-blue-900">{refinement_count}</div>
          </div>

          {/* Corrections */}
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <XCircle className="h-4 w-4 text-orange-600" />
              <span className="text-xs font-medium text-orange-700">Corrections</span>
            </div>
            <div className="text-2xl font-bold text-orange-900">{correction_count}</div>
          </div>

          {/* Re-queries */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <RefreshCw className="h-4 w-4 text-purple-600" />
              <span className="text-xs font-medium text-purple-700">Re-queries</span>
            </div>
            <div className="text-2xl font-bold text-purple-900">{requery_count}</div>
          </div>
        </div>

        {/* Rates and Sentiment */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Acceptance Rate */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <ThumbsUp className="h-4 w-4 text-green-600" />
                <span className="text-xs font-medium text-gray-700">Acceptance Rate</span>
              </div>
              <span className={`text-lg font-bold ${
                acceptance_rate >= 0.5 ? 'text-green-700' : 'text-gray-700'
              }`}>
                {(acceptance_rate * 100).toFixed(0)}%
              </span>
            </div>
            <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 rounded-full"
                style={{ width: `${acceptance_rate * 100}%` }}
              />
            </div>
          </div>

          {/* Correction Rate */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <ThumbsDown className="h-4 w-4 text-orange-600" />
                <span className="text-xs font-medium text-gray-700">Correction Rate</span>
              </div>
              <span className={`text-lg font-bold ${
                correction_rate >= 0.3 ? 'text-orange-700' : 'text-gray-700'
              }`}>
                {(correction_rate * 100).toFixed(0)}%
              </span>
            </div>
            <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-orange-500 rounded-full"
                style={{ width: `${correction_rate * 100}%` }}
              />
            </div>
          </div>

          {/* Net Sentiment */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                {net_sentiment >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                )}
                <span className="text-xs font-medium text-gray-700">Net Sentiment</span>
              </div>
              <span className={`text-lg font-bold ${
                net_sentiment >= 0.2 ? 'text-green-700' :
                net_sentiment <= -0.2 ? 'text-red-700' : 'text-gray-700'
              }`}>
                {net_sentiment >= 0 ? '+' : ''}{net_sentiment.toFixed(2)}
              </span>
            </div>
            {/* Sentiment gauge: -1 to +1 centered at 0 */}
            <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
              <div className="absolute left-1/2 w-0.5 h-full bg-gray-400" />
              {net_sentiment >= 0 ? (
                <div
                  className="absolute left-1/2 h-full bg-green-500 rounded-r-full"
                  style={{ width: `${net_sentiment * 50}%` }}
                />
              ) : (
                <div
                  className="absolute right-1/2 h-full bg-red-500 rounded-l-full"
                  style={{ width: `${Math.abs(net_sentiment) * 50}%` }}
                />
              )}
            </div>
          </div>
        </div>

        {/* Abandonment Warning */}
        {abandonment_detected && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-red-900">Abandonment Detected</h4>
                <p className="text-xs text-red-700 mt-1">
                  The user indicated giving up or moving on from this task. This may indicate
                  the responses weren't meeting their needs.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Summary */}
        {totalSignals > 0 && (
          <div className="border-t pt-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">
                Total signals detected: <span className="font-semibold text-gray-900">{totalSignals}</span>
              </span>
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1 text-green-600">
                  <ThumbsUp className="h-4 w-4" />
                  {positiveSignals} positive
                </span>
                <span className="flex items-center gap-1 text-orange-600">
                  <ThumbsDown className="h-4 w-4" />
                  {negativeSignals} negative
                </span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
