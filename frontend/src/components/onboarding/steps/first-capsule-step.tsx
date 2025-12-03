'use client';

import React, { useEffect, useState } from 'react';
import { OnboardingProgress } from '@/types/onboarding';

interface FirstCapsuleStepProps {
  onComplete: (data?: Record<string, any>) => void;
  progress: OnboardingProgress | null;
  isLoading: boolean;
}

const CAPSULE_CREATION_STEPS = [
  { id: 'initialize', label: 'Initializing Capsule Engine', icon: '⚡' },
  { id: 'connect', label: 'Connecting to AI Platform', icon: '🔗' },
  { id: 'generate', label: 'Generating Welcome Content', icon: '✨' },
  { id: 'attribute', label: 'Adding Attribution Metadata', icon: '🏷️' },
  { id: 'verify', label: 'Verifying Capsule Integrity', icon: '✅' },
  { id: 'finalize', label: 'Finalizing Your First Capsule', icon: '🎉' },
];

export function FirstCapsuleStep({ onComplete, progress, isLoading }: FirstCapsuleStepProps) {
  const [creationProgress, setCreationProgress] = useState<Record<string, boolean>>({});
  const [currentStep, setCurrentStep] = useState(0);
  const [capsulePreview, setCapsulePreview] = useState<any>(null);

  useEffect(() => {
    // Simulate capsule creation process
    const createCapsule = async () => {
      for (let i = 0; i < CAPSULE_CREATION_STEPS.length; i++) {
        setCurrentStep(i);
        
        // Simulate different step durations
        const stepDuration = i === 2 ? 2000 : 1000 + Math.random() * 1000; // Generation step takes longer
        await new Promise(resolve => setTimeout(resolve, stepDuration));
        
        setCreationProgress(prev => ({
          ...prev,
          [CAPSULE_CREATION_STEPS[i].id]: true
        }));

        // Show preview after generation step
        if (i === 2) {
          setCapsulePreview({
            id: 'welcome-capsule-001',
            type: 'chat',
            content: 'Welcome to UATP! This is your first capsule with full attribution tracking.',
            agent_id: progress?.personalization_data?.preferred_platform || 'openai-gpt4',
            timestamp: new Date().toISOString(),
            attribution: {
              human_prompt: 'Create a welcome message for UATP onboarding',
              model_response: 'Welcome to UATP! This is your first capsule with full attribution tracking.',
              trust_score: 0.95,
              verified: true
            }
          });
        }
      }

      // Auto-continue after creation completes
      setTimeout(() => {
        onComplete({
          first_capsule_created: true,
          capsule_id: 'welcome-capsule-001'
        });
      }, 1500);
    };

    createCapsule();
  }, [onComplete, progress]);

  const completedCount = Object.values(creationProgress).filter(Boolean).length;
  const progressPercentage = (completedCount / CAPSULE_CREATION_STEPS.length) * 100;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Creating Your First Capsule 🎯
        </h2>
        <p className="text-gray-600">
          We're creating your first UATP capsule with full attribution tracking. 
          This demonstrates the core functionality of the system.
        </p>
      </div>

      {/* Overall Progress */}
      <div className="bg-gray-100 rounded-full h-3 overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all duration-500 ease-out"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>

      {/* Creation Steps */}
      <div className="space-y-3">
        {CAPSULE_CREATION_STEPS.map((step, index) => {
          const isCompleted = creationProgress[step.id];
          const isCurrent = index === currentStep && !isCompleted;
          const isPending = index > currentStep;

          return (
            <div
              key={step.id}
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
              <div className="text-2xl mr-4">{step.icon}</div>
              
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">{step.label}</h3>
                <p className="text-sm text-gray-600">
                  {isCompleted 
                    ? 'Completed ✓' 
                    : isCurrent 
                      ? 'In progress...' 
                      : 'Waiting'
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

      {/* Capsule Preview */}
      {capsulePreview && (
        <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-6">
          <h4 className="font-medium text-purple-900 mb-3 flex items-center">
            <span className="mr-2">✨</span>
            Your First Capsule Preview
          </h4>
          
          <div className="bg-white rounded-lg p-4 border border-purple-100">
            <div className="flex items-start space-x-3">
              <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-purple-600 font-medium">AI</span>
              </div>
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="font-medium text-gray-900">UATP Assistant</span>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                    Verified ✓
                  </span>
                </div>
                <p className="text-gray-700 mb-3">{capsulePreview.content}</p>
                
                <div className="text-xs text-gray-500 space-y-1">
                  <div>📊 Trust Score: {(capsulePreview.attribution.trust_score * 100).toFixed(1)}%</div>
                  <div>🕒 Created: {new Date(capsulePreview.timestamp).toLocaleTimeString()}</div>
                  <div>🤖 Model: {capsulePreview.agent_id}</div>
                  <div>🔗 Capsule ID: {capsulePreview.id}</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="mt-4 text-sm text-purple-800">
            <p>🎉 This capsule demonstrates full attribution tracking, including:</p>
            <ul className="list-disc list-inside mt-2 space-y-1 text-xs">
              <li>Original human prompt and AI response</li>
              <li>Trust score and verification status</li>
              <li>Timestamp and model attribution</li>
              <li>Cryptographic integrity verification</li>
            </ul>
          </div>
        </div>
      )}

      {/* Completion Message */}
      {completedCount === CAPSULE_CREATION_STEPS.length && (
        <div className="text-center py-4">
          <div className="text-4xl mb-2">🎉</div>
          <div className="text-green-600 font-medium mb-2">
            Your First Capsule is Ready!
          </div>
          <div className="text-gray-600 text-sm">
            Proceeding to success milestone...
          </div>
        </div>
      )}

      {/* Educational Note */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h5 className="font-medium text-blue-900 mb-2">💡 What's happening here?</h5>
        <div className="text-sm text-blue-800 space-y-2">
          <p>
            UATP creates "capsules" that contain AI interactions with full attribution metadata. 
            Each capsule includes:
          </p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>The original human prompt</li>
            <li>The AI's complete response</li>
            <li>Trust and verification scores</li>
            <li>Temporal and model attribution</li>
            <li>Cryptographic integrity proofs</li>
          </ul>
          <p className="pt-2">
            This creates an auditable trail of all AI interactions for transparency and trust.
          </p>
        </div>
      </div>
    </div>
  );
}