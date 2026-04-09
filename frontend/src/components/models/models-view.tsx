'use client';

import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Cpu,
  BarChart3,
  MessageSquare,
  Coins,
  Brain,
  Wrench,
  TrendingUp,
  TrendingDown,
  Zap,
} from 'lucide-react';
import { AnyCapsule } from '@/types/api';

interface ModelStats {
  model: string;
  capsuleCount: number;
  correctionRate: number;
  acceptanceRate: number;
  avgReward: number;
  totalCorrectionCount: number;
  totalAcceptanceCount: number;
  totalTokens: number;
  avgTokensPerSession: number;
  hasThinkingCount: number;
  hasToolsCount: number;
  avgToolCalls: number;
  cacheHitRate: number;
}

interface AgentStats {
  agentId: string;
  capsuleCount: number;
  correctionRate: number;
  acceptanceRate: number;
  avgReward: number;
  models: string[];
}

function formatTokens(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return n.toLocaleString();
}

export function ModelsView() {
  // Fetch all capsules (use a large page)
  const { data, isLoading } = useQuery({
    queryKey: ['capsules-for-models', { page: 1, per_page: 500, demo_mode: false }],
    queryFn: () => api.getCapsules({ page: 1, per_page: 500, demo_mode: false }),
    staleTime: 1000 * 60 * 5,
  });

  const capsules: AnyCapsule[] = useMemo(() => {
    if (!data) return [];
    return ('capsules' in data ? data.capsules : Array.isArray(data) ? data : []) as AnyCapsule[];
  }, [data]);

  // Compute per-model stats
  const modelStats = useMemo(() => {
    const byModel: Record<string, {
      count: number;
      corrections: number;
      acceptances: number;
      rewardSum: number;
      rewardCount: number;
      tokens: number;
      thinkingCount: number;
      toolsCount: number;
      totalToolCalls: number;
      cacheHitSum: number;
      cacheHitCount: number;
    }> = {};

    capsules.forEach(cap => {
      const model = cap.payload?.economics?.model || 'unknown';
      if (!byModel[model]) {
        byModel[model] = {
          count: 0, corrections: 0, acceptances: 0,
          rewardSum: 0, rewardCount: 0, tokens: 0,
          thinkingCount: 0, toolsCount: 0, totalToolCalls: 0,
          cacheHitSum: 0, cacheHitCount: 0,
        };
      }
      const s = byModel[model];
      s.count++;

      const fb = cap.payload?.session_metadata?.feedback_signals;
      if (fb) {
        s.corrections += fb.correction_count || 0;
        s.acceptances += fb.acceptance_count || 0;
        if (fb.inferred_reward !== undefined) {
          s.rewardSum += fb.inferred_reward;
          s.rewardCount++;
        }
      }

      const econ = cap.payload?.economics;
      if (econ) {
        s.tokens += (econ.input_tokens || 0) + (econ.output_tokens || 0);
        if (econ.cache_hit_rate !== undefined) {
          s.cacheHitSum += econ.cache_hit_rate;
          s.cacheHitCount++;
        }
      }

      if (cap.payload?.extended_thinking) s.thinkingCount++;
      if (cap.payload?.tool_call_graph) {
        s.toolsCount++;
        s.totalToolCalls += cap.payload.tool_call_graph.total_tool_calls || 0;
      }
    });

    const results: ModelStats[] = Object.entries(byModel)
      .map(([model, s]) => ({
        model,
        capsuleCount: s.count,
        correctionRate: s.corrections + s.acceptances > 0
          ? s.corrections / (s.corrections + s.acceptances) : 0,
        acceptanceRate: s.corrections + s.acceptances > 0
          ? s.acceptances / (s.corrections + s.acceptances) : 0,
        avgReward: s.rewardCount > 0 ? s.rewardSum / s.rewardCount : 0,
        totalCorrectionCount: s.corrections,
        totalAcceptanceCount: s.acceptances,
        totalTokens: s.tokens,
        avgTokensPerSession: s.count > 0 ? s.tokens / s.count : 0,
        hasThinkingCount: s.thinkingCount,
        hasToolsCount: s.toolsCount,
        avgToolCalls: s.toolsCount > 0 ? s.totalToolCalls / s.toolsCount : 0,
        cacheHitRate: s.cacheHitCount > 0 ? s.cacheHitSum / s.cacheHitCount : 0,
      }))
      .filter(s => s.model !== 'unknown')
      .sort((a, b) => b.capsuleCount - a.capsuleCount);

    return results;
  }, [capsules]);

  // Compute per-agent stats
  const agentStats = useMemo(() => {
    const byAgent: Record<string, {
      count: number;
      corrections: number;
      acceptances: number;
      rewardSum: number;
      rewardCount: number;
      models: Set<string>;
    }> = {};

    capsules.forEach(cap => {
      const agent = cap.agent_id || cap.verification?.signer || 'unknown';
      if (!byAgent[agent]) {
        byAgent[agent] = {
          count: 0, corrections: 0, acceptances: 0,
          rewardSum: 0, rewardCount: 0, models: new Set(),
        };
      }
      const s = byAgent[agent];
      s.count++;

      const model = cap.payload?.economics?.model;
      if (model) s.models.add(model);

      const fb = cap.payload?.session_metadata?.feedback_signals;
      if (fb) {
        s.corrections += fb.correction_count || 0;
        s.acceptances += fb.acceptance_count || 0;
        if (fb.inferred_reward !== undefined) {
          s.rewardSum += fb.inferred_reward;
          s.rewardCount++;
        }
      }
    });

    return Object.entries(byAgent)
      .map(([agentId, s]) => ({
        agentId,
        capsuleCount: s.count,
        correctionRate: s.corrections + s.acceptances > 0
          ? s.corrections / (s.corrections + s.acceptances) : 0,
        acceptanceRate: s.corrections + s.acceptances > 0
          ? s.acceptances / (s.corrections + s.acceptances) : 0,
        avgReward: s.rewardCount > 0 ? s.rewardSum / s.rewardCount : 0,
        models: Array.from(s.models),
      }))
      .sort((a, b) => b.capsuleCount - a.capsuleCount);
  }, [capsules]);

  // Summary stats
  const totalWithFeedback = capsules.filter(c => c.payload?.session_metadata?.feedback_signals).length;
  const totalWithEconomics = capsules.filter(c => c.payload?.economics).length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6">
      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Cross-Model Analysis</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{capsules.length}</div>
              <div className="text-xs text-gray-600">Total Capsules</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{modelStats.length}</div>
              <div className="text-xs text-gray-600">Models</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{agentStats.length}</div>
              <div className="text-xs text-gray-600">Agents</div>
            </div>
            <div className="text-center p-3 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">{totalWithFeedback}</div>
              <div className="text-xs text-gray-600">With Feedback</div>
            </div>
            <div className="text-center p-3 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{totalWithEconomics}</div>
              <div className="text-xs text-gray-600">With Economics</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Model Comparison Table */}
      {modelStats.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Cpu className="h-5 w-5" />
              <span>Models</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="py-2 px-3 font-semibold text-gray-700">Model</th>
                    <th className="py-2 px-3 font-semibold text-gray-700 text-center">Capsules</th>
                    <th className="py-2 px-3 font-semibold text-gray-700 text-center">
                      <div className="flex items-center gap-1 justify-center">
                        <MessageSquare className="h-3 w-3" /> Feedback
                      </div>
                    </th>
                    <th className="py-2 px-3 font-semibold text-gray-700 text-center">Reward</th>
                    <th className="py-2 px-3 font-semibold text-gray-700 text-center">
                      <div className="flex items-center gap-1 justify-center">
                        <Coins className="h-3 w-3" /> Tokens
                      </div>
                    </th>
                    <th className="py-2 px-3 font-semibold text-gray-700 text-center">Cache Hit</th>
                    <th className="py-2 px-3 font-semibold text-gray-700 text-center">
                      <div className="flex items-center gap-1 justify-center">
                        <Brain className="h-3 w-3" /> Thinking
                      </div>
                    </th>
                    <th className="py-2 px-3 font-semibold text-gray-700 text-center">
                      <div className="flex items-center gap-1 justify-center">
                        <Wrench className="h-3 w-3" /> Tools
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {modelStats.map(m => (
                    <tr key={m.model} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-3">
                        <span className="font-mono text-xs text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                          {m.model}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-center font-semibold">{m.capsuleCount}</td>
                      <td className="py-3 px-3 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <span className="text-green-600 flex items-center gap-0.5">
                            <TrendingUp className="h-3 w-3" />
                            {m.totalAcceptanceCount}
                          </span>
                          <span className="text-orange-600 flex items-center gap-0.5">
                            <TrendingDown className="h-3 w-3" />
                            {m.totalCorrectionCount}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-3 text-center">
                        {m.avgReward > 0 ? (
                          <Badge
                            variant="outline"
                            className={`${
                              m.avgReward >= 0.8 ? 'bg-green-50 text-green-700 border-green-200' :
                              m.avgReward >= 0.6 ? 'bg-blue-50 text-blue-700 border-blue-200' :
                              m.avgReward >= 0.4 ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                              'bg-red-50 text-red-700 border-red-200'
                            }`}
                          >
                            {(m.avgReward * 100).toFixed(0)}%
                          </Badge>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-center font-mono text-xs">
                        {m.totalTokens > 0 ? formatTokens(m.totalTokens) : '—'}
                      </td>
                      <td className="py-3 px-3 text-center">
                        {m.cacheHitRate > 0 ? (
                          <span className="text-purple-700 font-semibold">
                            {(m.cacheHitRate * 100).toFixed(1)}%
                          </span>
                        ) : '—'}
                      </td>
                      <td className="py-3 px-3 text-center">
                        {m.hasThinkingCount > 0 ? (
                          <span className="text-purple-600">{m.hasThinkingCount}</span>
                        ) : '—'}
                      </td>
                      <td className="py-3 px-3 text-center">
                        {m.hasToolsCount > 0 ? (
                          <span className="text-orange-600">
                            {m.hasToolsCount} <span className="text-gray-400 text-xs">({m.avgToolCalls.toFixed(0)} avg)</span>
                          </span>
                        ) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Agent Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5" />
            <span>Agents</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="py-2 px-3 font-semibold text-gray-700">Agent</th>
                  <th className="py-2 px-3 font-semibold text-gray-700 text-center">Capsules</th>
                  <th className="py-2 px-3 font-semibold text-gray-700 text-center">Corrections</th>
                  <th className="py-2 px-3 font-semibold text-gray-700 text-center">Acceptances</th>
                  <th className="py-2 px-3 font-semibold text-gray-700 text-center">Avg Reward</th>
                  <th className="py-2 px-3 font-semibold text-gray-700">Models Used</th>
                </tr>
              </thead>
              <tbody>
                {agentStats.slice(0, 20).map(a => (
                  <tr key={a.agentId} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-3">
                      <span className="font-mono text-xs">{a.agentId}</span>
                    </td>
                    <td className="py-3 px-3 text-center font-semibold">{a.capsuleCount}</td>
                    <td className="py-3 px-3 text-center">
                      {a.correctionRate > 0 ? (
                        <span className="text-orange-600">{(a.correctionRate * 100).toFixed(0)}%</span>
                      ) : '—'}
                    </td>
                    <td className="py-3 px-3 text-center">
                      {a.acceptanceRate > 0 ? (
                        <span className="text-green-600">{(a.acceptanceRate * 100).toFixed(0)}%</span>
                      ) : '—'}
                    </td>
                    <td className="py-3 px-3 text-center">
                      {a.avgReward > 0 ? (
                        <Badge
                          variant="outline"
                          className={`${
                            a.avgReward >= 0.8 ? 'bg-green-50 text-green-700 border-green-200' :
                            a.avgReward >= 0.6 ? 'bg-blue-50 text-blue-700 border-blue-200' :
                            'bg-yellow-50 text-yellow-700 border-yellow-200'
                          }`}
                        >
                          {(a.avgReward * 100).toFixed(0)}%
                        </Badge>
                      ) : '—'}
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex flex-wrap gap-1">
                        {a.models.map(m => (
                          <Badge key={m} variant="outline" className="text-xs font-mono bg-gray-50">
                            {m.replace(/^claude-/, 'c-').replace(/-2025\d+$/, '')}
                          </Badge>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* No data state */}
      {modelStats.length === 0 && agentStats.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center text-gray-500">
            <Cpu className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p className="text-lg font-medium">No enrichment data yet</p>
            <p className="text-sm mt-1">
              Capsules with economics, extended thinking, and tool call data will appear here.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
