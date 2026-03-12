"""
Simple Policy - No Rego, just config.

A SimplePolicy defines rules for workflow verification:
- Required steps
- Allowed signers per step
- Optional step ordering
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from src.attestation.link import LinkAttestation


@dataclass
class PolicyViolation:
    """A single policy violation."""

    rule: str  # Which rule was violated
    message: str  # Human-readable description
    step: Optional[str] = None  # Which step (if applicable)
    severity: str = "error"  # error, warning


@dataclass
class PolicyResult:
    """Result of policy evaluation."""

    passed: bool
    violations: List[PolicyViolation] = field(default_factory=list)
    warnings: List[PolicyViolation] = field(default_factory=list)

    def add_violation(
        self, rule: str, message: str, step: Optional[str] = None
    ) -> None:
        """Add an error violation."""
        self.violations.append(PolicyViolation(rule=rule, message=message, step=step))
        self.passed = False

    def add_warning(self, rule: str, message: str, step: Optional[str] = None) -> None:
        """Add a warning (doesn't fail policy)."""
        self.warnings.append(
            PolicyViolation(rule=rule, message=message, step=step, severity="warning")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "passed": self.passed,
            "violations": [
                {"rule": v.rule, "message": v.message, "step": v.step}
                for v in self.violations
            ],
            "warnings": [
                {"rule": w.rule, "message": w.message, "step": w.step}
                for w in self.warnings
            ],
        }


@dataclass
class SimplePolicy:
    """
    Simple workflow policy without Rego.

    Defines:
    - required_steps: Steps that must be present
    - allowed_signers: Which key IDs can sign which steps
    - step_order: Required ordering (None = any order)
    - allow_extra_steps: Whether unlisted steps are allowed
    """

    name: str = "default"
    description: str = ""

    # Required steps (by name)
    required_steps: List[str] = field(default_factory=list)

    # Allowed signers per step: {"step_name": ["keyid1", "keyid2"]}
    allowed_signers: Dict[str, List[str]] = field(default_factory=dict)

    # Optional: required order of steps
    step_order: Optional[List[str]] = None

    # Allow steps not in required_steps?
    allow_extra_steps: bool = True

    # Require all materials to have digests?
    require_material_digests: bool = True

    # Require all products to have digests?
    require_product_digests: bool = True

    def evaluate(self, links: List[LinkAttestation]) -> PolicyResult:
        """
        Evaluate a list of links against this policy.

        Returns PolicyResult with pass/fail and violations.
        """
        result = PolicyResult(passed=True)

        # Check required steps
        step_names = {link.name for link in links}
        for required in self.required_steps:
            if required not in step_names:
                result.add_violation(
                    rule="required_step",
                    message=f"Required step '{required}' is missing",
                )

        # Check for extra steps
        if not self.allow_extra_steps:
            allowed = set(self.required_steps)
            for name in step_names:
                if name not in allowed:
                    result.add_violation(
                        rule="extra_step",
                        message=f"Step '{name}' is not allowed by policy",
                        step=name,
                    )

        # Check signer constraints
        for link in links:
            if link.name in self.allowed_signers:
                allowed_keys = self.allowed_signers[link.name]
                if link.signed_by and link.signed_by not in allowed_keys:
                    result.add_violation(
                        rule="signer_constraint",
                        message=f"Step '{link.name}' signed by unauthorized key '{link.signed_by}'",
                        step=link.name,
                    )
                elif not link.signed_by:
                    result.add_warning(
                        rule="missing_signature",
                        message=f"Step '{link.name}' has no signature",
                        step=link.name,
                    )

        # Check step order
        if self.step_order:
            actual_order = [link.name for link in links if link.name in self.step_order]
            expected_order = [s for s in self.step_order if s in step_names]

            if actual_order != expected_order:
                result.add_violation(
                    rule="step_order",
                    message=f"Steps out of order. Expected: {expected_order}, got: {actual_order}",
                )

        # Check digest requirements
        for link in links:
            if self.require_material_digests:
                for material in link.materials:
                    if not material.digest:
                        result.add_violation(
                            rule="material_digest",
                            message=f"Material '{material.name}' in step '{link.name}' has no digest",
                            step=link.name,
                        )

            if self.require_product_digests:
                for product in link.products:
                    if not product.digest:
                        result.add_violation(
                            rule="product_digest",
                            message=f"Product '{product.name}' in step '{link.name}' has no digest",
                            step=link.name,
                        )

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimplePolicy":
        """Deserialize from dictionary."""
        return cls(
            name=data.get("name", "default"),
            description=data.get("description", ""),
            required_steps=data.get("requiredSteps", []),
            allowed_signers=data.get("allowedSigners", {}),
            step_order=data.get("stepOrder"),
            allow_extra_steps=data.get("allowExtraSteps", True),
            require_material_digests=data.get("requireMaterialDigests", True),
            require_product_digests=data.get("requireProductDigests", True),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = {
            "name": self.name,
            "description": self.description,
            "requiredSteps": self.required_steps,
            "allowedSigners": self.allowed_signers,
            "allowExtraSteps": self.allow_extra_steps,
            "requireMaterialDigests": self.require_material_digests,
            "requireProductDigests": self.require_product_digests,
        }
        if self.step_order:
            result["stepOrder"] = self.step_order
        return result


# Predefined policies
PERMISSIVE_POLICY = SimplePolicy(
    name="permissive",
    description="No constraints - for development",
    require_material_digests=False,
    require_product_digests=False,
)

STRICT_POLICY = SimplePolicy(
    name="strict",
    description="Strict chain verification",
    allow_extra_steps=False,
    require_material_digests=True,
    require_product_digests=True,
)
