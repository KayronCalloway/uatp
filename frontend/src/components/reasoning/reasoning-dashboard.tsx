'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Brain,
  Search,
  Target,
  CheckCircle,
  AlertCircle,
  Clock,
  RefreshCw,
  Eye,
  Settings,
  TrendingUp,
  BarChart3,
  Activity,
  Zap,
  Filter,
  Calendar,
  Users,
  Globe,
  Shield,
  BookOpen,
  Code,
  Download,
  Upload,
  Play,
  Pause,
  Square,
  ArrowRight,
  Network,
  Layers,
  TreePine,
  GitBranch,
  Lightbulb,
  Microscope,
  Bot,
  MessageSquare,
  FileText,
  Database,
  Link,
  Hash
} from 'lucide-react';

interface ReasoningChain {
  id: string;
  name: string;
  description: string;
  type: 'deductive' | 'inductive' | 'abductive' | 'causal' | 'analogical';
  status: 'active' | 'paused' | 'completed' | 'failed';
  created_at: string;
  steps_count: number;
  confidence_score: number;
  complexity_level: 'simple' | 'moderate' | 'complex' | 'expert';
  execution_time: number;
  memory_usage: number;
  tags: string[];
}

interface ReasoningStep {
  id: string;
  chain_id: string;
  step_number: number;
  type: 'premise' | 'inference' | 'conclusion' | 'evidence' | 'contradiction';
  content: string;
  confidence: number;
  sources: string[];
  dependencies: string[];
  timestamp: string;
  reasoning_method: string;
  evidence_strength: number;
}

interface ReasoningAnalysis {
  id: string;
  chain_id: string;
  analysis_type: 'logical_validity' | 'soundness_check' | 'bias_detection' | 'coherence_analysis';
  result: 'valid' | 'invalid' | 'uncertain' | 'requires_review';
  confidence: number;
  findings: string[];
  recommendations: string[];
  performed_at: string;
}

interface ReasoningStats {
  total_chains: number;
  active_chains: number;
  avg_confidence: number;
  success_rate: number;
  chains_today: number;
  avg_execution_time: number;
  memory_efficiency: number;
  error_rate: number;
}

type ReasoningView = 'overview' | 'chains' | 'analysis' | 'validation' | 'templates' | 'settings';

export function ReasoningDashboard() {
  const { isDemoMode } = useDemoMode();

  const [activeView, setActiveView] = useState<ReasoningView>('overview');
  const [selectedChain, setSelectedChain] = useState<ReasoningChain | null>(null);
  const [selectedStep, setSelectedStep] = useState<ReasoningStep | null>(null);
  const [showNewChain, setShowNewChain] = useState(false);

  // Mock data - in real implementation, these would come from API endpoints
  const mockStats = isDemoMode ? {
    total_chains: 156,
    active_chains: 23,
    avg_confidence: 0.87,
    success_rate: 0.92,
    chains_today: 12,
    avg_execution_time: 2340,
    memory_efficiency: 0.85,
    error_rate: 0.03
  } : null;

  const mockChains = isDemoMode ? [
    {
      id: 'chain-001',
      name: 'Climate Impact Analysis',
      description: 'Multi-step reasoning about climate change effects on agricultural systems',
      type: 'causal',
      status: 'active',
      created_at: new Date(Date.now() - 3600000).toISOString(),
      steps_count: 15,
      confidence_score: 0.89,
      complexity_level: 'complex',
      execution_time: 4200,
      memory_usage: 256,
      tags: ['climate', 'agriculture', 'causal-analysis']
    },
    {
      id: 'chain-002',
      name: 'Medical Diagnosis Reasoning',
      description: 'Diagnostic reasoning chain for symptom analysis and treatment recommendations',
      type: 'abductive',
      status: 'completed',
      created_at: new Date(Date.now() - 7200000).toISOString(),
      steps_count: 22,
      confidence_score: 0.94,
      complexity_level: 'expert',
      execution_time: 6750,
      memory_usage: 512,
      tags: ['medical', 'diagnosis', 'healthcare']
    },
    {
      id: 'chain-003',
      name: 'Legal Precedent Analysis',
      description: 'Analogical reasoning comparing current case to historical precedents',
      type: 'analogical',
      status: 'active',
      created_at: new Date(Date.now() - 1800000).toISOString(),
      steps_count: 8,
      confidence_score: 0.76,
      complexity_level: 'moderate',
      execution_time: 1890,
      memory_usage: 128,
      tags: ['legal', 'precedent', 'case-analysis']
    },
    {
      id: 'chain-004',
      name: 'Scientific Hypothesis Testing',
      description: 'Deductive reasoning chain for hypothesis validation in experimental data',
      type: 'deductive',
      status: 'paused',
      created_at: new Date(Date.now() - 10800000).toISOString(),
      steps_count: 12,
      confidence_score: 0.82,
      complexity_level: 'complex',
      execution_time: 3100,
      memory_usage: 192,
      tags: ['science', 'hypothesis', 'experimental']
    }
  ] : [];

  const mockSteps = isDemoMode ? [
    {
      id: 'step-001',
      chain_id: 'chain-001',
      step_number: 1,
      type: 'premise',
      content: 'Global average temperatures have increased by 1.1°C since pre-industrial times',
      confidence: 0.95,
      sources: ['IPCC AR6 Report', 'NASA GISS Temperature Data'],
      dependencies: [],
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      reasoning_method: 'empirical_evidence',
      evidence_strength: 0.98
    },
    {
      id: 'step-002',
      chain_id: 'chain-001',
      step_number: 2,
      type: 'inference',
      content: 'Temperature increases affect precipitation patterns and growing seasons',
      confidence: 0.87,
      sources: ['Agricultural Climate Studies', 'Meteorological Data'],
      dependencies: ['step-001'],
      timestamp: new Date(Date.now() - 3400000).toISOString(),
      reasoning_method: 'causal_inference',
      evidence_strength: 0.85
    },
    {
      id: 'step-003',
      chain_id: 'chain-001',
      step_number: 3,
      type: 'evidence',
      content: 'Crop yield data shows 15% decrease in wheat production in affected regions',
      confidence: 0.91,
      sources: ['FAO Agricultural Statistics', 'Regional Yield Reports'],
      dependencies: ['step-002'],
      timestamp: new Date(Date.now() - 3200000).toISOString(),
      reasoning_method: 'statistical_analysis',
      evidence_strength: 0.89
    }
  ] : [];

  const getChainTypeIcon = (type: string) => {
    switch (type) {
      case 'deductive': return <ArrowRight className="h-4 w-4 text-blue-600" />;
      case 'inductive': return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'abductive': return <Lightbulb className="h-4 w-4 text-yellow-600" />;
      case 'causal': return <GitBranch className="h-4 w-4 text-purple-600" />;
      case 'analogical': return <Network className="h-4 w-4 text-orange-600" />;
      default: return <Brain className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return <Badge className="bg-green-100 text-green-800">Active</Badge>;
      case 'paused': return <Badge className="bg-yellow-100 text-yellow-800">Paused</Badge>;
      case 'completed': return <Badge className="bg-blue-100 text-blue-800">Completed</Badge>;
      case 'failed': return <Badge className="bg-red-100 text-red-800">Failed</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getComplexityBadge = (complexity: string) => {
    switch (complexity) {
      case 'simple': return <Badge className="bg-gray-100 text-gray-800">Simple</Badge>;
      case 'moderate': return <Badge className="bg-blue-100 text-blue-800">Moderate</Badge>;
      case 'complex': return <Badge className="bg-orange-100 text-orange-800">Complex</Badge>;
      case 'expert': return <Badge className="bg-red-100 text-red-800">Expert</Badge>;
      default: return <Badge variant="outline">{complexity}</Badge>;
    }
  };

  const getStepTypeIcon = (type: string) => {
    switch (type) {
      case 'premise': return <Database className="h-4 w-4 text-blue-600" />;
      case 'inference': return <Brain className="h-4 w-4 text-purple-600" />;
      case 'conclusion': return <Target className="h-4 w-4 text-green-600" />;
      case 'evidence': return <FileText className="h-4 w-4 text-orange-600" />;
      case 'contradiction': return <AlertCircle className="h-4 w-4 text-red-600" />;
      default: return <MessageSquare className="h-4 w-4 text-gray-600" />;
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <Brain className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Reasoning Chains</p>
                  <h3 className="text-2xl font-bold text-blue-900">
                    {(mockStats?.active_chains ?? 0)}/{(mockStats?.total_chains ?? 0)}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              {(mockStats?.chains_today ?? 0)} created today
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Avg Confidence</p>
                  <h3 className="text-2xl font-bold text-green-900">
                    {((mockStats?.avg_confidence ?? 0) * 100).toFixed(0)}%
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              {((mockStats?.success_rate ?? 0) * 100).toFixed(0)}% success rate
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                  <Clock className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Avg Execution</p>
                  <h3 className="text-2xl font-bold text-purple-900">
                    {((mockStats?.avg_execution_time ?? 0) / 1000).toFixed(1)}s
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              {((mockStats?.memory_efficiency ?? 0) * 100).toFixed(0)}% efficiency
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-amber-100 rounded-full flex items-center justify-center">
                  <Shield className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Error Rate</p>
                  <h3 className="text-2xl font-bold text-amber-900">
                    {((mockStats?.error_rate ?? 0) * 100).toFixed(1)}%
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              Well within targets
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Reasoning Chains */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Brain className="h-5 w-5" />
              <span>Active Reasoning Chains</span>
            </CardTitle>
            <Button onClick={() => setActiveView('chains')}>
              <Brain className="h-4 w-4 mr-2" />
              View All Chains
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockChains.filter(c => c.status === 'active').map((chain) => (
              <div key={chain.id} className="border rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {getChainTypeIcon(chain.type)}
                    <div>
                      <h3 className="font-semibold">{chain.name}</h3>
                      <p className="text-sm text-gray-600">{chain.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusBadge(chain.status)}
                    {getComplexityBadge(chain.complexity_level)}
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Steps:</span>
                    <span className="font-bold ml-1">{chain.steps_count}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Confidence:</span>
                    <span className="font-bold ml-1">{(chain.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Runtime:</span>
                    <span className="font-bold ml-1">{(chain.execution_time / 1000).toFixed(1)}s</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Memory:</span>
                    <span className="font-bold ml-1">{chain.memory_usage}MB</span>
                  </div>
                </div>

                <div className="flex items-center justify-between mt-4">
                  <div className="flex space-x-1">
                    {chain.tags.map((tag, idx) => (
                      <Badge key={idx} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  <div className="flex space-x-2">
                    <Button size="sm" variant="outline">
                      <Eye className="h-3 w-3 mr-1" />
                      View
                    </Button>
                    <Button size="sm" variant="outline">
                      <Pause className="h-3 w-3 mr-1" />
                      Pause
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Reasoning Types Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Reasoning Types</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { type: 'deductive', count: 45, color: 'bg-blue-500' },
                { type: 'inductive', count: 38, color: 'bg-green-500' },
                { type: 'abductive', count: 28, color: 'bg-yellow-500' },
                { type: 'causal', count: 32, color: 'bg-purple-500' },
                { type: 'analogical', count: 13, color: 'bg-orange-500' }
              ].map((item) => (
                <div key={item.type} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getChainTypeIcon(item.type)}
                    <span className="font-medium capitalize">{item.type}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${item.color}`}
                        style={{ width: `${(item.count / 45) * 100}%` }}
                      />
                    </div>
                    <span className="font-bold text-sm w-8">{item.count}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Recent Activity</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <div className="flex-1">
                  <p className="font-medium text-sm">Medical Diagnosis completed</p>
                  <p className="text-xs text-gray-500">94% confidence, 22 steps</p>
                </div>
                <span className="text-xs text-gray-500">2h ago</span>
              </div>

              <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                <Brain className="h-4 w-4 text-blue-600" />
                <div className="flex-1">
                  <p className="font-medium text-sm">Climate Impact started</p>
                  <p className="text-xs text-gray-500">Complex causal analysis</p>
                </div>
                <span className="text-xs text-gray-500">1h ago</span>
              </div>

              <div className="flex items-center space-x-3 p-3 bg-yellow-50 rounded-lg">
                <Pause className="h-4 w-4 text-yellow-600" />
                <div className="flex-1">
                  <p className="font-medium text-sm">Hypothesis Testing paused</p>
                  <p className="text-xs text-gray-500">Step 12 of 18</p>
                </div>
                <span className="text-xs text-gray-500">3h ago</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderChains = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Reasoning Chains</h2>
        <Button>
          <Brain className="h-4 w-4 mr-2" />
          New Chain
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {mockChains.map((chain) => (
          <Card key={chain.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getChainTypeIcon(chain.type)}
                  <div>
                    <CardTitle className="text-lg">{chain.name}</CardTitle>
                    <p className="text-sm text-gray-600">{chain.description}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {getStatusBadge(chain.status)}
                  {getComplexityBadge(chain.complexity_level)}
                  <Button size="sm" variant="outline">
                    <Settings className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">{chain.steps_count}</p>
                  <p className="text-xs text-gray-500">Steps</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">{(chain.confidence_score * 100).toFixed(0)}%</p>
                  <p className="text-xs text-gray-500">Confidence</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-purple-600">{(chain.execution_time / 1000).toFixed(1)}s</p>
                  <p className="text-xs text-gray-500">Runtime</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-orange-600">{chain.memory_usage}MB</p>
                  <p className="text-xs text-gray-500">Memory</p>
                </div>
                <div className="text-center">
                  <p className="text-sm font-bold">{new Date(chain.created_at).toLocaleDateString()}</p>
                  <p className="text-xs text-gray-500">Created</p>
                </div>
              </div>

              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">Progress</span>
                  <span className="text-sm text-gray-500">{chain.status === 'completed' ? '100%' : '75%'}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      chain.status === 'completed' ? 'bg-green-500' :
                      chain.status === 'active' ? 'bg-blue-500' :
                      chain.status === 'paused' ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: chain.status === 'completed' ? '100%' : '75%' }}
                  />
                </div>
              </div>

              <div className="flex justify-between items-center">
                <div className="flex space-x-1">
                  {chain.tags.map((tag, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
                <div className="flex space-x-2">
                  <Button size="sm" variant="outline">
                    <Eye className="h-3 w-3 mr-1" />
                    Inspect
                  </Button>
                  <Button size="sm" variant="outline">
                    <Download className="h-3 w-3 mr-1" />
                    Export
                  </Button>
                  {chain.status === 'active' && (
                    <Button size="sm" variant="outline">
                      <Pause className="h-3 w-3 mr-1" />
                      Pause
                    </Button>
                  )}
                  {chain.status === 'paused' && (
                    <Button size="sm" variant="outline">
                      <Play className="h-3 w-3 mr-1" />
                      Resume
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderView = () => {
    switch (activeView) {
      case 'chains':
        return renderChains();
      case 'analysis':
        return <div className="text-center text-gray-500 py-8">Reasoning analysis tools coming soon...</div>;
      case 'validation':
        return <div className="text-center text-gray-500 py-8">Logical validation interface coming soon...</div>;
      case 'templates':
        return <div className="text-center text-gray-500 py-8">Reasoning chain templates coming soon...</div>;
      case 'settings':
        return <div className="text-center text-gray-500 py-8">Reasoning engine settings coming soon...</div>;
      default:
        return renderOverview();
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="h-12 w-12 bg-purple-600 rounded-lg flex items-center justify-center">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900">Reasoning Dashboard</h1>
                <p className="text-slate-600">
                  {isDemoMode
                    ? 'Viewing simulated reasoning chains for demonstration'
                    : 'Advanced multi-step reasoning and logical analysis'
                  }
                </p>
              </div>
            </div>
            {isDemoMode && (
              <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-300">
                <Play className="h-3 w-3 mr-1" />
                Demo Data
              </Badge>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Show notice when in live mode with no data */}
      {!isDemoMode && !mockStats && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
                <p className="text-sm text-blue-700">
                  Reasoning chains will appear here when available. Toggle Demo Mode ON to see sample chains.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Navigation and Content - Only show if we have data */}
      {mockStats && (
        <>
          <div className="bg-white rounded-lg border">
            <div className="flex space-x-1 p-1">
              {[
                { id: 'overview', label: 'Overview', icon: BarChart3 },
                { id: 'chains', label: 'Chains', icon: Brain },
                { id: 'analysis', label: 'Analysis', icon: Microscope },
                { id: 'validation', label: 'Validation', icon: CheckCircle },
                { id: 'templates', label: 'Templates', icon: Layers },
                { id: 'settings', label: 'Settings', icon: Settings }
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <Button
                    key={item.id}
                    variant={activeView === item.id ? 'default' : 'ghost'}
                    onClick={() => setActiveView(item.id as ReasoningView)}
                    className="flex items-center space-x-2"
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Button>
                );
              })}
            </div>
          </div>

          {/* Content */}
          {renderView()}
        </>
      )}
    </div>
  );
}
