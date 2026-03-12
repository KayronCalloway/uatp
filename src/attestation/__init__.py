"""
UATP Attestation - in-toto/Witness inspired workflow attestations.

This module provides chain-of-custody verification for multi-step workflows:
- LinkAttestation: Single step with materials → products
- WorkflowAttestation: Ordered chain of links
- SimplePolicy: Config-based verification rules (no Rego)

Usage:
    from src.attestation import (
        LinkAttestation,
        WorkflowAttestation,
        SimplePolicy,
        ResourceDescriptor,
        AttestationVerifier,
    )

    # Create a workflow
    workflow = WorkflowAttestation(
        workflow_id="wf_123",
        name="AI Review Pipeline",
    )

    # Add steps
    step1 = LinkAttestation(name="model_inference")
    step1.add_capsule_material("input_caps_001", "sha256:abc...")
    step1.add_capsule_product("output_caps_002", "sha256:def...")
    workflow.add_step(step1)

    step2 = LinkAttestation(name="human_review")
    step2.add_capsule_material("output_caps_002", "sha256:def...")
    step2.add_capsule_product("final_caps_003", "sha256:ghi...")
    workflow.add_step(step2)

    # Verify
    result = workflow.verify()
    print(f"Chain valid: {result.is_valid}")
"""

# Materials
# Link Attestation
from src.attestation.link import (
    AttestationValidity,
    LinkAttestation,
)
from src.attestation.materials import (
    ResourceDescriptor,
    compute_digest,
)

# Policy
from src.attestation.policy import (
    PERMISSIVE_POLICY,
    STRICT_POLICY,
    PolicyResult,
    PolicyViolation,
    SimplePolicy,
)

# Verification
from src.attestation.verification import (
    AttestationVerifier,
    LinkVerificationResult,
    build_workflow_from_capsule_chain,
    create_link_from_capsules,
)

# Workflow
from src.attestation.workflow import (
    ChainVerificationResult,
    WorkflowAttestation,
    WorkflowVerificationResult,
)

__all__ = [
    # Materials
    "ResourceDescriptor",
    "compute_digest",
    # Link
    "LinkAttestation",
    "AttestationValidity",
    # Policy
    "SimplePolicy",
    "PolicyResult",
    "PolicyViolation",
    "PERMISSIVE_POLICY",
    "STRICT_POLICY",
    # Workflow
    "WorkflowAttestation",
    "WorkflowVerificationResult",
    "ChainVerificationResult",
    # Verification
    "AttestationVerifier",
    "LinkVerificationResult",
    "create_link_from_capsules",
    "build_workflow_from_capsule_chain",
]
