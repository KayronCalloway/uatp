'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useOnboarding } from '@/contexts/onboarding-context';
import { OnboardingStage, UserType } from '@/types/onboarding';
import { OnboardingProgress } from './onboarding-progress';
import { WelcomeStep } from './steps/welcome-step';
import { EnvironmentDetectionStep } from './steps/environment-detection-step';
import { PlatformSelectionStep } from './steps/platform-selection-step';
import { FirstCapsuleStep } from './steps/first-capsule-step';
import { SuccessStep } from './steps/success-step';
import { ApiKeySetup } from './api-key-setup';
import { SystemHealthIndicator } from './system-health-indicator';
import { SupportButton } from './support-button';
import { Card } from '@/components/ui/card';

const STEP_ORDER = [
  OnboardingStage.WELCOME,
  OnboardingStage.ENVIRONMENT_DETECTION,
  OnboardingStage.AI_INTEGRATION,
  OnboardingStage.FIRST_CAPSULE,
  OnboardingStage.SUCCESS_MILESTONE,
];

export function OnboardingWizard() {
  const router = useRouter();
  const { state, actions } = useOnboarding();
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  // Update current step based on progress
  useEffect(() => {
    if (state.progress) {
      console.log('Onboarding progress updated:', state.progress);
      const stageIndex = STEP_ORDER.indexOf(state.progress.current_stage);
      console.log('Current stage:', state.progress.current_stage, 'Stage index:', stageIndex);
      if (stageIndex !== -1) {
        console.log('Setting current step index to:', stageIndex);
        setCurrentStepIndex(stageIndex);
      }

      // Redirect to complete page if onboarding is done
      if (state.progress.current_stage === OnboardingStage.COMPLETE) {
        router.push('/onboarding/complete');
      }
    }
  }, [state.progress, router]);

  const handleStepComplete = async (stepData?: Record<string, any>) => {
    if (currentStepIndex === 0) {
      // Welcome step - start onboarding
      return; // This is handled by the welcome step itself
    } else {
      // Continue to next step
      await actions.continueOnboarding(stepData);
    }
  };

  const getCurrentStepComponent = () => {
    const currentStage = STEP_ORDER[currentStepIndex];

    switch (currentStage) {
      case OnboardingStage.WELCOME:
        return (
          <WelcomeStep
            onComplete={handleStepComplete}
            isLoading={state.isLoading}
            error={state.error}
          />
        );

      case OnboardingStage.ENVIRONMENT_DETECTION:
        return (
          <EnvironmentDetectionStep
            onComplete={handleStepComplete}
            progress={state.progress}
          />
        );

      case OnboardingStage.AI_INTEGRATION:
        return (
          <PlatformSelectionStep
            onComplete={handleStepComplete}
            availablePlatforms={state.availablePlatforms}
            isLoading={state.isLoading}
            error={state.error}
          />
        );

      case OnboardingStage.FIRST_CAPSULE:
        return (
          <FirstCapsuleStep
            onComplete={handleStepComplete}
            progress={state.progress}
            isLoading={state.isLoading}
          />
        );

      case OnboardingStage.SUCCESS_MILESTONE:
        return (
          <SuccessStep
            progress={state.progress}
            onContinue={() => router.push('/onboarding/complete')}
          />
        );

      default:
        return (
          <div className="text-center py-8">
            <p className="text-gray-600">Loading...</p>
          </div>
        );
    }
  };

  const getProgressPercentage = () => {
    return ((currentStepIndex + 1) / STEP_ORDER.length) * 100;
  };

  const getStepTitle = () => {
    const titles = {
      [OnboardingStage.WELCOME]: 'Welcome to UATP',
      [OnboardingStage.ENVIRONMENT_DETECTION]: 'Detecting Environment',
      [OnboardingStage.AI_INTEGRATION]: 'Connect AI Platform',
      [OnboardingStage.FIRST_CAPSULE]: 'Create First Capsule',
      [OnboardingStage.SUCCESS_MILESTONE]: 'Success!',
    };

    return titles[STEP_ORDER[currentStepIndex]] || 'Setting Up...';
  };

  const getStepDescription = () => {
    const descriptions = {
      [OnboardingStage.WELCOME]: 'Let\'s get you started with AI trust and attribution',
      [OnboardingStage.ENVIRONMENT_DETECTION]: 'We\'re optimizing the setup for your environment',
      [OnboardingStage.AI_INTEGRATION]: 'Connect to your preferred AI platform',
      [OnboardingStage.FIRST_CAPSULE]: 'Creating your first attributed capsule',
      [OnboardingStage.SUCCESS_MILESTONE]: 'Your UATP system is ready to use!',
    };

    return descriptions[STEP_ORDER[currentStepIndex]] || 'Processing...';
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                 UATP Setup
              </h1>
              <p className="text-gray-600 mt-1">
                Universal AI Trust Protocol
              </p>
            </div>
            <SystemHealthIndicator health={state.systemHealth} />
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <OnboardingProgress
            currentStep={currentStepIndex + 1}
            totalSteps={STEP_ORDER.length}
            percentage={getProgressPercentage()}
            title={getStepTitle()}
            description={getStepDescription()}
            estimatedTimeRemaining={state.progress?.estimated_completion_time}
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-2xl">
          <Card className="p-8 shadow-lg">
            {state.error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center">
                  <div className="text-red-500 mr-3">[WARN]</div>
                  <div>
                    <h3 className="text-red-800 font-medium">Setup Error</h3>
                    <p className="text-red-700 text-sm mt-1">{state.error}</p>
                  </div>
                </div>
              </div>
            )}

            {getCurrentStepComponent()}
          </Card>
        </div>
      </div>

      {/* Support Button */}
      <SupportButton />
    </div>
  );
}
