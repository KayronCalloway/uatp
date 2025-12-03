'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  Download,
  Settings,
  Eye,
  RefreshCw,
  TrendingUp,
  Target,
  Search,
  Filter,
  Calendar,
  BarChart3,
  PieChart,
  Globe,
  Users,
  Lock,
  Zap,
  Bell,
  BookOpen,
  Archive,
  Activity,
  Play,
  AlertCircle as AlertCircleIcon
} from 'lucide-react';

interface ComplianceFramework {
  id: string;
  name: string;
  description: string;
  version: string;
  status: 'active' | 'inactive' | 'deprecated';
  compliance_score: number;
  last_assessment: string;
  requirements_count: number;
  violations_count: number;
  category: 'privacy' | 'security' | 'financial' | 'ai-ethics' | 'general';
}

interface ComplianceViolation {
  id: string;
  framework_id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  requirement: string;
  detected_at: string;
  status: 'open' | 'acknowledged' | 'resolved' | 'false_positive';
  affected_systems: string[];
  remediation_steps?: string[];
  due_date?: string;
}

interface ComplianceReport {
  id: string;
  framework_id: string;
  generated_at: string;
  report_type: 'assessment' | 'audit' | 'certification' | 'incident';
  status: 'draft' | 'completed' | 'submitted' | 'approved';
  compliance_score: number;
  findings_count: number;
  file_url?: string;
}

interface ComplianceStats {
  total_frameworks: number;
  active_frameworks: number;
  overall_compliance_score: number;
  open_violations: number;
  resolved_this_month: number;
  upcoming_assessments: number;
}

type ComplianceView = 'overview' | 'frameworks' | 'violations' | 'reports' | 'assessments' | 'settings';

export function ComplianceDashboard() {
  const { isDemoMode } = useDemoMode();
  const [activeView, setActiveView] = useState<ComplianceView>('overview');
  const [selectedFramework, setSelectedFramework] = useState<ComplianceFramework | null>(null);
  const [selectedViolation, setSelectedViolation] = useState<ComplianceViolation | null>(null);

  // Mock data - only shown in demo mode
  const mockStats: ComplianceStats | null = isDemoMode ? {
    total_frameworks: 0,
    active_frameworks: 0,
    overall_compliance_score: 0,
    open_violations: 0,
    resolved_this_month: 0,
    upcoming_assessments: 0
  } : null;

  const mockFrameworks: ComplianceFramework[] = isDemoMode ? [] : [];

  const mockViolations: ComplianceViolation[] = isDemoMode ? [] : [];

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical': return <Badge className="bg-red-100 text-red-800">Critical</Badge>;
      case 'high': return <Badge className="bg-orange-100 text-orange-800">High</Badge>;
      case 'medium': return <Badge className="bg-yellow-100 text-yellow-800">Medium</Badge>;
      case 'low': return <Badge className="bg-blue-100 text-blue-800">Low</Badge>;
      default: return <Badge variant="outline">{severity}</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return <Badge className="bg-green-100 text-green-800">Active</Badge>;
      case 'inactive': return <Badge className="bg-gray-100 text-gray-800">Inactive</Badge>;
      case 'deprecated': return <Badge className="bg-red-100 text-red-800">Deprecated</Badge>;
      case 'open': return <Badge className="bg-red-100 text-red-800">Open</Badge>;
      case 'acknowledged': return <Badge className="bg-yellow-100 text-yellow-800">Acknowledged</Badge>;
      case 'resolved': return <Badge className="bg-green-100 text-green-800">Resolved</Badge>;
      case 'false_positive': return <Badge className="bg-gray-100 text-gray-800">False Positive</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'privacy': return <Lock className="h-4 w-4 text-blue-600" />;
      case 'security': return <Shield className="h-4 w-4 text-red-600" />;
      case 'financial': return <Target className="h-4 w-4 text-green-600" />;
      case 'ai-ethics': return <Zap className="h-4 w-4 text-purple-600" />;
      default: return <BookOpen className="h-4 w-4 text-gray-600" />;
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center">
                  <BarChart3 className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Overall Compliance</p>
                  <h3 className="text-2xl font-bold text-green-900">
                    {(mockStats.overall_compliance_score * 100).toFixed(0)}%
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              +2% from last quarter
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <BookOpen className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Active Frameworks</p>
                  <h3 className="text-2xl font-bold text-blue-900">
                    {mockStats.active_frameworks}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              of {mockStats.total_frameworks} total
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-red-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-red-100 rounded-full flex items-center justify-center">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Open Violations</p>
                  <h3 className="text-2xl font-bold text-red-900">
                    {mockStats.open_violations}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              3 critical, 5 high priority
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Resolved This Month</p>
                  <h3 className="text-2xl font-bold text-purple-900">
                    {mockStats.resolved_this_month}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              12% improvement
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Frameworks */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <BookOpen className="h-5 w-5" />
              <span>Active Compliance Frameworks</span>
            </CardTitle>
            <Button onClick={() => setActiveView('frameworks')}>
              View All Frameworks
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {mockFrameworks.filter(f => f.status === 'active').slice(0, 6).map((framework) => (
              <div key={framework.id} className="border rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {getCategoryIcon(framework.category)}
                    <h3 className="font-semibold text-sm">{framework.name}</h3>
                  </div>
                  {getStatusBadge(framework.status)}
                </div>
                <p className="text-xs text-gray-600 mb-3">{framework.description}</p>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>Compliance Score</span>
                    <span className="font-bold">{(framework.compliance_score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full" 
                      style={{ width: `${framework.compliance_score * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{framework.requirements_count} requirements</span>
                    <span>{framework.violations_count} violations</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Critical Violations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <span>Critical Violations</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockViolations.filter(v => v.severity === 'critical' || v.severity === 'high').map((violation) => (
                <div key={violation.id} className="border-l-4 border-l-red-500 bg-red-50 p-4 rounded-r-lg">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-sm">{violation.title}</h3>
                    {getSeverityBadge(violation.severity)}
                  </div>
                  <p className="text-xs text-gray-600 mb-2">{violation.description}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{mockFrameworks.find(f => f.id === violation.framework_id)?.name}</span>
                    <span>Due: {new Date(violation.due_date!).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Clock className="h-5 w-5" />
              <span>Upcoming Assessments</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-sm">GDPR Quarterly Review</p>
                  <p className="text-xs text-gray-500">Scheduled assessment</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold">Dec 15, 2024</p>
                  <Badge className="bg-yellow-100 text-yellow-800">7 days</Badge>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-sm">SOX Annual Audit</p>
                  <p className="text-xs text-gray-500">External audit</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold">Dec 28, 2024</p>
                  <Badge className="bg-blue-100 text-blue-800">20 days</Badge>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-sm">AI Ethics Review</p>
                  <p className="text-xs text-gray-500">Internal assessment</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold">Jan 5, 2025</p>
                  <Badge className="bg-green-100 text-green-800">28 days</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderFrameworks = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Compliance Frameworks</h2>
        <Button>
          <BookOpen className="h-4 w-4 mr-2" />
          Add Framework
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {mockFrameworks.map((framework) => (
          <Card key={framework.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getCategoryIcon(framework.category)}
                  <div>
                    <CardTitle className="text-lg">{framework.name}</CardTitle>
                    <p className="text-sm text-gray-600">Version {framework.version}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {getStatusBadge(framework.status)}
                  <Button size="sm" variant="outline">
                    <Settings className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 mb-4">{framework.description}</p>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">{(framework.compliance_score * 100).toFixed(0)}%</p>
                  <p className="text-xs text-gray-500">Compliance Score</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">{framework.requirements_count}</p>
                  <p className="text-xs text-gray-500">Requirements</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-red-600">{framework.violations_count}</p>
                  <p className="text-xs text-gray-500">Open Violations</p>
                </div>
                <div className="text-center">
                  <p className="text-sm font-bold">{new Date(framework.last_assessment).toLocaleDateString()}</p>
                  <p className="text-xs text-gray-500">Last Assessment</p>
                </div>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                <div 
                  className={`h-3 rounded-full ${
                    framework.compliance_score >= 0.9 ? 'bg-green-500' :
                    framework.compliance_score >= 0.8 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${framework.compliance_score * 100}%` }}
                />
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">
                  Category: <span className="capitalize font-medium">{framework.category}</span>
                </span>
                <div className="flex space-x-2">
                  <Button size="sm" variant="outline">
                    <Eye className="h-3 w-3 mr-1" />
                    View Details
                  </Button>
                  <Button size="sm" variant="outline">
                    <FileText className="h-3 w-3 mr-1" />
                    Assessment
                  </Button>
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
      case 'frameworks':
        return renderFrameworks();
      case 'violations':
        return <div className="text-center text-gray-500 py-8">Violation management interface coming soon...</div>;
      case 'reports':
        return <div className="text-center text-gray-500 py-8">Compliance reports dashboard coming soon...</div>;
      case 'assessments':
        return <div className="text-center text-gray-500 py-8">Assessment management interface coming soon...</div>;
      case 'settings':
        return <div className="text-center text-gray-500 py-8">Compliance settings panel coming soon...</div>;
      default:
        return renderOverview();
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <div className="h-12 w-12 bg-blue-600 rounded-lg flex items-center justify-center">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Compliance Dashboard</h1>
            <p className="text-slate-600">
              {isDemoMode
                ? 'Viewing simulated compliance and regulatory data for demonstration'
                : 'Monitor regulatory compliance and risk management'
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

      {/* Show notice when in live mode with no data */}
      {!isDemoMode && !mockStats && (
        <Card className="bg-blue-50 border-blue-200 mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircleIcon className="h-5 w-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
                <p className="text-sm text-blue-700">
                  Compliance data will appear here when frameworks are configured. Toggle Demo Mode ON to see sample data.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Navigation */}
      <div className="bg-white rounded-lg border">
        <div className="flex space-x-1 p-1">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'frameworks', label: 'Frameworks', icon: BookOpen },
            { id: 'violations', label: 'Violations', icon: AlertTriangle },
            { id: 'reports', label: 'Reports', icon: FileText },
            { id: 'assessments', label: 'Assessments', icon: Calendar },
            { id: 'settings', label: 'Settings', icon: Settings }
          ].map((item) => {
            const Icon = item.icon;
            return (
              <Button
                key={item.id}
                variant={activeView === item.id ? 'default' : 'ghost'}
                onClick={() => setActiveView(item.id as ComplianceView)}
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
    </div>
  );
}