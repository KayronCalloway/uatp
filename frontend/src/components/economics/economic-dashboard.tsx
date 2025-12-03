'use client';

import { useQuery } from '@tanstack/react-query';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { api } from '@/lib/api-client';
import { getMockEconomicData, mockApiCall } from '@/lib/mock-data';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DollarSign,
  TrendingUp,
  Users,
  ArrowUpDown,
  PieChart,
  RefreshCw,
  Clock,
  Building,
  Wallet,
  Target,
  Award,
  AlertCircle,
  Play
} from 'lucide-react';
import { formatDate } from '@/lib/utils';

export function EconomicDashboard() {
  const { isDemoMode } = useDemoMode();

  const { data: capsuleStats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['capsule-stats'],
    queryFn: api.getCapsuleStats,
    refetchInterval: 60000,
  });

  const { data: trustMetrics, isLoading: trustLoading } = useQuery({
    queryKey: ['trust-metrics'],
    queryFn: api.getTrustMetrics,
    refetchInterval: 60000,
  });

  // Use demo data only when demo mode is enabled
  const economicData = isDemoMode ? getMockEconomicData() : null;

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'dividend': return <Award className="h-4 w-4 text-green-600" />;
      case 'attribution': return <Target className="h-4 w-4 text-blue-600" />;
      case 'common_fund': return <Building className="h-4 w-4 text-purple-600" />;
      default: return <DollarSign className="h-4 w-4 text-gray-600" />;
    }
  };

  const getTransactionColor = (type: string) => {
    switch (type) {
      case 'dividend': return 'text-green-600';
      case 'attribution': return 'text-blue-600';
      case 'common_fund': return 'text-purple-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <CardTitle className="flex items-center space-x-2">
                <DollarSign className="h-5 w-5" />
                <span>Economic Dashboard</span>
              </CardTitle>
              {isDemoMode && (
                <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-300">
                  <Play className="h-3 w-3 mr-1" />
                  Demo Data
                </Badge>
              )}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchStats()}
              disabled={statsLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${statsLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            {isDemoMode
              ? 'Viewing simulated economic data for demonstration'
              : 'Economic transactions and attribution analytics'
            }
          </p>
        </CardHeader>
      </Card>

      {/* Show notice when in live mode with no data */}
      {!isDemoMode && !economicData && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
                <p className="text-sm text-blue-700">
                  Economic data will appear here when transactions are processed. Toggle Demo Mode ON to see sample data.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Economic Overview - Only show if we have data */}
      {economicData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Attribution Value</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${economicData.totalAttributionValue.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">+{economicData.monthlyGrowth}%</span> from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Dividends</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {economicData.activeDividends}
              </div>
              <p className="text-xs text-muted-foreground">
                Dividend streams active
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Common Fund</CardTitle>
              <Building className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${economicData.commonFundBalance.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">
                Available for distribution
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Monthly Payouts</CardTitle>
              <Wallet className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${economicData.payoutsThisMonth.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">
                Distributed this month
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Grid - Only show if we have data */}
      {economicData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Top Earners */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Users className="h-5 w-5" />
                <span>Top Earners</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {economicData.topEarners.map((earner, index) => (
                <div
                  key={earner.agent_id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-bold text-blue-600">
                        #{index + 1}
                      </span>
                    </div>
                    <div>
                      <div className="text-sm font-medium">
                        {earner.agent_id}
                      </div>
                      <div className="text-xs text-gray-500">
                        {earner.contributions} contributions
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-bold text-green-600">
                      ${earner.earnings.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Total earnings
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Attribution Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <PieChart className="h-5 w-5" />
              <span>Attribution Breakdown</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {capsuleStats?.types && Object.entries(capsuleStats.types).map(([type, count]) => {
                const percentage = ((count as number) / capsuleStats.total_capsules) * 100;
                const estimatedValue = (count as number) * 25; // Mock calculation
                
                return (
                  <div key={type} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="capitalize">{type}</span>
                      <span className="font-medium">${estimatedValue}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <div className="text-xs text-gray-500">
                      {count} capsules ({percentage.toFixed(1)}%)
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
      )}

      {/* Recent Transactions - Only show if we have data */}
      {economicData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <ArrowUpDown className="h-5 w-5" />
              <span>Recent Transactions</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {economicData.recentTransactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    {getTransactionIcon(transaction.type)}
                    <div>
                      <div className="text-sm font-medium">
                        {transaction.description}
                      </div>
                      <div className="text-xs text-gray-500">
                        {transaction.agent_id} • {formatDate(transaction.timestamp)}
                      </div>
                    </div>
                  </div>
                  <div className={`text-sm font-bold ${getTransactionColor(transaction.type)}`}>
                    +${transaction.amount.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Economic Insights - Only show in demo mode */}
      {economicData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5" />
              <span>Economic Insights</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <div className="flex items-start space-x-3">
                  <TrendingUp className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-green-900">Growing Attribution</h4>
                    <p className="text-sm text-green-800">
                      Attribution rewards have increased by 23% this month, indicating healthy network growth.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <div className="flex items-start space-x-3">
                  <Users className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-blue-900">Active Contributors</h4>
                    <p className="text-sm text-blue-800">
                      {trustMetrics?.length || 0} active agents contributing to the network with consistent participation.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                <div className="flex items-start space-x-3">
                  <Building className="h-5 w-5 text-purple-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-purple-900">Common Fund Health</h4>
                    <p className="text-sm text-purple-800">
                      Common fund balance is healthy, supporting network sustainability and growth initiatives.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="h-5 w-5 text-orange-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-orange-900">Distribution Efficiency</h4>
                    <p className="text-sm text-orange-800">
                      Economic distribution is running smoothly with minimal delays or disputes.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}