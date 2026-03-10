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
  Search as MirrorIcon,
  Shield,
  Settings,
  Eye,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  Download,
  Upload,
  RefreshCw,
  Target,
  Activity,
  Lock,
  Unlock,
  Zap,
  Filter,
  Calendar,
  BarChart3,
  Play,
  AlertCircle as AlertCircleIcon
} from 'lucide-react';

interface MirrorConfig {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  audit_frequency: 'real-time' | 'hourly' | 'daily' | 'weekly';
  target_systems: string[];
  audit_rules: string[];
  created_at: string;
  last_audit: string;
  audit_count: number;
  compliance_score: number;
}

interface AuditResult {
  id: string;
  config_id: string;
  timestamp: string;
  status: 'passed' | 'failed' | 'warning';
  findings: AuditFinding[];
  compliance_score: number;
  duration_ms: number;
}

interface AuditFinding {
  severity: 'high' | 'medium' | 'low' | 'info';
  category: string;
  description: string;
  recommendation?: string;
  affected_systems: string[];
}

type MirrorView = 'overview' | 'configurations' | 'audits' | 'compliance' | 'settings';

export function MirrorModeDashboard() {
  const { isDemoMode } = useDemoMode();

  const [activeView, setActiveView] = useState<MirrorView>('overview');
  const [selectedConfig, setSelectedConfig] = useState<MirrorConfig | null>(null);
  const [selectedAudit, setSelectedAudit] = useState<AuditResult | null>(null);
  const [showCreateConfig, setShowCreateConfig] = useState(false);

  // Mock data - only shown in demo mode
  const mockConfigs = isDemoMode ? [
    {
      id: 'config-001',
      name: 'Production Security Audit',
      description: 'Comprehensive security audit for production systems',
      enabled: true,
      audit_frequency: 'daily',
      target_systems: ['api-server', 'database', 'auth-service'],
      audit_rules: ['access-control', 'data-encryption', 'compliance-check'],
      created_at: new Date(Date.now() - 2592000000).toISOString(),
      last_audit: new Date(Date.now() - 3600000).toISOString(),
      audit_count: 30,
      compliance_score: 0.94
    },
    {
      id: 'config-002',
      name: 'AI Ethics Monitoring',
      description: 'Real-time monitoring of AI model behavior and ethics compliance',
      enabled: true,
      audit_frequency: 'real-time',
      target_systems: ['ai-models', 'inference-api'],
      audit_rules: ['bias-detection', 'fairness-check', 'transparency-audit'],
      created_at: new Date(Date.now() - 1944000000).toISOString(),
      last_audit: new Date(Date.now() - 300000).toISOString(),
      audit_count: 1247,
      compliance_score: 0.87
    },
    {
      id: 'config-003',
      name: 'Data Privacy Compliance',
      description: 'GDPR and privacy regulation compliance monitoring',
      enabled: false,
      audit_frequency: 'weekly',
      target_systems: ['user-data', 'analytics', 'third-party-integrations'],
      audit_rules: ['gdpr-compliance', 'data-retention', 'consent-tracking'],
      created_at: new Date(Date.now() - 1296000000).toISOString(),
      last_audit: new Date(Date.now() - 604800000).toISOString(),
      audit_count: 12,
      compliance_score: 0.91
    }
  ] : [];

  const mockAudits = isDemoMode ? [
    {
      id: 'audit-001',
      config_id: 'config-001',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      status: 'passed',
      findings: [
        {
          severity: 'low',
          category: 'Access Control',
          description: 'Some API endpoints have broader permissions than necessary',
          recommendation: 'Review and tighten API endpoint permissions',
          affected_systems: ['api-server']
        }
      ],
      compliance_score: 0.94,
      duration_ms: 2340
    },
    {
      id: 'audit-002',
      config_id: 'config-002',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      status: 'warning',
      findings: [
        {
          severity: 'medium',
          category: 'Bias Detection',
          description: 'Potential bias detected in model responses for demographic queries',
          recommendation: 'Retrain model with more diverse training data',
          affected_systems: ['ai-models']
        },
        {
          severity: 'low',
          category: 'Transparency',
          description: 'Model decision explanations could be more detailed',
          recommendation: 'Enhance explanation generation system',
          affected_systems: ['inference-api']
        }
      ],
      compliance_score: 0.87,
      duration_ms: 156
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
                  <Settings className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Active Configs</p>
                  <h3 className="text-2xl font-bold text-blue-900">
                    {mockConfigs.filter(c => c.enabled).length}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              {mockConfigs.length} total configurations
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
                  <p className="text-sm text-gray-600">Audits Today</p>
                  <h3 className="text-2xl font-bold text-green-900">47</h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              43 passed, 4 warnings
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                  <BarChart3 className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Avg Compliance</p>
                  <h3 className="text-2xl font-bold text-purple-900">91%</h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              +3% from last month
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-amber-100 rounded-full flex items-center justify-center">
                  <AlertTriangle className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Open Findings</p>
                  <h3 className="text-2xl font-bold text-amber-900">12</h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              3 high priority
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Configurations */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Active Mirror Configurations</span>
            </CardTitle>
            <Button onClick={() => setShowCreateConfig(true)}>
              <Settings className="h-4 w-4 mr-2" />
              New Configuration
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockConfigs.filter(c => c.enabled).map((config) => (
              <div key={config.id} className="border rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-semibold text-lg">{config.name}</h3>
                      <Badge variant="default">
                        {config.audit_frequency}
                      </Badge>
                      <Badge variant={config.enabled ? 'default' : 'secondary'}>
                        {config.enabled ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                    <p className="text-gray-600 mb-2">{config.description}</p>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>{config.target_systems.length} systems</span>
                      <span>{config.audit_rules.length} rules</span>
                      <span>{config.audit_count} audits completed</span>
                      <span>Last audit: {new Date(config.last_audit).toLocaleString()}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-green-600">
                      {(config.compliance_score * 100).toFixed(0)}%
                    </div>
                    <div className="text-sm text-gray-500">compliance</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Audit Results */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Recent Audit Results</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockAudits.slice(0, 3).map((audit) => (
              <div key={audit.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
                    audit.status === 'passed' ? 'bg-green-100' :
                    audit.status === 'warning' ? 'bg-amber-100' : 'bg-red-100'
                  }`}>
                    {audit.status === 'passed' ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : audit.status === 'warning' ? (
                      <AlertTriangle className="h-4 w-4 text-amber-600" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-sm">
                      {mockConfigs.find(c => c.id === audit.config_id)?.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(audit.timestamp).toLocaleString()} • {audit.findings.length} findings
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <p className="font-bold text-sm">{(audit.compliance_score * 100).toFixed(0)}%</p>
                    <p className="text-xs text-gray-500">{audit.duration_ms}ms</p>
                  </div>
                  <Button size="sm" variant="outline">
                    <Eye className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderConfigurations = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Mirror Configurations</h2>
        <Button onClick={() => setShowCreateConfig(true)}>
          <Settings className="h-4 w-4 mr-2" />
          Create Configuration
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {mockConfigs.map((config) => (
          <Card key={config.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <CardTitle className="text-lg">{config.name}</CardTitle>
                  <Badge variant={config.enabled ? 'default' : 'secondary'}>
                    {config.enabled ? 'Active' : 'Inactive'}
                  </Badge>
                  <Badge variant="outline">
                    {config.audit_frequency}
                  </Badge>
                </div>
                <div className="flex items-center space-x-2">
                  <Button size="sm" variant="outline">
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="outline">
                    <Settings className="h-4 w-4" />
                  </Button>
                  <Button 
                    size="sm" 
                    variant={config.enabled ? "destructive" : "default"}
                  >
                    {config.enabled ? <Lock className="h-4 w-4" /> : <Unlock className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">{config.description}</p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <p className="font-medium text-sm mb-2">Target Systems</p>
                  <div className="space-y-1">
                    {config.target_systems.map((system, idx) => (
                      <Badge key={idx} variant="outline" className="mr-1">
                        {system}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                <div>
                  <p className="font-medium text-sm mb-2">Audit Rules</p>
                  <div className="space-y-1">
                    {config.audit_rules.map((rule, idx) => (
                      <Badge key={idx} variant="outline" className="mr-1">
                        {rule}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                <div>
                  <p className="font-medium text-sm mb-2">Performance</p>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Compliance Score</span>
                      <span className="font-bold">{(config.compliance_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Total Audits</span>
                      <span className="font-bold">{config.audit_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Last Audit</span>
                      <span className="text-sm text-gray-500">
                        {new Date(config.last_audit).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full" 
                  style={{ width: `${config.compliance_score * 100}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 text-center">
                Overall Compliance Score: {(config.compliance_score * 100).toFixed(1)}%
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderView = () => {
    switch (activeView) {
      case 'configurations':
        return renderConfigurations();
      case 'audits':
        return <div className="text-center text-gray-500 py-8">Detailed audit history interface coming soon...</div>;
      case 'compliance':
        return <div className="text-center text-gray-500 py-8">Compliance tracking dashboard coming soon...</div>;
      case 'settings':
        return <div className="text-center text-gray-500 py-8">Mirror mode settings panel coming soon...</div>;
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
                <MirrorIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900">Mirror Mode</h1>
                <p className="text-slate-600">
                  {isDemoMode
                    ? 'Viewing simulated security audit data for demonstration'
                    : 'Advanced Security Auditing & Compliance Monitoring'
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
      {!isDemoMode && mockConfigs.length === 0 && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircleIcon className="h-5 w-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
                <p className="text-sm text-blue-700">
                  Mirror Mode audit configurations will appear here when available. Toggle Demo Mode ON to see sample audits.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Navigation and Content - Only show if we have data */}
      {mockConfigs.length > 0 && (
        <>
          <div className="bg-white rounded-lg border">
            <div className="flex space-x-1 p-1">
              {[
                { id: 'overview', label: 'Overview', icon: BarChart3 },
                { id: 'configurations', label: 'Configurations', icon: Settings },
                { id: 'audits', label: 'Audit History', icon: FileText },
                { id: 'compliance', label: 'Compliance', icon: Shield },
                { id: 'settings', label: 'Settings', icon: Target }
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <Button
                    key={item.id}
                    variant={activeView === item.id ? 'default' : 'ghost'}
                    onClick={() => setActiveView(item.id as MirrorView)}
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