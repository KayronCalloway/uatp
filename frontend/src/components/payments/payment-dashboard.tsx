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
  CreditCard,
  DollarSign,
  TrendingUp,
  Download,
  Plus,
  Wallet,
  ArrowUpRight,
  ArrowDownLeft,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  BarChart3,
  PieChart,
  Target,
  Settings,
  Link,
  Globe,
  Shield,
  Zap,
  Calendar,
  Filter,
  Search,
  Eye,
  Play
} from 'lucide-react';

interface PaymentMethod {
  id: string;
  type: 'stripe' | 'paypal' | 'bank' | 'crypto';
  name: string;
  last_four?: string;
  brand?: string;
  enabled: boolean;
  created_at: string;
  usage_count: number;
}

interface Transaction {
  id: string;
  type: 'payout' | 'dividend' | 'commission' | 'refund';
  amount: number;
  currency: string;
  status: 'completed' | 'pending' | 'failed' | 'cancelled';
  method: PaymentMethod;
  recipient?: string;
  description: string;
  timestamp: string;
  fees: number;
  net_amount: number;
}

interface PayoutSummary {
  total_earned: number;
  total_paid: number;
  pending_payouts: number;
  this_month_earnings: number;
  payment_methods: number;
  avg_transaction_amount: number;
}

type PaymentView = 'overview' | 'transactions' | 'payouts' | 'methods' | 'analytics' | 'settings';

export function PaymentDashboard() {
  const { isDemoMode } = useDemoMode();
  const [activeView, setActiveView] = useState<PaymentView>('overview');
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [showAddMethod, setShowAddMethod] = useState(false);
  const [dateRange, setDateRange] = useState('30d');

  // Mock data - only shown in demo mode
  const mockSummary: PayoutSummary | null = isDemoMode ? {
    total_earned: 24567.89,
    total_paid: 19234.56,
    pending_payouts: 2145.78,
    this_month_earnings: 3456.78,
    payment_methods: 3,
    avg_transaction_amount: 127.45
  } : null;

  const mockPaymentMethods: PaymentMethod[] = isDemoMode ? [] : [];

  const mockTransactions: Transaction[] = isDemoMode ? [] : [];

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'payout': return <ArrowUpRight className="h-4 w-4 text-green-600" />;
      case 'dividend': return <Target className="h-4 w-4 text-blue-600" />;
      case 'commission': return <Zap className="h-4 w-4 text-purple-600" />;
      case 'refund': return <ArrowDownLeft className="h-4 w-4 text-orange-600" />;
      default: return <DollarSign className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed': return <Badge className="bg-green-100 text-green-800">Completed</Badge>;
      case 'pending': return <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>;
      case 'failed': return <Badge className="bg-red-100 text-red-800">Failed</Badge>;
      case 'cancelled': return <Badge className="bg-gray-100 text-gray-800">Cancelled</Badge>;
      default: return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getPaymentMethodIcon = (type: string) => {
    switch (type) {
      case 'stripe': return <CreditCard className="h-4 w-4 text-blue-600" />;
      case 'paypal': return <Wallet className="h-4 w-4 text-blue-500" />;
      case 'bank': return <Link className="h-4 w-4 text-green-600" />;
      case 'crypto': return <Globe className="h-4 w-4 text-orange-500" />;
      default: return <DollarSign className="h-4 w-4 text-gray-600" />;
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
                  <DollarSign className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Earned</p>
                  <h3 className="text-2xl font-bold text-green-900">
                    ${mockSummary.total_earned.toLocaleString()}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              +12.3% from last month
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <ArrowUpRight className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total Paid Out</p>
                  <h3 className="text-2xl font-bold text-blue-900">
                    ${mockSummary.total_paid.toLocaleString()}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              78% of total earnings
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-amber-100 rounded-full flex items-center justify-center">
                  <Clock className="h-5 w-5 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Pending Payouts</p>
                  <h3 className="text-2xl font-bold text-amber-900">
                    ${mockSummary.pending_payouts.toLocaleString()}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              Processing within 2-3 days
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-purple-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">This Month</p>
                  <h3 className="text-2xl font-bold text-purple-900">
                    ${mockSummary.this_month_earnings.toLocaleString()}
                  </h3>
                </div>
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              On track for record month
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
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Button onClick={() => setActiveView('payouts')} className="flex items-center justify-center space-x-2 h-16">
              <ArrowUpRight className="h-5 w-5" />
              <span>Request Payout</span>
            </Button>
            <Button onClick={() => setActiveView('methods')} variant="outline" className="flex items-center justify-center space-x-2 h-16">
              <CreditCard className="h-5 w-5" />
              <span>Payment Methods</span>
            </Button>
            <Button onClick={() => setActiveView('transactions')} variant="outline" className="flex items-center justify-center space-x-2 h-16">
              <BarChart3 className="h-5 w-5" />
              <span>View Transactions</span>
            </Button>
            <Button variant="outline" className="flex items-center justify-center space-x-2 h-16">
              <Download className="h-5 w-5" />
              <span>Export Report</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Transactions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Clock className="h-5 w-5" />
              <span>Recent Transactions</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockTransactions.slice(0, 4).map((transaction) => (
                <div key={transaction.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="h-8 w-8 bg-white rounded-full flex items-center justify-center border">
                      {getTransactionIcon(transaction.type)}
                    </div>
                    <div>
                      <p className="font-medium text-sm capitalize">{transaction.type}</p>
                      <p className="text-xs text-gray-500">{transaction.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-sm">
                      ${transaction.amount.toLocaleString()}
                    </p>
                    {getStatusBadge(transaction.status)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <CreditCard className="h-5 w-5" />
              <span>Payment Methods</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockPaymentMethods.map((method) => (
                <div key={method.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="h-8 w-8 bg-white rounded-full flex items-center justify-center border">
                      {getPaymentMethodIcon(method.type)}
                    </div>
                    <div>
                      <p className="font-medium text-sm">{method.name}</p>
                      <p className="text-xs text-gray-500">{method.usage_count} transactions</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={method.enabled ? 'default' : 'secondary'}>
                      {method.enabled ? 'Active' : 'Inactive'}
                    </Badge>
                    <Button size="sm" variant="outline">
                      <Settings className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
              <Button 
                onClick={() => setShowAddMethod(true)}
                variant="outline" 
                className="w-full flex items-center justify-center space-x-2"
              >
                <Plus className="h-4 w-4" />
                <span>Add Payment Method</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderTransactions = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Transaction History</h2>
        <div className="flex items-center space-x-3">
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center space-x-4 mb-6">
            <div className="flex items-center space-x-2">
              <Search className="h-4 w-4 text-gray-400" />
              <Input placeholder="Search transactions..." className="w-64" />
            </div>
            <select className="rounded-md border border-gray-300 px-3 py-2">
              <option>All Types</option>
              <option>Payouts</option>
              <option>Dividends</option>
              <option>Commissions</option>
              <option>Refunds</option>
            </select>
            <select className="rounded-md border border-gray-300 px-3 py-2">
              <option>All Status</option>
              <option>Completed</option>
              <option>Pending</option>
              <option>Failed</option>
            </select>
            <select className="rounded-md border border-gray-300 px-3 py-2">
              <option>Last 30 days</option>
              <option>Last 90 days</option>
              <option>Last year</option>
              <option>All time</option>
            </select>
          </div>

          <div className="space-y-4">
            {mockTransactions.map((transaction) => (
              <div key={transaction.id} className="border rounded-lg p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="h-10 w-10 bg-white rounded-full flex items-center justify-center border-2">
                      {getTransactionIcon(transaction.type)}
                    </div>
                    <div>
                      <div className="flex items-center space-x-3 mb-1">
                        <h3 className="font-semibold capitalize">{transaction.type}</h3>
                        {getStatusBadge(transaction.status)}
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{transaction.description}</p>
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>{new Date(transaction.timestamp).toLocaleString()}</span>
                        <span>{transaction.method.name}</span>
                        <span>Fee: ${transaction.fees.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-green-600 mb-1">
                      ${transaction.amount.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-500">
                      Net: ${transaction.net_amount.toLocaleString()}
                    </div>
                    <Button size="sm" variant="outline" className="mt-2">
                      <Eye className="h-3 w-3 mr-1" />
                      Details
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderView = () => {
    switch (activeView) {
      case 'transactions':
        return renderTransactions();
      case 'payouts':
        return <div className="text-center text-gray-500 py-8">Payout request interface coming soon...</div>;
      case 'methods':
        return <div className="text-center text-gray-500 py-8">Payment method management coming soon...</div>;
      case 'analytics':
        return <div className="text-center text-gray-500 py-8">Payment analytics dashboard coming soon...</div>;
      case 'settings':
        return <div className="text-center text-gray-500 py-8">Payment settings panel coming soon...</div>;
      default:
        return renderOverview();
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <div className="h-12 w-12 bg-green-600 rounded-lg flex items-center justify-center">
            <DollarSign className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Payment Dashboard</h1>
            <p className="text-slate-600">
              {isDemoMode
                ? 'Viewing simulated payment and earnings data for demonstration'
                : 'Manage earnings, payouts, and payment methods'
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
      {!isDemoMode && !mockSummary && (
        <Card className="bg-blue-50 border-blue-200 mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
                <p className="text-sm text-blue-700">
                  Payment data will appear here when earnings are tracked. Toggle Demo Mode ON to see sample data.
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
            { id: 'transactions', label: 'Transactions', icon: Clock },
            { id: 'payouts', label: 'Payouts', icon: ArrowUpRight },
            { id: 'methods', label: 'Payment Methods', icon: CreditCard },
            { id: 'analytics', label: 'Analytics', icon: PieChart },
            { id: 'settings', label: 'Settings', icon: Settings }
          ].map((item) => {
            const Icon = item.icon;
            return (
              <Button
                key={item.id}
                variant={activeView === item.id ? 'default' : 'ghost'}
                onClick={() => setActiveView(item.id as PaymentView)}
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