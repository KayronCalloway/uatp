'use client';

import React from 'react';

interface OnboardingProgressProps {
  currentStep: number;
  totalSteps: number;
  percentage: number;
  title: string;
  description: string;
  estimatedTimeRemaining?: string;
}

export function OnboardingProgress({
  currentStep,
  totalSteps,
  percentage,
  title,
  description,
  estimatedTimeRemaining,
}: OnboardingProgressProps) {
  const getEstimatedTimeText = () => {
    if (!estimatedTimeRemaining) return null;
    
    const estimatedTime = new Date(estimatedTimeRemaining);
    const now = new Date();
    const diffMs = estimatedTime.getTime() - now.getTime();
    const diffMinutes = Math.max(0, Math.ceil(diffMs / (1000 * 60)));
    
    if (diffMinutes === 0) return 'Almost done!';
    if (diffMinutes === 1) return '~1 minute remaining';
    return `~${diffMinutes} minutes remaining`;
  };

  return (
    <div className="space-y-4">
      {/* Step Counter and Title */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <p className="text-gray-600 text-sm mt-1">{description}</p>
        </div>
        <div className="text-right">
          <div className="text-sm font-medium text-gray-900">
            Step {currentStep} of {totalSteps}
          </div>
          {getEstimatedTimeText() && (
            <div className="text-xs text-gray-500 mt-1">
              {getEstimatedTimeText()}
            </div>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="relative">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>
        
        {/* Step Indicators */}
        <div className="flex justify-between mt-2">
          {Array.from({ length: totalSteps }, (_, index) => {
            const stepNumber = index + 1;
            const isCompleted = stepNumber < currentStep;
            const isCurrent = stepNumber === currentStep;
            
            return (
              <div
                key={stepNumber}
                className={`
                  w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium
                  transition-colors duration-200
                  ${isCompleted 
                    ? 'bg-blue-500 text-white' 
                    : isCurrent 
                      ? 'bg-blue-100 text-blue-600 border-2 border-blue-500'
                      : 'bg-gray-200 text-gray-500'
                  }
                `}
              >
                {isCompleted ? '✓' : stepNumber}
              </div>
            );
          })}
        </div>
      </div>

      {/* Step Labels */}
      <div className="flex justify-between text-xs text-gray-500">
        <span>Welcome</span>
        <span>Environment</span>
        <span>Platform</span>
        <span>First Capsule</span>
        <span>Complete</span>
      </div>
    </div>
  );
}