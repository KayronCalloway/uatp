'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { MessageSquare, Info, Scale, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { PlainLanguageSummary } from '@/types/api';

interface PlainLanguageCardProps {
  summary: PlainLanguageSummary;
}

// Simplify overly technical text for plain language display
function simplifyText(text: string): string {
  if (!text) return '';

  // If text contains markdown tables or is very long, summarize it
  if (text.includes('|') && text.includes('---')) {
    // Extract key points from markdown table content
    const lines = text.split('\n').filter(line =>
      line.trim() &&
      !line.includes('---') &&
      !line.startsWith('|')
    );
    if (lines.length > 0) {
      return lines.slice(0, 2).join(' ').substring(0, 300) + (lines.length > 2 ? '...' : '');
    }
  }

  // Truncate very long text
  if (text.length > 400) {
    return text.substring(0, 400) + '...';
  }

  return text;
}

export function PlainLanguageCard({ summary }: PlainLanguageCardProps) {
  const [expanded, setExpanded] = useState(false);

  if (!summary) {
    return null;
  }

  const isLongDecision = summary.decision && summary.decision.length > 300;
  const displayDecision = expanded ? summary.decision : simplifyText(summary.decision);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-teal-600" />
          Plain Language Summary
          <span className="text-xs bg-teal-100 text-teal-800 px-2 py-1 rounded ml-auto">
            EU AI Act Article 13
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Decision */}
          <div className="p-4 bg-teal-50 rounded-lg border border-teal-200">
            <div className="flex items-center gap-2 mb-2">
              <Info className="w-5 h-5 text-teal-700" />
              <h4 className="font-semibold text-teal-900">Decision</h4>
            </div>
            <div className={expanded ? "max-h-96 overflow-y-auto" : ""}>
              <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {displayDecision}
              </p>
            </div>
            {isLongDecision && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="mt-2 text-sm text-teal-700 hover:text-teal-900 flex items-center gap-1"
              >
                {expanded ? (
                  <>Show less <ChevronUp className="w-4 h-4" /></>
                ) : (
                  <>Show full details <ChevronDown className="w-4 h-4" /></>
                )}
              </button>
            )}
          </div>

          {/* Why */}
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-2">Why This Decision?</h4>
            <p className="text-gray-800 leading-relaxed">
              {summary.why}
            </p>
          </div>

          {/* Key Factors */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">Key Factors</h4>
            <div className="space-y-2">
              {summary.key_factors.map((factor, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200"
                >
                  <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-semibold flex-shrink-0">
                    {index + 1}
                  </div>
                  <p className="text-gray-800 leading-relaxed flex-1">{factor}</p>
                </div>
              ))}
            </div>
          </div>

          {/* What If Different */}
          {summary.what_if_different && (
            <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
              <div className="flex items-center gap-2 mb-2">
                <HelpCircle className="w-5 h-5 text-amber-700" />
                <h4 className="font-semibold text-amber-900">
                  What Would Cause a Different Decision?
                </h4>
              </div>
              <p className="text-gray-800 leading-relaxed">
                {summary.what_if_different}
              </p>
            </div>
          )}

          {/* Your Rights */}
          {summary.your_rights && (
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center gap-2 mb-2">
                <Scale className="w-5 h-5 text-purple-700" />
                <h4 className="font-semibold text-purple-900">Your Rights</h4>
              </div>
              <p className="text-gray-800 leading-relaxed">
                {summary.your_rights}
              </p>
            </div>
          )}

          {/* How to Appeal */}
          {summary.how_to_appeal && (
            <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
              <h4 className="font-semibold text-indigo-900 mb-2">
                How to Request Review or Appeal
              </h4>
              <p className="text-gray-800 leading-relaxed">
                {summary.how_to_appeal}
              </p>
            </div>
          )}

          {/* Compliance Note */}
          <div className="p-3 bg-teal-50 border border-teal-200 rounded-lg">
            <div className="flex items-start gap-2">
              <Scale className="w-4 h-4 text-teal-600 mt-0.5" />
              <div className="text-sm text-teal-800">
                <span className="font-semibold">EU AI Act Compliant:</span> This plain
                language summary meets Article 13 transparency requirements, ensuring
                users can understand AI decisions in non-technical terms.
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
