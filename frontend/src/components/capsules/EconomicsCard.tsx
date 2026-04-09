'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Coins,
  Cpu,
  Zap,
  Database,
  Clock,
  Server,
} from 'lucide-react';

interface Economics {
  input_tokens?: number;
  output_tokens?: number;
  cache_read_tokens?: number;
  cache_write_tokens?: number;
  cache_hit_rate?: number;
  total_tokens?: number;
  model?: string;
  billing_provider?: string;
  estimated_cost_usd?: number;
  tokens_per_second?: number;
  time_to_first_token_ms?: number;
  // Ollama-specific
  eval_duration_ns?: number;
  total_duration_ns?: number;
  eval_count?: number;
}

interface EconomicsCardProps {
  economics: Economics;
}

function formatTokens(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString();
}

function formatCost(usd: number): string {
  if (usd < 0.01) return `$${usd.toFixed(4)}`;
  if (usd < 1) return `$${usd.toFixed(3)}`;
  return `$${usd.toFixed(2)}`;
}

function formatDuration(ns: number): string {
  const ms = ns / 1_000_000;
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function EconomicsCard({ economics }: EconomicsCardProps) {
  const {
    input_tokens,
    output_tokens,
    cache_read_tokens,
    cache_write_tokens,
    cache_hit_rate,
    total_tokens,
    model,
    billing_provider,
    estimated_cost_usd,
    tokens_per_second,
    time_to_first_token_ms,
    eval_duration_ns,
    total_duration_ns,
    eval_count,
  } = economics;

  const isOllama = billing_provider === 'ollama' || eval_duration_ns !== undefined;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Coins className="h-5 w-5" />
            <span>Economics</span>
          </CardTitle>
          <div className="flex items-center gap-2">
            {model && (
              <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200 font-mono text-xs">
                {model}
              </Badge>
            )}
            {billing_provider && (
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 text-xs capitalize">
                {billing_provider}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Token usage grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {input_tokens !== undefined && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-1">
                <Cpu className="h-3.5 w-3.5 text-blue-600" />
                <span className="text-xs font-medium text-blue-700">Input</span>
              </div>
              <div className="text-xl font-bold text-blue-900">
                {formatTokens(input_tokens)}
              </div>
            </div>
          )}

          {output_tokens !== undefined && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-1">
                <Zap className="h-3.5 w-3.5 text-green-600" />
                <span className="text-xs font-medium text-green-700">Output</span>
              </div>
              <div className="text-xl font-bold text-green-900">
                {formatTokens(output_tokens)}
              </div>
            </div>
          )}

          {cache_read_tokens !== undefined && cache_read_tokens > 0 && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-1">
                <Database className="h-3.5 w-3.5 text-purple-600" />
                <span className="text-xs font-medium text-purple-700">Cache Read</span>
              </div>
              <div className="text-xl font-bold text-purple-900">
                {formatTokens(cache_read_tokens)}
              </div>
            </div>
          )}

          {total_tokens !== undefined && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
              <div className="flex items-center gap-1.5 mb-1">
                <Server className="h-3.5 w-3.5 text-orange-600" />
                <span className="text-xs font-medium text-orange-700">Total</span>
              </div>
              <div className="text-xl font-bold text-orange-900">
                {formatTokens(total_tokens)}
              </div>
            </div>
          )}
        </div>

        {/* Cache hit rate bar */}
        {cache_hit_rate !== undefined && cache_hit_rate > 0 && (
          <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-purple-600" />
                <span className="text-sm font-semibold text-purple-900">Cache Hit Rate</span>
              </div>
              <span className="text-2xl font-bold text-purple-900">
                {(cache_hit_rate * 100).toFixed(1)}%
              </span>
            </div>
            <div className="relative h-3 bg-purple-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 rounded-full transition-all"
                style={{ width: `${cache_hit_rate * 100}%` }}
              />
            </div>
            {cache_write_tokens !== undefined && cache_write_tokens > 0 && (
              <div className="flex items-center justify-between mt-2 text-xs text-purple-700">
                <span>Cache writes: {formatTokens(cache_write_tokens)}</span>
                {cache_read_tokens !== undefined && (
                  <span>Cache reads: {formatTokens(cache_read_tokens)}</span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Performance metrics */}
        {(tokens_per_second || time_to_first_token_ms || eval_duration_ns) && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {tokens_per_second !== undefined && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <Zap className="h-3.5 w-3.5 text-yellow-600" />
                  <span className="text-xs font-medium text-gray-700">Throughput</span>
                </div>
                <div className="text-lg font-bold text-gray-900">
                  {tokens_per_second.toFixed(1)} <span className="text-xs font-normal text-gray-500">tok/s</span>
                </div>
              </div>
            )}

            {time_to_first_token_ms !== undefined && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <Clock className="h-3.5 w-3.5 text-blue-600" />
                  <span className="text-xs font-medium text-gray-700">TTFT</span>
                </div>
                <div className="text-lg font-bold text-gray-900">
                  {time_to_first_token_ms.toFixed(0)} <span className="text-xs font-normal text-gray-500">ms</span>
                </div>
              </div>
            )}

            {eval_duration_ns !== undefined && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <Clock className="h-3.5 w-3.5 text-green-600" />
                  <span className="text-xs font-medium text-gray-700">Eval Duration</span>
                </div>
                <div className="text-lg font-bold text-gray-900">
                  {formatDuration(eval_duration_ns)}
                </div>
              </div>
            )}

            {total_duration_ns !== undefined && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <Clock className="h-3.5 w-3.5 text-orange-600" />
                  <span className="text-xs font-medium text-gray-700">Total Duration</span>
                </div>
                <div className="text-lg font-bold text-gray-900">
                  {formatDuration(total_duration_ns)}
                </div>
              </div>
            )}

            {eval_count !== undefined && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <Cpu className="h-3.5 w-3.5 text-purple-600" />
                  <span className="text-xs font-medium text-gray-700">Eval Count</span>
                </div>
                <div className="text-lg font-bold text-gray-900">
                  {formatTokens(eval_count)}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Estimated cost */}
        {estimated_cost_usd !== undefined && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Coins className="h-4 w-4 text-yellow-600" />
                <span className="text-sm font-semibold text-yellow-900">Estimated Cost</span>
              </div>
              <span className="text-2xl font-bold text-yellow-900">
                {formatCost(estimated_cost_usd)}
              </span>
            </div>
          </div>
        )}

        {/* Ollama indicator */}
        {isOllama && !estimated_cost_usd && (
          <div className="text-xs text-gray-500 italic text-center">
            Local inference — no API cost
          </div>
        )}
      </CardContent>
    </Card>
  );
}
