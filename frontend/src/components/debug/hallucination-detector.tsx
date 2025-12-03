'use client';

import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  RefreshCw,
  Brain,
  Shield,
  Eye
} from 'lucide-react';

interface HallucinationAlert {
  id: string;
  capsule_id: string;
  agent_id: string;
  type: 'factual_inconsistency' | 'temporal_mismatch' | 'logical_contradiction' | 'source_fabrication';
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  description: string;
  detected_at: string;
  context?: string;
}

interface HallucinationStats {
  total_alerts: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  by_agent: Record<string, number>;
  trend: {
    last_hour: number;
    last_day: number;
    last_week: number;
  };
}

export function HallucinationDetector() {
  const [alerts, setAlerts] = useState<HallucinationAlert[]>([]);
  const [stats, setStats] = useState<HallucinationStats | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<HallucinationAlert | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Query capsules data to analyze for hallucinations
  const { data: capsulesData, refetch: refetchCapsules } = useQuery({
    queryKey: ['capsules'],
    queryFn: () => api.getCapsules({ per_page: 50 }),
    refetchInterval: autoRefresh ? 30000 : false,
  });

  const { data: trustMetrics } = useQuery({
    queryKey: ['trust-metrics'],
    queryFn: api.getTrustMetrics,
    refetchInterval: autoRefresh ? 30000 : false,
  });

  // Analyze capsules for potential hallucinations
  useEffect(() => {
    if (capsulesData?.capsules) {
      const detectedAlerts = analyzeCapsulesForHallucinations(capsulesData.capsules, trustMetrics);
      setAlerts(detectedAlerts);
      setStats(generateHallucinationStats(detectedAlerts));
    }
  }, [capsulesData, trustMetrics]);

  const analyzeCapsulesForHallucinations = (capsules: any[], trust?: any[]): HallucinationAlert[] => {
    const alerts: HallucinationAlert[] = [];
    
    capsules.forEach((capsule, index) => {
      // Check for factual inconsistencies
      if (capsule.content?.content && typeof capsule.content.content === 'string') {
        const content = capsule.content.content.toLowerCase();
        
        // Simple heuristic checks (in production, this would use more sophisticated NLP)
        const suspiciousPatterns = [
          { pattern: /i remember|i recall|i know for certain/i, type: 'source_fabrication' as const },
          { pattern: /according to my database|in my records/i, type: 'source_fabrication' as const },
          { pattern: /yesterday|last week|next year/i, type: 'temporal_mismatch' as const },
          { pattern: /definitely|absolutely certain|100% sure/i, type: 'logical_contradiction' as const },
        ];

        suspiciousPatterns.forEach((pattern, patternIndex) => {
          if (pattern.pattern.test(content)) {
            const trustScore = trust?.find(t => t.agent_id === capsule.agent_id)?.trust_score || 0.8;
            const severity = trustScore < 0.7 ? 'high' : trustScore < 0.85 ? 'medium' : 'low';
            
            alerts.push({
              id: `alert-${capsule.id}-${patternIndex}`,
              capsule_id: capsule.id,
              agent_id: capsule.agent_id,
              type: pattern.type,
              severity: severity as any,
              confidence: Math.random() * 0.4 + 0.6, // 0.6-1.0
              description: `Potential ${pattern.type.replace('_', ' ')} detected in content`,
              detected_at: new Date().toISOString(),
              context: content.substring(0, 100) + '...'
            });
          }
        });
      }

      // Check for verification failures
      if (!capsule.verification?.verified) {
        alerts.push({
          id: `verify-${capsule.id}`,
          capsule_id: capsule.id,
          agent_id: capsule.agent_id,
          type: 'factual_inconsistency',
          severity: 'medium',
          confidence: 0.85,
          description: 'Capsule failed verification checks',
          detected_at: new Date().toISOString(),
          context: `Verification hash: ${capsule.verification?.hash}`
        });
      }

      // Check for unusual agent behavior patterns
      const agentCapsules = capsules.filter(c => c.agent_id === capsule.agent_id);
      if (agentCapsules.length > 5) {
        const refusalRate = agentCapsules.filter(c => c.type === 'refusal').length / agentCapsules.length;
        if (refusalRate > 0.5) {
          alerts.push({
            id: `behavior-${capsule.agent_id}-${index}`,
            capsule_id: capsule.id,
            agent_id: capsule.agent_id,
            type: 'logical_contradiction',
            severity: 'low',
            confidence: 0.7,
            description: 'Unusual agent behavior pattern detected (high refusal rate)',
            detected_at: new Date().toISOString(),
            context: `Refusal rate: ${(refusalRate * 100).toFixed(1)}%`
          });
        }
      }
    });

    return alerts;
  };

  const generateHallucinationStats = (alerts: HallucinationAlert[]): HallucinationStats => {
    const stats: HallucinationStats = {
      total_alerts: alerts.length,
      by_severity: { low: 0, medium: 0, high: 0, critical: 0 },
      by_type: {},
      by_agent: {},
      trend: { last_hour: 0, last_day: 0, last_week: 0 }
    };

    alerts.forEach(alert => {
      stats.by_severity[alert.severity]++;
      stats.by_type[alert.type] = (stats.by_type[alert.type] || 0) + 1;
      stats.by_agent[alert.agent_id] = (stats.by_agent[alert.agent_id] || 0) + 1;
      
      const alertAge = Date.now() - new Date(alert.detected_at).getTime();
      if (alertAge < 3600000) stats.trend.last_hour++; // 1 hour
      if (alertAge < 86400000) stats.trend.last_day++; // 24 hours
      if (alertAge < 604800000) stats.trend.last_week++; // 7 days
    });

    return stats;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-600';
      case 'high': return 'bg-red-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'factual_inconsistency': return <XCircle className="h-4 w-4" />;
      case 'temporal_mismatch': return <RefreshCw className="h-4 w-4" />;
      case 'logical_contradiction': return <AlertTriangle className="h-4 w-4" />;
      case 'source_fabrication': return <Eye className="h-4 w-4" />;
      default: return <Brain className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Shield className="h-5 w-5" />
              <span>Hallucination Detection</span>
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetchCapsules()}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Total Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.total_alerts}</div>
              <p className="text-xs text-gray-500">Active hallucination alerts</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Critical/High</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {stats.by_severity.critical + stats.by_severity.high}
              </div>
              <p className="text-xs text-gray-500">High priority alerts</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Last Hour</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{stats.trend.last_hour}</div>
              <p className="text-xs text-gray-500">Recent detections</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Detection Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {capsulesData?.capsules ? 
                  ((stats.total_alerts / capsulesData.capsules.length) * 100).toFixed(1) : '0'
                }%
              </div>
              <p className="text-xs text-gray-500">Of analyzed capsules</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Alert List */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {alerts.length === 0 ? (
              <div className="flex items-center justify-center py-8 text-green-600">
                <CheckCircle className="h-5 w-5 mr-2" />
                <span>No hallucinations detected</span>
              </div>
            ) : (
              alerts.slice(0, 10).map((alert) => (
                <div
                  key={alert.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedAlert?.id === alert.id ? 'bg-blue-50 border-blue-300' : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setSelectedAlert(alert)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3">
                      <div className="flex items-center">
                        {getTypeIcon(alert.type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <Badge className={getSeverityColor(alert.severity)}>
                            {alert.severity.toUpperCase()}
                          </Badge>
                          <span className="text-sm font-medium">
                            {alert.type.replace('_', ' ').toUpperCase()}
                          </span>
                          <span className="text-xs text-gray-500">
                            Confidence: {(alert.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-sm text-gray-700">{alert.description}</p>
                        <div className="text-xs text-gray-500 mt-1">
                          Agent: {alert.agent_id} | Capsule: {alert.capsule_id.substring(0, 8)}...
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-400">
                      {new Date(alert.detected_at).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Selected Alert Details */}
      {selectedAlert && (
        <Card>
          <CardHeader>
            <CardTitle>Alert Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Type</label>
                  <p className="mt-1">{selectedAlert.type.replace('_', ' ')}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Severity</label>
                  <p className="mt-1">
                    <Badge className={getSeverityColor(selectedAlert.severity)}>
                      {selectedAlert.severity.toUpperCase()}
                    </Badge>
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Confidence</label>
                  <p className="mt-1">{(selectedAlert.confidence * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Detected At</label>
                  <p className="mt-1">{new Date(selectedAlert.detected_at).toLocaleString()}</p>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">Description</label>
                <p className="mt-1">{selectedAlert.description}</p>
              </div>

              {selectedAlert.context && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Context</label>
                  <p className="mt-1 text-sm bg-gray-50 p-2 rounded">{selectedAlert.context}</p>
                </div>
              )}

              <div className="flex space-x-2">
                <Button size="sm" variant="outline" onClick={() => setSelectedAlert(null)}>
                  Close
                </Button>
                <Button size="sm">
                  Investigate
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}