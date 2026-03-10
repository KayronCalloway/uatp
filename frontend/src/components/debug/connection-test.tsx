'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { api } from '@/lib/api-client';

export function ConnectionTest() {
  const [testResult, setTestResult] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const runConnectionTest = async () => {
    setIsLoading(true);
    setTestResult('Testing connection...');

    try {
      // Test basic health endpoint
      const health = await api.healthCheck();
      setTestResult(`Success! Connected to server. Status: ${health.status}, Version: ${health.version}`);
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setTestResult(`Connection failed: ${errorMessage}`);
      console.error('Connection test error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Connection Test</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Button
          onClick={runConnectionTest}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? 'Testing...' : 'Test Connection'}
        </Button>

        {testResult && (
          <div className={`p-3 rounded-md text-sm ${
            testResult.includes('Success')
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}>
            {testResult}
          </div>
        )}

        <div className="text-sm text-gray-600">
          <p>API URL: {process.env.NEXT_PUBLIC_UATP_API_URL || 'http://localhost:8000'}</p>
          <p>API Key: {process.env.NEXT_PUBLIC_UATP_API_KEY ? 'Set' : 'Not set'}</p>
        </div>
      </CardContent>
    </Card>
  );
}
