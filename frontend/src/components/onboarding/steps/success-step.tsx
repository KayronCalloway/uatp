'use client';

import React from 'react';
import { OnboardingProgress } from '@/types/onboarding';
import { Button } from '@/components/ui/button';

interface SuccessStepProps {
  progress: OnboardingProgress | null;
  onContinue: () => void;
}

export function SuccessStep({ progress, onContinue }: SuccessStepProps) {
  const getCompletionTime = () => {
    if (!progress?.start_time) return 'a few minutes';
    
    const startTime = new Date(progress.start_time);
    const now = new Date();
    const diffMs = now.getTime() - startTime.getTime();
    const diffMinutes = Math.round(diffMs / (1000 * 60));
    
    if (diffMinutes < 1) return 'less than a minute';
    if (diffMinutes === 1) return '1 minute';
    return `${diffMinutes} minutes`;
  };

  const getPersonalizedMessage = () => {
    const userType = progress?.user_type;
    
    switch (userType) {
      case 'developer':
        return {
          title: 'Development Environment Ready! 👨‍💻',
          message: 'Your UATP development environment is configured with API access, debugging tools, and code examples.',
          nextSteps: [
            'Explore the API documentation',
            'Try the interactive code examples',
            'Set up CI/CD integration',
            'Join the developer community'
          ]
        };
        
      case 'enterprise':
        return {
          title: 'Enterprise System Activated! 🏢',
          message: 'Your enterprise-grade UATP system is ready with security, compliance, and governance features.',
          nextSteps: [
            'Configure team access controls',
            'Review compliance settings',
            'Set up audit logging',
            'Schedule team training'
          ]
        };
        
      case 'researcher':
        return {
          title: 'Research Environment Ready! 🔬',
          message: 'Your UATP research setup is complete with transparency tools and data export capabilities.',
          nextSteps: [
            'Explore attribution analytics',
            'Set up research workflows',
            'Export data for analysis',
            'Connect with research community'
          ]
        };
        
      case 'business_user':
        return {
          title: 'Business System Ready! 💼',
          message: 'Your UATP business environment is configured for team collaboration and reporting.',
          nextSteps: [
            'Invite team members',
            'Set up project workflows',
            'Configure reporting dashboards',
            'Explore business features'
          ]
        };
        
      default:
        return {
          title: 'UATP System Ready! 🚀',
          message: 'Your UATP system is configured and ready for AI trust and attribution tracking.',
          nextSteps: [
            'Create more capsules',
            'Explore the dashboard',
            'Try different AI models',
            'Learn advanced features'
          ]
        };
    }
  };

  const personalizedContent = getPersonalizedMessage();

  return (
    <div className="space-y-6 text-center">
      {/* Success Animation */}
      <div className="relative">
        <div className="text-8xl animate-bounce">🎉</div>
        <div className="absolute inset-0 text-8xl animate-pulse opacity-50">✨</div>
      </div>

      {/* Success Message */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          {personalizedContent.title}
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          {personalizedContent.message}
        </p>
      </div>

      {/* Completion Stats */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
        <h3 className="font-semibold text-green-900 mb-4">What You've Accomplished:</h3>
        <div className="grid md:grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div className="flex items-center justify-center text-green-700">
              <span className="mr-2">✅</span>
              System configured and optimized
            </div>
            <div className="flex items-center justify-center text-green-700">
              <span className="mr-2">✅</span>
              AI platform connected and tested
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-center text-green-700">
              <span className="mr-2">✅</span>
              First capsule created with attribution
            </div>
            <div className="flex items-center justify-center text-green-700">
              <span className="mr-2">✅</span>
              Ready for production use
            </div>
          </div>
        </div>
        
        <div className="mt-4 pt-4 border-t border-green-200">
          <div className="text-green-800 font-medium">
            ⏱️ Setup completed in {getCompletionTime()}!
          </div>
        </div>
      </div>

      {/* Next Steps */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-4">Recommended Next Steps:</h3>
        <div className="grid md:grid-cols-2 gap-3">
          {personalizedContent.nextSteps.map((step, index) => (
            <div key={index} className="flex items-center text-blue-800 text-sm">
              <span className="mr-2 text-blue-500">→</span>
              {step}
            </div>
          ))}
        </div>
      </div>

      {/* System Information */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3">System Information:</h4>
        <div className="grid md:grid-cols-3 gap-4 text-xs text-gray-600">
          <div>
            <div className="font-medium text-gray-700">User Type</div>
            <div className="capitalize">{progress?.user_type?.replace('_', ' ')}</div>
          </div>
          <div>
            <div className="font-medium text-gray-700">Stages Completed</div>
            <div>{progress?.completed_stages?.length || 0}/5</div>
          </div>
          <div>
            <div className="font-medium text-gray-700">Success Metrics</div>
            <div>
              {Object.keys(progress?.success_metrics || {}).length} tracked
            </div>
          </div>
        </div>
      </div>

      {/* Action Button */}
      <div className="pt-4">
        <Button
          onClick={onContinue}
          className="px-8 py-3 text-lg font-medium bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700"
        >
          Continue to Dashboard 🚀
        </Button>
      </div>

      {/* Celebration Elements */}
      <div className="text-sm text-gray-500 space-y-2">
        <div className="flex items-center justify-center space-x-4">
          <span className="flex items-center">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse" />
            System Active
          </span>
          <span className="flex items-center">
            <span className="w-2 h-2 bg-blue-500 rounded-full mr-1 animate-pulse" />
            Attribution Tracking
          </span>
          <span className="flex items-center">
            <span className="w-2 h-2 bg-purple-500 rounded-full mr-1 animate-pulse" />
            Trust Verified
          </span>
        </div>
        <p>
          Welcome to the future of AI trust and attribution! 🌟
        </p>
      </div>
    </div>
  );
}