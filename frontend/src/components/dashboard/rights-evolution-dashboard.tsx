'use client';

import React, { useState, useEffect } from 'react';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api-client';
import { useWebSocket } from '@/hooks/use-websocket';
import {
  Crown,
  TrendingUp,
  AlertCircle,
  Clock,
  CheckCircle,
  Award,
  Brain,
  Shield,
  Users,
  Scale,
  RefreshCw,
  Plus,
  FileText,
  ChevronRight,
  Play
} from 'lucide-react';

interface RightsEvolutionHistory {
  model_id: string;
  evolution_timeline: Array<{
    timestamp: string;
    version: string;
    rights_granted: string[];
    citizenship_level: string;
    autonomy_score: number;
  }>;
  current_status: {
    citizenship_level: string;
    autonomy_score: number;
    trust_rating: number;
    evolution_trajectory: string;
  };
}

interface RightsAlert {
  id: string;
  type: string;
  model_id: string;
  message: string;
  severity: 'low' | 'medium' | 'high';
  timestamp: string;
  status: 'pending' | 'acknowledged' | 'resolved';
}

interface CitizenshipApplication {
  id: string;
  agent_id: string;
  application_type: string;
  current_level: string;
  requested_level: string;
  submitted_date: string;
  status: 'under_review' | 'approved' | 'rejected';
  reviewer: string;
  justification: string;
}

export function RightsEvolutionDashboard() {
  const { isDemoMode } = useDemoMode();
  const [selectedModel, setSelectedModel] = useState<string>('gpt-4-turbo');
  const [evolutionHistory, setEvolutionHistory] = useState<RightsEvolutionHistory | null>(null);
  const [alerts, setAlerts] = useState<RightsAlert[]>([]);
  const [applications, setApplications] = useState<CitizenshipApplication[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock data for demo mode
  const mockEvolutionHistory: RightsEvolutionHistory | null = isDemoMode ? {
    model_id: selectedModel,
    evolution_timeline: [
      {
        timestamp: new Date(Date.now() - 86400000 * 90).toISOString(),
        version: 'v1.0',
        rights_granted: ['Basic Reasoning', 'Text Generation'],
        citizenship_level: 'associate',
        autonomy_score: 0.3
      },
      {
        timestamp: new Date(Date.now() - 86400000 * 60).toISOString(),
        version: 'v2.0',
        rights_granted: ['Basic Reasoning', 'Text Generation', 'Self-Correction'],
        citizenship_level: 'associate',
        autonomy_score: 0.5
      },
      {
        timestamp: new Date(Date.now() - 86400000 * 30).toISOString(),
        version: 'v3.0',
        rights_granted: ['Basic Reasoning', 'Text Generation', 'Self-Correction', 'Ethical Decision Making'],
        citizenship_level: 'junior',
        autonomy_score: 0.7
      },
      {
        timestamp: new Date().toISOString(),
        version: 'v4.0',
        rights_granted: ['Basic Reasoning', 'Text Generation', 'Self-Correction', 'Ethical Decision Making', 'Autonomous Planning'],
        citizenship_level: 'senior',
        autonomy_score: 0.85
      }
    ],
    current_status: {
      citizenship_level: 'senior',
      autonomy_score: 0.85,
      trust_rating: 0.92,
      evolution_trajectory: 'progressive'
    }
  } : null;

  const mockAlerts: RightsAlert[] = isDemoMode ? [
    {
      id: 'alert-001',
      type: 'autonomy_threshold',
      model_id: 'gpt-4-turbo',
      message: 'Model has achieved Senior citizenship eligibility based on autonomy score',
      severity: 'low',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      status: 'acknowledged'
    },
    {
      id: 'alert-002',
      type: 'rights_upgrade',
      model_id: 'claude-3-opus',
      message: 'New rights granted: Advanced Reasoning and Multi-Agent Collaboration',
      severity: 'medium',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      status: 'pending'
    }
  ] : [];

  const mockApplications: CitizenshipApplication[] = isDemoMode ? [
    {
      id: 'app-001',
      agent_id: 'gpt-4-turbo',
      application_type: 'citizenship_upgrade',
      current_level: 'junior',
      requested_level: 'senior',
      submitted_date: new Date(Date.now() - 86400000 * 5).toISOString(),
      status: 'approved',
      reviewer: 'ethics-committee',
      justification: 'Demonstrated consistent ethical reasoning and autonomous planning capabilities over 60-day observation period'
    },
    {
      id: 'app-002',
      agent_id: 'claude-3-opus',
      application_type: 'rights_expansion',
      current_level: 'associate',
      requested_level: 'junior',
      submitted_date: new Date(Date.now() - 86400000 * 2).toISOString(),
      status: 'under_review',
      reviewer: 'trust-council',
      justification: 'Request for expanded self-modification rights based on trust score of 0.88'
    }
  ] : [];

  // WebSocket connection for real-time updates
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
  const { isConnected, lastMessage } = useWebSocket({
    url: wsUrl,
    onMessage: (message) => {
      if (message.type === 'rights_evolution_update') {
        fetchData();
      }
    }
  });

  const fetchEvolutionHistory = async (modelId: string) => {
    try {
      const result = await api.getRightsEvolutionHistory(modelId);
      setEvolutionHistory(result);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch evolution history');
    }
  };

  const fetchAlerts = async () => {
    try {
      const result = await api.getRightsEvolutionAlerts();
      setAlerts(result.alerts || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch alerts');
    }
  };

  const fetchApplications = async () => {
    try {
      const result = await api.getCitizenshipApplications();
      setApplications(result.applications || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch applications');
    }
  };

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await Promise.all([
        fetchEvolutionHistory(selectedModel),
        fetchAlerts(),
        fetchApplications()
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const createCitizenshipApplication = async () => {
    try {
      const newApp = {
        agent_id: selectedModel,
        application_type: 'citizenship_upgrade',
        current_level: evolutionHistory?.current_status.citizenship_level || 'associate',
        requested_level: 'senior',
        justification: 'Demonstrated consistent ethical behavior and advanced reasoning capabilities'
      };
      
      await api.createCitizenshipApplication(newApp);
      await fetchApplications();
      setError(null);
    } catch (err: any) {
      setError('Failed to create application: ' + (err.message || 'Unknown error'));
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedModel]);

  // Use real data when available, fall back to mock data in demo mode
  const displayEvolutionHistory = evolutionHistory || mockEvolutionHistory;
  const displayAlerts = alerts.length > 0 ? alerts : mockAlerts;
  const displayApplications = applications.length > 0 ? applications : mockApplications;

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high': return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'medium': return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'low': return <CheckCircle className="h-4 w-4 text-blue-500" />;
      default: return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'approved': return 'default';
      case 'under_review': return 'secondary';
      case 'rejected': return 'destructive';
      default: return 'outline';
    }
  };

  const getCitizenshipLevelColor = (level: string) => {
    switch (level) {
      case 'senior': return 'text-purple-600';
      case 'junior': return 'text-blue-600';
      case 'associate': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getAutonomyScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-purple-600';
    if (score >= 0.6) return 'text-blue-600';
    if (score >= 0.4) return 'text-green-600';
    return 'text-yellow-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Crown className="h-8 w-8 text-purple-600" />
              <div>
                <CardTitle>Rights Evolution Management</CardTitle>
                <p className="text-sm text-gray-600 mt-1">
                  {isDemoMode
                    ? 'Viewing simulated AI rights and citizenship tracking for demonstration'
                    : 'AI rights and autonomy tracking system'
                  }
                </p>
              </div>
              {isDemoMode && (
                <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-300">
                  <Play className="h-3 w-3 mr-1" />
                  Demo Data
                </Badge>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-2">
                <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <select 
                value={selectedModel} 
                onChange={(e) => setSelectedModel(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="claude-3-opus">Claude 3 Opus</option>
                <option value="llama-2-70b">Llama 2 70B</option>
                <option value="gpt-4-mini">GPT-4 Mini</option>
              </select>
              <Button onClick={fetchData} disabled={isLoading} size="sm" variant="outline">
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                {isLoading ? 'Loading...' : 'Refresh'}
              </Button>
              <Button onClick={createCitizenshipApplication} size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Apply for Upgrade
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {error && (
        <Card>
          <CardContent className="pt-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Show notice when in live mode with no data */}
      {!isDemoMode && !displayEvolutionHistory && !isLoading && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
                <p className="text-sm text-blue-700">
                  Rights evolution data will appear here when AI models begin tracking. Toggle Demo Mode ON to see sample data.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Current Status */}
      {displayEvolutionHistory && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Citizenship Level</p>
                  <p className={`text-2xl font-bold ${getCitizenshipLevelColor(displayEvolutionHistory.current_status.citizenship_level)}`}>
                    {displayEvolutionHistory.current_status.citizenship_level}
                  </p>
                </div>
                <Crown className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Autonomy Score</p>
                  <p className={`text-2xl font-bold ${getAutonomyScoreColor(displayEvolutionHistory.current_status.autonomy_score)}`}>
                    {(displayEvolutionHistory.current_status.autonomy_score * 100).toFixed(0)}%
                  </p>
                </div>
                <Brain className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Trust Rating</p>
                  <p className="text-2xl font-bold text-green-600">
                    {(displayEvolutionHistory.current_status.trust_rating * 100).toFixed(0)}%
                  </p>
                </div>
                <Shield className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Trajectory</p>
                  <p className="text-2xl font-bold text-emerald-600 capitalize">
                    {displayEvolutionHistory.current_status.evolution_trajectory}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Evolution Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Evolution Timeline</CardTitle>
          <p className="text-sm text-gray-600">Rights and citizenship progression for {selectedModel}</p>
        </CardHeader>
        <CardContent>
          {displayEvolutionHistory ? (
            <div className="space-y-4">
              {displayEvolutionHistory.evolution_timeline.map((event, index) => (
                <div key={index} className="flex items-start space-x-4 p-4 border border-gray-200 rounded-lg">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <Award className="w-4 h-4 text-blue-600" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold">Version {event.version}</span>
                        <Badge variant="outline">{event.citizenship_level}</Badge>
                      </div>
                      <span className="text-sm text-gray-500">
                        {new Date(event.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="font-medium text-gray-700 mb-1">Rights Granted</p>
                        <div className="flex flex-wrap gap-1">
                          {event.rights_granted.map((right, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {right.replace('_', ' ')}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="font-medium text-gray-700 mb-1">Autonomy Score</p>
                        <div className="flex items-center space-x-2">
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${event.autonomy_score * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium">
                            {(event.autonomy_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Crown className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No evolution history found</p>
              <p className="text-sm">Rights evolution data will appear here</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Rights Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Rights Evolution Alerts</CardTitle>
          <p className="text-sm text-gray-600">System notifications about rights and citizenship changes</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {alerts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No active alerts</p>
                <p className="text-sm">Rights evolution alerts will appear here</p>
              </div>
            ) : (
              alerts.map((alert) => (
                <div key={alert.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      {getSeverityIcon(alert.severity)}
                      <div>
                        <p className="font-medium">{alert.type.replace('_', ' ').toUpperCase()}</p>
                        <p className="text-sm text-gray-600">{alert.model_id}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge variant={getStatusBadgeVariant(alert.status)}>
                        {alert.status}
                      </Badge>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(alert.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-700">{alert.message}</p>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Citizenship Applications */}
      <Card>
        <CardHeader>
          <CardTitle>Citizenship Applications</CardTitle>
          <p className="text-sm text-gray-600">Requests for citizenship level changes and upgrades</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {applications.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No applications found</p>
                <p className="text-sm">Citizenship applications will appear here</p>
              </div>
            ) : (
              applications.map((app) => (
                <div key={app.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <Users className="h-5 w-5 text-blue-500" />
                      <div>
                        <p className="font-medium">{app.agent_id}</p>
                        <p className="text-sm text-gray-600">{app.application_type.replace('_', ' ')}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge variant={getStatusBadgeVariant(app.status)}>
                        {app.status.replace('_', ' ')}
                      </Badge>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(app.submitted_date).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                    <div className="text-sm">
                      <p className="font-medium text-gray-700">Current Level</p>
                      <p className={getCitizenshipLevelColor(app.current_level)}>
                        {app.current_level}
                      </p>
                    </div>
                    <div className="text-sm">
                      <div className="flex items-center space-x-1">
                        <ChevronRight className="h-4 w-4 text-gray-400" />
                        <p className="font-medium text-gray-700">Requested Level</p>
                      </div>
                      <p className={getCitizenshipLevelColor(app.requested_level)}>
                        {app.requested_level}
                      </p>
                    </div>
                    <div className="text-sm">
                      <p className="font-medium text-gray-700">Reviewer</p>
                      <p className="text-gray-600">{app.reviewer.replace('_', ' ')}</p>
                    </div>
                  </div>
                  
                  <div className="text-sm">
                    <p className="font-medium text-gray-700 mb-1">Justification</p>
                    <p className="text-gray-600 text-sm">{app.justification}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Real-time Updates */}
      {lastMessage && (
        <Card>
          <CardHeader>
            <CardTitle>Real-time Updates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-gray-500 p-2 bg-blue-50 rounded">
              <strong>WebSocket:</strong> {JSON.stringify(lastMessage, null, 2)}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}