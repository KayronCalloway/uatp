"""
Workflow Attestation - Ordered chain of LinkAttestations.

A WorkflowAttestation represents a complete workflow:
- Multiple steps (links)
- Chain verification (products → materials)
- Policy evaluation
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.attestation.link import LinkAttestation
from src.attestation.materials import ResourceDescriptor
from src.attestation.policy import PERMISSIVE_POLICY, PolicyResult, SimplePolicy


@dataclass
class ChainVerificationResult:
    """Result of verifying the chain of custody."""

    is_valid: bool
    verified_handoffs: int
    total_handoffs: int
    breaks: List[Dict[str, Any]] = field(default_factory=list)

    def add_break(
        self,
        from_step: str,
        to_step: str,
        missing_material: str,
        message: str,
    ) -> None:
        """Record a chain break."""
        self.breaks.append(
            {
                "fromStep": from_step,
                "toStep": to_step,
                "missingMaterial": missing_material,
                "message": message,
            }
        )
        self.is_valid = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "isValid": self.is_valid,
            "verifiedHandoffs": self.verified_handoffs,
            "totalHandoffs": self.total_handoffs,
            "breaks": self.breaks,
        }


@dataclass
class WorkflowVerificationResult:
    """Complete verification result for a workflow."""

    workflow_id: str
    is_valid: bool
    chain_result: ChainVerificationResult
    policy_result: PolicyResult
    step_count: int
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "workflowId": self.workflow_id,
            "isValid": self.is_valid,
            "chain": self.chain_result.to_dict(),
            "policy": self.policy_result.to_dict(),
            "stepCount": self.step_count,
            "verifiedAt": self.verified_at.isoformat(),
        }


@dataclass
class WorkflowAttestation:
    """
    A complete workflow with ordered steps.

    Key verification: step[i].products ⊇ step[i+1].materials

    This ensures tamper-evident chain of custody:
    - Each step's inputs must come from previous step's outputs
    - Hashes link steps together
    - Any modification breaks the chain
    """

    workflow_id: str
    name: str = ""
    description: str = ""

    # Steps in order
    steps: List[LinkAttestation] = field(default_factory=list)

    # Policy for verification
    policy: SimplePolicy = field(default_factory=lambda: PERMISSIVE_POLICY)

    # Workflow metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed

    # Optional: associate with a capsule
    capsule_id: Optional[str] = None

    def __repr__(self) -> str:
        """Concise string representation for debugging."""
        return f"WorkflowAttestation(id={self.workflow_id!r}, steps={len(self.steps)}, status={self.status!r})"

    def add_step(self, link: LinkAttestation) -> None:
        """Add a step to the workflow."""
        self.steps.append(link)
        if self.status == "pending":
            self.status = "running"

    def complete(self) -> None:
        """Mark workflow as completed."""
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)

    def fail(self, reason: Optional[str] = None) -> None:
        """Mark workflow as failed."""
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc)

    @property
    def is_complete(self) -> bool:
        """Check if workflow has completed (success or failure)."""
        return self.status in ("completed", "failed")

    @property
    def step_count(self) -> int:
        """Get number of steps in workflow."""
        return len(self.steps)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get workflow duration in seconds (None if not complete)."""
        if self.completed_at:
            delta = self.completed_at - self.created_at
            return delta.total_seconds()
        return None

    def verify_chain(self) -> ChainVerificationResult:
        """
        Verify that products flow into materials.

        For each consecutive pair of steps:
        - Every material in step[i+1] must match a product in step[i]
        """
        total_handoffs = max(0, len(self.steps) - 1)
        result = ChainVerificationResult(
            is_valid=True,
            verified_handoffs=0,
            total_handoffs=total_handoffs,
        )

        if len(self.steps) < 2:
            # Single step or empty: chain is trivially valid
            return result

        for i in range(len(self.steps) - 1):
            prev_step = self.steps[i]
            next_step = self.steps[i + 1]

            # Check that all materials in next_step match products in prev_step
            all_matched = True
            for material in next_step.materials:
                if not prev_step.products_contain(material):
                    result.add_break(
                        from_step=prev_step.name,
                        to_step=next_step.name,
                        missing_material=material.name or material.uri,
                        message=f"Material '{material.name}' not found in products of '{prev_step.name}'",
                    )
                    all_matched = False

            if all_matched:
                result.verified_handoffs += 1

        return result

    def verify(self) -> WorkflowVerificationResult:
        """
        Full verification: chain + policy.

        Returns comprehensive verification result.
        """
        chain_result = self.verify_chain()
        policy_result = self.policy.evaluate(self.steps)

        is_valid = chain_result.is_valid and policy_result.passed

        return WorkflowVerificationResult(
            workflow_id=self.workflow_id,
            is_valid=is_valid,
            chain_result=chain_result,
            policy_result=policy_result,
            step_count=len(self.steps),
        )

    def get_step(self, name: str) -> Optional[LinkAttestation]:
        """Get a step by name."""
        for step in self.steps:
            if step.name == name:
                return step
        return None

    def get_step_by_id(self, step_id: str) -> Optional[LinkAttestation]:
        """Get a step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_all_materials(self) -> List[ResourceDescriptor]:
        """Get all unique materials across all steps."""
        seen = set()
        materials = []
        for step in self.steps:
            for material in step.materials:
                key = material.canonical_digest() or material.uri
                if key not in seen:
                    seen.add(key)
                    materials.append(material)
        return materials

    def get_all_products(self) -> List[ResourceDescriptor]:
        """Get all unique products across all steps."""
        seen = set()
        products = []
        for step in self.steps:
            for product in step.products:
                key = product.canonical_digest() or product.uri
                if key not in seen:
                    seen.add(key)
                    products.append(product)
        return products

    def get_final_products(self) -> List[ResourceDescriptor]:
        """Get products of the final step."""
        if self.steps:
            return self.steps[-1].products
        return []

    def canonical_bytes(self) -> bytes:
        """Get canonical representation for signing."""
        canonical = {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "steps": [step.to_dict() for step in self.steps],
            "policy": self.policy.to_dict(),
        }
        return json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )

    def content_hash(self) -> str:
        """Get SHA256 of canonical content."""
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowAttestation":
        """Deserialize from dictionary."""
        steps = [LinkAttestation.from_dict(s) for s in data.get("steps", [])]

        policy = PERMISSIVE_POLICY
        if "policy" in data:
            policy = SimplePolicy.from_dict(data["policy"])

        workflow = cls(
            workflow_id=data["workflowId"],
            name=data.get("name", ""),
            description=data.get("description", ""),
            steps=steps,
            policy=policy,
            status=data.get("status", "pending"),
            capsule_id=data.get("capsuleId"),
        )

        if data.get("createdAt"):
            workflow.created_at = datetime.fromisoformat(data["createdAt"])
        if data.get("completedAt"):
            workflow.completed_at = datetime.fromisoformat(data["completedAt"])

        return workflow

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = {
            "workflowId": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "policy": self.policy.to_dict(),
            "status": self.status,
            "createdAt": self.created_at.isoformat(),
        }

        if self.completed_at:
            result["completedAt"] = self.completed_at.isoformat()
        if self.capsule_id:
            result["capsuleId"] = self.capsule_id

        return result
