"""
Demo script for federated registry functionality.
"""
import asyncio
import json
import uuid
from datetime import datetime, timezone

from src.integrations.federated_registry import (
    FederatedModelRegistry,
    FederationRole,
    FederationMember,
)
from src.integrations.governance_enhanced_registry import GovernanceEnabledLLMRegistry
from src.integrations.multimodal_adapters import MultiModalReasoningStep


async def demo_federated_registry():
    """Demonstrate the federated registry functionality."""

    # Create a base registry
    base_registry = GovernanceEnabledLLMRegistry()

    # Create a federated registry
    fed_registry = FederatedModelRegistry(
        member_id="org1",
        member_name="Organization One",
        registry_path="./federation_data",
        base_registry=base_registry,
    )

    # Create some federation members
    member2 = FederationMember(
        id="org2",
        name="Organization Two",
        role=FederationRole.VALIDATOR,
        verify_key="ed25519:8a1e3c52c8c8fbaf3b79df8846a9e3c19f29f7a7db3b8196c7d1e7dd02fca7c3",
        endpoint="https://org2.example.com/api/federation",
        last_active=datetime.now(timezone.utc),
        trust_score=0.9,
    )

    member3 = FederationMember(
        id="org3",
        name="Organization Three",
        role=FederationRole.MEMBER,
        verify_key="ed25519:2f567d8a7c6bf3e1a2c9d1e7bd879a8c7f9b1a2d3e4f5a6b7c8d9e1f2a3b4c5d",
        endpoint="https://org3.example.com/api/federation",
        last_active=datetime.now(timezone.utc),
        trust_score=0.8,
    )

    # Add members to federation
    await fed_registry.add_federation_member(member2)
    await fed_registry.add_federation_member(member3)
    print(f"Added {len(fed_registry.members)} federation members")

    # Register a provider and model with the federation
    try:
        # First register the provider with the base registry
        await fed_registry.base_registry.register_provider(
            provider_id="mistral",
            name="Mistral AI",
            endpoint="https://api.mistral.ai/v1",
            api_key="sk-test-key",
            metadata={"capabilities": ["text", "code"]},
        )

        # Then register the model with the federation
        await fed_registry.register_model_with_federation(
            model_id="mixtral-8x7b",
            provider="mistral",
            access_level=2,  # RESTRICTED level
            metadata={"capabilities": ["text", "code"]},
        )
        print("Registered model with federation")
    except Exception as e:
        print(f"Error registering model: {e}")

    # Create mock reasoning steps
    reasoning_steps = [
        MultiModalReasoningStep(
            step_id=1,
            operation="text_analysis",
            reasoning="Initial analysis of query",
            confidence=0.9,
        ),
        MultiModalReasoningStep(
            step_id=2,
            operation="knowledge_retrieval",
            reasoning="Retrieved relevant knowledge",
            confidence=0.85,
            parent_step_id=1,
        ),
        MultiModalReasoningStep(
            step_id=3,
            operation="response_generation",
            reasoning="Generated response based on retrieved knowledge",
            confidence=0.92,
            parent_step_id=2,
        ),
    ]

    # Distribute a reasoning trace
    trace_id = str(uuid.uuid4())
    capsule_id = await fed_registry.distribute_reasoning_trace(
        trace_id=trace_id,
        provider="mistral",
        reasoning_steps=reasoning_steps,
        metadata={"query": "What is UATP?"},
    )
    print(f"Distributed reasoning trace, capsule ID: {capsule_id}")

    # Query federated traces
    query = {
        "provider": "mistral",
        "after": (
            datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        ).isoformat(),
    }

    traces = await fed_registry.aggregate_federated_traces(query)
    print(f"Found {len(traces)} traces matching query")
    for trace_id, trace_list in traces.items():
        for trace in trace_list:
            print(
                f" - Trace ID: {trace_id}, Provider: {trace.get('provider', 'unknown')}, Source: {trace.get('source', 'local')}"
            )

    # Try applying a governance decision from a federation member
    policy_updates = {
        "model_access_levels": {
            "gpt-4": "PUBLIC",  # Change access level
            "mixtral-8x7b": "GOVERNANCE_REQUIRED",  # Change access level
        }
    }

    success = await fed_registry.apply_governance_decision(
        decision_id=str(uuid.uuid4()),
        policy_updates=policy_updates,
        member_id="org2",  # From Organization Two (a validator)
    )

    if success:
        print("Applied governance decision successfully")
    else:
        print("Failed to apply governance decision")

    print("Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(demo_federated_registry())
