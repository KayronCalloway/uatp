'use client';

import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Brain,
  ChevronDown,
  ChevronRight,
  Wrench,
  MessageSquare,
} from 'lucide-react';

interface ThinkingTurn {
  timestamp: string;
  thinking: string;
  thinking_length: number;
  response_length: number;
  had_tool_calls: boolean;
}

interface ExtendedThinking {
  turns: ThinkingTurn[];
  total_thinking_chars: number;
  total_response_chars: number;
  thinking_to_response_ratio: number;
  turns_with_thinking: number;
}

interface ExtendedThinkingCardProps {
  thinking: ExtendedThinking;
}

function formatChars(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}

function getDepthLabel(ratio: number): { label: string; color: string } {
  if (ratio > 2) return { label: 'Deep Thinking', color: 'bg-purple-100 text-purple-700 border-purple-200' };
  if (ratio >= 1) return { label: 'Balanced', color: 'bg-blue-100 text-blue-700 border-blue-200' };
  if (ratio >= 0.5) return { label: 'Action-Oriented', color: 'bg-green-100 text-green-700 border-green-200' };
  return { label: 'Shallow', color: 'bg-yellow-100 text-yellow-700 border-yellow-200' };
}

export function ExtendedThinkingCard({ thinking }: ExtendedThinkingCardProps) {
  const [expandedTurns, setExpandedTurns] = useState<Set<number>>(new Set());
  const [showAll, setShowAll] = useState(false);

  const { turns, total_thinking_chars, total_response_chars, thinking_to_response_ratio, turns_with_thinking } = thinking;
  const depth = getDepthLabel(thinking_to_response_ratio);

  const toggleTurn = (index: number) => {
    setExpandedTurns(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  // Show first 10 turns or all
  const displayTurns = showAll ? turns : turns.slice(0, 10);
  const hasMore = turns.length > 10;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Brain className="h-5 w-5" />
            <span>Extended Thinking</span>
          </CardTitle>
          <Badge variant="outline" className={depth.color}>
            {depth.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
            <div className="text-xs font-medium text-purple-700 mb-1">Thinking Turns</div>
            <div className="text-2xl font-bold text-purple-900">
              {turns_with_thinking}
              <span className="text-sm font-normal text-purple-600">/{turns.length}</span>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="text-xs font-medium text-blue-700 mb-1">Total Thinking</div>
            <div className="text-2xl font-bold text-blue-900">
              {formatChars(total_thinking_chars)}
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="text-xs font-medium text-green-700 mb-1">Total Response</div>
            <div className="text-2xl font-bold text-green-900">
              {formatChars(total_response_chars)}
            </div>
          </div>

          <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
            <div className="text-xs font-medium text-orange-700 mb-1">Think:Response</div>
            <div className="text-2xl font-bold text-orange-900">
              {thinking_to_response_ratio > 100
                ? '∞'
                : `${thinking_to_response_ratio.toFixed(1)}x`}
            </div>
          </div>
        </div>

        {/* Thinking/Response ratio bar */}
        {total_response_chars > 0 && (
          <div>
            <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
              <span>Thinking ({((total_thinking_chars / (total_thinking_chars + total_response_chars)) * 100).toFixed(0)}%)</span>
              <span>Response ({((total_response_chars / (total_thinking_chars + total_response_chars)) * 100).toFixed(0)}%)</span>
            </div>
            <div className="flex h-2 rounded-full overflow-hidden">
              <div
                className="bg-purple-500"
                style={{ width: `${(total_thinking_chars / (total_thinking_chars + total_response_chars)) * 100}%` }}
              />
              <div
                className="bg-blue-400"
                style={{ width: `${(total_response_chars / (total_thinking_chars + total_response_chars)) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Turns list */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">
            Thinking Turns ({turns.length})
          </h4>
          <div className="space-y-2">
            {displayTurns.map((turn, i) => (
              <div key={i} className="border border-gray-200 rounded-lg overflow-hidden">
                <button
                  className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
                  onClick={() => toggleTurn(i)}
                >
                  <div className="flex items-center gap-2">
                    {expandedTurns.has(i) ? (
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    )}
                    <span className="text-xs font-mono text-gray-500">#{i + 1}</span>
                    <span className="text-xs text-gray-600">
                      {formatChars(turn.thinking_length)} chars
                    </span>
                    {turn.had_tool_calls && (
                      <Wrench className="h-3 w-3 text-orange-500" />
                    )}
                    {turn.response_length > 0 && (
                      <div className="flex items-center gap-1">
                        <MessageSquare className="h-3 w-3 text-blue-500" />
                        <span className="text-xs text-blue-600">{formatChars(turn.response_length)}</span>
                      </div>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(turn.timestamp).toLocaleTimeString()}
                  </span>
                </button>
                {expandedTurns.has(i) && turn.thinking && (
                  <div className="px-3 py-2 bg-white border-t border-gray-100">
                    <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono leading-relaxed max-h-96 overflow-y-auto">
                      {turn.thinking}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>

          {hasMore && !showAll && (
            <Button
              variant="outline"
              size="sm"
              className="w-full mt-3"
              onClick={() => setShowAll(true)}
            >
              Show all {turns.length} turns
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
