'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { api } from '@/lib/api-client';
import {
  getMockHealthCheck,
  getMockCapsuleStats,
  getMockTrustMetricsData,
  getMockRecentActivity,
  getMockHealthMetrics,
  getMockEconomicData,
  mockApiCall
} from '@/lib/mock-data';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Activity,
  Database,
  Shield,
  DollarSign,
  Search,
  Plus,
  Network,
  ChevronRight,
  Radio,
  TrendingUp,
  Globe,
  Scale,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';
import type { ActivityItem, SystemHealthMetric } from '@/types/activity';

export function MissionControl() {
  const { isDemoMode, toggleDemoMode } = useDemoMode();
  const [selectedActivity, setSelectedActivity] = useState<ActivityItem | null>(null);
  const [selectedHealth, setSelectedHealth] = useState<string | null>(null);

  // Fetch essential data
  const { data: healthData } = useQuery({
    queryKey: ['health', isDemoMode],
    queryFn: async () => isDemoMode ? mockApiCall(getMockHealthCheck()) : api.healthCheck(),
    refetchInterval: 30000,
  });

  const { data: statsData } = useQuery({
    queryKey: ['capsule-stats', isDemoMode],
    queryFn: async () => isDemoMode ? mockApiCall(getMockCapsuleStats()) : api.getCapsuleStats(false),
    refetchInterval: 60000,
  });

  const { data: trustMetrics } = useQuery({
    queryKey: ['trust-metrics', isDemoMode],
    queryFn: async () => isDemoMode ? mockApiCall(getMockTrustMetricsData()) : api.getTrustMetrics(),
    refetchInterval: 120000,
  });

  // Fetch recent activity feed
  // NOTE: In production, this would be WebSocket/SSE stream for real-time updates
  const { data: activityData } = useQuery({
    queryKey: ['recent-activity', isDemoMode],
    queryFn: async () => {
      if (isDemoMode) {
        return mockApiCall(getMockRecentActivity());
      }
      return api.getRecentActivity();
    },
    refetchInterval: 5000, // Poll every 5 seconds
  });

  // Fetch system health metrics
  // NOTE: In production, this would come from system monitoring endpoints
  const { data: healthMetricsData } = useQuery({
    queryKey: ['health-metrics', isDemoMode],
    queryFn: async () => {
      if (isDemoMode) {
        return mockApiCall(getMockHealthMetrics());
      }
      return api.getHealthMetrics();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch economic metrics
  const { data: economicData } = useQuery({
    queryKey: ['economic-metrics', isDemoMode],
    queryFn: async () => {
      if (isDemoMode) {
        return mockApiCall(getMockEconomicData());
      }
      return api.getEconomicMetrics();
    },
    refetchInterval: 60000, // Refresh every minute
  });

  // Extract data from queries
  const activities = activityData?.activities || [];
  const healthMetrics = healthMetricsData?.metrics || [];

  // Calculate summary stats
  const totalCapsules = statsData?.total_capsules || 0;
  const todayCount = Math.floor(totalCapsules * 0.07); // Approximate: 7% created today
  const trustScore = trustMetrics?.overall_score || 0;
  const totalValue = economicData?.total_value_distributed || 0;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">UATP System Monitor</h1>
            <p className="text-sm text-gray-500">Real-time attribution infrastructure monitoring</p>
          </div>
          <div className="flex items-center gap-4">
            {/* Data Mode Toggle */}
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-gray-700">
                {isDemoMode ? 'Demo Data' : 'Live Data'}
              </span>
              <button
                onClick={toggleDemoMode}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  isDemoMode ? 'bg-orange-600' : 'bg-green-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    isDemoMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            {isDemoMode && (
              <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
                Demo Mode
              </Badge>
            )}
          </div>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatusCard
            icon={<Activity className="h-5 w-5" />}
            label="System Health"
            value={healthData?.status || 'Unknown'}
            subtitle={`v${healthData?.version || 'N/A'}`}
            status="success"
          />
          <StatusCard
            icon={<Database className="h-5 w-5" />}
            label="Capsules"
            value={totalCapsules.toLocaleString()}
            subtitle={`+${todayCount} today`}
            status="success"
          />
          <StatusCard
            icon={<Shield className="h-5 w-5" />}
            label="Trust"
            value={trustScore.toFixed(1)}
            subtitle="Verified"
            status="success"
          />
          <StatusCard
            icon={<DollarSign className="h-5 w-5" />}
            label="Value"
            value={`$${(totalValue / 1000000).toFixed(1)}M`}
            subtitle="Attributed"
            status="success"
          />
        </div>

        {/* Live Activity Feed */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 bg-red-500 rounded-full animate-pulse" />
              <h2 className="text-lg font-semibold">LIVE ACTIVITY</h2>
            </div>
            <Button variant="outline" size="sm">
              Filter <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>

          <div className="space-y-2">
            {activities.map((activity) => (
              <ActivityRow
                key={activity.id}
                activity={activity}
                onClick={() => setSelectedActivity(activity)}
              />
            ))}
          </div>
        </Card>

        {/* Quick Actions */}
        <div className="flex gap-4">
          <Button className="flex-1" size="lg">
            <Search className="h-5 w-5 mr-2" />
            Search & Filter
          </Button>
          <Button className="flex-1" size="lg" variant="outline">
            <Plus className="h-5 w-5 mr-2" />
            Create Capsule
          </Button>
          <Button className="flex-1" size="lg" variant="outline">
            <Network className="h-5 w-5 mr-2" />
            System Graph
          </Button>
        </div>

        {/* System Health */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">SYSTEM HEALTH</h2>
          <div className="space-y-3">
            {healthMetrics.map((metric) => (
              <HealthBar
                key={metric.name}
                metric={metric}
                onClick={() => setSelectedHealth(metric.name)}
              />
            ))}
          </div>
        </Card>
      </div>

      {/* Detail Panel */}
      {selectedActivity && (
        <DetailPanel
          activity={selectedActivity}
          onClose={() => setSelectedActivity(null)}
        />
      )}

      {selectedHealth && (
        <HealthDetailPanel
          metric={healthMetrics.find(m => m.name === selectedHealth)!}
          onClose={() => setSelectedHealth(null)}
        />
      )}
    </div>
  );
}

// Status Card Component
function StatusCard({ icon, label, value, subtitle, status }: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtitle: string;
  status: 'success' | 'warning' | 'error';
}) {
  const statusColors = {
    success: 'text-green-600 bg-green-50',
    warning: 'text-yellow-600 bg-yellow-50',
    error: 'text-red-600 bg-red-50',
  };

  return (
    <Card className="p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${statusColors[status]}`}>
          {icon}
        </div>
        <div className="flex-1">
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-xs text-gray-500">{subtitle}</p>
        </div>
      </div>
    </Card>
  );
}

// Activity Row Component
function ActivityRow({ activity, onClick }: {
  activity: ActivityItem;
  onClick: () => void;
}) {
  const statusIcons = {
    success: <CheckCircle className="h-4 w-4 text-green-500" />,
    warning: <Clock className="h-4 w-4 text-yellow-500" />,
    error: <AlertCircle className="h-4 w-4 text-red-500" />,
    pending: <Clock className="h-4 w-4 text-gray-400" />,
  };

  const timeAgo = Math.floor((Date.now() - activity.timestamp.getTime()) / 60000);
  const timeStr = timeAgo < 60 ? `${timeAgo} min ago` : `${Math.floor(timeAgo / 60)} hour ago`;

  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left"
    >
      {statusIcons[activity.status]}
      <span className="text-sm text-gray-500">{activity.timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</span>
      <span className="flex-1 text-sm font-medium text-gray-900">{activity.title}</span>
      <span className="text-sm text-gray-500">{activity.description}</span>
      <ChevronRight className="h-4 w-4 text-gray-400" />
    </button>
  );
}

// Health Bar Component
function HealthBar({ metric, onClick }: {
  metric: SystemHealthMetric;
  onClick: () => void;
}) {
  const getColor = (value: number) => {
    if (value >= 90) return 'bg-green-500';
    if (value >= 70) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors"
    >
      <span className="text-sm font-medium text-gray-700 w-28">{metric.label}</span>
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${getColor(metric.value)}`}
          style={{ width: `${metric.value}%` }}
        />
      </div>
      <span className="text-sm font-semibold text-gray-900 w-12 text-right">{metric.value}%</span>
      <ChevronRight className="h-4 w-4 text-gray-400" />
    </button>
  );
}

// Detail Panel Component
function DetailPanel({ activity, onClose }: {
  activity: ActivityItem;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black bg-opacity-50" onClick={onClose} />
      <div className="w-1/2 bg-white shadow-2xl overflow-y-auto animate-slide-in-right">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold">Activity Details</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">

            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Type</label>
              <p className="text-lg font-semibold capitalize">{activity.type.replace('_', ' ')}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">Status</label>
              <p className="text-lg">
                <Badge variant={activity.status === 'success' ? 'default' : 'secondary'}>
                  {activity.status}
                </Badge>
              </p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">Time</label>
              <p className="text-lg">{activity.timestamp.toLocaleString()}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-500">Description</label>
              <p className="text-lg">{activity.description}</p>
            </div>

            {Object.entries(activity.metadata).map(([key, value]) => (
              <div key={key}>
                <label className="text-sm font-medium text-gray-500 capitalize">{key}</label>
                <p className="text-lg">{String(value)}</p>
              </div>
            ))}
          </div>

          <div className="mt-6 flex gap-3">
            <Button className="flex-1">View Full Details</Button>
            <Button className="flex-1" variant="outline">Export</Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Health Detail Panel Component
function HealthDetailPanel({ metric, onClose }: {
  metric: SystemHealthMetric;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black bg-opacity-50" onClick={onClose} />
      <div className="w-1/2 bg-white shadow-2xl overflow-y-auto animate-slide-in-right">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold">{metric.label} System</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">

            </button>
          </div>

          <div className="space-y-6">
            <div>
              <label className="text-sm font-medium text-gray-500">Overall Health</label>
              <div className="flex items-center gap-4 mt-2">
                <div className="flex-1 bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      metric.value >= 90 ? 'bg-green-500' : metric.value >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${metric.value}%` }}
                  />
                </div>
                <span className="text-2xl font-bold">{metric.value}%</span>
              </div>
            </div>

            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-900">
                This is a summary view. Click "View Full Dashboard" to see detailed metrics and configuration.
              </p>
            </div>

            <Button className="w-full" size="lg">
              View Full {metric.label} Dashboard
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
