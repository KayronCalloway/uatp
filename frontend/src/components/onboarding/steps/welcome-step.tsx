'use client';

import React, { useState } from 'react';
import { UserType, UserPreferences } from '@/types/onboarding';
import { useOnboarding } from '@/contexts/onboarding-context';
import { Button } from '@/components/ui/button';
import { logger } from '@/lib/logger';

interface WelcomeStepProps {
  onComplete: (data?: Record<string, any>) => void;
  isLoading: boolean;
  error: string | null;
}

const USER_TYPE_OPTIONS = [
  {
    type: UserType.CASUAL_USER,
    icon: '',
    title: 'Just Getting Started',
    description: 'I want to try UATP with minimal setup (5 min)',
    benefits: ['Quick setup', 'Smart defaults', 'Guided experience'],
  },
  {
    type: UserType.DEVELOPER,
    icon: '‍',
    title: 'Developer',
    description: 'I want to integrate UATP into my applications (10 min)',
    benefits: ['API access', 'Development tools', 'Code examples'],
  },
  {
    type: UserType.BUSINESS_USER,
    icon: '',
    title: 'Business User',
    description: 'I need AI attribution for business use (7 min)',
    benefits: ['Business features', 'Team collaboration', 'Reporting'],
  },
  {
    type: UserType.RESEARCHER,
    icon: '',
    title: 'Researcher',
    description: 'I need transparent AI for research (10 min)',
    benefits: ['Research tools', 'Data transparency', 'Export features'],
  },
  {
    type: UserType.ENTERPRISE,
    icon: '',
    title: 'Enterprise',
    description: 'I need enterprise-grade AI governance (20 min)',
    benefits: ['Enterprise security', 'Compliance tools', 'Advanced governance'],
  },
];

export function WelcomeStep({ onComplete, isLoading, error }: WelcomeStepProps) {
  const { actions } = useOnboarding();
  const [selectedUserType, setSelectedUserType] = useState<UserType | null>(null);
  const [additionalPreferences, setAdditionalPreferences] = useState<Partial<UserPreferences>>({});

  const handleUserTypeSelect = (userType: UserType) => {
    setSelectedUserType(userType);
  };

  const handleStartOnboarding = async () => {
    if (!selectedUserType) return;

    const preferences: UserPreferences = {
      user_type: selectedUserType,
      ...additionalPreferences,
    };

    logger.debug('Starting onboarding with preferences:', preferences);

    try {
      await actions.startOnboarding(preferences);
      logger.debug('Onboarding started successfully');
    } catch (error) {
      logger.error('Failed to start onboarding:', error);
    }
  };

  const getAdditionalQuestions = () => {
    if (!selectedUserType) return null;

    switch (selectedUserType) {
      case UserType.DEVELOPER:
        return (
          <div className="space-y-4 mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-gray-900">Quick questions to optimize your setup:</h4>
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="mr-2"
                  onChange={(e) => setAdditionalPreferences(prev => ({ ...prev, has_git: e.target.checked }))}
                />
                <span className="text-sm">I use Git for version control</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="mr-2"
                  onChange={(e) => setAdditionalPreferences(prev => ({ ...prev, has_ide: e.target.checked }))}
                />
                <span className="text-sm">I use an IDE or code editor</span>
              </label>
              <div>
                <label className="text-sm text-gray-700">Python experience:</label>
                <select
                  className="ml-2 text-sm border rounded px-2 py-1"
                  onChange={(e) => setAdditionalPreferences(prev => ({
                    ...prev,
                    python_experience: e.target.value as 'beginner' | 'intermediate' | 'advanced'
                  }))}
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </select>
              </div>
            </div>
          </div>
        );

      case UserType.ENTERPRISE:
        return (
          <div className="space-y-4 mt-6 p-4 bg-purple-50 rounded-lg">
            <h4 className="font-medium text-gray-900">Enterprise requirements:</h4>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-700">Organization size:</label>
                <select
                  className="ml-2 text-sm border rounded px-2 py-1"
                  onChange={(e) => setAdditionalPreferences(prev => ({
                    ...prev,
                    organization_size: parseInt(e.target.value)
                  }))}
                >
                  <option value="50">50-100 employees</option>
                  <option value="200">100-500 employees</option>
                  <option value="1000">500+ employees</option>
                </select>
              </div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="mr-2"
                  onChange={(e) => setAdditionalPreferences(prev => ({ ...prev, compliance_requirements: e.target.checked }))}
                />
                <span className="text-sm">We have compliance requirements (GDPR, SOC2, etc.)</span>
              </label>
              <div>
                <label className="text-sm text-gray-700">Scalability needs:</label>
                <select
                  className="ml-2 text-sm border rounded px-2 py-1"
                  onChange={(e) => setAdditionalPreferences(prev => ({
                    ...prev,
                    scalability_needs: e.target.value as 'low' | 'medium' | 'high'
                  }))}
                >
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>
          </div>
        );

      case UserType.RESEARCHER:
        return (
          <div className="space-y-4 mt-6 p-4 bg-green-50 rounded-lg">
            <h4 className="font-medium text-gray-900">Research focus:</h4>
            <div>
              <label className="text-sm text-gray-700">Primary use case:</label>
              <select
                className="ml-2 text-sm border rounded px-2 py-1"
                onChange={(e) => setAdditionalPreferences(prev => ({ ...prev, use_case: e.target.value }))}
              >
                <option value="research">General research</option>
                <option value="academic">Academic research</option>
                <option value="ai_research">AI/ML research</option>
              </select>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Welcome to UATP!
        </h2>
        <p className="text-gray-600">
          Choose your experience level to get personalized setup that works best for you.
        </p>
      </div>

      {/* User Type Selection */}
      <div className="space-y-3">
        {USER_TYPE_OPTIONS.map((option) => (
          <div
            key={option.type}
            className={`
              border-2 rounded-lg p-4 cursor-pointer transition-all duration-200
              hover:border-blue-300 hover:bg-blue-50
              ${selectedUserType === option.type
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 bg-white'
              }
            `}
            onClick={() => handleUserTypeSelect(option.type)}
          >
            <div className="flex items-start space-x-4">
              <div className="text-3xl">{option.icon}</div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-gray-900">{option.title}</h3>
                  <div className={`
                    w-5 h-5 rounded-full border-2 transition-colors
                    ${selectedUserType === option.type
                      ? 'border-blue-500 bg-blue-500'
                      : 'border-gray-300'
                    }
                  `}>
                    {selectedUserType === option.type && (
                      <div className="w-full h-full rounded-full bg-white scale-50" />
                    )}
                  </div>
                </div>
                <p className="text-gray-600 text-sm mt-1">{option.description}</p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {option.benefits.map((benefit) => (
                    <span
                      key={benefit}
                      className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full"
                    >
                      {benefit}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Additional Questions */}
      {getAdditionalQuestions()}

      {/* Action Button */}
      <div className="pt-4">
        <Button
          onClick={handleStartOnboarding}
          disabled={!selectedUserType || isLoading}
          className="w-full py-3 text-lg font-medium"
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2" />
              Starting Setup...
            </div>
          ) : (
            `Get Started - ${selectedUserType ? USER_TYPE_OPTIONS.find(o => o.type === selectedUserType)?.title : 'Choose Option'}`
          )}
        </Button>
      </div>

      {/* Confidence Building Elements */}
      <div className="text-center text-sm text-gray-500 space-y-2">
        <div className="flex items-center justify-center space-x-4">
          <span className="flex items-center">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-1" />
            Secure Setup
          </span>
          <span className="flex items-center">
            <span className="w-2 h-2 bg-blue-500 rounded-full mr-1" />
            No Account Required
          </span>
          <span className="flex items-center">
            <span className="w-2 h-2 bg-purple-500 rounded-full mr-1" />
            Open Source
          </span>
        </div>
        <p>Your data stays on your system. Setup can be completed offline.</p>
      </div>
    </div>
  );
}
