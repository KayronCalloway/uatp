'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface TestResult {
  endpoint: string;
  status: 'pending' | 'success' | 'error' | 'unauthorized';
  message: string;
  data?: any;
}

export function BackendIntegrationTest() {
  const [results, setResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const testEndpoints = [
    { name: 'Health Check', test: () => apiClient.healthCheck() },
    { name: 'Index Page', test: () => apiClient.getIndex() },
    { name: 'Capsules List', test: () => apiClient.listCapsules() },
    { name: 'Trust Metrics', test: () => apiClient.getTrustMetrics() },
    { name: 'Capsule Stats', test: () => apiClient.getCapsuleStats() },
    { name: 'Governance Stats', test: () => apiClient.getGovernanceStats() },
    { name: 'Federation Stats', test: () => apiClient.getFederationStats() },
    { name: 'Economic Metrics', test: () => apiClient.getEconomicMetrics() },
  ];

  const runTests = async () => {
    setIsRunning(true);
    setResults([]);
    
    for (const endpoint of testEndpoints) {
      setResults(prev => [...prev, {
        endpoint: endpoint.name,
        status: 'pending',
        message: 'Testing...'
      }]);

      try {
        const data = await endpoint.test();
        setResults(prev => prev.map(r => 
          r.endpoint === endpoint.name 
            ? { ...r, status: 'success', message: 'Success!', data }
            : r
        ));
      } catch (error: any) {
        const isUnauthorized = error.message?.includes('API key required') || error.response?.status === 401;
        setResults(prev => prev.map(r => 
          r.endpoint === endpoint.name 
            ? { 
                ...r, 
                status: isUnauthorized ? 'unauthorized' : 'error', 
                message: error.message || 'Unknown error',
                data: error.response?.data
              }
            : r
        ));
      }
    }
    
    setIsRunning(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'text-green-600';
      case 'error': return 'text-red-600';
      case 'unauthorized': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return '●';
      case 'error': return '●';
      case 'unauthorized': return '●';
      case 'pending': return '○';
      default: return '○';
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Backend Integration Test</h2>
        <Button onClick={runTests} disabled={isRunning}>
          {isRunning ? 'Running Tests...' : 'Run API Tests'}
        </Button>
      </div>

      <div className="space-y-4">
        {results.map((result, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold flex items-center gap-2">
                {getStatusIcon(result.status)}
                {result.endpoint}
              </h3>
              <span className={`text-sm font-medium ${getStatusColor(result.status)}`}>
                {result.status.toUpperCase()}
              </span>
            </div>
            
            <p className={`text-sm ${getStatusColor(result.status)}`}>
              {result.message}
            </p>

            {result.data && (
              <details className="mt-3">
                <summary className="text-sm text-gray-600 cursor-pointer">
                  View Response Data
                </summary>
                <pre className="text-xs bg-gray-100 p-2 rounded mt-2 overflow-x-auto">
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              </details>
            )}
          </div>
        ))}
      </div>

      {results.length === 0 && !isRunning && (
        <div className="text-center text-gray-500 py-8">
          Click "Run API Tests" to test backend integration
        </div>
      )}

      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold text-blue-800 mb-2">Integration Status</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <strong>Backend URL:</strong> {process.env.NEXT_PUBLIC_UATP_API_URL || 'Not configured'}
          </div>
          <div>
            <strong>API Key:</strong> {process.env.NEXT_PUBLIC_UATP_API_KEY ? 'Configured' : 'Not configured'}
          </div>
          <div>
            <strong>Mock Fallback:</strong> {process.env.NEXT_PUBLIC_ENABLE_MOCK_FALLBACK || 'false'}
          </div>
          <div>
            <strong>Real API:</strong> {process.env.NEXT_PUBLIC_ENABLE_REAL_API || 'false'}
          </div>
        </div>
      </div>
    </Card>
  );
}