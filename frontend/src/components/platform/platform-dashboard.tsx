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
  Key,
  Plus,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Settings,
  Trash2,
  RefreshCw,
  Copy,
  Globe,
  Zap,
  Shield,
  Activity,
  TrendingUp,
  Calendar,
  Users,
  Target,
  Link,
  Download,
  Upload,
  Search,
  Filter,
  Bell,
  Lock,
  Unlock,
  Code,
  BookOpen,
  Play
} from 'lucide-react';

interface Platform {
  id: string;
  name: string;
  description: string;
  logo_url?: string;
  status: 'active' | 'inactive' | 'deprecated';
  supported_models: string[];
  pricing_model: 'pay-per-use' | 'subscription' | 'free' | 'enterprise';
  documentation_url?: string;
}

interface APIKey {
  id: string;
  platform_id: string;
  name: string;
  key_preview: string;
  status: 'active' | 'inactive' | 'expired' | 'revoked';
  created_at: string;
  last_used: string;
  usage_count: number;
  usage_limit?: number;
  expires_at?: string;
  scopes: string[];
  environment: 'production' | 'development' | 'testing';
}

interface PlatformUsage {
  platform_id: string;
  requests_today: number;
  requests_this_month: number;
  errors_today: number;
  avg_response_time: number;
  cost_this_month: number;
  quota_used: number;
  quota_limit: number;
}

interface APIKeyStats {
  total_keys: number;
  active_keys: number;
  keys_used_today: number;
  total_platforms: number;
  total_requests_today: number;
  total_cost_this_month: number;
}

type PlatformView = 'overview' | 'platforms' | 'keys' | 'usage' | 'integration' | 'settings';

export function PlatformDashboard() {
  const { isDemoMode } = useDemoMode();

  const [activeView, setActiveView] = useState<PlatformView>('overview');
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | null>(null);
  const [selectedKey, setSelectedKey] = useState<APIKey | null>(null);
  const [showAddKey, setShowAddKey] = useState(false);
  const [showKeyValue, setShowKeyValue] = useState<{[key: string]: boolean}>({});

  // Mock data - only shown in demo mode
  const mockStats = isDemoMode ? {
    total_keys: 12,
    active_keys: 9,
    keys_used_today: 7,
    total_platforms: 5,
    total_requests_today: 2847,
    total_cost_this_month: 234.56
  } : null;

  const mockPlatforms = isDemoMode ? [
    {
      id: 'openai',
      name: 'OpenAI',
      description: 'GPT-4, GPT-3.5, DALL-E, Whisper, and other OpenAI models',
      status: 'active',
      supported_models: ['gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo', 'dall-e-3', 'whisper-1'],
      pricing_model: 'pay-per-use',
      documentation_url: 'https://platform.openai.com/docs'
    },
    {
      id: 'anthropic',
      name: 'Anthropic',
      description: 'Claude 3 Opus, Sonnet, and Haiku models',
      status: 'active',
      supported_models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
      pricing_model: 'pay-per-use',
      documentation_url: 'https://docs.anthropic.com/'
    },
    {
      id: 'huggingface',
      name: 'Hugging Face',
      description: 'Open-source AI models and inference API',
      status: 'active',
      supported_models: ['meta-llama/Llama-2-70b-chat-hf', 'microsoft/DialoGPT-large'],
      pricing_model: 'free',
      documentation_url: 'https://huggingface.co/docs'
    },
    {
      id: 'cohere',
      name: 'Cohere',
      description: 'Command and Embed models for text generation and embeddings',
      status: 'inactive',
      supported_models: ['command', 'command-light', 'embed-english-v2.0'],
      pricing_model: 'subscription',
      documentation_url: 'https://docs.cohere.ai/'
    },
    {
      id: 'google',
      name: 'Google AI',
      description: 'Gemini, PaLM, and other Google AI models',
      status: 'active',
      supported_models: ['gemini-pro', 'gemini-pro-vision', 'palm-2'],
      pricing_model: 'pay-per-use',
      documentation_url: 'https://ai.google.dev/'
    }
  ] : [];

  const mockAPIKeys = isDemoMode ? [
    {
      id: 'key-001',
      platform_id: 'openai',
      name: 'Production API Key',
      key_preview: 'sk-proj-...xyz123',
      status: 'active',
      created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
      last_used: new Date(Date.now() - 3600000).toISOString(),
      usage_count: 15647,
      usage_limit: 100000,
      scopes: ['gpt-4', 'gpt-3.5-turbo', 'dall-e-3'],
      environment: 'production'
    },
    {
      id: 'key-002',
      platform_id: 'anthropic',
      name: 'Claude Development Key',
      key_preview: 'sk-ant-...abc789',
      status: 'active',
      created_at: new Date(Date.now() - 86400000 * 15).toISOString(),
      last_used: new Date(Date.now() - 1800000).toISOString(),
      usage_count: 8934,
      scopes: ['claude-3-sonnet', 'claude-3-haiku'],
      environment: 'development'
    },
    {
      id: 'key-003',
      platform_id: 'huggingface',
      name: 'HF Inference API',
      key_preview: 'hf_...def456',
      status: 'active',
      created_at: new Date(Date.now() - 86400000 * 60).toISOString(),
      last_used: new Date(Date.now() - 86400000).toISOString(),
      usage_count: 2341,
      scopes: ['inference-api'],
      environment: 'production'
    },
    {
      id: 'key-004',
      platform_id: 'openai',
      name: 'Testing Key',
      key_preview: 'sk-proj-...test99',
      status: 'inactive',
      created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
      last_used: new Date(Date.now() - 86400000 * 3).toISOString(),
      usage_count: 234,
      expires_at: new Date(Date.now() + 86400000 * 30).toISOString(),
      scopes: ['gpt-3.5-turbo'],
      environment: 'testing'
    }
  ] : [];

  const mockUsage: PlatformUsage[] = DEMO_MODE ? [
    {
      platform_id: 'openai',
      requests_today: 1247,
      requests_this_month: 45678,
      errors_today: 12,
      avg_response_time: 850,
      cost_this_month: 187.45,
      quota_used: 75,
      quota_limit: 100
    },
    {
      platform_id: 'anthropic',
      requests_today: 892,
      requests_this_month: 23456,
      errors_today: 3,
      avg_response_time: 1200,
      cost_this_month: 47.11,
      quota_used: 45,
      quota_limit: 100
    },
    {
      platform_id: 'huggingface',
      requests_today: 456,
      requests_this_month: 12890,
      errors_today: 8,
      avg_response_time: 2100,
      cost_this_month: 0,
      quota_used: 30,
      quota_limit: 100
    }
  ] : [];

  const getPlatformIcon = (platformId: string) => {
    switch (platformId) {
      case 'openai': return <Globe className="h-5 w-5 text-green-600" />;
      case 'anthropic': return <Zap className="h-5 w-5 text-orange-600" />;
      case 'huggingface': return <Target className="h-5 w-5 text-yellow-600" />;
      case 'google': return <Search className="h-5 w-5 text-blue-600" />;
      case 'cohere': return <Code className="h-5 w-5 text-purple-600" />;
      default: return <Globe className="h-5 w-5 text-gray-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return <Badge className="bg-green-100 text-green-800">Active</Badge>;
      case 'inactive': return <Badge className="bg-gray-100 text-gray-800">Inactive</Badge>;
      case 'expired': return <Badge className="bg-red-100 text-red-800">Expired</Badge>;
      case 'revoked': return <Badge className="bg-red-100 text-red-800">Revoked</Badge>;
      case 'deprecated': return <Badge className="bg-yellow-100 text-yellow-800">Deprecated</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getEnvironmentBadge = (environment: string) => {
    switch (environment) {
      case 'production': return <Badge className="bg-red-100 text-red-800">Production</Badge>;
      case 'development': return <Badge className="bg-blue-100 text-blue-800">Development</Badge>;
      case 'testing': return <Badge className="bg-yellow-100 text-yellow-800">Testing</Badge>;
      default: return <Badge variant="outline">{environment}</Badge>;
    }
  };

  const toggleKeyVisibility = (keyId: string) => {
    setShowKeyValue(prev => ({
      ...prev,
      [keyId]: !prev[keyId]
    }));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // In real implementation, show toast notification
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
                  <Key className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">API Keys</p>
                  <h3 className="text-2xl font-bold text-blue-900">
                    {mockStats.active_keys}/{mockStats.total_keys}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              {mockStats.keys_used_today} keys used today
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center">
                  <Globe className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Platforms</p>
                  <h3 className="text-2xl font-bold text-green-900">
                    {mockPlatforms.filter(p => p.status === 'active').length}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              {mockPlatforms.length} total integrated
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                  <Activity className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Requests Today</p>
                  <h3 className="text-2xl font-bold text-purple-900">
                    {mockStats.total_requests_today.toLocaleString()}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              +15% from yesterday
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-amber-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Cost This Month</p>
                  <h3 className="text-2xl font-bold text-amber-900">
                    ${mockStats.total_cost_this_month}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              Within budget limits
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Platform Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Globe className="h-5 w-5" />
              <span>Platform Status</span>
            </CardTitle>
            <Button onClick={() => setActiveView('platforms')}>
              Manage Platforms
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {mockPlatforms.filter(p => p.status === 'active').map((platform) => {
              const usage = mockUsage.find(u => u.platform_id === platform.id);
              return (
                <div key={platform.id} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      {getPlatformIcon(platform.id)}
                      <h3 className="font-semibold">{platform.name}</h3>
                    </div>
                    {getStatusBadge(platform.status)}
                  </div>

                  {usage && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Today's Requests</span>
                        <span className="font-bold">{usage.requests_today.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Response Time</span>
                        <span className="font-bold">{usage.avg_response_time}ms</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Cost This Month</span>
                        <span className="font-bold">${usage.cost_this_month}</span>
                      </div>

                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                          <span>Quota Usage</span>
                          <span>{usage.quota_used}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              usage.quota_used >= 80 ? 'bg-red-500' :
                              usage.quota_used >= 60 ? 'bg-yellow-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${usage.quota_used}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Recent API Keys */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Key className="h-5 w-5" />
              <span>Recent API Keys</span>
            </CardTitle>
            <Button onClick={() => setActiveView('keys')}>
              <Plus className="h-4 w-4 mr-2" />
              Add API Key
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockAPIKeys.slice(0, 4).map((key) => {
              const platform = mockPlatforms.find(p => p.id === key.platform_id);
              return (
                <div key={key.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center space-x-4">
                    <div className="h-10 w-10 bg-gray-100 rounded-full flex items-center justify-center">
                      {getPlatformIcon(key.platform_id)}
                    </div>
                    <div>
                      <div className="flex items-center space-x-3 mb-1">
                        <h3 className="font-semibold">{key.name}</h3>
                        {getStatusBadge(key.status)}
                        {getEnvironmentBadge(key.environment)}
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span>{platform?.name}</span>
                        <span>{key.usage_count.toLocaleString()} uses</span>
                        <span>Last used: {new Date(key.last_used).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button size="sm" variant="outline">
                      <Eye className="h-4 w-4" />
                    </Button>
                    <Button size="sm" variant="outline">
                      <Settings className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderPlatforms = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">AI Platforms</h2>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add Platform
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {mockPlatforms.map((platform) => {
          const usage = mockUsage.find(u => u.platform_id === platform.id);
          const keyCount = mockAPIKeys.filter(k => k.platform_id === platform.id).length;

          return (
            <Card key={platform.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getPlatformIcon(platform.id)}
                    <div>
                      <CardTitle className="text-xl">{platform.name}</CardTitle>
                      <p className="text-sm text-gray-600">{platform.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getStatusBadge(platform.status)}
                    <Button size="sm" variant="outline">
                      <Settings className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                  <div>
                    <p className="font-medium text-sm mb-2">Supported Models</p>
                    <div className="space-y-1">
                      {platform.supported_models.slice(0, 3).map((model, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs mr-1 mb-1">
                          {model}
                        </Badge>
                      ))}
                      {platform.supported_models.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{platform.supported_models.length - 3} more
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div>
                    <p className="font-medium text-sm mb-2">API Keys</p>
                    <div className="space-y-2">
                      <div className="text-2xl font-bold text-blue-600">{keyCount}</div>
                      <div className="text-xs text-gray-500">
                        {mockAPIKeys.filter(k => k.platform_id === platform.id && k.status === 'active').length} active
                      </div>
                    </div>
                  </div>

                  <div>
                    <p className="font-medium text-sm mb-2">Usage Today</p>
                    <div className="space-y-2">
                      <div className="text-2xl font-bold text-green-600">
                        {usage?.requests_today.toLocaleString() || '0'}
                      </div>
                      <div className="text-xs text-gray-500">
                        {usage?.errors_today || 0} errors
                      </div>
                    </div>
                  </div>

                  <div>
                    <p className="font-medium text-sm mb-2">Cost This Month</p>
                    <div className="space-y-2">
                      <div className="text-2xl font-bold text-purple-600">
                        ${usage?.cost_this_month.toFixed(2) || '0.00'}
                      </div>
                      <div className="text-xs text-gray-500 capitalize">
                        {platform.pricing_model} model
                      </div>
                    </div>
                  </div>
                </div>

                {usage && (
                  <div className="mb-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium">Monthly Quota</span>
                      <span className="text-sm text-gray-500">{usage.quota_used}% used</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          usage.quota_used >= 80 ? 'bg-red-500' :
                          usage.quota_used >= 60 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${usage.quota_used}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="flex justify-between items-center">
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>Avg Response: {usage?.avg_response_time}ms</span>
                    {platform.documentation_url && (
                      <a
                        href={platform.documentation_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-1 text-blue-600 hover:underline"
                      >
                        <BookOpen className="h-3 w-3" />
                        <span>Docs</span>
                      </a>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <Button size="sm" variant="outline">
                      <Key className="h-3 w-3 mr-1" />
                      Manage Keys
                    </Button>
                    <Button size="sm" variant="outline">
                      <Activity className="h-3 w-3 mr-1" />
                      View Usage
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );

  const renderView = () => {
    switch (activeView) {
      case 'platforms':
        return renderPlatforms();
      case 'keys':
        return <div className="text-center text-gray-500 py-8">API key management interface coming soon...</div>;
      case 'usage':
        return <div className="text-center text-gray-500 py-8">Usage analytics dashboard coming soon...</div>;
      case 'integration':
        return <div className="text-center text-gray-500 py-8">Integration guide and tutorials coming soon...</div>;
      case 'settings':
        return <div className="text-center text-gray-500 py-8">Platform settings panel coming soon...</div>;
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
              <div className="h-12 w-12 bg-indigo-600 rounded-lg flex items-center justify-center">
                <Key className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900">Platform Management</h1>
                <p className="text-slate-600">
                  {isDemoMode
                    ? 'Viewing simulated platform integrations for demonstration'
                    : 'Manage AI platform integrations and API keys'
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
                  Platform integrations and API keys will appear here when configured. Toggle Demo Mode ON to see sample data.
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
                { id: 'platforms', label: 'Platforms', icon: Globe },
                { id: 'keys', label: 'API Keys', icon: Key },
                { id: 'usage', label: 'Usage', icon: Activity },
                { id: 'integration', label: 'Integration', icon: Code },
                { id: 'settings', label: 'Settings', icon: Settings }
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <Button
                    key={item.id}
                    variant={activeView === item.id ? 'default' : 'ghost'}
                    onClick={() => setActiveView(item.id as PlatformView)}
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
