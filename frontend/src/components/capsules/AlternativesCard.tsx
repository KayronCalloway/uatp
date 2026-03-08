'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { GitBranch, CheckCircle, XCircle, TrendingUp } from 'lucide-react';
import { Alternative } from '@/types/api';

interface AlternativesCardProps {
  alternatives: Alternative[];
}

export function AlternativesCard({ alternatives }: AlternativesCardProps) {
  if (!alternatives || alternatives.length === 0) {
    return null;
  }

  // Sort by score (highest first)
  const sortedAlternatives = [...alternatives].sort((a, b) =>
    (b.score || 0) - (a.score || 0)
  );

  const maxScore = Math.max(...sortedAlternatives.map(a => a.score || 0));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <GitBranch className="w-5 h-5 text-indigo-600" />
          Alternatives Considered ({alternatives.length})
          <span className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded ml-auto">
            Methodology Shown
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {sortedAlternatives.map((alt, index) => {
            const isSelected = alt.score === maxScore;
            const scorePercent = alt.score ? (alt.score * 100).toFixed(1) : 'N/A';

            return (
              <div
                key={index}
                className={`p-4 rounded-lg border-2 transition-all ${
                  isSelected
                    ? 'bg-green-50 border-green-300'
                    : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                }`}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start gap-3 flex-1">
                    {isSelected ? (
                      <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                    ) : (
                      <XCircle className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900">
                        {alt.option}
                      </div>
                      {isSelected && (
                        <div className="text-xs text-green-700 font-medium mt-1">
                           Selected Option
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Score */}
                  {alt.score !== undefined && (
                    <div className="flex flex-col items-end">
                      <div className={`text-xl font-bold ${
                        isSelected ? 'text-green-700' : 'text-gray-600'
                      }`}>
                        {scorePercent}
                      </div>
                      <div className="text-xs text-gray-500">score</div>
                    </div>
                  )}
                </div>

                {/* Score Bar */}
                {alt.score !== undefined && (
                  <div className="mb-3">
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          isSelected ? 'bg-green-500' : 'bg-gray-400'
                        }`}
                        style={{ width: `${(alt.score || 0) * 100}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Why Not Chosen */}
                {!isSelected && alt.why_not_chosen && (
                  <div className="p-3 bg-white rounded border border-gray-200">
                    <div className="text-xs text-gray-600 font-medium mb-1">
                      Why not chosen:
                    </div>
                    <div className="text-sm text-gray-800">
                      {alt.why_not_chosen}
                    </div>
                  </div>
                )}

                {/* Additional Data */}
                {alt.data && Object.keys(alt.data).length > 0 && (
                  <div className="mt-3 p-3 bg-white rounded border border-gray-200">
                    <div className="text-xs text-gray-600 font-medium mb-2">
                      Additional Details:
                    </div>
                    <div className="space-y-1">
                      {Object.entries(alt.data).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-sm">
                          <span className="text-gray-600">{key}:</span>
                          <span className="font-medium text-gray-800">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Methodology Note */}
        <div className="mt-4 p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
          <div className="flex items-start gap-2">
            <TrendingUp className="w-4 h-4 text-indigo-600 mt-0.5" />
            <div className="text-sm text-indigo-800">
              <span className="font-semibold">Court-Admissible Methodology:</span> This
              decision shows {alternatives.length} alternatives evaluated with scoring,
              demonstrating a systematic decision-making process required for Daubert admissibility.
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
