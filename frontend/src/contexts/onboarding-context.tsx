'use client';

import React, { createContext, useContext, useReducer, useEffect } from 'react';
import {
  OnboardingState,
  OnboardingActions,
  OnboardingProgress,
  UserType,
  OnboardingStage,
  UserPreferences,
  PlatformInfo,
  SystemHealth,
  SupportResponse
} from '@/types/onboarding';
import { api } from '@/lib/api-client';

// Initial state
const initialState: OnboardingState = {
  isActive: false,
  progress: null,
  currentStep: null,
  availablePlatforms: {},
  systemHealth: null,
  error: null,
  isLoading: false,
};

// Action types
type OnboardingAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_PROGRESS'; payload: OnboardingProgress }
  | { type: 'SET_PLATFORMS'; payload: Record<string, PlatformInfo> }
  | { type: 'SET_SYSTEM_HEALTH'; payload: SystemHealth }
  | { type: 'SET_ACTIVE'; payload: boolean }
  | { type: 'RESET' };

// Reducer
function onboardingReducer(state: OnboardingState, action: OnboardingAction): OnboardingState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    case 'SET_PROGRESS':
      return {
        ...state,
        progress: action.payload,
        isActive: action.payload.current_stage !== OnboardingStage.COMPLETE,
        error: null,
        isLoading: false
      };
    case 'SET_PLATFORMS':
      return { ...state, availablePlatforms: action.payload };
    case 'SET_SYSTEM_HEALTH':
      return { ...state, systemHealth: action.payload };
    case 'SET_ACTIVE':
      return { ...state, isActive: action.payload };
    case 'RESET':
      return { ...initialState };
    default:
      return state;
  }
}

// Context
const OnboardingContext = createContext<{
  state: OnboardingState;
  actions: OnboardingActions;
}>({
  state: initialState,
  actions: {} as OnboardingActions,
});

// Generate unique user ID
const generateUserId = (): string => {
  return `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Get or create user ID
const getUserId = (): string => {
  if (typeof window === 'undefined') return generateUserId();

  let userId = localStorage.getItem('uatp_onboarding_user_id');
  if (!userId) {
    userId = generateUserId();
    localStorage.setItem('uatp_onboarding_user_id', userId);
  }
  return userId;
};

// Provider component
export function OnboardingProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(onboardingReducer, initialState);

  // Actions
  const actions: OnboardingActions = {
    startOnboarding: async (preferences: UserPreferences) => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true });
        dispatch({ type: 'SET_ERROR', payload: null });

        const userId = getUserId();
        const response = await api.startOnboarding(userId, preferences);

        if (response.success && response.progress) {
          console.log('Setting onboarding progress:', response.progress);
          dispatch({ type: 'SET_PROGRESS', payload: response.progress });

          // Store onboarding state in localStorage
          localStorage.setItem('uatp_onboarding_progress', JSON.stringify(response.progress));
        } else {
          throw new Error(response.error || 'Failed to start onboarding');
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        dispatch({ type: 'SET_ERROR', payload: errorMessage });
        console.error('Failed to start onboarding:', error);
      }
    },

    continueOnboarding: async (stepData?: Record<string, any>) => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true });
        dispatch({ type: 'SET_ERROR', payload: null });

        const userId = getUserId();
        const response = await api.continueOnboarding(userId, stepData);

        if (response.success && response.progress) {
          dispatch({ type: 'SET_PROGRESS', payload: response.progress });

          // Update stored progress
          localStorage.setItem('uatp_onboarding_progress', JSON.stringify(response.progress));
        } else {
          throw new Error(response.error || 'Failed to continue onboarding');
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        dispatch({ type: 'SET_ERROR', payload: errorMessage });
        console.error('Failed to continue onboarding:', error);
      }
    },

    selectUserType: (userType: UserType) => {
      // This is handled in the UI state, can trigger onboarding start
      actions.startOnboarding({ user_type: userType });
    },

    selectPlatform: (platformId: string) => {
      // Continue onboarding with selected platform
      actions.continueOnboarding({ preferred_platform: platformId });
    },

    getSupport: async (issueType?: string, message?: string): Promise<SupportResponse> => {
      try {
        const userId = getUserId();
        const response = await api.getOnboardingSupport(userId, issueType, message);

        if (response.success && response.data) {
          return response.data;
        } else {
          throw new Error(response.error || 'Failed to get support');
        }
      } catch (error) {
        console.error('Failed to get support:', error);
        // Return fallback support response
        return {
          message: 'Support is temporarily unavailable. Please check our documentation or try again later.',
          issue_type: issueType || 'general_question',
          immediate_actions: [
            'Check the getting started guide',
            'Review system requirements',
            'Try refreshing the page'
          ],
          resources: [
            { title: 'Documentation', url: '/docs', type: 'documentation' },
            { title: 'FAQ', url: '/docs/faq', type: 'documentation' }
          ]
        };
      }
    },

    resetOnboarding: () => {
      localStorage.removeItem('uatp_onboarding_progress');
      localStorage.removeItem('uatp_onboarding_user_id');
      dispatch({ type: 'RESET' });
    },
  };

  // Load saved progress on mount
  useEffect(() => {
    const loadSavedProgress = async () => {
      try {
        const savedProgress = localStorage.getItem('uatp_onboarding_progress');
        if (savedProgress) {
          const progress: OnboardingProgress = JSON.parse(savedProgress);
          dispatch({ type: 'SET_PROGRESS', payload: progress });
        }

        // Load available platforms
        const platformsResponse = await api.getAvailablePlatforms();
        if (platformsResponse.success && platformsResponse.data) {
          dispatch({ type: 'SET_PLATFORMS', payload: platformsResponse.data });
        }

        // Load system health
        const healthResponse = await api.getOnboardingSystemHealth();
        if (healthResponse.success && healthResponse.data) {
          dispatch({ type: 'SET_SYSTEM_HEALTH', payload: healthResponse.data });
        }
      } catch (error) {
        console.error('Failed to load onboarding data:', error);
      }
    };

    loadSavedProgress();
  }, []);

  // Monitor system health periodically
  useEffect(() => {
    const healthInterval = setInterval(async () => {
      try {
        const response = await api.getOnboardingSystemHealth();
        if (response.success && response.data) {
          dispatch({ type: 'SET_SYSTEM_HEALTH', payload: response.data });
        }
      } catch (error) {
        console.error('Health check failed:', error);
      }
    }, 30000); // Check every 30 seconds

    return () => clearInterval(healthInterval);
  }, []);

  return (
    <OnboardingContext.Provider value={{ state, actions }}>
      {children}
    </OnboardingContext.Provider>
  );
}

// Hook for using onboarding context
export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error('useOnboarding must be used within an OnboardingProvider');
  }
  return context;
}

// Utility hooks for specific onboarding data
export function useOnboardingProgress() {
  const { state } = useOnboarding();
  return state.progress;
}

export function useOnboardingStage() {
  const { state } = useOnboarding();
  return state.progress?.current_stage || null;
}

export function useAvailablePlatforms() {
  const { state } = useOnboarding();
  return state.availablePlatforms;
}

export function useSystemHealth() {
  const { state } = useOnboarding();
  return state.systemHealth;
}

export function useOnboardingError() {
  const { state } = useOnboarding();
  return state.error;
}

export function useIsOnboardingActive() {
  const { state } = useOnboarding();
  return state.isActive;
}
