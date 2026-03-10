"""
Support Assistant

Provides contextual help, automated troubleshooting, and intelligent
support guidance for onboarding users. Uses the user's current progress
and system state to provide targeted assistance.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class IssueType(Enum):
    """Types of issues users might encounter"""

    SETUP_FAILED = "setup_failed"
    API_KEY_ISSUE = "api_key_issue"
    CONNECTION_ERROR = "connection_error"
    PERFORMANCE_ISSUE = "performance_issue"
    INTEGRATION_FAILED = "integration_failed"
    CAPSULE_CREATION_FAILED = "capsule_creation_failed"
    GENERAL_QUESTION = "general_question"
    FEATURE_REQUEST = "feature_request"


class SupportLevel(Enum):
    """Support intervention levels"""

    SELF_SERVICE = "self_service"
    GUIDED_HELP = "guided_help"
    HUMAN_SUPPORT = "human_support"
    EMERGENCY = "emergency"


@dataclass
class SupportContext:
    """Context information for support requests"""

    user_id: str
    user_type: Optional[str] = None
    onboarding_stage: Optional[str] = None
    system_health: Optional[Dict[str, Any]] = None
    recent_actions: List[str] = field(default_factory=list)
    error_history: List[str] = field(default_factory=list)
    integration_status: Dict[str, Any] = field(default_factory=dict)
    environment_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SupportResponse:
    """Response from support assistant"""

    issue_type: IssueType
    support_level: SupportLevel
    title: str
    message: str

    # Actionable solutions
    immediate_actions: List[str] = field(default_factory=list)
    step_by_step_guide: List[Dict[str, str]] = field(default_factory=list)

    # Additional resources
    documentation_links: List[Dict[str, str]] = field(default_factory=list)
    video_tutorials: List[Dict[str, str]] = field(default_factory=list)

    # Escalation options
    escalation_available: bool = False
    escalation_message: str = ""

    # Preventive guidance
    prevention_tips: List[str] = field(default_factory=list)

    # Metadata
    confidence_score: float = 0.0
    estimated_resolution_time: Optional[str] = None


@dataclass
class TroubleshootingFlow:
    """Guided troubleshooting flow"""

    flow_id: str
    title: str
    description: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    completed: bool = False
    success: bool = False


class SupportAssistant:
    """
    Intelligent support assistant providing contextual help and troubleshooting.

    Features:
    - Contextual help based on user progress
    - Automated issue diagnosis
    - Step-by-step troubleshooting flows
    - Proactive issue prevention
    - Smart escalation routing
    """

    def __init__(self):
        """Initialize support assistant"""
        self.active_support_sessions: Dict[str, Dict[str, Any]] = {}
        self.troubleshooting_flows: Dict[str, TroubleshootingFlow] = {}
        self.knowledge_base = self._initialize_knowledge_base()

        logger.info("Support Assistant initialized")

    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """Initialize knowledge base with common issues and solutions"""

        return {
            "setup_issues": {
                "python_version": {
                    "problem": "Incompatible Python version",
                    "solution": "UATP requires Python 3.8 or higher. Please upgrade your Python installation.",
                    "steps": [
                        "Check current Python version: python --version",
                        "Download Python 3.8+ from python.org",
                        "Install and restart your terminal",
                        "Verify installation: python --version",
                    ],
                },
                "missing_dependencies": {
                    "problem": "Required dependencies not installed",
                    "solution": "Install missing Python packages.",
                    "steps": [
                        "Install requirements: pip install -r requirements.txt",
                        "If pip fails, try: pip install --upgrade pip",
                        "For conda users: conda install -c conda-forge <package>",
                        "Verify installation: pip list",
                    ],
                },
                "permission_error": {
                    "problem": "Permission denied during setup",
                    "solution": "Fix file permissions or run with appropriate privileges.",
                    "steps": [
                        "On Unix/Mac: chmod +x setup_script",
                        "Or run with sudo: sudo python setup.py",
                        "On Windows: Run as Administrator",
                        "Check directory permissions",
                    ],
                },
            },
            "api_key_issues": {
                "missing_key": {
                    "problem": "API key not found",
                    "solution": "Set your API key as an environment variable.",
                    "steps": [
                        "Get API key from your AI platform dashboard",
                        "Set environment variable: export OPENAI_API_KEY='your-key'",
                        "On Windows: set OPENAI_API_KEY=your-key",
                        "Restart your application to load the new variable",
                    ],
                },
                "invalid_key": {
                    "problem": "API key is invalid or expired",
                    "solution": "Verify and update your API key.",
                    "steps": [
                        "Check your API key in the platform dashboard",
                        "Ensure the key has proper permissions",
                        "Generate a new key if expired",
                        "Update your environment variable",
                    ],
                },
                "quota_exceeded": {
                    "problem": "API quota exceeded",
                    "solution": "Check your usage limits and billing.",
                    "steps": [
                        "Check usage in your platform dashboard",
                        "Verify billing information is up to date",
                        "Upgrade plan if needed",
                        "Wait for quota reset if on free tier",
                    ],
                },
            },
            "connection_issues": {
                "network_error": {
                    "problem": "Network connection failed",
                    "solution": "Check your internet connection and firewall settings.",
                    "steps": [
                        "Test internet connection: ping google.com",
                        "Check firewall settings for UATP",
                        "Try using a VPN if in restricted network",
                        "Verify DNS settings",
                    ],
                },
                "proxy_issues": {
                    "problem": "Corporate proxy blocking connections",
                    "solution": "Configure proxy settings for UATP.",
                    "steps": [
                        "Get proxy settings from IT department",
                        "Set HTTP_PROXY environment variable",
                        "Set HTTPS_PROXY environment variable",
                        "Configure SSL certificate verification",
                    ],
                },
            },
            "integration_issues": {
                "platform_not_responding": {
                    "problem": "AI platform not responding",
                    "solution": "Check platform status and retry.",
                    "steps": [
                        "Check platform status page",
                        "Wait 5 minutes and retry",
                        "Try different model if available",
                        "Contact platform support if persistent",
                    ],
                },
                "model_not_available": {
                    "problem": "Requested model not available",
                    "solution": "Use an available model or check access.",
                    "steps": [
                        "Check available models in platform docs",
                        "Verify your account has access to the model",
                        "Try a similar model as alternative",
                        "Contact platform support for access",
                    ],
                },
            },
        }

    async def get_contextual_help(
        self,
        user_progress: Optional[Any] = None,
        issue_type: Optional[str] = None,
        user_message: Optional[str] = None,
    ) -> SupportResponse:
        """
        Get contextual help based on user's current situation

        Args:
            user_progress: Current onboarding progress
            issue_type: Specific issue type if known
            user_message: User's description of the problem

        Returns:
            SupportResponse with targeted help
        """

        # Build support context
        context = await self._build_support_context(user_progress)

        # Analyze the issue
        if issue_type:
            analyzed_issue = IssueType(issue_type)
        else:
            analyzed_issue = await self._analyze_issue(context, user_message)

        # Generate support response
        response = await self._generate_support_response(
            analyzed_issue, context, user_message
        )

        # Store support session
        if user_progress and hasattr(user_progress, "user_id"):
            self.active_support_sessions[user_progress.user_id] = {
                "context": context,
                "issue_type": analyzed_issue,
                "response": response,
                "timestamp": datetime.now(timezone.utc),
            }

        return response

    async def _build_support_context(
        self, user_progress: Optional[Any]
    ) -> SupportContext:
        """Build comprehensive support context"""

        if not user_progress:
            return SupportContext(user_id="anonymous")

        context = SupportContext(
            user_id=getattr(user_progress, "user_id", "unknown"),
            user_type=getattr(user_progress, "user_type", {}).value
            if hasattr(getattr(user_progress, "user_type", {}), "value")
            else None,
            onboarding_stage=getattr(user_progress, "current_stage", {}).value
            if hasattr(getattr(user_progress, "current_stage", {}), "value")
            else None,
        )

        # Add environment info if available
        if hasattr(user_progress, "personalization_data"):
            data = user_progress.personalization_data
            if "environment" in data:
                context.environment_info = data["environment"]
            if "integration" in data:
                context.integration_status = data["integration"]

        return context

    async def _analyze_issue(
        self, context: SupportContext, user_message: Optional[str]
    ) -> IssueType:
        """Analyze the issue based on context and user message"""

        # If no message, infer from context
        if not user_message:
            # Infer issue based on onboarding stage
            if context.onboarding_stage == "environment_detection":
                return IssueType.SETUP_FAILED
            elif context.onboarding_stage == "ai_integration":
                return IssueType.INTEGRATION_FAILED
            elif context.onboarding_stage == "first_capsule":
                return IssueType.CAPSULE_CREATION_FAILED
            else:
                return IssueType.GENERAL_QUESTION

        # Analyze user message
        message_lower = user_message.lower()

        # Keyword-based issue detection
        if any(word in message_lower for word in ["setup", "install", "configure"]):
            return IssueType.SETUP_FAILED
        elif any(word in message_lower for word in ["api key", "key", "token", "auth"]):
            return IssueType.API_KEY_ISSUE
        elif any(
            word in message_lower
            for word in ["connection", "network", "timeout", "connect"]
        ):
            return IssueType.CONNECTION_ERROR
        elif any(
            word in message_lower for word in ["slow", "performance", "lag", "speed"]
        ):
            return IssueType.PERFORMANCE_ISSUE
        elif any(
            word in message_lower
            for word in ["integration", "platform", "openai", "anthropic"]
        ):
            return IssueType.INTEGRATION_FAILED
        elif any(word in message_lower for word in ["capsule", "create", "generation"]):
            return IssueType.CAPSULE_CREATION_FAILED
        elif any(
            word in message_lower
            for word in ["feature", "request", "suggestion", "enhancement"]
        ):
            return IssueType.FEATURE_REQUEST
        else:
            return IssueType.GENERAL_QUESTION

    async def _generate_support_response(
        self,
        issue_type: IssueType,
        context: SupportContext,
        user_message: Optional[str],
    ) -> SupportResponse:
        """Generate targeted support response"""

        if issue_type == IssueType.SETUP_FAILED:
            return await self._handle_setup_issue(context, user_message)
        elif issue_type == IssueType.API_KEY_ISSUE:
            return await self._handle_api_key_issue(context, user_message)
        elif issue_type == IssueType.CONNECTION_ERROR:
            return await self._handle_connection_issue(context, user_message)
        elif issue_type == IssueType.PERFORMANCE_ISSUE:
            return await self._handle_performance_issue(context, user_message)
        elif issue_type == IssueType.INTEGRATION_FAILED:
            return await self._handle_integration_issue(context, user_message)
        elif issue_type == IssueType.CAPSULE_CREATION_FAILED:
            return await self._handle_capsule_issue(context, user_message)
        elif issue_type == IssueType.FEATURE_REQUEST:
            return await self._handle_feature_request(context, user_message)
        else:
            return await self._handle_general_question(context, user_message)

    async def _handle_setup_issue(
        self, context: SupportContext, message: Optional[str]
    ) -> SupportResponse:
        """Handle setup-related issues"""

        # Check common setup issues
        if context.environment_info:
            python_version = context.environment_info.python_version
            if python_version and python_version < "3.8":
                kb_item = self.knowledge_base["setup_issues"]["python_version"]
                return SupportResponse(
                    issue_type=IssueType.SETUP_FAILED,
                    support_level=SupportLevel.GUIDED_HELP,
                    title="Python Version Issue",
                    message=kb_item["solution"],
                    step_by_step_guide=[
                        {"step": i + 1, "description": step}
                        for i, step in enumerate(kb_item["steps"])
                    ],
                    confidence_score=0.9,
                    estimated_resolution_time="5-10 minutes",
                )

        # Generic setup help
        return SupportResponse(
            issue_type=IssueType.SETUP_FAILED,
            support_level=SupportLevel.GUIDED_HELP,
            title="Setup Help",
            message="I'll help you resolve this setup issue. Let's go through the common solutions step by step.",
            immediate_actions=[
                "Check Python version (python --version)",
                "Verify all requirements are installed",
                "Check file permissions",
            ],
            step_by_step_guide=[
                {"step": 1, "description": "Verify Python 3.8+ is installed"},
                {
                    "step": 2,
                    "description": "Install requirements: pip install -r requirements.txt",
                },
                {"step": 3, "description": "Run setup script: python setup.py"},
                {
                    "step": 4,
                    "description": "Test installation: python -c 'import src; print(\"Success\"))'",
                },
            ],
            documentation_links=[
                {"title": "Installation Guide", "url": "/docs/installation"},
                {"title": "Troubleshooting", "url": "/docs/troubleshooting"},
            ],
            confidence_score=0.7,
            estimated_resolution_time="10-15 minutes",
        )

    async def _handle_api_key_issue(
        self, context: SupportContext, message: Optional[str]
    ) -> SupportResponse:
        """Handle API key related issues"""

        # Check which platform might be the issue
        platform = "your AI platform"
        if message and "openai" in message.lower():
            platform = "OpenAI"
        elif message and "anthropic" in message.lower():
            platform = "Anthropic"

        return SupportResponse(
            issue_type=IssueType.API_KEY_ISSUE,
            support_level=SupportLevel.GUIDED_HELP,
            title=f"{platform} API Key Issue",
            message=f"It looks like there's an issue with your {platform} API key. Let me help you fix this.",
            immediate_actions=[
                f"Check if your {platform} API key is set as an environment variable",
                "Verify the API key is valid and not expired",
                "Ensure the key has proper permissions",
            ],
            step_by_step_guide=[
                {
                    "step": 1,
                    "description": f"Get your API key from the {platform} dashboard",
                },
                {
                    "step": 2,
                    "description": "Set environment variable (Linux/Mac): export OPENAI_API_KEY='your-key-here'",
                },
                {
                    "step": 3,
                    "description": "Set environment variable (Windows): set OPENAI_API_KEY=your-key-here",
                },
                {"step": 4, "description": "Restart your terminal/application"},
                {"step": 5, "description": "Test the connection"},
            ],
            documentation_links=[
                {"title": "API Key Setup Guide", "url": "/docs/api-keys"},
                {
                    "title": f"{platform} Documentation",
                    "url": f"https://docs.{platform.lower()}.com",
                },
            ],
            prevention_tips=[
                "Store API keys as environment variables, never in code",
                "Use a .env file for local development",
                "Regularly rotate your API keys for security",
            ],
            confidence_score=0.85,
            estimated_resolution_time="5 minutes",
        )

    async def _handle_connection_issue(
        self, context: SupportContext, message: Optional[str]
    ) -> SupportResponse:
        """Handle connection related issues"""

        return SupportResponse(
            issue_type=IssueType.CONNECTION_ERROR,
            support_level=SupportLevel.GUIDED_HELP,
            title="Connection Issue",
            message="I'll help you diagnose and fix this connection problem.",
            immediate_actions=[
                "Check your internet connection",
                "Test if the AI platform is accessible",
                "Verify firewall settings",
            ],
            step_by_step_guide=[
                {"step": 1, "description": "Test internet: ping google.com"},
                {"step": 2, "description": "Check platform status page"},
                {"step": 3, "description": "Try connecting from a different network"},
                {"step": 4, "description": "Check corporate firewall/proxy settings"},
                {
                    "step": 5,
                    "description": "Contact your network administrator if needed",
                },
            ],
            escalation_available=True,
            escalation_message="If connection issues persist, our technical team can help diagnose network-specific problems.",
            confidence_score=0.7,
            estimated_resolution_time="10-20 minutes",
        )

    async def _handle_performance_issue(
        self, context: SupportContext, message: Optional[str]
    ) -> SupportResponse:
        """Handle performance related issues"""

        return SupportResponse(
            issue_type=IssueType.PERFORMANCE_ISSUE,
            support_level=SupportLevel.SELF_SERVICE,
            title="Performance Optimization",
            message="Let me help you improve system performance.",
            immediate_actions=[
                "Check system resource usage",
                "Close unnecessary applications",
                "Restart the UATP service",
            ],
            step_by_step_guide=[
                {
                    "step": 1,
                    "description": "Open system monitor to check CPU/memory usage",
                },
                {
                    "step": 2,
                    "description": "Close heavy applications if resources are low",
                },
                {"step": 3, "description": "Restart UATP with: python run.py"},
                {"step": 4, "description": "Monitor performance in the dashboard"},
                {
                    "step": 5,
                    "description": "Consider upgrading hardware if issues persist",
                },
            ],
            prevention_tips=[
                "Monitor system resources regularly",
                "Keep only essential applications running",
                "Consider SSD storage for better performance",
            ],
            confidence_score=0.6,
            estimated_resolution_time="5-15 minutes",
        )

    async def _handle_integration_issue(
        self, context: SupportContext, message: Optional[str]
    ) -> SupportResponse:
        """Handle AI platform integration issues"""

        return SupportResponse(
            issue_type=IssueType.INTEGRATION_FAILED,
            support_level=SupportLevel.GUIDED_HELP,
            title="AI Platform Integration Issue",
            message="Let's troubleshoot your AI platform integration step by step.",
            immediate_actions=[
                "Check API key configuration",
                "Test platform connectivity",
                "Verify model availability",
            ],
            step_by_step_guide=[
                {"step": 1, "description": "Verify API key is correctly set"},
                {"step": 2, "description": "Test connection manually"},
                {"step": 3, "description": "Check if the model is available"},
                {"step": 4, "description": "Review platform status page"},
                {"step": 5, "description": "Try with a different model"},
            ],
            documentation_links=[
                {"title": "Integration Guide", "url": "/docs/integrations"},
                {"title": "Supported Platforms", "url": "/docs/platforms"},
            ],
            confidence_score=0.8,
            estimated_resolution_time="10 minutes",
        )

    async def _handle_capsule_issue(
        self, context: SupportContext, message: Optional[str]
    ) -> SupportResponse:
        """Handle capsule creation issues"""

        return SupportResponse(
            issue_type=IssueType.CAPSULE_CREATION_FAILED,
            support_level=SupportLevel.GUIDED_HELP,
            title="Capsule Creation Issue",
            message="I'll help you create your first capsule successfully.",
            immediate_actions=[
                "Check if AI integration is working",
                "Verify you have a valid prompt",
                "Ensure system is properly initialized",
            ],
            step_by_step_guide=[
                {"step": 1, "description": "Test AI integration first"},
                {"step": 2, "description": "Start with a simple prompt"},
                {"step": 3, "description": "Check system logs for errors"},
                {"step": 4, "description": "Try creating capsule through dashboard"},
                {"step": 5, "description": "Contact support if issue persists"},
            ],
            video_tutorials=[
                {
                    "title": "Creating Your First Capsule",
                    "url": "/tutorials/first-capsule",
                }
            ],
            confidence_score=0.75,
            estimated_resolution_time="5-10 minutes",
        )

    async def _handle_feature_request(
        self, context: SupportContext, message: Optional[str]
    ) -> SupportResponse:
        """Handle feature requests"""

        return SupportResponse(
            issue_type=IssueType.FEATURE_REQUEST,
            support_level=SupportLevel.SELF_SERVICE,
            title="Feature Request",
            message="Thank you for your feature suggestion! Here's how you can submit it properly.",
            immediate_actions=[
                "Check if the feature already exists",
                "Review our roadmap",
                "Submit detailed feature request",
            ],
            step_by_step_guide=[
                {"step": 1, "description": "Search existing documentation"},
                {"step": 2, "description": "Check our public roadmap"},
                {"step": 3, "description": "Submit request via our feedback form"},
                {"step": 4, "description": "Join our community for discussions"},
            ],
            documentation_links=[
                {"title": "Feature Roadmap", "url": "/roadmap"},
                {"title": "Community Forum", "url": "/community"},
            ],
            confidence_score=1.0,
            estimated_resolution_time="2 minutes",
        )

    async def _handle_general_question(
        self, context: SupportContext, message: Optional[str]
    ) -> SupportResponse:
        """Handle general questions"""

        return SupportResponse(
            issue_type=IssueType.GENERAL_QUESTION,
            support_level=SupportLevel.SELF_SERVICE,
            title="General Help",
            message="I'm here to help! Here are some resources that might answer your question.",
            immediate_actions=[
                "Check our documentation",
                "Browse frequently asked questions",
                "Join our community forum",
            ],
            documentation_links=[
                {"title": "Getting Started Guide", "url": "/docs/getting-started"},
                {"title": "FAQ", "url": "/docs/faq"},
                {"title": "API Documentation", "url": "/docs/api"},
            ],
            escalation_available=True,
            escalation_message="If you can't find what you're looking for, our support team is here to help!",
            confidence_score=0.5,
            estimated_resolution_time="Variable",
        )

    async def start_troubleshooting_flow(
        self, user_id: str, issue_type: IssueType
    ) -> TroubleshootingFlow:
        """Start an interactive troubleshooting flow"""

        flow_id = f"{user_id}_{issue_type.value}_{int(datetime.now().timestamp())}"

        # Create troubleshooting steps based on issue type
        if issue_type == IssueType.SETUP_FAILED:
            steps = [
                {
                    "id": 1,
                    "title": "Check Python Version",
                    "description": "Verify Python 3.8+ is installed",
                    "action": "python --version",
                    "expected": "Python 3.8 or higher",
                },
                {
                    "id": 2,
                    "title": "Install Dependencies",
                    "description": "Install required packages",
                    "action": "pip install -r requirements.txt",
                    "expected": "All packages installed successfully",
                },
                {
                    "id": 3,
                    "title": "Test Installation",
                    "description": "Verify UATP can be imported",
                    "action": "python -c 'import src; print(\"Success\")'",
                    "expected": "Success message printed",
                },
            ]
        else:
            # Generic troubleshooting steps
            steps = [
                {
                    "id": 1,
                    "title": "Identify Issue",
                    "description": "Gather information about the problem",
                    "action": "Describe the issue in detail",
                    "expected": "Clear problem description",
                },
                {
                    "id": 2,
                    "title": "Check System Status",
                    "description": "Verify system health",
                    "action": "Check system dashboard",
                    "expected": "System appears healthy",
                },
            ]

        flow = TroubleshootingFlow(
            flow_id=flow_id,
            title=f"Troubleshooting {issue_type.value.replace('_', ' ').title()}",
            description=f"Step-by-step troubleshooting for {issue_type.value}",
            steps=steps,
        )

        self.troubleshooting_flows[flow_id] = flow
        return flow

    async def continue_troubleshooting_flow(
        self, flow_id: str, step_result: Dict[str, Any]
    ) -> TroubleshootingFlow:
        """Continue troubleshooting flow with step result"""

        if flow_id not in self.troubleshooting_flows:
            raise ValueError(f"Troubleshooting flow {flow_id} not found")

        flow = self.troubleshooting_flows[flow_id]

        # Process current step result
        current_step = flow.steps[flow.current_step]
        current_step["result"] = step_result
        current_step["completed"] = True

        # Move to next step
        flow.current_step += 1

        # Check if flow is complete
        if flow.current_step >= len(flow.steps):
            flow.completed = True
            flow.success = step_result.get("success", False)

        return flow

    async def get_proactive_suggestions(self, context: SupportContext) -> List[str]:
        """Get proactive suggestions based on user context"""

        suggestions = []

        # Suggestions based on user type
        if context.user_type == "developer":
            suggestions.extend(
                [
                    "Explore the API documentation for advanced integration",
                    "Set up automated testing for your capsules",
                    "Configure development environment with debug logging",
                ]
            )
        elif context.user_type == "business_user":
            suggestions.extend(
                [
                    "Set up monitoring dashboard for business metrics",
                    "Configure cost tracking for AI usage",
                    "Explore reporting features for stakeholders",
                ]
            )

        # Suggestions based on onboarding stage
        if context.onboarding_stage == "success_milestone":
            suggestions.extend(
                [
                    "Explore advanced features like governance",
                    "Set up automated attribution tracking",
                    "Join the UATP community for tips and best practices",
                ]
            )

        return suggestions

    async def get_support_metrics(self) -> Dict[str, Any]:
        """Get support system metrics"""

        return {
            "active_sessions": len(self.active_support_sessions),
            "troubleshooting_flows": len(self.troubleshooting_flows),
            "knowledge_base_items": sum(
                len(category) for category in self.knowledge_base.values()
            ),
            "recent_issues": [
                session["issue_type"].value
                for session in self.active_support_sessions.values()
            ],
        }
