'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useOnboarding } from '@/contexts/onboarding-context';
import { logger } from '@/lib/logger';

export function useOnboardingFlow() {
  const router = useRouter();
  const pathname = usePathname();
  const { state } = useOnboarding();
  const [shouldShowOnboarding, setShouldShowOnboarding] = useState<boolean | null>(null);

  useEffect(() => {
    const checkOnboardingStatus = async () => {
      // Don't show onboarding on onboarding pages
      if (pathname.startsWith('/onboarding')) {
        setShouldShowOnboarding(false);
        return;
      }

      // Check if user has actually created a persistent account (not just completed wizard)
      const userId = localStorage.getItem('uatp_onboarding_user_id');
      const isDismissedThisSession = sessionStorage.getItem('uatp_onboarding_dismissed_session');

      // Always show banner unless dismissed this session
      if (isDismissedThisSession) {
        setShouldShowOnboarding(false);
        return;
      }

      // Check actual user account status from backend via API client
      if (userId) {
        try {
          // Import API client dynamically to avoid circular deps
          const { apiClient } = await import('@/lib/api-client');
          const userData = await apiClient.getOnboardingStatus(userId);

          // Only hide banner if user has persistent account with verified status
          if (userData.success && userData.progress?.user_type) {
            setShouldShowOnboarding(false);
            return;
          }
        } catch (error) {
          logger.debug('Could not check user status, showing onboarding banner');
        }
      }

      // Show onboarding banner by default for all users who haven't created accounts
      setShouldShowOnboarding(true);
    };

    checkOnboardingStatus();
  }, [pathname, state.progress, state.isActive]);

  const startOnboarding = () => {
    router.push('/onboarding');
  };

  const dismissOnboarding = () => {
    // Only dismiss for this session, will show again on next visit
    sessionStorage.setItem('uatp_onboarding_dismissed_session', 'true');
    setShouldShowOnboarding(false);
  };

  const completeOnboarding = async (registrationData?: {
    email?: string;
    username?: string;
    password?: string;
    full_name?: string;
  }) => {
    try {
      const userId = localStorage.getItem('uatp_onboarding_user_id');
      if (!userId) {
        logger.error('No user ID found for onboarding completion');
        return;
      }

      // Complete onboarding via API client
      const { apiClient } = await import('@/lib/api-client');
      const result = await apiClient.continueOnboarding(userId, {
        registration_data: registrationData,
        completion_step: true
      });

      if (result.success) {
        localStorage.setItem('uatp_user_id', userId);
        localStorage.removeItem('uatp_onboarding_progress');
        localStorage.removeItem('uatp_onboarding_dismissed_session');
        setShouldShowOnboarding(false);
      } else {
        logger.error('Failed to complete onboarding:', result.error);
      }
    } catch (error) {
      logger.error('Failed to complete onboarding:', error);
    }
  };

  return {
    shouldShowOnboarding,
    startOnboarding,
    dismissOnboarding,
    completeOnboarding,
    isOnboardingPath: pathname.startsWith('/onboarding'),
    onboardingProgress: state.progress,
  };
}
