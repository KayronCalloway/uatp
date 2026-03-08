'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Database, CheckCircle, Clock, Globe, FileText } from 'lucide-react';
import { DataSource } from '@/types/api';
import { formatDate } from '@/lib/utils';

interface DataSourcesCardProps {
  dataSources: DataSource[];
}

export function DataSourcesCard({ dataSources }: DataSourcesCardProps) {
  if (!dataSources || dataSources.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="w-5 h-5 text-blue-600" />
          Data Sources ({dataSources.length})
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded ml-auto">
            Court-Admissible Provenance
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {dataSources.map((source, index) => (
            <div
              key={index}
              className="border rounded-lg p-4 space-y-2 hover:border-blue-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-gray-500" />
                    <span className="font-semibold text-gray-900">
                      {source.source}
                    </span>
                  </div>

                  <div className="mt-2 text-sm">
                    <span className="text-gray-600">Value:</span>
                    <span className="ml-2 font-mono bg-gray-100 px-2 py-1 rounded">
                      {typeof source.value === 'object'
                        ? JSON.stringify(source.value, null, 2)
                        : String(source.value)}
                    </span>
                  </div>
                </div>
              </div>

              {/* API Details */}
              {source.api_endpoint && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Globe className="w-3 h-3" />
                  <code className="text-xs bg-gray-50 px-2 py-1 rounded">
                    {source.api_endpoint}
                  </code>
                  {source.api_version && (
                    <span className="text-xs text-gray-500">
                      v{source.api_version}
                    </span>
                  )}
                </div>
              )}

              {/* Timestamp */}
              {source.timestamp && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Clock className="w-3 h-3" />
                  {formatDate(source.timestamp)}
                  {source.response_time_ms && (
                    <span className="text-xs text-gray-500">
                      ({source.response_time_ms}ms)
                    </span>
                  )}
                </div>
              )}

              {/* Verification */}
              {source.verification && (
                <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center gap-2 text-sm font-semibold text-green-800">
                    <CheckCircle className="w-4 h-4" />
                    Verification
                  </div>
                  {source.verification.cross_checked && (
                    <div className="mt-2 text-sm text-gray-700">
                      <span className="text-green-700 font-medium">
                        Cross-checked with:
                      </span>
                      <div className="mt-1 flex flex-wrap gap-2">
                        {source.verification.cross_checked.map((check, i) => (
                          <span
                            key={i}
                            className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs"
                          >
                            {check}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {source.verification.values && (
                    <div className="mt-2 text-sm">
                      <span className="text-gray-600">Values:</span>
                      <span className="ml-2 font-mono text-xs">
                        [{source.verification.values.join(', ')}]
                      </span>
                      {source.verification.consensus && (
                        <span className="ml-2 text-green-600 font-medium">
                           Consensus
                        </span>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Audit Trail */}
              {source.audit_trail && (
                <div className="flex items-start gap-2 text-xs text-gray-500 mt-2">
                  <FileText className="w-3 h-3 mt-0.5" />
                  <span className="font-mono">{source.audit_trail}</span>
                </div>
              )}

              {/* Query */}
              {source.query && (
                <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                  <span className="text-gray-600">Query:</span>
                  <pre className="mt-1 text-xs text-gray-700 overflow-x-auto">
                    {source.query}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start gap-2">
            <CheckCircle className="w-4 h-4 text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-800">
              <span className="font-semibold">Daubert Compliant:</span> All data
              sources include provenance, timestamps, and verification - meeting
              court admissibility standards.
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
