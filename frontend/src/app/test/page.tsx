'use client';

import Link from 'next/link';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { BackendIntegrationTest } from '@/components/debug/backend-integration-test';

export default function TestPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>UATP Frontend is Working!</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p>If you can see this page, the React/Next.js frontend is running successfully.</p>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-semibold text-green-800">System Status:</h3>
                <ul className="text-sm text-green-700 mt-2 space-y-1">
                  <li>• Next.js 15.4.1 running</li>
                  <li>• React components loading</li>
                  <li>• TailwindCSS styling active</li>
                  <li>• No auth loading loop</li>
                </ul>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-800">Available Routes:</h3>
                <ul className="text-sm text-blue-700 mt-2 space-y-1">
                  <li><Link href="/" className="underline hover:text-blue-900">/ - Main Application</Link></li>
                  <li><Link href="/test" className="underline hover:text-blue-900">/test - This Test Page</Link></li>
                </ul>
              </div>

              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h3 className="font-semibold text-purple-800">Features Ready:</h3>
                <ul className="text-sm text-purple-700 mt-2 space-y-1">
                  <li>• Universe Visualization (3D capsule rendering)</li>
                  <li>• Hallucination Detection (AI content analysis)</li>
                  <li>• Backend API Integration (http://localhost:8000)</li>
                  <li>• Real-time System Monitoring</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Backend Integration Test */}
        <div className="mt-8">
          <BackendIntegrationTest />
        </div>
      </div>
    </div>
  );
}
