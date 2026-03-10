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
  Database,
  Search,
  Plus,
  Eye,
  CheckCircle,
  AlertTriangle,
  Network,
  Target,
  GitBranch,
  DollarSign,
  RefreshCw,
  Filter,
  BookOpen,
  Brain,
  Zap,
  TrendingUp,
  Users,
  Clock,
  Settings,
  Play,
  AlertCircle
} from 'lucide-react';

interface KnowledgeSource {
  id: string;
  title: string;
  content_type: string;
  url?: string;
  author?: string;
  created_at: string;
  confidence_score: number;
  verification_status: 'verified' | 'pending' | 'rejected';
  usage_count: number;
  quality_score: number;
  cluster_id?: string;
}

interface KnowledgeCluster {
  id: string;
  name: string;
  description: string;
  source_count: number;
  created_at: string;
  quality_score: number;
  topics: string[];
}

interface AKCStats {
  total_sources: number;
  verified_sources: number;
  pending_sources: number;
  total_clusters: number;
  total_lineages: number;
  dividend_pool: number;
  monthly_usage: number;
}

type AKCView = 'overview' | 'sources' | 'clusters' | 'lineage' | 'dividends' | 'search';

export function AKCDashboard() {
  const { isDemoMode } = useDemoMode();

  const [activeView, setActiveView] = useState<AKCView>('overview');
  const [selectedSource, setSelectedSource] = useState<KnowledgeSource | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<KnowledgeCluster | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddSource, setShowAddSource] = useState(false);

  // Mock data - only shown in demo mode
  const mockStats = isDemoMode ? {
    total_sources: 12847,
    verified_sources: 9234,
    pending_sources: 1456,
    total_clusters: 342,
    total_lineages: 5678,
    dividend_pool: 45672.89,
    monthly_usage: 156789
  } : null;

  const mockSources = isDemoMode ? [
    {
      id: 'src-001',
      title: 'Machine Learning Fundamentals',
      content_type: 'research_paper',
      url: 'https://arxiv.org/abs/1234.5678',
      author: 'Dr. Jane Smith',
      created_at: new Date().toISOString(),
      confidence_score: 0.94,
      verification_status: 'verified',
      usage_count: 1247,
      quality_score: 0.89,
      cluster_id: 'cluster-ai-ml'
    },
    {
      id: 'src-002',
      title: 'Quantum Computing Advances 2025',
      content_type: 'journal_article',
      url: 'https://nature.com/articles/quantum-2025',
      author: 'Prof. John Doe',
      created_at: new Date(Date.now() - 86400000).toISOString(),
      confidence_score: 0.97,
      verification_status: 'verified',
      usage_count: 892,
      quality_score: 0.95,
      cluster_id: 'cluster-quantum'
    },
    {
      id: 'src-003',
      title: 'AI Ethics Guidelines',
      content_type: 'whitepaper',
      author: 'Ethics Committee',
      created_at: new Date(Date.now() - 172800000).toISOString(),
      confidence_score: 0.87,
      verification_status: 'pending',
      usage_count: 456,
      quality_score: 0.82
    }
  ] : [];

  const mockClusters = isDemoMode ? [
    {
      id: 'cluster-ai-ml',
      name: 'Artificial Intelligence & Machine Learning',
      description: 'Core concepts, algorithms, and applications in AI/ML',
      source_count: 1247,
      created_at: new Date(Date.now() - 2592000000).toISOString(),
      quality_score: 0.91,
      topics: ['neural networks', 'deep learning', 'supervised learning', 'reinforcement learning']
    },
    {
      id: 'cluster-quantum',
      name: 'Quantum Computing',
      description: 'Quantum algorithms, hardware, and theoretical foundations',
      source_count: 432,
      created_at: new Date(Date.now() - 1944000000).toISOString(),
      quality_score: 0.88,
      topics: ['quantum algorithms', 'quantum gates', 'quantum entanglement', 'quantum supremacy']
    },
    {
      id: 'cluster-ethics',
      name: 'AI Ethics & Safety',
      description: 'Ethical considerations and safety measures in AI development',
      source_count: 789,
      created_at: new Date(Date.now() - 1296000000).toISOString(),
      quality_score: 0.85,
      topics: ['bias mitigation', 'fairness', 'transparency', 'accountability']
    }
  ] : [];

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <Database className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Knowledge Sources</p>
                  <h3 className="text-2xl font-bold text-blue-900">{mockStats.total_sources.toLocaleString()}</h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              {mockStats.verified_sources.toLocaleString()} verified
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center">
                  <Network className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Knowledge Clusters</p>
                  <h3 className="text-2xl font-bold text-green-900">{mockStats.total_clusters}</h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              Organized by topic
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                  <GitBranch className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Usage Lineages</p>
                  <h3 className="text-2xl font-bold text-purple-900">{mockStats.total_lineages.toLocaleString()}</h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              Attribution chains
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-amber-100 rounded-full flex items-center justify-center">
                  <DollarSign className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Dividend Pool</p>
                  <h3 className="text-2xl font-bold text-amber-900">${mockStats.dividend_pool.toLocaleString()}</h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              Monthly distribution
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5" />
            <span>Quick Actions</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button 
              onClick={() => setActiveView('sources')}
              className="flex items-center justify-center space-x-2 h-16"
            >
              <Database className="h-5 w-5" />
              <span>Manage Sources</span>
            </Button>
            <Button 
              onClick={() => setActiveView('clusters')}
              variant="outline"
              className="flex items-center justify-center space-x-2 h-16"
            >
              <Network className="h-5 w-5" />
              <span>View Clusters</span>
            </Button>
            <Button 
              onClick={() => setActiveView('search')}
              variant="outline"
              className="flex items-center justify-center space-x-2 h-16"
            >
              <Search className="h-5 w-5" />
              <span>Discover Knowledge</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Clock className="h-5 w-5" />
              <span>Recent Sources</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockSources.slice(0, 3).map((source) => (
                <div key={source.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <BookOpen className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-sm">{source.title}</p>
                      <p className="text-xs text-gray-500">{source.content_type}</p>
                    </div>
                  </div>
                  <Badge variant={source.verification_status === 'verified' ? 'default' : 'secondary'}>
                    {source.verification_status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5" />
              <span>Top Performing Clusters</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockClusters.slice(0, 3).map((cluster) => (
                <div key={cluster.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                      <Network className="h-4 w-4 text-green-600" />
                    </div>
                    <div>
                      <p className="font-medium text-sm">{cluster.name}</p>
                      <p className="text-xs text-gray-500">{cluster.source_count} sources</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-sm">{(cluster.quality_score * 100).toFixed(0)}%</p>
                    <p className="text-xs text-gray-500">quality</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderSources = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Knowledge Sources</h2>
        <Button onClick={() => setShowAddSource(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Source
        </Button>
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="flex items-center space-x-2">
              <Search className="h-4 w-4 text-gray-400" />
              <Input placeholder="Search sources..." />
            </div>
            <select className="rounded-md border border-gray-300 px-3 py-2">
              <option>All Types</option>
              <option>Research Paper</option>
              <option>Journal Article</option>
              <option>Whitepaper</option>
              <option>Book</option>
            </select>
            <select className="rounded-md border border-gray-300 px-3 py-2">
              <option>All Status</option>
              <option>Verified</option>
              <option>Pending</option>
              <option>Rejected</option>
            </select>
            <Button variant="outline">
              <Filter className="h-4 w-4 mr-2" />
              More Filters
            </Button>
          </div>

          <div className="space-y-4">
            {mockSources.map((source) => (
              <div key={source.id} className="border rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-semibold text-lg">{source.title}</h3>
                      <Badge variant={source.verification_status === 'verified' ? 'default' : 'secondary'}>
                        {source.verification_status}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                      <span>{source.content_type}</span>
                      {source.author && <span>by {source.author}</span>}
                      <span>{source.usage_count} uses</span>
                      <span>Quality: {(source.quality_score * 100).toFixed(0)}%</span>
                    </div>
                    {source.url && (
                      <a href={source.url} target="_blank" rel="noopener noreferrer" 
                         className="text-blue-600 hover:underline text-sm">
                        {source.url}
                      </a>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button size="sm" variant="outline">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <div className="text-right">
                      <div className="w-16 bg-gray-200 rounded-full h-2 mb-1">
                        <div 
                          className="bg-blue-500 h-2 rounded-full" 
                          style={{ width: `${source.confidence_score * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">
                        {(source.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderClusters = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Knowledge Clusters</h2>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Create Cluster
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockClusters.map((cluster) => (
          <Card key={cluster.id} className="hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => setSelectedCluster(cluster)}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{cluster.name}</CardTitle>
                <Badge>{cluster.source_count} sources</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">{cluster.description}</p>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Quality Score</span>
                  <span className="font-bold">{(cluster.quality_score * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-green-500 h-2 rounded-full" 
                    style={{ width: `${cluster.quality_score * 100}%` }}
                  />
                </div>
                <div className="flex flex-wrap gap-1 mt-3">
                  {cluster.topics.slice(0, 3).map((topic, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {topic}
                    </Badge>
                  ))}
                  {cluster.topics.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{cluster.topics.length - 3} more
                    </Badge>
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
      case 'sources':
        return renderSources();
      case 'clusters':
        return renderClusters();
      case 'lineage':
        return <div className="text-center text-gray-500 py-8">Knowledge lineage tracking interface coming soon...</div>;
      case 'dividends':
        return <div className="text-center text-gray-500 py-8">Dividend distribution dashboard coming soon...</div>;
      case 'search':
        return <div className="text-center text-gray-500 py-8">Advanced knowledge discovery interface coming soon...</div>;
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
              <div className="h-12 w-12 bg-blue-600 rounded-lg flex items-center justify-center">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900">AKC Dashboard</h1>
                <p className="text-slate-600">
                  {isDemoMode
                    ? 'Viewing simulated knowledge classification data for demonstration'
                    : 'Automatic Knowledge Classification & Attribution'
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
                  AKC knowledge sources and clusters will appear here when available. Toggle Demo Mode ON to see sample data.
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
                { id: 'overview', label: 'Overview', icon: TrendingUp },
                { id: 'sources', label: 'Sources', icon: Database },
                { id: 'clusters', label: 'Clusters', icon: Network },
                { id: 'lineage', label: 'Lineage', icon: GitBranch },
                { id: 'dividends', label: 'Dividends', icon: DollarSign },
                { id: 'search', label: 'Discovery', icon: Search }
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <Button
                    key={item.id}
                    variant={activeView === item.id ? 'default' : 'ghost'}
                    onClick={() => setActiveView(item.id as AKCView)}
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