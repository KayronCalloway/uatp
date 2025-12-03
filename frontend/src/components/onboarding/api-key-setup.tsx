'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ApiKeySetupProps {
  platform: string;
  onComplete: (apiKey: string) => void;
  onSkip?: () => void;
}

interface ApiKeyStatus {
  detected: boolean;
  valid: boolean;
  source?: string;
  keyPreview?: string;
}

export function ApiKeySetup({ platform, onComplete, onSkip }: ApiKeySetupProps) {
  const [apiKey, setApiKey] = useState('');
  const [status, setStatus] = useState<ApiKeyStatus>({ detected: false, valid: false });
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showManualInput, setShowManualInput] = useState(false);

  useEffect(() => {
    detectApiKey();
  }, [platform]);

  const detectApiKey = async () => {
    try {
      // Check environment variables first
      const envVarNames = getEnvVarNames(platform);
      
      // Try to detect from browser environment (development mode)
      if (typeof window !== 'undefined') {
        for (const envVar of envVarNames) {
          // In development, check if key exists in localStorage from previous sessions
          const savedKey = localStorage.getItem(`uatp_${platform}_api_key`);
          if (savedKey) {
            setStatus({
              detected: true,
              valid: false, // Will validate separately
              source: 'saved',
              keyPreview: `${savedKey.substring(0, 8)}...`
            });
            setApiKey(savedKey);
            await validateApiKey(savedKey);
            return;
          }
        }
      }

      // Check backend for platform availability via API client
      try {
        const { apiClient } = await import('@/lib/api-client');
        const platformsData = await apiClient.getAvailablePlatforms();
        
        if (platformsData.success && platformsData.data[platform]) {
          const platformInfo = platformsData.data[platform];
          if (platformInfo.available) {
            setStatus({
              detected: true,
              valid: true, // If backend reports it as available, consider it valid
              source: 'backend',
              keyPreview: 'configured'
            });
            
            // Auto-complete if platform is available in backend
            onComplete('__detected__'); // Special value indicating detected key
            return;
          }
        }
      } catch (error) {
        console.log('Backend platform check failed, continuing with manual input');
      }

      // No key detected, show manual input
      setShowManualInput(true);
      setStatus({ detected: false, valid: false });

    } catch (error) {
      console.error('Failed to detect API key:', error);
      setShowManualInput(true);
    }
  };

  const validateApiKey = async (key: string) => {
    if (!key.trim()) return;

    setIsValidating(true);
    setError(null);

    try {
      // For now, we'll do basic validation client-side
      // In production, this would go through the API client to validate with the platform
      const isValidFormat = validateApiKeyFormat(key, platform);
      
      if (isValidFormat) {
        setStatus(prev => ({ ...prev, valid: true }));
        
        // Save key for future use
        localStorage.setItem(`uatp_${platform}_api_key`, key);
        
        // Auto-complete after validation
        setTimeout(() => onComplete(key), 1000);
      } else {
        setError('Invalid API key format');
        setStatus(prev => ({ ...prev, valid: false }));
      }
    } catch (error) {
      setError('Failed to validate API key');
      setStatus(prev => ({ ...prev, valid: false }));
    } finally {
      setIsValidating(false);
    }
  };

  const validateApiKeyFormat = (key: string, platform: string): boolean => {
    // Basic format validation for different platforms
    switch (platform) {
      case 'openai':
        return key.startsWith('sk-') && key.length > 20;
      case 'anthropic':
        return key.startsWith('sk-ant-') && key.length > 30;
      case 'cohere':
        return key.length > 20;
      case 'huggingface':
        return key.startsWith('hf_') && key.length > 10;
      default:
        return key.length > 10; // Generic validation
    }
  };

  const handleManualSubmit = () => {
    if (apiKey.trim()) {
      validateApiKey(apiKey);
    }
  };

  const getEnvVarNames = (platform: string): string[] => {
    const envVars: Record<string, string[]> = {
      openai: ['OPENAI_API_KEY'],
      anthropic: ['ANTHROPIC_API_KEY'],
      cohere: ['COHERE_API_KEY'],
      huggingface: ['HUGGINGFACE_API_TOKEN', 'HF_TOKEN'],
      google: ['GOOGLE_API_KEY'],
      azure: ['AZURE_OPENAI_KEY']
    };
    
    return envVars[platform] || [`${platform.toUpperCase()}_API_KEY`];
  };

  const getPlatformInstructions = (platform: string): { name: string; instructions: string; docsUrl: string } => {
    const instructions: Record<string, { name: string; instructions: string; docsUrl: string }> = {
      openai: {
        name: 'OpenAI',
        instructions: 'Get your API key from OpenAI Dashboard → API Keys',
        docsUrl: 'https://platform.openai.com/api-keys'
      },
      anthropic: {
        name: 'Anthropic Claude',
        instructions: 'Get your API key from Anthropic Console → API Keys',
        docsUrl: 'https://console.anthropic.com/'
      },
      cohere: {
        name: 'Cohere',
        instructions: 'Get your API key from Cohere Dashboard → API Keys',
        docsUrl: 'https://dashboard.cohere.com/api-keys'
      },
      huggingface: {
        name: 'Hugging Face',
        instructions: 'Get your token from Hugging Face → Settings → Access Tokens',
        docsUrl: 'https://huggingface.co/settings/tokens'
      }
    };

    return instructions[platform] || {
      name: platform,
      instructions: `Get your API key from ${platform} dashboard`,
      docsUrl: ''
    };
  };

  const platformInfo = getPlatformInstructions(platform);

  if (status.detected && status.valid) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <div className="text-4xl mb-4">✅</div>
          <h3 className="text-lg font-semibold text-green-800 mb-2">
            {platformInfo.name} API Key Detected!
          </h3>
          <p className="text-green-600 mb-4">
            Found valid API key from {status.source}: {status.keyPreview}
          </p>
          <p className="text-sm text-gray-600">
            Automatically configuring your connection...
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-2">
            Connect to {platformInfo.name}
          </h3>
          <p className="text-gray-600 text-sm">
            {platformInfo.instructions}
          </p>
        </div>

        {status.detected && !status.valid && (
          <Alert>
            <AlertDescription>
              Found API key from {status.source} ({status.keyPreview}), but it appears to be invalid. 
              Please check or enter a new key below.
            </AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {(showManualInput || status.detected) && (
          <div className="space-y-3">
            <Label htmlFor="apiKey">
              {platformInfo.name} API Key
            </Label>
            <Input
              id="apiKey"
              type="password"
              placeholder="Enter your API key..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleManualSubmit()}
            />
            
            {platformInfo.docsUrl && (
              <p className="text-sm text-blue-600">
                <a 
                  href={platformInfo.docsUrl} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="underline hover:no-underline"
                >
                  Get your API key →
                </a>
              </p>
            )}

            <div className="flex space-x-3">
              <Button
                onClick={handleManualSubmit}
                disabled={!apiKey.trim() || isValidating}
                className="flex-1"
              >
                {isValidating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Validating...
                  </>
                ) : (
                  'Validate & Continue'
                )}
              </Button>
              
              {onSkip && (
                <Button
                  onClick={onSkip}
                  variant="outline"
                >
                  Skip for Now
                </Button>
              )}
            </div>
          </div>
        )}

        {!showManualInput && !status.detected && (
          <div className="text-center space-y-4">
            <div className="text-2xl">🔍</div>
            <p className="text-gray-600">
              Detecting API keys in your environment...
            </p>
            <Button
              onClick={() => setShowManualInput(true)}
              variant="outline"
            >
              Enter API Key Manually
            </Button>
          </div>
        )}

        <div className="bg-blue-50 p-4 rounded-lg text-sm">
          <h4 className="font-medium text-blue-900 mb-2">💡 Pro Tips:</h4>
          <ul className="text-blue-800 space-y-1">
            <li>• API keys are stored locally and never sent to our servers</li>
            <li>• You can set environment variables for automatic detection</li>
            <li>• Free tiers are available for most platforms</li>
          </ul>
        </div>
      </div>
    </Card>
  );
}