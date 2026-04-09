'use client';

import { useState, useMemo } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Wrench,
  ChevronDown,
  ChevronRight,
  BarChart3,
} from 'lucide-react';

interface ToolInvocation {
  tool: string;
  call_id: string;
  arguments: string;
  timestamp: string;
  result?: string;
  reasoning_before?: string;
}

interface ToolCallGraph {
  invocations: ToolInvocation[];
  tool_frequency: Record<string, number>;
  total_tool_calls: number;
  unique_tools: number;
}

interface ToolCallGraphCardProps {
  toolCallGraph: ToolCallGraph;
}

// Color palette for tools
const TOOL_COLORS: Record<string, string> = {
  Bash: 'bg-green-500',
  Edit: 'bg-blue-500',
  Read: 'bg-purple-500',
  Write: 'bg-indigo-500',
  Grep: 'bg-orange-500',
  Glob: 'bg-teal-500',
  TaskCreate: 'bg-yellow-500',
  TaskUpdate: 'bg-yellow-600',
  TaskList: 'bg-yellow-400',
  TaskOutput: 'bg-yellow-700',
  Task: 'bg-yellow-500',
  WebFetch: 'bg-red-500',
};

function getToolColor(tool: string): string {
  return TOOL_COLORS[tool] || 'bg-gray-500';
}

function truncateArgs(args: string, max: number = 120): string {
  try {
    const parsed = JSON.parse(args);
    const summary = Object.entries(parsed)
      .map(([k, v]) => {
        const val = typeof v === 'string' ? v : JSON.stringify(v);
        return `${k}: ${val.length > 60 ? val.slice(0, 60) + '…' : val}`;
      })
      .join(', ');
    return summary.length > max ? summary.slice(0, max) + '…' : summary;
  } catch {
    return args.length > max ? args.slice(0, max) + '…' : args;
  }
}

export function ToolCallGraphCard({ toolCallGraph }: ToolCallGraphCardProps) {
  const [showInvocations, setShowInvocations] = useState(false);
  const [expandedInvocations, setExpandedInvocations] = useState<Set<number>>(new Set());
  const [visibleCount, setVisibleCount] = useState(25);

  const { invocations, tool_frequency, total_tool_calls, unique_tools } = toolCallGraph;

  // Sort frequency by count descending
  const sortedFrequency = useMemo(
    () => Object.entries(tool_frequency).sort((a, b) => b[1] - a[1]),
    [tool_frequency]
  );

  const maxFreq = sortedFrequency.length > 0 ? sortedFrequency[0][1] : 1;

  const toggleInvocation = (index: number) => {
    setExpandedInvocations(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Wrench className="h-5 w-5" />
            <span>Tool Usage</span>
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
              {total_tool_calls} calls
            </Badge>
            <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
              {unique_tools} tools
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Frequency bar chart */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="h-4 w-4 text-gray-500" />
            <h4 className="text-sm font-semibold text-gray-700">Tool Frequency</h4>
          </div>
          <div className="space-y-2">
            {sortedFrequency.map(([tool, count]) => (
              <div key={tool} className="flex items-center gap-3">
                <div className="w-24 text-right">
                  <span className="text-xs font-mono text-gray-700">{tool}</span>
                </div>
                <div className="flex-1 relative">
                  <div className="h-6 bg-gray-100 rounded overflow-hidden">
                    <div
                      className={`h-full ${getToolColor(tool)} rounded transition-all opacity-80`}
                      style={{ width: `${(count / maxFreq) * 100}%` }}
                    />
                  </div>
                </div>
                <div className="w-12 text-right">
                  <span className="text-xs font-semibold text-gray-900">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Invocations list */}
        <div className="border-t pt-4">
          <button
            className="flex items-center gap-2 text-sm font-semibold text-gray-700 hover:text-gray-900 transition-colors"
            onClick={() => setShowInvocations(!showInvocations)}
          >
            {showInvocations ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
            Invocation Log ({invocations.length})
          </button>

          {showInvocations && (
            <div className="mt-3 space-y-1">
              {invocations.slice(0, visibleCount).map((inv, i) => (
                <div key={i} className="border border-gray-100 rounded overflow-hidden">
                  <button
                    className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-gray-50 transition-colors text-left"
                    onClick={() => toggleInvocation(i)}
                  >
                    {expandedInvocations.has(i) ? (
                      <ChevronDown className="h-3 w-3 text-gray-400 flex-shrink-0" />
                    ) : (
                      <ChevronRight className="h-3 w-3 text-gray-400 flex-shrink-0" />
                    )}
                    <span className="text-xs font-mono text-gray-400 w-8">#{i + 1}</span>
                    <Badge
                      variant="outline"
                      className={`text-xs px-1.5 py-0 ${getToolColor(inv.tool)} text-white border-0`}
                    >
                      {inv.tool}
                    </Badge>
                    <span className="text-xs text-gray-500 truncate flex-1">
                      {truncateArgs(inv.arguments)}
                    </span>
                    <span className="text-xs text-gray-400 flex-shrink-0">
                      {new Date(inv.timestamp).toLocaleTimeString()}
                    </span>
                  </button>
                  {expandedInvocations.has(i) && (
                    <div className="px-3 py-2 bg-gray-50 border-t border-gray-100 space-y-2">
                      <div>
                        <span className="text-xs font-semibold text-gray-600">Arguments:</span>
                        <pre className="text-xs font-mono text-gray-700 whitespace-pre-wrap mt-1 max-h-48 overflow-y-auto">
                          {(() => {
                            try {
                              return JSON.stringify(JSON.parse(inv.arguments), null, 2);
                            } catch {
                              return inv.arguments;
                            }
                          })()}
                        </pre>
                      </div>
                      {inv.reasoning_before && (
                        <div>
                          <span className="text-xs font-semibold text-gray-600">Reasoning:</span>
                          <p className="text-xs text-gray-700 mt-1">{inv.reasoning_before}</p>
                        </div>
                      )}
                      <div className="text-xs text-gray-400">
                        Call ID: {inv.call_id}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {invocations.length > visibleCount && (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full mt-2"
                  onClick={() => setVisibleCount(prev => prev + 50)}
                >
                  Show more ({invocations.length - visibleCount} remaining)
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
