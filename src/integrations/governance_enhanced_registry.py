"""
Governance-Enhanced LLM Registry Module for UATP Capsule Engine.

This module extends the advanced LLM registry to include governance capabilities,
allowing AI reasoning traces to be validated against governance policies and
enabling governance-aware model selection.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.capsule_schema import ReasoningStep
from src.governance.advanced_governance import (
    GovernanceAction,
    ProposalType,
    VotingMethod,
    governance_engine,
)

# Import from existing modules
from src.integrations.advanced_llm_registry import (
    LLMOutput,
    LLMProviderAdapter,
    create_and_sign_reasoning_capsule,
)

logger = logging.getLogger(__name__)


class GovernancePolicyViolation(Exception):
    """Exception raised when an LLM request violates a governance policy."""

    pass


class ModelAccessPolicy:
    """Represents an access policy for a specific LLM model."""

    def __init__(
        self,
        model_id: str,
        required_authorization_level: int = 0,
        content_policies: List[Dict[str, Any]] = None,
        usage_limits: Dict[str, Any] = None,
        cost_limits: Dict[str, Any] = None,
    ):
        self.model_id = model_id
        self.required_authorization_level = required_authorization_level
        self.content_policies = content_policies or []
        self.usage_limits = usage_limits or {
            "tokens_per_day": 1000000,
            "requests_per_minute": 60,
        }
        self.cost_limits = cost_limits or {
            "max_cost_per_request": 10.0,
            "max_daily_cost": 100.0,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary."""
        return {
            "model_id": self.model_id,
            "required_authorization_level": self.required_authorization_level,
            "content_policies": self.content_policies,
            "usage_limits": self.usage_limits,
            "cost_limits": self.cost_limits,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelAccessPolicy":
        """Create policy from dictionary."""
        return cls(
            model_id=data["model_id"],
            required_authorization_level=data.get("required_authorization_level", 0),
            content_policies=data.get("content_policies"),
            usage_limits=data.get("usage_limits"),
            cost_limits=data.get("cost_limits"),
        )


class GovernanceEnabledLLMRegistry:
    """
    Enhanced LLM Registry with governance capabilities.

    This class extends the functionality of the advanced LLM registry with:
    - Model access governance
    - Content policy enforcement
    - Governance-aware model selection
    - Auditable reasoning trace validation
    - Integration with the UATP governance engine
    """

    def __init__(self):
        self.providers: Dict[str, LLMProviderAdapter] = {}
        self.model_policies: Dict[str, ModelAccessPolicy] = {}
        self.usage_statistics: Dict[str, Dict[str, Any]] = {}
        self.authorization_levels: Dict[str, int] = {}  # user_id -> level

        # Default models by capability
        self.default_models = {
            "general": None,
            "code": None,
            "safety": None,
            "creative": None,
        }

        # Load governance policies from config (if available)
        self._load_governance_policies()

    def _load_governance_policies(self) -> None:
        """Load governance policies from configuration files."""
        try:
            policy_path = os.environ.get(
                "UATP_POLICY_PATH",
                os.path.join(
                    os.path.dirname(__file__), "../../config/model_policies.json"
                ),
            )
            if os.path.exists(policy_path):
                with open(policy_path) as f:
                    policies_data = json.load(f)

                for policy_data in policies_data.get("model_policies", []):
                    policy = ModelAccessPolicy.from_dict(policy_data)
                    self.model_policies[policy.model_id] = policy

                self.default_models.update(policies_data.get("default_models", {}))
                logger.info(f"Loaded {len(self.model_policies)} model policies")
            else:
                logger.warning(f"Policy file not found: {policy_path}")
        except Exception as e:
            logger.error(f"Failed to load governance policies: {e}")

    def register_provider(self, provider: LLMProviderAdapter) -> None:
        """Register a new LLM provider adapter."""
        self.providers[provider.provider_id] = provider
        logger.info(f"Registered provider: {provider.provider_id}")

        # Initialize usage statistics for this provider
        if provider.provider_id not in self.usage_statistics:
            self.usage_statistics[provider.provider_id] = {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "models": {},
            }

    def get_model_policy(self, model_id: str) -> Optional[ModelAccessPolicy]:
        """Get policy for a specific model."""
        # Try exact match
        if model_id in self.model_policies:
            return self.model_policies[model_id]

        # Try provider-level policy (using provider prefix)
        provider_id = model_id.split(":")[0] if ":" in model_id else None
        if provider_id and f"{provider_id}:*" in self.model_policies:
            return self.model_policies[f"{provider_id}:*"]

        # No specific policy found, return None
        return None

    def can_access_model(
        self, model_id: str, user_id: str, estimated_cost: float = 0.0
    ) -> Tuple[bool, str]:
        """Check if user can access the specified model."""
        policy = self.get_model_policy(model_id)
        if not policy:
            return True, "No policy restrictions"

        # Check authorization level
        user_auth_level = self.authorization_levels.get(user_id, 0)
        if user_auth_level < policy.required_authorization_level:
            return (
                False,
                f"Insufficient authorization level ({user_auth_level} < {policy.required_authorization_level})",
            )

        # Check cost limits
        if estimated_cost > policy.cost_limits.get(
            "max_cost_per_request", float("inf")
        ):
            return (
                False,
                f"Cost exceeds per-request limit ({estimated_cost} > {policy.cost_limits.get('max_cost_per_request')})",
            )

        # Check daily cost and usage (simplified)
        model_stats = (
            self.usage_statistics.get(model_id.split(":")[0], {})
            .get("models", {})
            .get(model_id, {})
        )
        daily_cost = model_stats.get("daily_cost", 0.0)
        daily_tokens = model_stats.get("daily_tokens", 0)

        if daily_cost + estimated_cost > policy.cost_limits.get(
            "max_daily_cost", float("inf")
        ):
            return False, "Daily cost limit would be exceeded"

        if daily_tokens > policy.usage_limits.get("tokens_per_day", float("inf")):
            return False, "Daily token limit exceeded"

        return True, "Access granted"

    async def select_model_for_task(
        self,
        task_type: str,
        user_id: str,
        context_length: int = 0,
        preference: str = None,
    ) -> str:
        """
        Select the best model for a specific task based on governance policies.

        Args:
            task_type: Type of task (e.g., 'general', 'code', 'safety')
            user_id: ID of the user making the request
            context_length: Length of the input context
            preference: Preferred model or provider (optional)

        Returns:
            model_id: ID of the selected model
        """
        # If user has a specific preference and has access, use it
        if preference:
            can_access, _ = self.can_access_model(preference, user_id)
            if can_access:
                return preference

        # Use task-specific default if available
        if task_type in self.default_models and self.default_models[task_type]:
            default_model = self.default_models[task_type]
            can_access, _ = self.can_access_model(default_model, user_id)
            if can_access:
                return default_model

        # Fallback: Find any accessible model from all providers
        available_models = []
        for provider_id, provider in self.providers.items():
            models = await provider.list_models()
            for model in models:
                model_id = f"{provider_id}:{model}"
                can_access, _ = self.can_access_model(model_id, user_id)
                if can_access:
                    available_models.append(model_id)

        if available_models:
            # Simple heuristic: pick the first available model
            # Could be enhanced with more sophisticated selection logic
            return available_models[0]

        raise GovernancePolicyViolation(
            "No accessible models available for this user and task"
        )

    async def generate_with_governance(
        self,
        model_id: str,
        prompt: str,
        user_id: str,
        system_prompt: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> LLMOutput:
        """
        Generate text from an LLM with governance checks.

        This performs the following governance functions:
        1. Checks if the user can access the model
        2. Validates the request against content policies
        3. Records usage for audit purposes
        4. Updates governance statistics
        """
        # Check access permissions
        can_access, message = self.can_access_model(model_id, user_id)
        if not can_access:
            raise GovernancePolicyViolation(f"Access denied: {message}")

        # Split model_id into provider and model parts
        if ":" not in model_id:
            raise ValueError(
                f"Invalid model_id format: {model_id}. Expected format: provider:model"
            )

        provider_id, model_name = model_id.split(":", 1)

        # Get provider
        if provider_id not in self.providers:
            raise ValueError(f"Provider not registered: {provider_id}")

        provider = self.providers[provider_id]

        # Generate with the provider
        result = await provider.generate(
            model=model_name,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Augment with governance metadata
        result.metadata["governance"] = {
            "user_id": user_id,
            "authorized_by": "governance_registry",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "policy_version": "1.0",
        }

        # Record usage statistics
        self._update_usage_stats(provider_id, model_name, result)

        # Create governance audit record
        self._create_governance_audit(user_id, model_id, result)

        return result

    def _update_usage_stats(
        self, provider_id: str, model_name: str, result: LLMOutput
    ) -> None:
        """Update usage statistics for billing and governance."""

        # Update provider-level stats
        if provider_id in self.usage_statistics:
            stats = self.usage_statistics[provider_id]
            stats["total_requests"] += 1
            stats["total_tokens"] += result.total_tokens
            stats["total_cost"] += result.cost

            # Update model-level stats
            if model_name not in stats["models"]:
                stats["models"][model_name] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0,
                    "daily_tokens": 0,
                    "daily_cost": 0.0,
                    "last_reset": datetime.now(timezone.utc).isoformat(),
                }

            model_stats = stats["models"][model_name]
            model_stats["requests"] += 1
            model_stats["tokens"] += result.total_tokens
            model_stats["cost"] += result.cost
            model_stats["daily_tokens"] += result.total_tokens
            model_stats["daily_cost"] += result.cost

    def _create_governance_audit(
        self, user_id: str, model_id: str, result: LLMOutput
    ) -> None:
        """Create audit record for governance tracking."""
        # Create a governance action record
        action = GovernanceAction(
            action_id=str(uuid.uuid4()),
            proposal_id="system_authorized",  # System-authorized action
            action_type="llm_generation",
            executor_id=user_id,
            executed_at=datetime.now(timezone.utc),
            success=True,
            result={
                "model_id": model_id,
                "tokens": result.total_tokens,
                "cost": result.cost,
                "trace_id": result.trace_id,
            },
            metadata={
                "content_length": len(result.content),
                "governance_version": "1.0",
            },
        )

        # Add to governance engine
        if hasattr(governance_engine, "executed_actions"):
            governance_engine.executed_actions[action.action_id] = action

    async def create_governance_proposal_for_model(
        self,
        model_id: str,
        user_id: str,
        request_type: str,  # e.g., "access_increase", "limit_change"
        justification: str,
        proposed_changes: Dict[str, Any],
    ) -> str:
        """
        Create a governance proposal to modify model access policies.

        Returns:
            proposal_id: The ID of the created proposal
        """
        # Check if user is registered as stakeholder
        if user_id not in governance_engine.stakeholders:
            # Register with minimal stake for proposal creation
            governance_engine.register_stakeholder(
                stakeholder_id=user_id,
                initial_stake=governance_engine.governance_parameters.get(
                    "min_stake_to_propose", 1000.0
                ),
            )

        # Format proposal description
        description = f"""
        Model Access Policy Change Request
        ---------------------------------
        Model: {model_id}
        Requested by: {user_id}
        Request type: {request_type}

        Justification:
        {justification}

        Proposed Changes:
        {json.dumps(proposed_changes, indent=2)}
        """

        # Create governance proposal
        proposal_id = governance_engine.create_proposal(
            title=f"Model Policy Change: {model_id} - {request_type}",
            description=description,
            proposal_type=ProposalType.PARAMETER_UPDATE,
            proposer_id=user_id,
            voting_method=VotingMethod.SIMPLE_MAJORITY,
            execution_data={
                "parameter_name": f"model_policy.{model_id.replace(':', '_')}",
                "new_value": proposed_changes,
            },
        )

        return proposal_id

    async def create_and_sign_governance_reasoning_capsule(
        self,
        reasoning_steps: List[ReasoningStep],
        user_id: str,
        signing_key_hex: str,
        model_id: str,
        governance_metadata: Dict[str, Any] = None,
    ) -> Dict:
        """
        Create a reasoning trace capsule with governance attestations.

        This extends the standard reasoning capsule with additional governance
        metadata and policy validation attestations.
        """
        # Create base reasoning capsule
        capsule = create_and_sign_reasoning_capsule(
            reasoning_steps=reasoning_steps,
            signer_name=f"UATP-{user_id}",
            signing_key_hex=signing_key_hex,
        )

        # Add governance metadata to capsule
        governance_data = governance_metadata or {}
        governance_data.update(
            {
                "governance_version": "1.0",
                "policy_validated": True,
                "model_id": model_id,
                "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                "authorized_by": "governance_registry",
            }
        )

        # Check if metadata already exists, create if not
        if (
            not hasattr(capsule.reasoning_trace, "metadata")
            or capsule.reasoning_trace.metadata is None
        ):
            capsule.reasoning_trace.metadata = {}

        # Add governance data to metadata
        capsule.reasoning_trace.metadata["governance"] = governance_data

        # Return updated capsule as dict for easy serialization
        return capsule.model_dump()

    def reset_daily_limits(self) -> None:
        """Reset daily usage limits for all models."""
        now = datetime.now(timezone.utc).isoformat()

        for _provider_id, stats in self.usage_statistics.items():
            for _model_name, model_stats in stats.get("models", {}).items():
                model_stats["daily_tokens"] = 0
                model_stats["daily_cost"] = 0.0
                model_stats["last_reset"] = now

        logger.info("Daily usage limits reset")


# Create a global instance for easy import
governance_registry = GovernanceEnabledLLMRegistry()


async def demo_governance_enhanced_registry():
    """Demonstrate the governance-enhanced registry."""
    from src.integrations.advanced_llm_registry import MockOpenAIAdapter

    # Register a mock provider
    mock_provider = MockOpenAIAdapter()
    governance_registry.register_provider(mock_provider)

    # Set authorization levels
    governance_registry.authorization_levels = {"user1": 1, "user2": 2, "admin": 10}

    # Set model policies
    governance_registry.model_policies = {
        "mock_openai:gpt-4-mock": ModelAccessPolicy(
            model_id="mock_openai:gpt-4-mock",
            required_authorization_level=2,  # Higher auth required
            cost_limits={"max_cost_per_request": 5.0},
        ),
        "mock_openai:gpt-3.5-turbo-mock": ModelAccessPolicy(
            model_id="mock_openai:gpt-3.5-turbo-mock",
            required_authorization_level=1,  # Lower auth required
            cost_limits={"max_cost_per_request": 1.0},
        ),
    }

    # Set default models
    governance_registry.default_models = {
        "general": "mock_openai:gpt-3.5-turbo-mock",
        "code": "mock_openai:gpt-4-mock",
    }

    print("Demonstrating governance-enhanced registry...")

    # Test model selection
    selected_model = await governance_registry.select_model_for_task(
        task_type="general", user_id="user1"
    )
    print(f"Selected model for 'general' task: {selected_model}")

    # Test model access enforcement
    try:
        # User1 only has level 1, cannot access gpt-4-mock which requires level 2
        await governance_registry.generate_with_governance(
            model_id="mock_openai:gpt-4-mock", prompt="Tell me a joke", user_id="user1"
        )
    except GovernancePolicyViolation as e:
        print(f"Expected policy violation: {e}")

    # Test successful generation with proper access level
    try:
        result = await governance_registry.generate_with_governance(
            model_id="mock_openai:gpt-3.5-turbo-mock",  # User1 has access to this
            prompt="Tell me a joke",
            user_id="user1",
        )
        print(f"Generated content: {result.content}")
        print(f"Governance metadata: {result.metadata.get('governance')}")
    except GovernancePolicyViolation as e:
        print(f"Unexpected policy violation: {e}")

    # Create a governance proposal for model access
    proposal_id = await governance_registry.create_governance_proposal_for_model(
        model_id="mock_openai:gpt-4-mock",
        user_id="user1",
        request_type="access_increase",
        justification="Need advanced capabilities for project X",
        proposed_changes={"required_authorization_level": 1},  # Lower the requirement
    )
    print(f"Created governance proposal: {proposal_id}")

    # Show usage statistics
    print("Usage statistics:")
    print(json.dumps(governance_registry.usage_statistics, indent=2))


if __name__ == "__main__":
    import asyncio

    # Run the demo
    asyncio.run(demo_governance_enhanced_registry())
