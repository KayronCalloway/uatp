'use client';

import React, { useState, useEffect } from 'react';
import { PlatformInfo } from '@/types/onboarding';
import { Button } from '@/components/ui/button';

interface PlatformSelectionStepProps {
  onComplete: (data?: Record<string, any>) => void;
  availablePlatforms: Record<string, PlatformInfo>;
  isLoading: boolean;
  error: string | null;
}

export function PlatformSelectionStep({
  onComplete,
  availablePlatforms,
  isLoading,
  error
}: PlatformSelectionStepProps) {
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [showApiKeyInput, setShowApiKeyInput] = useState(false);
  const [apiKey, setApiKey] = useState('');

  // Auto-select if only one platform is available
  useEffect(() => {
    const availablePlatformIds = Object.entries(availablePlatforms)
      .filter(([_, platform]) => platform.available)
      .map(([id]) => id);

    if (availablePlatformIds.length === 1 && !selectedPlatform) {
      setSelectedPlatform(availablePlatformIds[0]);
    }
  }, [availablePlatforms, selectedPlatform]);

  const handlePlatformSelect = (platformId: string) => {
    setSelectedPlatform(platformId);
    const platform = availablePlatforms[platformId];

    if (platform.requires_api_key && !platform.available) {
      setShowApiKeyInput(true);
    } else {
      setShowApiKeyInput(false);
    }
  };

  const handleConnect = () => {
    if (!selectedPlatform) return;

    const connectionData: Record<string, any> = {
      preferred_platform: selectedPlatform,
    };

    if (showApiKeyInput && apiKey.trim()) {
      connectionData.api_key = apiKey.trim();
    }

    onComplete(connectionData);
  };

  const getPlatformStatusBadge = (platform: PlatformInfo) => {
    if (platform.available) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
          [OK] Ready to use
        </span>
      );
    } else if (platform.requires_api_key) {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
           API Key needed
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
           Setup needed
        </span>
      );
    }
  };

  const getRecommendedPlatform = (): string | null => {
    // Find the first available platform
    const available = Object.entries(availablePlatforms).find(([_, platform]) => platform.available);
    if (available) return available[0];

    // Otherwise, recommend OpenAI as most user-friendly
    if (availablePlatforms.openai) return 'openai';

    // Return first platform if no OpenAI
    return Object.keys(availablePlatforms)[0] || null;
  };

  const recommendedPlatform = getRecommendedPlatform();
  const platformsArray = Object.entries(availablePlatforms);

  if (platformsArray.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-4xl mb-4">[WARN]</div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No AI Platforms Detected</h3>
        <p className="text-gray-600 mb-4">
          We couldn't detect any compatible AI platforms. You can still continue and set this up later.
        </p>
        <Button onClick={() => onComplete({ skip_platform: true })}>
          Continue Without Platform
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Connect Your AI Platform
        </h2>
        <p className="text-gray-600">
          Choose your preferred AI platform. We'll set up the integration with optimal configuration.
        </p>
      </div>

      {/* Recommended Platform Highlight */}
      {recommendedPlatform && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-blue-500 mr-2"></span>
            <span className="text-blue-800 font-medium">
              Recommended: {availablePlatforms[recommendedPlatform].name}
            </span>
          </div>
          <p className="text-blue-700 text-sm mt-1">
            {availablePlatforms[recommendedPlatform].available
              ? 'This platform is ready to use immediately.'
              : 'This platform is the most popular and user-friendly option.'
            }
          </p>
        </div>
      )}

      {/* Platform Selection */}
      <div className="space-y-3">
        {platformsArray.map(([platformId, platform]) => (
          <div
            key={platformId}
            className={`
              border-2 rounded-lg p-4 cursor-pointer transition-all duration-200
              hover:border-blue-300 hover:bg-blue-50
              ${selectedPlatform === platformId
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 bg-white'
              }
              ${!platform.available ? 'opacity-75' : ''}
            `}
            onClick={() => handlePlatformSelect(platformId)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="font-semibold text-gray-900">{platform.name}</h3>
                  {getPlatformStatusBadge(platform)}
                  {platformId === recommendedPlatform && (
                    <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded-full">
                      Recommended
                    </span>
                  )}
                </div>

                <p className="text-gray-600 text-sm mb-3">{platform.description}</p>

                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <span> ~{platform.estimated_setup_time} min setup</span>
                  {platform.requires_api_key && (
                    <span> API key required</span>
                  )}
                </div>

                {/* Setup Instructions Preview */}
                {platform.setup_instructions && platform.setup_instructions.length > 0 && (
                  <div className="mt-3 text-xs text-gray-600">
                    <div className="font-medium mb-1">Setup steps:</div>
                    <ul className="list-disc list-inside space-y-1">
                      {platform.setup_instructions.slice(0, 2).map((instruction, index) => (
                        <li key={index}>{instruction}</li>
                      ))}
                      {platform.setup_instructions.length > 2 && (
                        <li>...and {platform.setup_instructions.length - 2} more steps</li>
                      )}
                    </ul>
                  </div>
                )}
              </div>

              <div className="ml-4">
                <div className={`
                  w-5 h-5 rounded-full border-2 transition-colors
                  ${selectedPlatform === platformId
                    ? 'border-blue-500 bg-blue-500'
                    : 'border-gray-300'
                  }
                `}>
                  {selectedPlatform === platformId && (
                    <div className="w-full h-full rounded-full bg-white scale-50" />
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* API Key Input */}
      {showApiKeyInput && selectedPlatform && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="font-medium text-yellow-900 mb-2">
             API Key Required for {availablePlatforms[selectedPlatform].name}
          </h4>
          <p className="text-yellow-800 text-sm mb-3">
            Enter your API key to connect to {availablePlatforms[selectedPlatform].name}.
            This will be stored securely on your local system.
          </p>
          <input
            type="password"
            placeholder="Enter your API key..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-xs text-yellow-700 mt-2">
            Don't have an API key? Visit the {availablePlatforms[selectedPlatform].name} dashboard to get one.
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex space-x-3">
        <Button
          onClick={handleConnect}
          disabled={!selectedPlatform || isLoading || (showApiKeyInput && !apiKey.trim())}
          className="flex-1 py-3 text-lg font-medium"
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2" />
              Connecting...
            </div>
          ) : (
            `Connect ${selectedPlatform ? availablePlatforms[selectedPlatform].name : 'Platform'}`
          )}
        </Button>

        <Button
          onClick={() => onComplete({ skip_platform: true })}
          variant="outline"
          className="px-6"
        >
          Skip for Now
        </Button>
      </div>

      {/* Help Text */}
      <div className="text-center text-sm text-gray-500">
        <p>
           Your API keys are encrypted and stored locally. They never leave your system.
        </p>
        <p className="mt-1">
          You can add more platforms later from the dashboard.
        </p>
      </div>
    </div>
  );
}
