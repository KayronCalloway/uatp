// TypeScript types for UATP Onboarding System Integration

export enum OnboardingStage {
  WELCOME = "welcome",
  ENVIRONMENT_DETECTION = "environment_detection", 
  QUICK_SETUP = "quick_setup",
  AI_INTEGRATION = "ai_integration",
  FIRST_CAPSULE = "first_capsule",
  SUCCESS_MILESTONE = "success_milestone",
  ADVANCED_FEATURES = "advanced_features",
  COMPLETE = "complete"
}

export enum UserType {
  DEVELOPER = "developer",
  BUSINESS_USER = "business_user", 
  RESEARCHER = "researcher",
  CASUAL_USER = "casual_user",
  ENTERPRISE = "enterprise"
}

export interface OnboardingProgress {
  user_id: string;
  user_type: UserType;
  current_stage: OnboardingStage;
  completed_stages: OnboardingStage[];
  start_time: string;
  estimated_completion_time?: string;
  personalization_data: Record<string, any>;
  success_metrics: Record<string, any>;
}

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  estimated_duration: number; // seconds
  required: boolean;
  prerequisites: string[];
  user_types: UserType[];
}

export interface UserPreferences {
  user_type?: UserType;
  has_git?: boolean;
  has_ide?: boolean;
  python_experience?: 'beginner' | 'intermediate' | 'advanced';
  organization_size?: number;
  use_case?: string;
  compliance_requirements?: boolean;
  scalability_needs?: 'low' | 'medium' | 'high';
}

export interface EnvironmentInfo {
  has_openai_key: boolean;
  has_anthropic_key: boolean;
  platform_detections: Record<string, boolean>;
  system_info: {
    os: string;
    node_version?: string;
    python_version?: string;
  };
}

export interface PlatformInfo {
  id: string;
  name: string;
  description: string;
  available: boolean;
  estimated_setup_time: number; // minutes
  requires_api_key: boolean;
  setup_instructions?: string[];
}

export interface OnboardingApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  progress?: OnboardingProgress;
  next_step?: {
    stage: string;
    title: string;
    description: string;
  };
}

export interface SystemHealth {
  overall_status: 'excellent' | 'good' | 'warning' | 'critical';
  score: number;
  summary: string;
  components: Record<string, {
    status: string;
    score: number;
    details: string;
  }>;
}

export interface SupportResponse {
  message: string;
  issue_type: string;
  immediate_actions: string[];
  resources: Array<{
    title: string;
    url: string;
    type: 'documentation' | 'video' | 'tutorial';
  }>;
  estimated_resolution_time?: number;
}

// UI State Types
export interface OnboardingState {
  isActive: boolean;
  progress: OnboardingProgress | null;
  currentStep: OnboardingStep | null;
  availablePlatforms: Record<string, PlatformInfo>;
  systemHealth: SystemHealth | null;
  error: string | null;
  isLoading: boolean;
}

export interface OnboardingActions {
  startOnboarding: (preferences: UserPreferences) => Promise<void>;
  continueOnboarding: (stepData?: Record<string, any>) => Promise<void>;
  selectUserType: (userType: UserType) => void;
  selectPlatform: (platformId: string) => void;
  getSupport: (issueType?: string, message?: string) => Promise<SupportResponse>;
  resetOnboarding: () => void;
}

// WebSocket Event Types
export interface OnboardingWebSocketMessage {
  type: 'progress_update' | 'health_update' | 'platform_status' | 'error';
  data: any;
  timestamp: string;
}

export interface OnboardingProgressUpdate {
  type: 'progress_update';
  data: OnboardingProgress;
}

export interface OnboardingHealthUpdate {
  type: 'health_update';
  data: {
    status: string;
    score: number;
    summary: string;
  };
}