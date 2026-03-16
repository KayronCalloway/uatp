'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Link2, Hash, Shield, AlertCircle, CheckCircle } from 'lucide-react';
import { ChainContext } from '@/types/api';

interface ChainContextCardProps {
  chainContext: ChainContext;
}

export function ChainContextCard({ chainContext }: ChainContextCardProps) {
  if (!chainContext) {
    return null;
  }

  const {
    chain_id,
    position,
    previous_hash,
    merkle_root,
    consensus_method
  } = chainContext;

  const isGenesis = previous_hash === 'genesis';
  const hasMerkleRoot = merkle_root !== null && merkle_root !== undefined;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Link2 className="w-5 h-5 text-indigo-600" />
          Blockchain Context
          <span className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded ml-auto">
            UATP v7.4
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Chain Position Overview */}
          <div className="grid grid-cols-2 gap-4">
            {/* Chain ID */}
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Link2 className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-700">Chain ID</span>
              </div>
              <div className="text-lg font-bold text-blue-900 font-mono">
                {chain_id}
              </div>
            </div>

            {/* Position in Chain */}
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Hash className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium text-purple-700">Position</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-purple-900">{position}</span>
                {isGenesis && (
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded font-semibold">
                    Genesis
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Previous Hash */}
          <div className={`p-4 border rounded-lg ${
            isGenesis
              ? 'bg-green-50 border-green-200'
              : 'bg-gray-50 border-gray-200'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              <Hash className={`w-4 h-4 ${isGenesis ? 'text-green-600' : 'text-gray-600'}`} />
              <span className={`text-sm font-medium ${isGenesis ? 'text-green-700' : 'text-gray-700'}`}>
                Previous Hash
              </span>
            </div>
            {isGenesis ? (
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-sm text-green-800 font-semibold">
                  Genesis Block - First in Chain
                </span>
              </div>
            ) : (
              <div className="text-sm font-mono text-gray-800 break-all">
                {previous_hash}
              </div>
            )}
          </div>

          {/* Merkle Root */}
          <div className={`p-4 border rounded-lg ${
            hasMerkleRoot
              ? 'bg-green-50 border-green-200'
              : 'bg-yellow-50 border-yellow-200'
          }`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Shield className={`w-4 h-4 ${hasMerkleRoot ? 'text-green-600' : 'text-yellow-600'}`} />
                <span className={`text-sm font-medium ${hasMerkleRoot ? 'text-green-700' : 'text-yellow-700'}`}>
                  Merkle Root
                </span>
              </div>
              {hasMerkleRoot ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <AlertCircle className="w-4 h-4 text-yellow-600" />
              )}
            </div>
            {hasMerkleRoot ? (
              <div className="text-sm font-mono text-gray-800 break-all">
                {merkle_root}
              </div>
            ) : (
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-yellow-800">
                  <span className="font-semibold">Not yet computed:</span> Merkle root will be
                  calculated when the chain is sealed for enhanced integrity verification.
                </div>
              </div>
            )}
          </div>

          {/* Consensus Method */}
          <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-indigo-600" />
              <span className="text-sm font-medium text-indigo-700">Consensus Method</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-indigo-900 capitalize">
                {consensus_method.replace(/_/g, ' ')}
              </span>
              {consensus_method === 'proof-of-attribution' && (
                <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded font-semibold">
                  Economic
                </span>
              )}
            </div>
            {consensus_method === 'proof-of-attribution' && (
              <p className="text-xs text-indigo-600 mt-2">
                Uses economic contribution weights to validate capsule authenticity
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
