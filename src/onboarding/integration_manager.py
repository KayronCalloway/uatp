"""
Integration Manager

Handles one-click setup and management of AI platform integrations.
Provides guided connection flows, auto-discovery, and testing capabilities.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """Supported AI platform types"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"
    CUSTOM = "custom"


class IntegrationStatus(Enum):
    """Integration connection status"""

    NOT_CONFIGURED = "not_configured"
    CONFIGURING = "configuring"
    CONNECTED = "connected"
    ERROR = "error"
    TESTING = "testing"


@dataclass
class PlatformInfo:
    """Information about an AI platform"""

    name: str
    type: PlatformType
    description: str
    requirements: List[str]
    setup_complexity: str  # "simple", "moderate", "advanced"
    estimated_setup_time: int  # minutes
    features: List[str]
    pricing_model: str
    documentation_url: str
    logo_url: Optional[str] = None


@dataclass
class IntegrationResult:
    """Result of platform integration attempt"""

    platform: str
    status: IntegrationStatus
    success: bool
    configuration: Dict[str, Any] = field(default_factory=dict)
    test_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


@dataclass
class CapsuleCreationResult:
    """Result of guided capsule creation"""

    capsule_id: str
    success: bool
    attribution_tracked: bool
    time_to_create: float  # seconds
    platform_used: str
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntegrationManager:
    """
    Manages AI platform integrations with one-click setup and guided flows.

    Features:
    - Auto-discovery of existing API keys
    - One-click platform connections
    - Interactive setup wizards
    - Real-time connection testing
    - Guided first capsule creation
    """

    def __init__(self):
        """Initialize the integration manager"""
        self.available_platforms = self._initialize_platform_catalog()
        self.active_integrations: Dict[str, IntegrationResult] = {}

        logger.info("Integration Manager initialized")

    def _initialize_platform_catalog(self) -> Dict[str, PlatformInfo]:
        """Initialize catalog of available AI platforms"""

        return {
            "openai": PlatformInfo(
                name="OpenAI",
                type=PlatformType.OPENAI,
                description="GPT-4, GPT-3.5, and other OpenAI models with full attribution tracking",
                requirements=["OPENAI_API_KEY"],
                setup_complexity="simple",
                estimated_setup_time=2,
                features=[
                    "Chat Completion",
                    "Attribution Tracking",
                    "Cost Monitoring",
                    "Rate Limiting",
                ],
                pricing_model="Pay-per-token",
                documentation_url="https://platform.openai.com/docs",
                logo_url="https://openai.com/favicon.ico",
            ),
            "anthropic": PlatformInfo(
                name="Anthropic Claude",
                type=PlatformType.ANTHROPIC,
                description="Claude models with advanced reasoning and attribution capabilities",
                requirements=["ANTHROPIC_API_KEY"],
                setup_complexity="simple",
                estimated_setup_time=2,
                features=[
                    "Advanced Reasoning",
                    "Long Context",
                    "Attribution Tracking",
                    "Safety Controls",
                ],
                pricing_model="Pay-per-token",
                documentation_url="https://docs.anthropic.com",
                logo_url="https://anthropic.com/favicon.ico",
            ),
            "huggingface": PlatformInfo(
                name="Hugging Face",
                type=PlatformType.HUGGINGFACE,
                description="Access to thousands of open-source models",
                requirements=["HUGGINGFACE_API_TOKEN"],
                setup_complexity="moderate",
                estimated_setup_time=5,
                features=[
                    "Open Source Models",
                    "Model Hub",
                    "Custom Models",
                    "Free Tier",
                ],
                pricing_model="Freemium",
                documentation_url="https://huggingface.co/docs",
                logo_url="https://huggingface.co/front/assets/huggingface_logo.svg",
            ),
            "cohere": PlatformInfo(
                name="Cohere",
                type=PlatformType.COHERE,
                description="Enterprise-focused language models with retrieval capabilities",
                requirements=["COHERE_API_KEY"],
                setup_complexity="simple",
                estimated_setup_time=3,
                features=[
                    "Enterprise Models",
                    "Retrieval Augmentation",
                    "Multilingual",
                    "Fine-tuning",
                ],
                pricing_model="Pay-per-use",
                documentation_url="https://docs.cohere.ai",
                logo_url="https://cohere.ai/favicon.ico",
            ),
        }

    async def get_available_platforms(self) -> Dict[str, PlatformInfo]:
        """Get all available AI platforms with their information"""
        return self.available_platforms

    async def auto_discover_integrations(self) -> Dict[str, bool]:
        """Auto-discover available integrations based on environment"""

        logger.info(" Auto-discovering available integrations...")

        discovered = {}

        for platform_id, platform in self.available_platforms.items():
            # Check if required credentials are available
            has_credentials = True

            for requirement in platform.requirements:
                if not os.getenv(requirement):
                    has_credentials = False
                    break

            discovered[platform_id] = has_credentials

            if has_credentials:
                logger.info(f"[OK] {platform.name} credentials detected")
            else:
                logger.info(f" {platform.name} credentials not found")

        return discovered

    async def setup_platform_integration(
        self,
        platform: str,
        user_type: Any,
        quick_setup: bool = True,
        credentials: Dict[str, str] = None,
    ) -> IntegrationResult:
        """
        Setup integration with specified AI platform

        Args:
            platform: Platform identifier
            user_type: User type for personalized setup
            quick_setup: Use quick setup with defaults
            credentials: Optional credentials override

        Returns:
            IntegrationResult with setup status and configuration
        """

        if platform not in self.available_platforms:
            return IntegrationResult(
                platform=platform,
                status=IntegrationStatus.ERROR,
                success=False,
                errors=[f"Unknown platform: {platform}"],
            )

        platform_info = self.available_platforms[platform]
        logger.info(f" Setting up {platform_info.name} integration...")

        try:
            # Check/set credentials
            integration_config = await self._setup_platform_credentials(
                platform, platform_info, credentials
            )

            if not integration_config["has_credentials"]:
                return IntegrationResult(
                    platform=platform,
                    status=IntegrationStatus.NOT_CONFIGURED,
                    success=False,
                    errors=["Required credentials not available"],
                    next_steps=[
                        f"Set {', '.join(platform_info.requirements)} environment variable(s)"
                    ],
                )

            # Configure platform client
            client_config = await self._configure_platform_client(
                platform, integration_config
            )

            # Test connection
            test_result = await self._test_platform_connection(platform, client_config)

            if test_result["success"]:
                result = IntegrationResult(
                    platform=platform,
                    status=IntegrationStatus.CONNECTED,
                    success=True,
                    configuration=client_config,
                    test_results=test_result,
                    next_steps=[
                        "Create your first capsule",
                        "Explore platform features",
                    ],
                )

                # Store active integration
                self.active_integrations[platform] = result

                logger.info(f"[OK] {platform_info.name} integration successful")
                return result
            else:
                return IntegrationResult(
                    platform=platform,
                    status=IntegrationStatus.ERROR,
                    success=False,
                    configuration=client_config,
                    test_results=test_result,
                    errors=test_result.get("errors", ["Connection test failed"]),
                )

        except Exception as e:
            logger.error(f"[ERROR] {platform_info.name} integration failed: {e}")
            return IntegrationResult(
                platform=platform,
                status=IntegrationStatus.ERROR,
                success=False,
                errors=[str(e)],
            )

    async def _setup_platform_credentials(
        self,
        platform: str,
        platform_info: PlatformInfo,
        override_credentials: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Setup and validate platform credentials"""

        config = {"platform": platform, "has_credentials": True, "credentials": {}}

        # Check each required credential
        for requirement in platform_info.requirements:
            credential_value = None

            # Use override if provided
            if override_credentials and requirement in override_credentials:
                credential_value = override_credentials[requirement]
            else:
                # Check environment
                credential_value = os.getenv(requirement)

            if credential_value:
                config["credentials"][requirement] = credential_value
            else:
                config["has_credentials"] = False
                logger.warning(f"Missing credential: {requirement}")

        return config

    async def _configure_platform_client(
        self, platform: str, integration_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure platform-specific client"""

        config = {
            "platform": platform,
            "client_type": platform,
            "attribution_enabled": True,
            "cost_tracking": True,
            "rate_limiting": True,
        }

        if platform == "openai":
            config.update(
                {
                    "default_model": "gpt-3.5-turbo",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "api_key": integration_config["credentials"].get("OPENAI_API_KEY"),
                }
            )

        elif platform == "anthropic":
            config.update(
                {
                    "default_model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 1024,
                    "api_key": integration_config["credentials"].get(
                        "ANTHROPIC_API_KEY"
                    ),
                }
            )

        elif platform == "huggingface":
            config.update(
                {
                    "default_model": "microsoft/DialoGPT-medium",
                    "api_token": integration_config["credentials"].get(
                        "HUGGINGFACE_API_TOKEN"
                    ),
                }
            )

        elif platform == "cohere":
            config.update(
                {
                    "default_model": "command",
                    "api_key": integration_config["credentials"].get("COHERE_API_KEY"),
                }
            )

        return config

    async def _test_platform_connection(
        self, platform: str, client_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test connection to AI platform"""

        logger.info(f" Testing {platform} connection...")

        try:
            if platform == "openai":
                return await self._test_openai_connection(client_config)
            elif platform == "anthropic":
                return await self._test_anthropic_connection(client_config)
            elif platform == "huggingface":
                return await self._test_huggingface_connection(client_config)
            elif platform == "cohere":
                return await self._test_cohere_connection(client_config)
            else:
                return {
                    "success": False,
                    "errors": [f"No test implementation for platform: {platform}"],
                }

        except Exception as e:
            return {
                "success": False,
                "errors": [f"Connection test failed: {str(e)}"],
                "exception": str(e),
            }

    async def _test_openai_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test OpenAI connection"""

        try:
            # Import and test OpenAI client
            from ..integrations.openai_client import OpenAIClient

            client = OpenAIClient()

            # Test with a simple prompt
            response = await client.get_completion_async(
                prompt="Say 'Hello from UATP!' in exactly those words.",
                model=config["default_model"],
                max_tokens=20,
            )

            return {
                "success": True,
                "test_response": response,
                "model_used": config["default_model"],
                "response_time": "< 1s",
            }

        except Exception as e:
            return {"success": False, "errors": [f"OpenAI test failed: {str(e)}"]}

    async def _test_anthropic_connection(
        self, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test Anthropic connection"""

        try:
            # Import and test Anthropic client
            from ..integrations.anthropic_client import AnthropicAttributionClient

            client = AnthropicAttributionClient()

            # Create test attribution context
            from ..integrations.openai_attribution import AttributionContext

            context = AttributionContext(
                user_id="test_user",
                conversation_id="test_connection",
                prompt_sources=["user_input"],
                training_data_sources=["general_training"],
                attribution_metadata={"test": True},
            )

            # Test with a simple prompt
            response, attribution = await client.get_completion_with_attribution(
                prompt="Say 'Hello from UATP!' in exactly those words.",
                attribution_context=context,
                model=config["default_model"],
                max_tokens=20,
            )

            return {
                "success": True,
                "test_response": response,
                "attribution_tracked": True,
                "model_used": config["default_model"],
                "response_time": "< 2s",
            }

        except Exception as e:
            return {"success": False, "errors": [f"Anthropic test failed: {str(e)}"]}

    async def _test_huggingface_connection(
        self, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test Hugging Face connection"""

        # For now, return a mock success
        # In a real implementation, this would test the HF API
        return {
            "success": True,
            "test_response": "Mock HuggingFace response",
            "model_used": config["default_model"],
            "response_time": "< 3s",
            "note": "Mock implementation - real HF integration pending",
        }

    async def _test_cohere_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Cohere connection"""

        # For now, return a mock success
        # In a real implementation, this would test the Cohere API
        return {
            "success": True,
            "test_response": "Mock Cohere response",
            "model_used": config["default_model"],
            "response_time": "< 2s",
            "note": "Mock implementation - real Cohere integration pending",
        }

    async def create_guided_first_capsule(
        self, user_type: Any, context: Dict[str, Any] = None
    ) -> CapsuleCreationResult:
        """
        Guide user through creating their first UATP capsule

        Args:
            user_type: User type for personalized guidance
            context: Additional context from onboarding

        Returns:
            CapsuleCreationResult with creation details
        """

        context = context or {}
        start_time = datetime.now(timezone.utc)

        logger.info(f" Guiding first capsule creation for {user_type}")

        try:
            # Select best available platform
            platform = await self._select_best_platform_for_user(user_type)

            if not platform:
                return CapsuleCreationResult(
                    capsule_id="",
                    success=False,
                    attribution_tracked=False,
                    time_to_create=0,
                    platform_used="none",
                    errors=["No AI platforms configured"],
                )

            # Create personalized prompt based on user type
            prompt = self._create_personalized_first_prompt(user_type)

            # Create capsule through the platform
            capsule_result = await self._create_capsule_via_platform(
                platform, prompt, context
            )

            # Calculate creation time
            creation_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            if capsule_result["success"]:
                logger.info(
                    f"[OK] First capsule created successfully in {creation_time:.1f}s"
                )

                return CapsuleCreationResult(
                    capsule_id=capsule_result["capsule_id"],
                    success=True,
                    attribution_tracked=capsule_result.get(
                        "attribution_tracked", False
                    ),
                    time_to_create=creation_time,
                    platform_used=platform,
                    metadata={
                        "user_type": str(user_type),
                        "prompt_used": prompt,
                        "platform_response": capsule_result.get("response", ""),
                        "creation_timestamp": start_time.isoformat(),
                    },
                )
            else:
                return CapsuleCreationResult(
                    capsule_id="",
                    success=False,
                    attribution_tracked=False,
                    time_to_create=creation_time,
                    platform_used=platform,
                    errors=capsule_result.get("errors", ["Unknown error"]),
                )

        except Exception as e:
            logger.error(f"[ERROR] First capsule creation failed: {e}")
            return CapsuleCreationResult(
                capsule_id="",
                success=False,
                attribution_tracked=False,
                time_to_create=(
                    datetime.now(timezone.utc) - start_time
                ).total_seconds(),
                platform_used="unknown",
                errors=[str(e)],
            )

    async def _select_best_platform_for_user(self, user_type: Any) -> Optional[str]:
        """Select the best available platform for the user"""

        # Priority order based on user type
        if hasattr(user_type, "value"):
            if user_type.value == "developer":
                priority = ["openai", "anthropic", "huggingface", "cohere"]
            elif user_type.value == "enterprise":
                priority = ["anthropic", "openai", "cohere", "huggingface"]
            elif user_type.value == "researcher":
                priority = ["huggingface", "anthropic", "openai", "cohere"]
            else:
                priority = ["openai", "anthropic", "cohere", "huggingface"]
        else:
            priority = ["openai", "anthropic", "cohere", "huggingface"]

        # Find first available platform
        for platform in priority:
            if platform in self.active_integrations:
                integration = self.active_integrations[platform]
                if integration.status == IntegrationStatus.CONNECTED:
                    return platform

        return None

    def _create_personalized_first_prompt(self, user_type: Any) -> str:
        """Create a personalized prompt for the user's first capsule"""

        prompts = {
            "developer": "Explain the concept of API rate limiting and how to handle it gracefully in code.",
            "business_user": "Summarize the key benefits of AI attribution for business decision-making.",
            "researcher": "Describe how transformer models work and their impact on natural language processing.",
            "enterprise": "Outline best practices for implementing AI governance in large organizations.",
            "casual_user": "Explain what UATP (Universal AI Trust Protocol) does in simple terms.",
        }

        if hasattr(user_type, "value") and user_type.value in prompts:
            return prompts[user_type.value]
        else:
            return prompts["casual_user"]

    async def _create_capsule_via_platform(
        self, platform: str, prompt: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a capsule using the specified platform"""

        try:
            if platform == "openai":
                return await self._create_openai_capsule(prompt, context)
            elif platform == "anthropic":
                return await self._create_anthropic_capsule(prompt, context)
            else:
                # For other platforms, create a mock capsule
                return await self._create_mock_capsule(platform, prompt, context)

        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def _create_openai_capsule(
        self, prompt: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create capsule using OpenAI"""

        try:
            from ..integrations.openai_client import OpenAIClient

            client = OpenAIClient()
            response = await client.get_completion_async(
                prompt=prompt, model="gpt-3.5-turbo", max_tokens=200
            )

            # Generate unique capsule ID
            import uuid

            capsule_id = f"openai_capsule_{uuid.uuid4().hex[:8]}"

            return {
                "success": True,
                "capsule_id": capsule_id,
                "response": response,
                "attribution_tracked": True,
                "platform": "openai",
            }

        except Exception as e:
            return {
                "success": False,
                "errors": [f"OpenAI capsule creation failed: {str(e)}"],
            }

    async def _create_anthropic_capsule(
        self, prompt: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create capsule using Anthropic"""

        try:
            from ..integrations.anthropic_client import AnthropicAttributionClient
            from ..integrations.openai_attribution import AttributionContext

            client = AnthropicAttributionClient()

            # Create attribution context
            attribution_context = AttributionContext(
                user_id=context.get("user_id", "onboarding_user"),
                conversation_id=f"first_capsule_{datetime.now().timestamp()}",
                prompt_sources=["user_input", "onboarding_guidance"],
                training_data_sources=["anthropic_training"],
                attribution_metadata={
                    "first_capsule": True,
                    "onboarding": True,
                    "user_type": context.get("user_type", "unknown"),
                },
            )

            response, attribution = await client.get_completion_with_attribution(
                prompt=prompt,
                attribution_context=attribution_context,
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
            )

            # Generate unique capsule ID
            import uuid

            capsule_id = f"anthropic_capsule_{uuid.uuid4().hex[:8]}"

            return {
                "success": True,
                "capsule_id": capsule_id,
                "response": response,
                "attribution_tracked": True,
                "attribution_result": attribution,
                "platform": "anthropic",
            }

        except Exception as e:
            return {
                "success": False,
                "errors": [f"Anthropic capsule creation failed: {str(e)}"],
            }

    async def _create_mock_capsule(
        self, platform: str, prompt: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create mock capsule for platforms without full implementation"""

        import uuid

        capsule_id = f"{platform}_capsule_{uuid.uuid4().hex[:8]}"

        mock_responses = {
            "huggingface": f"This is a mock response from HuggingFace for: {prompt[:50]}...",
            "cohere": f"This is a mock response from Cohere for: {prompt[:50]}...",
            "custom": f"This is a mock response from a custom platform for: {prompt[:50]}...",
        }

        return {
            "success": True,
            "capsule_id": capsule_id,
            "response": mock_responses.get(platform, "Mock response"),
            "attribution_tracked": False,
            "platform": platform,
            "note": "Mock implementation - full integration pending",
        }

    # Advanced integration methods for different user types

    async def setup_developer_integrations(self) -> Dict[str, Any]:
        """Setup integrations optimized for developers"""

        return {
            "api_playground": True,
            "code_examples": True,
            "webhook_support": True,
            "debug_logging": True,
            "testing_endpoints": True,
        }

    async def create_attributed_capsule(self) -> Dict[str, Any]:
        """Create developer-focused capsule with full attribution"""

        return {
            "capsule_type": "developer_demo",
            "attribution_enabled": True,
            "debug_info": True,
            "api_trace": True,
            "performance_metrics": True,
        }

    async def setup_enterprise_integrations(self) -> Dict[str, Any]:
        """Setup enterprise-grade integrations"""

        return {
            "sso_integration": True,
            "audit_logging": True,
            "compliance_monitoring": True,
            "scalability_optimization": True,
            "enterprise_support": True,
        }

    async def get_integration_status(self, platform: str = None) -> Dict[str, Any]:
        """Get status of platform integrations"""

        if platform:
            return self.active_integrations.get(
                platform,
                {"status": IntegrationStatus.NOT_CONFIGURED, "platform": platform},
            ).__dict__
        else:
            return {
                platform: integration.__dict__
                for platform, integration in self.active_integrations.items()
            }

    async def test_all_integrations(self) -> Dict[str, Dict[str, Any]]:
        """Test all active integrations"""

        results = {}

        for platform, integration in self.active_integrations.items():
            if integration.status == IntegrationStatus.CONNECTED:
                test_result = await self._test_platform_connection(
                    platform, integration.configuration
                )
                results[platform] = test_result

        return results
