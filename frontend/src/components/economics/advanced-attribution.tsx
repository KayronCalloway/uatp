'use client';

import { useState } from 'react';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  TrendingUp,
  DollarSign,
  Users,
  Brain,
  Network,
  Calculator,
  Award,
  PieChart,
  BarChart3,
  Target,
  Zap,
  Scale,
  Clock,
  GitBranch,
  AlertCircle,
  Play
} from 'lucide-react';

interface AttributionModel {
  id: string;
  name: string;
  type: 'direct' | 'collaborative' | 'temporal' | 'network' | 'impact';
  description: string;
  weight: number;
  active: boolean;
  formula: string;
  parameters: Record<string, number>;
}

interface AttributionResult {
  agentId: string;
  agentName: string;
  totalAttribution: number;
  breakdown: {
    direct: number;
    collaborative: number;
    temporal: number;
    network: number;
    impact: number;
  };
  rank: number;
  change: number;
  contributions: {
    capsules: number;
    quality: number;
    collaboration: number;
    impact: number;
  };
}

interface AttributionAnalysis {
  model: string;
  timestamp: string;
  totalValue: number;
  participants: number;
  results: AttributionResult[];
  modelWeights: Record<string, number>;
  convergence: number;
}

export function AdvancedAttribution() {
  const { isDemoMode } = useDemoMode();
  const [selectedModel, setSelectedModel] = useState<string>('hybrid');
  const [selectedAgent, setSelectedAgent] = useState<AttributionResult | null>(null);
  const [timeRange, setTimeRange] = useState<string>('30d');

  // Attribution models - only shown in demo mode
  const models: AttributionModel[] = isDemoMode ? [
    {
      id: 'direct',
      name: 'Direct Contribution',
      type: 'direct' as const,
      description: 'Simple attribution based on direct capsule contributions',
      weight: 0.3,
      active: true,
      formula: 'sum(capsule_value * quality_score)',
      parameters: { quality_threshold: 0.7, decay_rate: 0.95 }
    },
    {
      id: 'collaborative',
      name: 'Collaborative Impact',
      type: 'collaborative' as const,
      description: 'Attribution based on joint capsule creation and cross-references',
      weight: 0.25,
      active: true,
      formula: 'sum(collaboration_score * joint_value)',
      parameters: { collaboration_bonus: 1.5, min_collaborators: 2 }
    },
    {
      id: 'temporal',
      name: 'Temporal Dynamics',
      type: 'temporal' as const,
      description: 'Time-weighted attribution with recency bias and momentum',
      weight: 0.2,
      active: true,
      formula: 'sum(value * time_decay * momentum)',
      parameters: { decay_factor: 0.98, momentum_window: 7 }
    },
    {
      id: 'network',
      name: 'Network Effects',
      type: 'network' as const,
      description: 'Attribution based on network position and influence',
      weight: 0.15,
      active: true,
      formula: 'pagerank_score * influence_multiplier',
      parameters: { damping_factor: 0.85, influence_threshold: 0.1 }
    },
    {
      id: 'impact',
      name: 'Impact Measurement',
      type: 'impact' as const,
      description: 'Attribution based on downstream usage and citation impact',
      weight: 0.1,
      active: true,
      formula: 'sum(citation_count * citation_weight)',
      parameters: { citation_decay: 0.9, max_depth: 3 }
    }
  ] : [];

  // Mock attribution results - only shown in demo mode
  const analysis = isDemoMode ? ({
    model: 'hybrid',
    timestamp: new Date().toISOString(),
    totalValue: 567890.25,
    participants: 2156,
    results: [
      {
        agentId: 'agent-001',
        agentName: 'Dr. Sarah Chen',
        totalAttribution: 12847.50,
        breakdown: {
          direct: 4500.00,
          collaborative: 3200.00,
          temporal: 2500.00,
          network: 1800.00,
          impact: 847.50
        },
        rank: 1,
        change: 0.15,
        contributions: {
          capsules: 156,
          quality: 0.94,
          collaboration: 0.87,
          impact: 0.89
        }
      },
      {
        agentId: 'agent-002',
        agentName: 'Alex Rodriguez',
        totalAttribution: 9834.75,
        breakdown: {
          direct: 3800.00,
          collaborative: 2900.00,
          temporal: 1900.00,
          network: 1000.00,
          impact: 234.75
        },
        rank: 2,
        change: 0.08,
        contributions: {
          capsules: 134,
          quality: 0.89,
          collaboration: 0.92,
          impact: 0.76
        }
      },
      {
        agentId: 'agent-003',
        agentName: 'Dr. Michael Johnson',
        totalAttribution: 8765.25,
        breakdown: {
          direct: 3200.00,
          collaborative: 2100.00,
          temporal: 2000.00,
          network: 1200.00,
          impact: 265.25
        },
        rank: 3,
        change: -0.05,
        contributions: {
          capsules: 98,
          quality: 0.91,
          collaboration: 0.78,
          impact: 0.83
        }
      },
      {
        agentId: 'agent-004',
        agentName: 'Emma Williams',
        totalAttribution: 7234.80,
        breakdown: {
          direct: 2800.00,
          collaborative: 1900.00,
          temporal: 1600.00,
          network: 800.00,
          impact: 134.80
        },
        rank: 4,
        change: 0.12,
        contributions: {
          capsules: 87,
          quality: 0.86,
          collaboration: 0.84,
          impact: 0.71
        }
      },
      {
        agentId: 'agent-005',
        agentName: 'David Kim',
        totalAttribution: 6543.45,
        breakdown: {
          direct: 2400.00,
          collaborative: 1800.00,
          temporal: 1400.00,
          network: 700.00,
          impact: 243.45
        },
        rank: 5,
        change: 0.03,
        contributions: {
          capsules: 76,
          quality: 0.82,
          collaboration: 0.88,
          impact: 0.79
        }
      }
    ],
    modelWeights: {
      direct: 0.3,
      collaborative: 0.25,
      temporal: 0.2,
      network: 0.15,
      impact: 0.1
    },
    convergence: 0.94
  } as AttributionAnalysis) : null;

  const getModelIcon = (type: AttributionModel['type']) => {
    switch (type) {
      case 'direct': return <Target className="h-4 w-4" />;
      case 'collaborative': return <Network className="h-4 w-4" />;
      case 'temporal': return <Clock className="h-4 w-4" />;
      case 'network': return <GitBranch className="h-4 w-4" />;
      case 'impact': return <Zap className="h-4 w-4" />;
      default: return <Calculator className="h-4 w-4" />;
    }
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return '↗';
    if (change < 0) return '↘';
    return '→';
  };

  const renderModelConfiguration = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Scale className="h-5 w-5 mr-2" />
          Attribution Models
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {models.map((model) => (
            <div key={model.id} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center space-x-3">
                {getModelIcon(model.type)}
                <div>
                  <h4 className="font-medium">{model.name}</h4>
                  <p className="text-sm text-gray-500">{model.description}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className="text-sm font-medium">Weight: {(model.weight * 100).toFixed(0)}%</span>
                <Badge variant={model.active ? 'default' : 'secondary'}>
                  {model.active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">
              Model convergence: {((analysis?.convergence ?? 0) * 100).toFixed(1)}%
            </span>
            <Button variant="outline" size="sm">
              <Calculator className="h-4 w-4 mr-2" />
              Recalculate
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderAttributionResults = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Award className="h-5 w-5 mr-2" />
          Attribution Results
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {(analysis?.results ?? []).map((result) => (
            <div
              key={result.agentId}
              className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                selectedAgent?.agentId === result.agentId ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
              }`}
              onClick={() => setSelectedAgent(result)}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-full">
                    <span className="text-sm font-bold text-blue-600">#{result.rank}</span>
                  </div>
                  <div>
                    <h4 className="font-medium">{result.agentName}</h4>
                    <p className="text-sm text-gray-500">{result.agentId}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold">${result.totalAttribution.toLocaleString()}</div>
                  <div className={`text-sm ${getChangeColor(result.change)}`}>
                    {getChangeIcon(result.change)} {Math.abs(result.change * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-5 gap-2 mt-3">
                <div className="text-center">
                  <div className="text-xs text-gray-500">Direct</div>
                  <div className="text-sm font-medium">${result.breakdown.direct.toLocaleString()}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-500">Collab</div>
                  <div className="text-sm font-medium">${result.breakdown.collaborative.toLocaleString()}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-500">Temporal</div>
                  <div className="text-sm font-medium">${result.breakdown.temporal.toLocaleString()}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-500">Network</div>
                  <div className="text-sm font-medium">${result.breakdown.network.toLocaleString()}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-500">Impact</div>
                  <div className="text-sm font-medium">${result.breakdown.impact.toLocaleString()}</div>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t">
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Capsules:</span>
                    <span className="ml-1 font-medium">{result.contributions.capsules}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Quality:</span>
                    <span className="ml-1 font-medium">{(result.contributions.quality * 100).toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Collab:</span>
                    <span className="ml-1 font-medium">{(result.contributions.collaboration * 100).toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Impact:</span>
                    <span className="ml-1 font-medium">{(result.contributions.impact * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );

  const renderAnalytics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <PieChart className="h-5 w-5 mr-2" />
            Attribution Distribution
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(analysis?.modelWeights ?? {}).map(([model, weight]) => (
              <div key={model} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getModelIcon(model as AttributionModel['type'])}
                  <span className="capitalize">{model}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${weight * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">{(weight * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="h-5 w-5 mr-2" />
            System Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-500">Total Value:</span>
              <span className="font-medium">${(analysis?.totalValue ?? 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Participants:</span>
              <span className="font-medium">{(analysis?.participants ?? 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Convergence:</span>
              <span className="font-medium">{((analysis?.convergence ?? 0) * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Last Updated:</span>
              <span className="font-medium">{analysis?.timestamp ? new Date(analysis.timestamp).toLocaleTimeString() : 'N/A'}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div>
                <h1 className="text-2xl font-bold flex items-center">
                  <Brain className="h-6 w-6 mr-2" />
                  Advanced Attribution
                </h1>
                <p className="text-sm text-gray-600 mt-1">
                  {isDemoMode
                    ? 'Viewing simulated attribution analysis for demonstration'
                    : 'Multi-model attribution analysis and optimization'
                  }
                </p>
              </div>
              {isDemoMode && (
                <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-300">
                  <Play className="h-3 w-3 mr-1" />
                  Demo Data
                </Badge>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="px-3 py-2 border rounded-md"
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="1y">Last year</option>
              </select>
              {analysis && (
                <Button>
                  <Calculator className="h-4 w-4 mr-2" />
                  Recompute
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Show notice when in live mode with no data */}
      {!isDemoMode && !analysis && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
                <p className="text-sm text-blue-700">
                  Attribution analysis will appear here when available. Toggle Demo Mode ON to see sample analysis.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Overview Stats - Only show if we have analysis data */}
      {analysis && (
        <>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <DollarSign className="h-4 w-4 mr-2" />
              Total Attribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${(analysis?.totalValue ?? 0).toLocaleString()}</div>
            <p className="text-xs text-gray-500">Distributed value</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <Users className="h-4 w-4 mr-2" />
              Participants
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(analysis?.participants ?? 0).toLocaleString()}</div>
            <p className="text-xs text-gray-500">Active contributors</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <TrendingUp className="h-4 w-4 mr-2" />
              Convergence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{((analysis?.convergence ?? 0) * 100).toFixed(1)}%</div>
            <p className="text-xs text-gray-500">Model stability</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <Calculator className="h-4 w-4 mr-2" />
              Active Models
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{models.filter(m => m.active).length}</div>
            <p className="text-xs text-gray-500">Attribution algorithms</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {renderModelConfiguration()}
        {renderAttributionResults()}
      </div>

      {/* Analytics */}
      {renderAnalytics()}

      {/* Selected Agent Details */}
      {selectedAgent && (
        <Card>
          <CardHeader>
            <CardTitle>Attribution Breakdown: {selectedAgent.agentName}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">Attribution Components</h4>
                <div className="space-y-2">
                  {Object.entries(selectedAgent.breakdown).map(([component, value]) => (
                    <div key={component} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {getModelIcon(component as AttributionModel['type'])}
                        <span className="capitalize">{component}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-600 h-2 rounded-full"
                            style={{ width: `${(value / selectedAgent.totalAttribution) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">${value.toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-3">Performance Metrics</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Rank:</span>
                    <span className="font-medium">#{selectedAgent.rank}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Change:</span>
                    <span className={`font-medium ${getChangeColor(selectedAgent.change)}`}>
                      {getChangeIcon(selectedAgent.change)} {Math.abs(selectedAgent.change * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Capsules:</span>
                    <span className="font-medium">{selectedAgent.contributions.capsules}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Quality Score:</span>
                    <span className="font-medium">{(selectedAgent.contributions.quality * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Collaboration:</span>
                    <span className="font-medium">{(selectedAgent.contributions.collaboration * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Impact Score:</span>
                    <span className="font-medium">{(selectedAgent.contributions.impact * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
        </>
      )}
    </div>
  );
}
