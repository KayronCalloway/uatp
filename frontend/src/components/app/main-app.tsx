'use client';

import { useState } from 'react';
import { AppLayoutWithNav, ViewType } from '@/components/layout/app-layout';
import { Dashboard } from '@/components/dashboard/dashboard';
import { SystemOverviewDashboard } from '@/components/dashboard/system-overview-dashboard';
import { CapsuleExplorer } from '@/components/capsules/capsule-explorer';
import { TrustDashboard } from '@/components/trust/trust-dashboard';
import { EconomicDashboard } from '@/components/economics/economic-dashboard';
import { UniversePreview } from '@/components/universe/universe-preview';
import { UniverseVisualization } from '@/components/universe/universe-visualization';
import { FederationDashboard } from '@/components/federation/federation-dashboard';
import { GovernanceDashboard } from '@/components/governance/governance-dashboard';
import { OrganizationDashboard } from '@/components/organization/organization-dashboard';
import { AdvancedAttribution } from '@/components/economics/advanced-attribution';
import { HallucinationDetector } from '@/components/hallucination/hallucination-detector';
import { ConnectionTest } from '@/components/debug/connection-test';
import { APIConnectivityTest } from '@/components/debug/api-connectivity-test';
import { RightsEvolutionDashboard } from '@/components/dashboard/rights-evolution-dashboard';
import { LiveCaptureDashboard } from '@/components/dashboard/live-capture-dashboard';
import { ChainSealingDashboard } from '@/components/dashboard/chain-sealing-dashboard';
import { AKCDashboard } from '@/components/akc/akc-dashboard';
import { MirrorModeDashboard } from '@/components/mirror-mode/mirror-mode-dashboard';
import { PaymentDashboard } from '@/components/payments/payment-dashboard';
import { ComplianceDashboard } from '@/components/compliance/compliance-dashboard';
import { PlatformDashboard } from '@/components/platform/platform-dashboard';
import { ReasoningDashboard } from '@/components/reasoning/reasoning-dashboard';
import { SystemGraphView } from '@/components/system/system-graph-view';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { OnboardingBanner } from '@/components/onboarding/onboarding-banner';
import {
  TrendingUp,
  Globe,
  Settings as SettingsIcon,
  Construction
} from 'lucide-react';

export function MainApp() {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <SystemOverviewDashboard />;
      
      case 'capsules':
        return <CapsuleExplorer />;
      
      case 'trust':
        return <TrustDashboard />;
      
      case 'analytics':
        return <EconomicDashboard />;
      
      case 'universe':
        return <UniverseVisualization />;
      
      case 'federation':
        return <FederationDashboard />;
      
      case 'governance':
        return <GovernanceDashboard />;
      
      case 'organization':
        return <OrganizationDashboard />;
      
      case 'attribution':
        return <AdvancedAttribution />;
      
      case 'rights-evolution':
        return <RightsEvolutionDashboard />;
      
      case 'live-capture':
        return <LiveCaptureDashboard />;
      
      case 'chain-sealing':
        return <ChainSealingDashboard />;
      
      case 'akc':
        return <AKCDashboard />;
      
      case 'mirror-mode':
        return <MirrorModeDashboard />;
      
      case 'payments':
        return <PaymentDashboard />;
      
      case 'compliance':
        return <ComplianceDashboard />;
      
      case 'platforms':
        return <PlatformDashboard />;
      
      case 'reasoning':
        return <ReasoningDashboard />;

      case 'system':
        return <SystemGraphView />;

      case 'debug':
        return <DebugView />;
      
      case 'settings':
        return <ComingSoonCard title="Settings" description="System configuration coming soon" />;
      
      default:
        return <Dashboard onViewChange={setCurrentView} />;
    }
  };

  return (
    <AppLayoutWithNav currentView={currentView} onViewChange={setCurrentView}>
      {renderView()}
    </AppLayoutWithNav>
  );
}

function DebugView() {
  const [activeTab, setActiveTab] = useState<'api' | 'connection' | 'hallucination'>('api');

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Debug & Diagnostics</CardTitle>
          <div className="flex space-x-2 mt-4">
            <button
              onClick={() => setActiveTab('api')}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                activeTab === 'api'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              API Connectivity
            </button>
            <button
              onClick={() => setActiveTab('connection')}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                activeTab === 'connection'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Connection Test
            </button>
            <button
              onClick={() => setActiveTab('hallucination')}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${
                activeTab === 'hallucination'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Hallucination Detection
            </button>
          </div>
        </CardHeader>
      </Card>

      {activeTab === 'api' && <APIConnectivityTest />}
      {activeTab === 'connection' && <ConnectionTest />}
      {activeTab === 'hallucination' && <HallucinationDetector />}
    </div>
  );
}

function ComingSoonCard({ title, description }: { title: string; description: string }) {
  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader className="text-center">
        <div className="flex justify-center mb-4">
          <Construction className="h-12 w-12 text-gray-400" />
        </div>
        <CardTitle className="text-xl">{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-center">
        <p className="text-gray-600 mb-6">{description}</p>
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">Coming Soon</h3>
          <p className="text-sm text-blue-800">
            This feature is part of our roadmap for civilization-scale infrastructure.
            Stay tuned for updates!
          </p>
        </div>
      </CardContent>
    </Card>
  );
}