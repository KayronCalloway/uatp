"""
UATP Onboarding Orchestrator

The master coordinator for client onboarding experiences.
Provides a unified interface that orchestrates all onboarding components
for maximum simplicity and effectiveness.
"""

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .health_monitor import SystemHealthMonitor
from .integration_manager import IntegrationManager
from .setup_wizard import InteractiveSetupWizard
from .support_assistant import SupportAssistant

logger = logging.getLogger(__name__)


class OnboardingStage(Enum):
    """Onboarding stages with progressive disclosure"""

    WELCOME = "welcome"
    ENVIRONMENT_DETECTION = "environment_detection"
    QUICK_SETUP = "quick_setup"
    AI_INTEGRATION = "ai_integration"
    FIRST_CAPSULE = "first_capsule"
    SUCCESS_MILESTONE = "success_milestone"
    ADVANCED_FEATURES = "advanced_features"
    COMPLETE = "complete"


class UserType(Enum):
    """User archetypes for personalized onboarding"""

    DEVELOPER = "developer"
    BUSINESS_USER = "business_user"
    RESEARCHER = "researcher"
    CASUAL_USER = "casual_user"
    ENTERPRISE = "enterprise"


@dataclass
class OnboardingProgress:
    """Tracks user progress through onboarding"""

    user_id: str
    user_type: UserType
    current_stage: OnboardingStage = OnboardingStage.WELCOME
    completed_stages: List[OnboardingStage] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    estimated_completion_time: Optional[datetime] = None
    personalization_data: Dict[str, Any] = field(default_factory=dict)
    success_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OnboardingStep:
    """Individual onboarding step definition"""

    id: str
    title: str
    description: str
    estimated_duration: int  # seconds
    required: bool = True
    prerequisites: List[str] = field(default_factory=list)
    user_types: List[UserType] = field(default_factory=list)
    action_handler: Optional[Callable] = None
    success_criteria: Optional[Callable] = None


class OnboardingOrchestrator:
    """
    Master coordinator for UATP client onboarding.

    Provides a unified, intuitive experience that adapts to user needs
    and ensures successful system activation within minutes.
    """

    def __init__(self):
        """Initialize the onboarding orchestrator"""
        self.setup_wizard = InteractiveSetupWizard()
        self.integration_manager = IntegrationManager()
        self.health_monitor = SystemHealthMonitor()
        self.support_assistant = SupportAssistant()

        # Track active onboarding sessions
        self.active_sessions: Dict[str, OnboardingProgress] = {}

        # Define onboarding flows for different user types
        self._initialize_onboarding_flows()

        logger.info("UATP Onboarding Orchestrator initialized")

    def _initialize_onboarding_flows(self):
        """Initialize personalized onboarding flows"""

        # Quick start flow for casual users (5-minute target)
        self.quick_flow = [
            OnboardingStep(
                id="welcome_quick",
                title="Welcome to UATP!",
                description="Let's get you up and running in under 5 minutes",
                estimated_duration=30,
                user_types=[UserType.CASUAL_USER, UserType.BUSINESS_USER],
            ),
            OnboardingStep(
                id="auto_detect",
                title="Smart Environment Detection",
                description="We're automatically detecting your setup...",
                estimated_duration=15,
                action_handler=self._auto_detect_environment,
            ),
            OnboardingStep(
                id="one_click_setup",
                title="One-Click Setup",
                description="Setting up your UATP system with smart defaults",
                estimated_duration=60,
                action_handler=self._one_click_setup,
            ),
            OnboardingStep(
                id="ai_quick_connect",
                title="Connect Your AI Platform",
                description="Choose your preferred AI platform and we'll handle the rest",
                estimated_duration=120,
                action_handler=self._quick_ai_setup,
            ),
            OnboardingStep(
                id="first_success",
                title="Create Your First Capsule",
                description="Let's create your first UATP capsule together",
                estimated_duration=90,
                action_handler=self._guided_first_capsule,
            ),
        ]

        # Developer flow (10-minute target)
        self.developer_flow = [
            OnboardingStep(
                id="welcome_dev",
                title="Welcome, Developer!",
                description="Let's set up your development environment for UATP",
                estimated_duration=30,
                user_types=[UserType.DEVELOPER],
            ),
            OnboardingStep(
                id="env_analysis",
                title="Development Environment Analysis",
                description="Analyzing your dev environment and suggesting optimal configuration",
                estimated_duration=45,
                action_handler=self._analyze_dev_environment,
            ),
            OnboardingStep(
                id="api_key_setup",
                title="Secure API Key Management",
                description="Setting up secure credential management",
                estimated_duration=90,
                action_handler=self._setup_api_keys,
            ),
            OnboardingStep(
                id="integration_wizard",
                title="AI Platform Integration",
                description="Configure integrations with your preferred AI platforms",
                estimated_duration=180,
                action_handler=self._developer_integration_setup,
            ),
            OnboardingStep(
                id="first_capsule_dev",
                title="Your First Attributed Capsule",
                description="Create a capsule with full attribution tracking",
                estimated_duration=150,
                action_handler=self._developer_first_capsule,
            ),
            OnboardingStep(
                id="testing_tools",
                title="Testing & Debugging Tools",
                description="Explore the development tools and debugging capabilities",
                estimated_duration=120,
                action_handler=self._setup_dev_tools,
            ),
        ]

        # Enterprise flow (15-minute target)
        self.enterprise_flow = [
            OnboardingStep(
                id="welcome_enterprise",
                title="Welcome to UATP Enterprise",
                description="Setting up enterprise-grade AI trust infrastructure",
                estimated_duration=60,
                user_types=[UserType.ENTERPRISE],
            ),
            OnboardingStep(
                id="security_assessment",
                title="Security Requirements Assessment",
                description="Analyzing your security and compliance needs",
                estimated_duration=120,
                action_handler=self._assess_enterprise_security,
            ),
            OnboardingStep(
                id="infrastructure_setup",
                title="Infrastructure Configuration",
                description="Setting up scalable, production-ready infrastructure",
                estimated_duration=300,
                action_handler=self._setup_enterprise_infrastructure,
            ),
            OnboardingStep(
                id="integration_suite",
                title="Enterprise AI Integration Suite",
                description="Connecting to your enterprise AI platforms and tools",
                estimated_duration=240,
                action_handler=self._enterprise_integrations,
            ),
            OnboardingStep(
                id="governance_setup",
                title="Governance & Compliance",
                description="Configuring governance, audit trails, and compliance features",
                estimated_duration=180,
                action_handler=self._setup_governance,
            ),
            OnboardingStep(
                id="team_onboarding",
                title="Team Member Onboarding",
                description="Setting up access controls and team member accounts",
                estimated_duration=120,
                action_handler=self._setup_team_access,
            ),
        ]

    async def start_onboarding(
        self, user_id: str, user_preferences: Dict[str, Any] = None
    ) -> OnboardingProgress:
        """
        Start personalized onboarding for a user

        Args:
            user_id: Unique identifier for the user
            user_preferences: Optional user preferences and context

        Returns:
            OnboardingProgress object tracking the session
        """

        # Detect user type and preferences
        user_type = await self._detect_user_type(user_preferences or {})

        # Create onboarding progress tracker
        progress = OnboardingProgress(
            user_id=user_id,
            user_type=user_type,
            personalization_data=user_preferences or {},
        )

        # Store active session
        self.active_sessions[user_id] = progress

        # Estimate completion time based on user type
        progress.estimated_completion_time = self._estimate_completion_time(user_type)

        logger.info(f"Started onboarding for user {user_id} as {user_type.value}")

        # Begin with welcome and user type confirmation
        return await self._execute_welcome_stage(progress)

    async def _detect_user_type(self, preferences: Dict[str, Any]) -> UserType:
        """Intelligently detect user type based on context and preferences"""

        # Check explicit preference
        if "user_type" in preferences:
            try:
                return UserType(preferences["user_type"])
            except ValueError:
                pass

        # Detect based on environment and context
        context_score = {
            UserType.DEVELOPER: 0,
            UserType.BUSINESS_USER: 0,
            UserType.RESEARCHER: 0,
            UserType.CASUAL_USER: 0,
            UserType.ENTERPRISE: 0,
        }

        # Check for development indicators
        if preferences.get("has_git", False) or preferences.get("has_ide", False):
            context_score[UserType.DEVELOPER] += 2

        if preferences.get("python_experience") == "advanced":
            context_score[UserType.DEVELOPER] += 2

        # Check for business indicators
        if preferences.get("organization_size", 0) > 50:
            context_score[UserType.ENTERPRISE] += 3
        elif preferences.get("organization_size", 0) > 10:
            context_score[UserType.BUSINESS_USER] += 2

        # Check for research indicators
        if preferences.get("use_case") in ["research", "academic", "ai_research"]:
            context_score[UserType.RESEARCHER] += 3

        # Check for enterprise indicators
        if preferences.get("compliance_requirements", False):
            context_score[UserType.ENTERPRISE] += 2

        if preferences.get("scalability_needs") == "high":
            context_score[UserType.ENTERPRISE] += 2

        # Default to casual user if no strong indicators
        max_score = max(context_score.values())
        if max_score == 0:
            return UserType.CASUAL_USER

        # Return highest scoring type
        return max(context_score.items(), key=lambda x: x[1])[0]

    def _estimate_completion_time(self, user_type: UserType) -> datetime:
        """Estimate onboarding completion time based on user type"""
        from datetime import timedelta

        duration_minutes = {
            UserType.CASUAL_USER: 5,
            UserType.BUSINESS_USER: 7,
            UserType.RESEARCHER: 10,
            UserType.DEVELOPER: 12,
            UserType.ENTERPRISE: 20,
        }

        minutes = duration_minutes.get(user_type, 10)
        return datetime.now(timezone.utc) + timedelta(minutes=minutes)

    def serialize_progress(self, progress: OnboardingProgress) -> Dict[str, Any]:
        """Serialize onboarding progress with proper datetime handling"""
        progress_dict = asdict(progress)

        # Convert datetime objects to ISO strings
        if progress_dict.get("start_time"):
            progress_dict["start_time"] = progress.start_time.isoformat()
        if progress_dict.get("estimated_completion_time"):
            progress_dict["estimated_completion_time"] = (
                progress.estimated_completion_time.isoformat()
            )

        # Convert enums to values
        progress_dict["user_type"] = progress.user_type.value
        progress_dict["current_stage"] = progress.current_stage.value
        progress_dict["completed_stages"] = [
            stage.value for stage in progress.completed_stages
        ]

        return progress_dict

    async def _execute_welcome_stage(
        self, progress: OnboardingProgress
    ) -> OnboardingProgress:
        """Execute the welcome stage with personalized messaging"""

        progress.current_stage = OnboardingStage.WELCOME

        # Show personalized welcome based on user type
        welcome_messages = {
            UserType.CASUAL_USER: {
                "title": "Welcome to UATP! ",
                "message": "Let's get you creating AI capsules in under 5 minutes. No technical knowledge required!",
                "next_action": "Start Quick Setup",
            },
            UserType.DEVELOPER: {
                "title": "Welcome, Developer! ‍",
                "message": "Let's set up your UATP development environment with full attribution tracking.",
                "next_action": "Analyze Dev Environment",
            },
            UserType.ENTERPRISE: {
                "title": "Welcome to UATP Enterprise ",
                "message": "Setting up enterprise-grade AI trust infrastructure for your organization.",
                "next_action": "Begin Security Assessment",
            },
            UserType.RESEARCHER: {
                "title": "Welcome, Researcher! ",
                "message": "Let's configure UATP for your research needs with full transparency and attribution.",
                "next_action": "Configure Research Environment",
            },
            UserType.BUSINESS_USER: {
                "title": "Welcome to UATP! ",
                "message": "We'll have you using AI with full attribution in just a few minutes.",
                "next_action": "Quick Business Setup",
            },
        }

        welcome = welcome_messages[progress.user_type]
        progress.personalization_data["welcome"] = welcome

        # Mark welcome as completed
        progress.completed_stages.append(OnboardingStage.WELCOME)
        progress.current_stage = OnboardingStage.ENVIRONMENT_DETECTION

        logger.info(f"Welcome stage completed for {progress.user_id}")
        return progress

    async def continue_onboarding(
        self, user_id: str, step_data: Dict[str, Any] = None
    ) -> OnboardingProgress:
        """Continue onboarding process to next step"""

        if user_id not in self.active_sessions:
            # Session expired or lost, create a new one with the provided data
            logger.warning(
                f"No active session for user {user_id}, creating new session"
            )
            preferences = step_data or {}
            progress = await self.start_onboarding(user_id, preferences)
            return progress

        progress = self.active_sessions[user_id]

        # Execute current stage
        if progress.current_stage == OnboardingStage.ENVIRONMENT_DETECTION:
            return await self._execute_environment_detection(progress, step_data or {})
        elif progress.current_stage == OnboardingStage.QUICK_SETUP:
            return await self._execute_quick_setup(progress, step_data or {})
        elif progress.current_stage == OnboardingStage.AI_INTEGRATION:
            return await self._execute_ai_integration(progress, step_data or {})
        elif progress.current_stage == OnboardingStage.FIRST_CAPSULE:
            return await self._execute_first_capsule(progress, step_data or {})
        elif progress.current_stage == OnboardingStage.SUCCESS_MILESTONE:
            return await self._execute_success_milestone(progress)
        else:
            # Stage completed
            return progress

    async def _execute_environment_detection(
        self, progress: OnboardingProgress, data: Dict[str, Any]
    ) -> OnboardingProgress:
        """Auto-detect user environment and suggest optimal configuration"""

        # Use setup wizard for environment detection
        env_info = await self.setup_wizard.detect_environment()

        # Convert EnvironmentInfo dataclass to dict for serialization
        from dataclasses import asdict

        progress.personalization_data["environment"] = asdict(env_info)
        progress.completed_stages.append(OnboardingStage.ENVIRONMENT_DETECTION)
        progress.current_stage = OnboardingStage.QUICK_SETUP

        return progress

    async def _execute_quick_setup(
        self, progress: OnboardingProgress, data: Dict[str, Any]
    ) -> OnboardingProgress:
        """Execute quick setup with smart defaults"""

        # Use setup wizard for system initialization
        setup_result = await self.setup_wizard.quick_setup(
            user_type=progress.user_type, preferences=progress.personalization_data
        )

        progress.personalization_data["setup"] = setup_result
        progress.completed_stages.append(OnboardingStage.QUICK_SETUP)
        progress.current_stage = OnboardingStage.AI_INTEGRATION

        return progress

    async def _execute_ai_integration(
        self, progress: OnboardingProgress, data: Dict[str, Any]
    ) -> OnboardingProgress:
        """Execute AI platform integration setup"""

        # Get available AI platforms
        available_platforms = await self.integration_manager.get_available_platforms()

        # For quick users, suggest the most popular platform
        if progress.user_type in [UserType.CASUAL_USER, UserType.BUSINESS_USER]:
            if "preferred_platform" not in data:
                # Auto-suggest based on environment
                suggested_platform = self._suggest_ai_platform(
                    progress.personalization_data
                )
                data["preferred_platform"] = suggested_platform

        # Setup integration
        if "preferred_platform" in data:
            # Prepare credentials if API key was provided
            credentials = None
            if "api_key" in data and data["api_key"]:
                platform = data["preferred_platform"]
                if platform == "openai":
                    credentials = {"OPENAI_API_KEY": data["api_key"]}
                elif platform == "anthropic":
                    credentials = {"ANTHROPIC_API_KEY": data["api_key"]}
                elif platform == "cohere":
                    credentials = {"COHERE_API_KEY": data["api_key"]}
                elif platform == "huggingface":
                    credentials = {"HUGGINGFACE_API_TOKEN": data["api_key"]}

            integration_result = (
                await self.integration_manager.setup_platform_integration(
                    platform=data["preferred_platform"],
                    user_type=progress.user_type,
                    quick_setup=True,
                    credentials=credentials,
                )
            )
            progress.personalization_data["integration"] = integration_result

        progress.completed_stages.append(OnboardingStage.AI_INTEGRATION)
        progress.current_stage = OnboardingStage.FIRST_CAPSULE

        return progress

    async def _execute_first_capsule(
        self, progress: OnboardingProgress, data: Dict[str, Any]
    ) -> OnboardingProgress:
        """Guide user through creating their first capsule"""

        # Use integration manager to create first capsule
        first_capsule_result = (
            await self.integration_manager.create_guided_first_capsule(
                user_type=progress.user_type, context=progress.personalization_data
            )
        )

        progress.personalization_data["first_capsule"] = first_capsule_result
        progress.success_metrics["first_capsule_created"] = True
        progress.success_metrics["time_to_first_capsule"] = (
            datetime.now(timezone.utc) - progress.start_time
        ).total_seconds()

        progress.completed_stages.append(OnboardingStage.FIRST_CAPSULE)
        progress.current_stage = OnboardingStage.SUCCESS_MILESTONE

        return progress

    async def _execute_success_milestone(
        self, progress: OnboardingProgress
    ) -> OnboardingProgress:
        """Celebrate success and offer next steps"""

        # Calculate onboarding success metrics
        total_time = (datetime.now(timezone.utc) - progress.start_time).total_seconds()
        progress.success_metrics["total_onboarding_time"] = total_time
        progress.success_metrics["onboarding_completed"] = True

        # Determine success level based on time and completion
        if total_time < 300:  # Under 5 minutes
            success_level = "excellent"
        elif total_time < 600:  # Under 10 minutes
            success_level = "good"
        else:
            success_level = "completed"

        progress.success_metrics["success_level"] = success_level

        # Generate personalized next steps recommendations
        next_steps = self._generate_next_steps(progress)
        progress.personalization_data["next_steps"] = next_steps

        progress.completed_stages.append(OnboardingStage.SUCCESS_MILESTONE)
        progress.current_stage = OnboardingStage.COMPLETE

        logger.info(f"Onboarding completed for {progress.user_id} in {total_time:.1f}s")

        return progress

    def _suggest_ai_platform(self, personalization_data: Dict[str, Any]) -> str:
        """Suggest optimal AI platform based on user context"""

        # Simple heuristics for platform suggestion
        env_info = personalization_data.get("environment", {})

        # If OpenAI API key detected, suggest OpenAI
        if env_info.get("has_openai_key"):
            return "openai"

        # If Anthropic API key detected, suggest Anthropic
        if env_info.get("has_anthropic_key"):
            return "anthropic"

        # Default to most user-friendly option
        return "openai"

    def _generate_next_steps(
        self, progress: OnboardingProgress
    ) -> List[Dict[str, Any]]:
        """Generate personalized next steps based on user type and completion"""

        base_steps = [
            {
                "title": "Explore the Dashboard",
                "description": "View your system health and capsule activity",
                "action": "open_dashboard",
                "estimated_time": "2 minutes",
            },
            {
                "title": "Create More Capsules",
                "description": "Try different types of AI interactions",
                "action": "create_capsule",
                "estimated_time": "5 minutes",
            },
        ]

        # Add user-type specific recommendations
        if progress.user_type == UserType.DEVELOPER:
            base_steps.extend(
                [
                    {
                        "title": "Explore the API",
                        "description": "Try the REST API and see code examples",
                        "action": "view_api_docs",
                        "estimated_time": "10 minutes",
                    },
                    {
                        "title": "Set Up CI/CD Integration",
                        "description": "Integrate UATP into your development workflow",
                        "action": "setup_cicd",
                        "estimated_time": "15 minutes",
                    },
                ]
            )
        elif progress.user_type == UserType.ENTERPRISE:
            base_steps.extend(
                [
                    {
                        "title": "Configure Team Access",
                        "description": "Add team members and set up role-based access",
                        "action": "team_management",
                        "estimated_time": "10 minutes",
                    },
                    {
                        "title": "Review Compliance Settings",
                        "description": "Ensure all compliance requirements are met",
                        "action": "compliance_review",
                        "estimated_time": "15 minutes",
                    },
                ]
            )

        return base_steps

    async def get_onboarding_status(self, user_id: str) -> Optional[OnboardingProgress]:
        """Get current onboarding status for a user"""
        return self.active_sessions.get(user_id)

    async def get_health_status(self) -> Dict[str, Any]:
        """Get system health status for onboarding users"""
        return await self.health_monitor.get_system_health()

    async def get_support_context(
        self, user_id: str, issue_type: str = None
    ) -> Dict[str, Any]:
        """Get contextual support information for onboarding"""

        progress = self.active_sessions.get(user_id)
        return await self.support_assistant.get_contextual_help(
            user_progress=progress, issue_type=issue_type
        )

    # Handler methods for different flows (to be implemented by specific steps)
    async def _auto_detect_environment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-detect environment handler"""
        return await self.setup_wizard.detect_environment()

    async def _one_click_setup(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """One-click setup handler"""
        return await self.setup_wizard.quick_setup(
            user_type=UserType.CASUAL_USER, preferences=context
        )

    async def _quick_ai_setup(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Quick AI setup handler"""
        platform = self._suggest_ai_platform(context)
        return await self.integration_manager.setup_platform_integration(
            platform=platform, user_type=UserType.CASUAL_USER, quick_setup=True
        )

    async def _guided_first_capsule(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Guided first capsule creation handler"""
        return await self.integration_manager.create_guided_first_capsule(
            user_type=UserType.CASUAL_USER, context=context
        )

    # Developer-specific handlers
    async def _analyze_dev_environment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze development environment"""
        return await self.setup_wizard.analyze_development_environment()

    async def _setup_api_keys(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup secure API key management"""
        return await self.setup_wizard.setup_secure_credentials()

    async def _developer_integration_setup(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Developer-focused integration setup"""
        return await self.integration_manager.setup_developer_integrations()

    async def _developer_first_capsule(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Developer first capsule with full attribution"""
        return await self.integration_manager.create_attributed_capsule()

    async def _setup_dev_tools(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup development and debugging tools"""
        return await self.setup_wizard.setup_development_tools()

    # Enterprise-specific handlers
    async def _assess_enterprise_security(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess enterprise security requirements"""
        return await self.setup_wizard.assess_security_requirements()

    async def _setup_enterprise_infrastructure(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Setup enterprise infrastructure"""
        return await self.setup_wizard.setup_production_infrastructure()

    async def _enterprise_integrations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup enterprise AI integrations"""
        return await self.integration_manager.setup_enterprise_integrations()

    async def _setup_governance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup governance and compliance"""
        return await self.setup_wizard.setup_governance_framework()

    async def _setup_team_access(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup team member access and roles"""
        return await self.setup_wizard.setup_team_management()
