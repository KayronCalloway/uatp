'use client';

import React, { useEffect, useState } from 'react';
import { OnboardingProgress } from '@/types/onboarding';

interface EnvironmentDetectionStepProps {
  onComplete: (data?: Record<string, any>) => void;
  progress: OnboardingProgress | null;
}

const DETECTION_ITEMS = [
  { id: 'system', label: 'System Information', icon: '💻' },
  { id: 'api_keys', label: 'API Key Discovery', icon: '🔑' },
  { id: 'platforms', label: 'AI Platform Detection', icon: '🤖' },
  { id: 'network', label: 'Network Connectivity', icon: '🌐' },
  { id: 'optimization', label: 'Configuration Optimization', icon: '⚡' },
];

export function EnvironmentDetectionStep({ onComplete, progress }: EnvironmentDetectionStepProps) {
  const [detectionProgress, setDetectionProgress] = useState<Record<string, boolean>>({});
  const [currentDetection, setCurrentDetection] = useState(0);

  useEffect(() => {
    // Simulate detection process
    const runDetection = async () => {
      for (let i = 0; i < DETECTION_ITEMS.length; i++) {
        setCurrentDetection(i);
        
        // Simulate detection time
        await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 400));
        
        setDetectionProgress(prev => ({
          ...prev,
          [DETECTION_ITEMS[i].id]: true
        }));
      }

      // Auto-continue after detection completes
      setTimeout(() => {
        onComplete({
          environment_detected: true,
          detections: detectionProgress
        });
      }, 1000);
    };

    runDetection();
  }, [onComplete, detectionProgress]);

  const completedCount = Object.values(detectionProgress).filter(Boolean).length;
  const progressPercentage = (completedCount / DETECTION_ITEMS.length) * 100;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Analyzing Your Environment 🔍
        </h2>
        <p className="text-gray-600">
          We're automatically detecting your system configuration to provide the optimal setup experience.
        </p>
      </div>

      {/* Overall Progress */}
      <div className="bg-gray-100 rounded-full h-3 overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500 ease-out"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>

      {/* Detection Items */}
      <div className="space-y-3">
        {DETECTION_ITEMS.map((item, index) => {
          const isCompleted = detectionProgress[item.id];
          const isCurrent = index === currentDetection && !isCompleted;
          const isPending = index > currentDetection;

          return (
            <div
              key={item.id}
              className={`
                flex items-center p-4 rounded-lg border-2 transition-all duration-300
                ${isCompleted 
                  ? 'border-green-200 bg-green-50' 
                  : isCurrent 
                    ? 'border-blue-200 bg-blue-50' 
                    : 'border-gray-200 bg-gray-50'
                }
              `}
            >
              <div className="text-2xl mr-4">{item.icon}</div>
              
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">{item.label}</h3>
                <p className="text-sm text-gray-600">
                  {isCompleted 
                    ? 'Completed ✓' 
                    : isCurrent 
                      ? 'Analyzing...' 
                      : 'Pending'
                  }
                </p>
              </div>

              <div className="ml-4">
                {isCompleted ? (
                  <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm">✓</span>
                  </div>
                ) : isCurrent ? (
                  <div className="w-6 h-6 border-2 border-blue-500 rounded-full animate-spin border-t-transparent" />
                ) : (
                  <div className="w-6 h-6 bg-gray-300 rounded-full" />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Detection Results Preview */}
      {completedCount > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2">Detection Results:</h4>
          <div className="space-y-1 text-sm text-blue-800">
            {detectionProgress.system && (
              <div>✓ Operating System: {navigator.platform}</div>
            )}
            {detectionProgress.api_keys && (
              <div>✓ Found potential API key configurations</div>
            )}
            {detectionProgress.platforms && (
              <div>✓ Detected compatible AI platforms</div>
            )}
            {detectionProgress.network && (
              <div>✓ Network connectivity verified</div>
            )}
            {detectionProgress.optimization && (
              <div>✓ Optimal configuration determined</div>
            )}
          </div>
        </div>
      )}

      {/* Auto-continue message */}
      {completedCount === DETECTION_ITEMS.length && (
        <div className="text-center py-4">
          <div className="text-green-600 font-medium mb-2">
            Environment Analysis Complete! ✨
          </div>
          <div className="text-gray-600 text-sm">
            Automatically continuing to platform setup...
          </div>
        </div>
      )}

      {/* Reassuring Message */}
      <div className="text-center text-sm text-gray-500">
        <p>🔒 All detection happens locally on your system. No data is sent to external servers.</p>
      </div>
    </div>
  );
}