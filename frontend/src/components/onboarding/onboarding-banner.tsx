'use client';

import React from 'react';
import { useOnboardingFlow } from '@/hooks/use-onboarding-flow';
import { useIsCreator } from '@/contexts/creator-context';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { CreatorDashboard } from '@/components/creator/creator-dashboard';

export function OnboardingBanner() {
  const { 
    shouldShowOnboarding, 
    startOnboarding, 
    dismissOnboarding,
    onboardingProgress 
  } = useOnboardingFlow();
  
  const isCreator = useIsCreator();

  // Show Creator Dashboard for creators
  if (isCreator) {
    return <CreatorDashboard />;
  }

  if (!shouldShowOnboarding) {
    return null;
  }

  const isReturningUser = onboardingProgress && onboardingProgress.completed_stages.length > 0;

  return (
    <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 mb-6">
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-2xl">🚀</span>
              <h3 className="text-lg font-semibold text-blue-900">
                {isReturningUser ? 'Complete Your UATP Setup' : 'Welcome to UATP!'}
              </h3>
            </div>
            
            <p className="text-blue-800 mb-4">
              {isReturningUser 
                ? `You're ${onboardingProgress.completed_stages.length}/5 steps through setup. Let's finish configuring your AI trust and attribution system.`
                : 'Get started with AI trust and attribution in just a few minutes. We\'ll guide you through the setup process.'
              }
            </p>

            {isReturningUser && (
              <div className="mb-4">
                <div className="flex items-center space-x-2 text-sm text-blue-700">
                  <span>Progress:</span>
                  <div className="bg-blue-200 rounded-full h-2 flex-1 max-w-xs overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 rounded-full transition-all duration-300"
                      style={{ 
                        width: `${(onboardingProgress.completed_stages.length / 5) * 100}%` 
                      }}
                    />
                  </div>
                  <span>{onboardingProgress.completed_stages.length}/5</span>
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 mb-4 text-sm">
              <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                ⚡ 5-minute setup
              </span>
              <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full">
                🔒 Secure & private
              </span>
              <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full">
                🎯 Personalized for you
              </span>
            </div>

            <div className="flex space-x-3">
              <Button
                onClick={startOnboarding}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {isReturningUser ? 'Continue Setup' : 'Get Started'}
              </Button>
              
              <Button
                onClick={dismissOnboarding}
                variant="outline"
                className="border-blue-300 text-blue-700 hover:bg-blue-50"
              >
                Maybe Later
              </Button>
            </div>
          </div>

          {/* Close Button */}
          <button
            onClick={dismissOnboarding}
            className="text-blue-400 hover:text-blue-600 ml-4"
            title="Dismiss"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </Card>
  );
}