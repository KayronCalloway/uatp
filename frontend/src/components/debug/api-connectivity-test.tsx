'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, RefreshCw, Clock, Database } from 'lucide-react';

export function APIConnectivityTest() {
  const [testEndpoints, setTestEndpoints] = useState(false);

  // Test health endpoint
  const { data: healthData, isLoading: healthLoading, error: healthError } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.healthCheck(),
    enabled: testEndpoints,
    retry: 1
  });

  // Test capsules endpoint
  const { data: capsulesData, isLoading: capsulesLoading, error: capsulesError } = useQuery({
    queryKey: ['capsules-test'],
    queryFn: () => api.getCapsules({ per_page: 5 }),
    enabled: testEndpoints,
    retry: 1
  });

  // Test metrics endpoint
  const { data: metricsData, isLoading: metricsLoading, error: metricsError } = useQuery({
    queryKey: ['metrics-test'],
    queryFn: () => api.getMetrics(),
    enabled: testEndpoints,
    retry: 1
  });

  const runTests = () => {
    setTestEndpoints(true);
  };

  const resetTests = () => {
    setTestEndpoints(false);
  };

  const getStatusIcon = (loading: boolean, error: any, data: any) => {
    if (loading) return <Clock className="h-4 w-4 text-yellow-500" />;
    if (error) return <XCircle className="h-4 w-4 text-red-500" />;
    if (data) return <CheckCircle className="h-4 w-4 text-green-500" />;
    return <RefreshCw className="h-4 w-4 text-gray-400" />;
  };

  const getStatusText = (loading: boolean, error: any, data: any) => {
    if (loading) return "Testing...";
    if (error) return `Failed: ${error.message}`;
    if (data) return "Success";
    return "Not tested";
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Database className="h-5 w-5" />
            <span>API Connectivity Test</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <Button onClick={runTests} disabled={testEndpoints}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Run Tests
              </Button>
              <Button onClick={resetTests} variant="outline">
                Reset
              </Button>
            </div>

            {testEndpoints && (
              <div className="space-y-4 pt-4 border-t">
                <h3 className="font-semibold">Endpoint Tests:</h3>

                {/* Health Test */}
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(healthLoading, healthError, healthData)}
                    <span className="font-medium">/health</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">
                      {getStatusText(healthLoading, healthError, healthData)}
                    </Badge>
                    {healthData && (
                      <Badge className="bg-green-100 text-green-800">
                        {healthData.status}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Capsules Test */}
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(capsulesLoading, capsulesError, capsulesData)}
                    <span className="font-medium">/capsules</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">
                      {getStatusText(capsulesLoading, capsulesError, capsulesData)}
                    </Badge>
                    {capsulesData && (
                      <Badge className="bg-blue-100 text-blue-800">
                        {capsulesData.capsules?.length || 0} capsules
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Metrics Test */}
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(metricsLoading, metricsError, metricsData)}
                    <span className="font-medium">/metrics</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline">
                      {getStatusText(metricsLoading, metricsError, metricsData)}
                    </Badge>
                  </div>
                </div>
              </div>
            )}

            {/* Real Data Preview */}
            {capsulesData && (
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-semibold mb-2">Sample Real Data:</h4>
                <pre className="text-xs overflow-x-auto">
                  {JSON.stringify(capsulesData.capsules?.[0], null, 2)}
                </pre>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
