'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useOnboarding } from '@/contexts/onboarding-context';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export function OnboardingComplete() {
  const router = useRouter();
  const { state, actions } = useOnboarding();

  useEffect(() => {
    // Mark onboarding as inactive when viewing complete page
    if (state.isActive) {
      // This can be handled by the context, but we'll leave it active for now
      // to allow users to restart if needed
    }
  }, [state.isActive]);

  const handleLaunchDashboard = () => {
    // Clear onboarding state and redirect to main dashboard
    actions.resetOnboarding();
    router.push('/');
  };

  const handleRestartOnboarding = () => {
    actions.resetOnboarding();
    router.push('/onboarding');
  };

  const getCompletionStats = () => {
    if (!state.progress) return null;

    const startTime = new Date(state.progress.start_time);
    const completionTime = state.progress.success_metrics?.total_onboarding_time || 0;
    const successLevel = state.progress.success_metrics?.success_level || 'completed';

    return {
      completionTime: completionTime < 60 ? 'less than a minute' : `${Math.round(completionTime / 60)} minutes`,
      successLevel,
      userType: state.progress.user_type,
      completedStages: state.progress.completed_stages?.length || 0
    };
  };

  const stats = getCompletionStats();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-4xl space-y-8">
        {/* Success Header */}
        <div className="text-center space-y-4">
          <div className="text-8xl animate-bounce">🎉</div>
          <h1 className="text-4xl font-bold text-gray-900">
            Congratulations!
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Your UATP system is fully configured and ready to provide 
            world-class AI trust and attribution tracking.
          </p>
        </div>

        {/* Completion Summary */}
        <Card className="p-8 bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <div className="text-center space-y-6">
            <h2 className="text-2xl font-semibold text-green-900">
              Setup Complete! ✨
            </h2>

            {stats && (
              <div className="grid md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">
                    {stats.completionTime}
                  </div>
                  <div className="text-green-700 text-sm">
                    Setup Time
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">
                    {stats.completedStages}/5
                  </div>
                  <div className="text-green-700 text-sm">
                    Stages Completed
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600 capitalize">
                    {stats.successLevel}
                  </div>
                  <div className="text-green-700 text-sm">
                    Success Level
                  </div>
                </div>
              </div>
            )}

            <div className="bg-white bg-opacity-50 rounded-lg p-4">
              <h3 className="font-semibold text-green-900 mb-3">What You've Accomplished:</h3>
              <div className="grid md:grid-cols-2 gap-3 text-sm text-green-800">
                <div className="flex items-center">
                  <span className="mr-2">✅</span>
                  Environment optimized for your needs
                </div>
                <div className="flex items-center">
                  <span className="mr-2">✅</span>
                  AI platform connected and verified
                </div>
                <div className="flex items-center">
                  <span className="mr-2">✅</span>
                  First capsule created with full attribution
                </div>
                <div className="flex items-center">
                  <span className="mr-2">✅</span>
                  System ready for production use
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* What's Next */}
        <Card className="p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6 text-center">
            What's Next? 🚀
          </h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-800 flex items-center">
                <span className="mr-2">🎯</span>
                Immediate Next Steps
              </h3>
              <ul className="space-y-3 text-sm text-gray-600">
                <li className="flex items-start">
                  <span className="mr-2 text-blue-500">→</span>
                  <div>
                    <strong>Explore the Dashboard:</strong> See your system health, capsule activity, and trust metrics
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="mr-2 text-blue-500">→</span>
                  <div>
                    <strong>Create More Capsules:</strong> Try different types of AI interactions and see full attribution
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="mr-2 text-blue-500">→</span>
                  <div>
                    <strong>Invite Team Members:</strong> Share the power of AI attribution with your colleagues
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="mr-2 text-blue-500">→</span>
                  <div>
                    <strong>Explore Advanced Features:</strong> Dive into governance, analytics, and specialized tools
                  </div>
                </li>
              </ul>
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold text-gray-800 flex items-center">
                <span className="mr-2">📚</span>
                Learning Resources
              </h3>
              <ul className="space-y-3 text-sm text-gray-600">
                <li className="flex items-start">
                  <span className="mr-2 text-purple-500">📖</span>
                  <div>
                    <strong>User Guide:</strong> Complete documentation for all UATP features
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="mr-2 text-purple-500">🎥</span>
                  <div>
                    <strong>Video Tutorials:</strong> Step-by-step guides for advanced workflows
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="mr-2 text-purple-500">💬</span>
                  <div>
                    <strong>Community Forum:</strong> Connect with other UATP users and experts
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="mr-2 text-purple-500">🔧</span>
                  <div>
                    <strong>API Documentation:</strong> Integrate UATP into your existing workflows
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            onClick={handleLaunchDashboard}
            className="px-8 py-3 text-lg font-medium bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
          >
            Launch UATP Dashboard 🚀
          </Button>
          
          <Button
            onClick={handleRestartOnboarding}
            variant="outline"
            className="px-6 py-3 text-sm"
          >
            Restart Onboarding
          </Button>
        </div>

        {/* System Status */}
        <Card className="p-6 bg-blue-50 border-blue-200">
          <div className="text-center space-y-3">
            <h3 className="font-semibold text-blue-900">System Status</h3>
            <div className="flex items-center justify-center space-x-6 text-sm">
              <div className="flex items-center text-green-700">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse" />
                <span>UATP Engine Active</span>
              </div>
              <div className="flex items-center text-blue-700">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-2 animate-pulse" />
                <span>Attribution Tracking</span>
              </div>
              <div className="flex items-center text-purple-700">
                <div className="w-3 h-3 bg-purple-500 rounded-full mr-2 animate-pulse" />
                <span>Trust Verification</span>
              </div>
            </div>
            <p className="text-blue-800 text-xs">
              Your system is running optimally and ready for use
            </p>
          </div>
        </Card>

        {/* Footer Message */}
        <div className="text-center text-gray-500 text-sm space-y-2">
          <p>
            🌟 Welcome to the future of AI trust and attribution!
          </p>
          <p>
            Thank you for choosing UATP - Universal AI Trust Protocol
          </p>
        </div>
      </div>
    </div>
  );
}