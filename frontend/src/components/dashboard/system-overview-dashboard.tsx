'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Activity,
  Home,
  Video,
  Link,
  Bot,
  Globe,
  Building2,
  DollarSign,
  Shield,
  CheckCircle,
  Server,
  Target,
  Lock,
  ChevronRight
} from 'lucide-react';
import { LiveCaptureDashboard } from './live-capture-dashboard';
import { ChainSealingDashboard } from './chain-sealing-dashboard';
import { RightsEvolutionDashboard } from './rights-evolution-dashboard';
import { FederationDashboard } from '@/components/federation/federation-dashboard';
import { GovernanceDashboard } from '@/components/governance/governance-dashboard';
import { EconomicDashboard } from '@/components/economics/economic-dashboard';
import { TrustDashboard } from '@/components/trust/trust-dashboard';

type DashboardView =
  | 'overview'
  | 'live-capture'
  | 'chain-sealing'
  | 'rights-evolution'
  | 'federation'
  | 'governance'
  | 'economics'
  | 'trust';

export function SystemOverviewDashboard() {
  const [activeView, setActiveView] = useState<DashboardView>('overview');

  const dashboardSections = [
    { id: 'overview', name: 'System Overview', icon: Home, color: 'blue' },
    { id: 'live-capture', name: 'Live Capture', icon: Video, color: 'green' },
    { id: 'chain-sealing', name: 'Chain Sealing', icon: Link, color: 'purple' },
    { id: 'rights-evolution', name: 'AI Rights', icon: Bot, color: 'amber' },
    { id: 'federation', name: 'Federation', icon: Globe, color: 'indigo' },
    { id: 'governance', name: 'Governance', icon: Building2, color: 'slate' },
    { id: 'economics', name: 'Economics', icon: DollarSign, color: 'emerald' },
    { id: 'trust', name: 'Trust System', icon: Shield, color: 'red' },
  ];

  const renderDashboard = () => {
    switch (activeView) {
      case 'live-capture':
        return <LiveCaptureDashboard />;
      case 'chain-sealing':
        return <ChainSealingDashboard />;
      case 'rights-evolution':
        return <RightsEvolutionDashboard />;
      case 'federation':
        return <FederationDashboard />;
      case 'governance':
        return <GovernanceDashboard />;
      case 'economics':
        return <EconomicDashboard />;
      case 'trust':
        return <TrustDashboard />;
      default:
        return (
          <div className="space-y-8">
            {/* Professional Header */}
            <div className="flex items-center space-x-4 mb-8">
              <div className="h-12 w-12 bg-blue-600 rounded-lg flex items-center justify-center">
                <Activity className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900 tracking-tight">System Overview</h1>
                <p className="text-slate-600">Civilization-grade AI attribution infrastructure</p>
              </div>
            </div>

            {/* System Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="border-l-4 border-l-green-500 bg-green-50/50">
                <div className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-green-900">System Status</h3>
                        <p className="text-sm text-green-700">All systems operational</p>
                      </div>
                    </div>
                    <Badge variant="default" className="bg-green-500">Active</Badge>
                  </div>
                </div>
              </Card>

              <Card className="border-l-4 border-l-blue-500 bg-blue-50/50">
                <div className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <Server className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-blue-900">Backend API</h3>
                        <p className="text-sm text-blue-700">Full integration active</p>
                      </div>
                    </div>
                    <Badge variant="default" className="bg-blue-500">Online</Badge>
                  </div>
                </div>
              </Card>

              <Card className="border-l-4 border-l-purple-500 bg-purple-50/50">
                <div className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                        <Target className="h-5 w-5 text-purple-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-purple-900">Features</h3>
                        <p className="text-sm text-purple-700">15+ components ready</p>
                      </div>
                    </div>
                    <Badge variant="default" className="bg-purple-500">Ready</Badge>
                  </div>
                </div>
              </Card>

              <Card className="border-l-4 border-l-amber-500 bg-amber-50/50">
                <div className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="h-10 w-10 bg-amber-100 rounded-full flex items-center justify-center">
                        <Lock className="h-5 w-5 text-amber-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-amber-900">Security</h3>
                        <p className="text-sm text-amber-700">Production ready</p>
                      </div>
                    </div>
                    <Badge variant="default" className="bg-amber-500">Secured</Badge>
                  </div>
                </div>
              </Card>
            </div>

            {/* Professional Feature Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <Video className="h-5 w-5 text-green-600" />
                  </div>
                  <h3 className="font-semibold text-slate-900">Live Capture System</h3>
                </div>
                <p className="text-sm text-slate-600 mb-4">
                  Real-time conversation capture from Claude Code, Cursor, and Windsurf
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setActiveView('live-capture')}
                  className="w-full flex items-center justify-center space-x-2"
                >
                  <span>View Details</span>
                  <ChevronRight className="h-3 w-3" />
                </Button>
              </Card>

              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="h-10 w-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <Link className="h-5 w-5 text-purple-600" />
                  </div>
                  <h3 className="font-semibold text-slate-900">Chain Sealing</h3>
                </div>
                <p className="text-sm text-slate-600 mb-4">
                  Cryptographic sealing and verification of capsule chains
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setActiveView('chain-sealing')}
                  className="w-full flex items-center justify-center space-x-2"
                >
                  <span>View Details</span>
                  <ChevronRight className="h-3 w-3" />
                </Button>
              </Card>

              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="h-10 w-10 bg-amber-100 rounded-lg flex items-center justify-center">
                    <Bot className="h-5 w-5 text-amber-600" />
                  </div>
                  <h3 className="font-semibold text-slate-900">AI Rights Evolution</h3>
                </div>
                <p className="text-sm text-slate-600 mb-4">
                  Dynamic rights management based on AI behavior and trust
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setActiveView('rights-evolution')}
                  className="w-full flex items-center justify-center space-x-2"
                >
                  <span>View Details</span>
                  <ChevronRight className="h-3 w-3" />
                </Button>
              </Card>

              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="h-10 w-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                    <Globe className="h-5 w-5 text-indigo-600" />
                  </div>
                  <h3 className="font-semibold text-slate-900">Federation Network</h3>
                </div>
                <p className="text-sm text-slate-600 mb-4">
                  Multi-node federation for distributed UATP deployment
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setActiveView('federation')}
                  className="w-full flex items-center justify-center space-x-2"
                >
                  <span>View Details</span>
                  <ChevronRight className="h-3 w-3" />
                </Button>
              </Card>

              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="h-10 w-10 bg-slate-100 rounded-lg flex items-center justify-center">
                    <Building2 className="h-5 w-5 text-slate-600" />
                  </div>
                  <h3 className="font-semibold text-slate-900">Governance System</h3>
                </div>
                <p className="text-sm text-slate-600 mb-4">
                  Democratic governance with proposals and voting mechanisms
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setActiveView('governance')}
                  className="w-full flex items-center justify-center space-x-2"
                >
                  <span>View Details</span>
                  <ChevronRight className="h-3 w-3" />
                </Button>
              </Card>

              <Card className="p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="h-10 w-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                    <DollarSign className="h-5 w-5 text-emerald-600" />
                  </div>
                  <h3 className="font-semibold text-slate-900">Economic Engine</h3>
                </div>
                <p className="text-sm text-slate-600 mb-4">
                  Attribution economics and compensation mechanisms
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setActiveView('economics')}
                  className="w-full flex items-center justify-center space-x-2"
                >
                  <span>View Details</span>
                  <ChevronRight className="h-3 w-3" />
                </Button>
              </Card>
            </div>

            {/* System Architecture */}
            <Card className="p-6">
              <div className="flex items-center space-x-3 mb-6">
                <div className="h-8 w-8 bg-slate-600 rounded-lg flex items-center justify-center">
                  <Server className="h-4 w-4 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900">System Architecture</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-3 text-blue-800 flex items-center space-x-2">
                    <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
                    <span>Backend Components</span>
                  </h4>
                  <ul className="text-sm space-y-2">
                    <li className="flex items-center space-x-2"><CheckCircle className="h-3 w-3 text-green-500" /><span>Quart Web Framework</span></li>
                    <li className="flex items-center space-x-2"><CheckCircle className="h-3 w-3 text-green-500" /><span>SQLite Database with Migrations</span></li>
                    <li className="flex items-center space-x-2"><CheckCircle className="h-3 w-3 text-green-500" /><span>Async Request Processing</span></li>
                    <li className="flex items-center space-x-2"><CheckCircle className="h-3 w-3 text-green-500" /><span>Prometheus Metrics</span></li>
                    <li className="flex items-center space-x-2"><CheckCircle className="h-3 w-3 text-green-500" /><span>JWT Authentication</span></li>
                    <li className="flex items-center space-x-2"><CheckCircle className="h-3 w-3 text-green-500" /><span>Rate Limiting & CORS</span></li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-3 text-emerald-800 flex items-center space-x-2">
                    <div className="h-2 w-2 bg-emerald-500 rounded-full"></div>
                    <span>Frontend Components</span>
                  </h4>
                  <ul className="text-sm space-y-2">
                    <li className="flex items-center space-x-2"><CheckCircle className="h-3 w-3 text-green-500" /><span>Next.js 15.4.1 Framework</span></li>
                    <li className="flex items-center space-x-2"><CheckCircle className="h-3 w-3 text-green-500" /><span>React Query for API State</span></li>
                    <li className="flex items-center space-x-2"><CheckCircle className="h-3 w-3 text-green-500" /><span>TailwindCSS Styling</span></li>
                    <li className="flex items-center space-x-2"><CheckCircle className="h-3 w-3 text-green-500" /><span>Real-time API Integration</span></li>
                    <li className="flex items-center space-x-2"><CheckCircle className="h-3 w-3 text-green-500" /><span>Interactive Dashboards</span></li>
                    <li className="flex items-center space-x-2"><CheckCircle className="h-3 w-3 text-green-500" /><span>3D Universe Visualization</span></li>
                  </ul>
                </div>
              </div>
            </Card>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8 overflow-x-auto py-4">
            {dashboardSections.map((section) => {
              const IconComponent = section.icon;
              return (
                <Button
                  key={section.id}
                  variant={activeView === section.id ? "default" : "ghost"}
                  onClick={() => setActiveView(section.id as DashboardView)}
                  className="flex items-center space-x-2 whitespace-nowrap"
                >
                  <IconComponent className="h-4 w-4" />
                  <span>{section.name}</span>
                </Button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderDashboard()}
      </div>
    </div>
  );
}
