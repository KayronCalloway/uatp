"""
Attestation Verification - Chain and workflow verification utilities.

Provides high-level verification functions for:
- Individual link verification
- Chain-of-custody verification
- Full workflow verification
"""

import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Lazy-loaded signature verification
_nacl_available: Optional[bool] = None
_VerifyKey = None
_BadSignatureError = None


def _ensure_nacl():
    """Lazy-load nacl module once."""
    global _nacl_available, _VerifyKey, _BadSignatureError
    if _nacl_available is None:
        try:
            from nacl.exceptions import BadSignatureError
            from nacl.signing import VerifyKey

            _VerifyKey = VerifyKey
            _BadSignatureError = BadSignatureError
            _nacl_available = True
        except ImportError:
            _nacl_available = False
    return _nacl_available


from src.attestation.link import LinkAttestation
from src.attestation.materials import ResourceDescriptor, compute_digest
from src.attestation.policy import PolicyResult, SimplePolicy
from src.attestation.workflow import (
    ChainVerificationResult,
    WorkflowAttestation,
    WorkflowVerificationResult,
)


@dataclass
class LinkVerificationResult:
    """Result of verifying a single link."""

    link_name: str
    step_id: str
    is_valid: bool
    signature_valid: Optional[bool] = None  # None if not signed
    content_hash_valid: Optional[bool] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "linkName": self.link_name,
            "stepId": self.step_id,
            "isValid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }
        if self.signature_valid is not None:
            result["signatureValid"] = self.signature_valid
        if self.content_hash_valid is not None:
            result["contentHashValid"] = self.content_hash_valid
        return result


class AttestationVerifier:
    """
    Verifier for links and workflows.

    Provides verification without requiring database access.
    """

    def __init__(self, public_keys: Optional[Dict[str, bytes]] = None):
        """
        Initialize verifier.

        Args:
            public_keys: Dict of keyid → public key bytes for signature verification
        """
        self.public_keys = public_keys or {}

    def verify_link(
        self,
        link: LinkAttestation,
        expected_hash: Optional[str] = None,
    ) -> LinkVerificationResult:
        """
        Verify a single link attestation.

        Checks:
        - Content hash matches (if expected_hash provided)
        - Signature valid (if signed and key available)
        - Materials have digests
        - Products have digests
        """
        result = LinkVerificationResult(
            link_name=link.name,
            step_id=link.step_id or "",
            is_valid=True,
        )

        # Check content hash
        if expected_hash:
            actual_hash = link.content_hash()
            if actual_hash == expected_hash:
                result.content_hash_valid = True
            else:
                result.content_hash_valid = False
                result.is_valid = False
                result.errors.append(
                    f"Content hash mismatch: expected {expected_hash[:16]}..., got {actual_hash[:16]}..."
                )

        # Check signature (if present)
        if link.signature and link.signed_by:
            if link.signed_by in self.public_keys:
                # Verify signature
                try:
                    is_valid = self._verify_signature(
                        link.canonical_bytes(),
                        link.signature,
                        self.public_keys[link.signed_by],
                    )
                    result.signature_valid = is_valid
                    if not is_valid:
                        result.is_valid = False
                        result.errors.append("Signature verification failed")
                except Exception as e:
                    result.signature_valid = False
                    result.is_valid = False
                    result.errors.append(f"Signature verification error: {e}")
            else:
                result.warnings.append(
                    f"Cannot verify signature: unknown key {link.signed_by}"
                )
        elif link.signed_by and not link.signature:
            result.warnings.append("Link has signer but no signature")

        # Check material digests
        for material in link.materials:
            if not material.digest:
                result.warnings.append(f"Material '{material.name}' has no digest")

        # Check product digests
        for product in link.products:
            if not product.digest:
                result.warnings.append(f"Product '{product.name}' has no digest")

        return result

    def verify_chain(
        self,
        links: List[LinkAttestation],
    ) -> ChainVerificationResult:
        """
        Verify chain of custody between links.

        Checks that step[i].products ⊇ step[i+1].materials
        """
        total_handoffs = max(0, len(links) - 1)
        result = ChainVerificationResult(
            is_valid=True,
            verified_handoffs=0,
            total_handoffs=total_handoffs,
        )

        if len(links) < 2:
            return result

        for i in range(len(links) - 1):
            prev = links[i]
            next_link = links[i + 1]

            all_matched = True
            for material in next_link.materials:
                found = False
                for product in prev.products:
                    if product.matches_digest(material):
                        found = True
                        break

                if not found:
                    result.add_break(
                        from_step=prev.name,
                        to_step=next_link.name,
                        missing_material=material.name or material.uri,
                        message=f"Material '{material.name}' digest not in previous products",
                    )
                    all_matched = False

            if all_matched:
                result.verified_handoffs += 1

        return result

    def verify_workflow(
        self,
        workflow: WorkflowAttestation,
    ) -> WorkflowVerificationResult:
        """
        Full workflow verification.

        Combines chain verification + policy evaluation.
        """
        chain_result = self.verify_chain(workflow.steps)
        policy_result = workflow.policy.evaluate(workflow.steps)

        is_valid = chain_result.is_valid and policy_result.passed

        return WorkflowVerificationResult(
            workflow_id=workflow.workflow_id,
            is_valid=is_valid,
            chain_result=chain_result,
            policy_result=policy_result,
            step_count=len(workflow.steps),
        )

    def _verify_signature(
        self,
        message: bytes,
        signature: str,
        public_key: bytes,
    ) -> bool:
        """
        Verify Ed25519 signature.

        Override this method for different signature algorithms.
        """
        if not _ensure_nacl():
            return False
        try:
            verify_key = _VerifyKey(public_key)
            sig_bytes = base64.b64decode(signature)
            verify_key.verify(message, sig_bytes)
            return True
        except (_BadSignatureError, Exception):
            return False


def create_link_from_capsules(
    step_name: str,
    input_capsules: List[Tuple[str, str]],  # [(capsule_id, content_hash), ...]
    output_capsules: List[Tuple[str, str]],
    command: Optional[List[str]] = None,
    byproducts: Optional[Dict[str, Any]] = None,
) -> LinkAttestation:
    """
    Create a LinkAttestation from capsule IDs.

    Convenience function for building links from capsule references.
    """
    link = LinkAttestation(name=step_name, command=command, byproducts=byproducts or {})

    for capsule_id, content_hash in input_capsules:
        link.add_capsule_material(capsule_id, content_hash)

    for capsule_id, content_hash in output_capsules:
        link.add_capsule_product(capsule_id, content_hash)

    return link


def build_workflow_from_capsule_chain(
    workflow_id: str,
    capsule_chain: List[Dict[str, Any]],
    policy: Optional[SimplePolicy] = None,
) -> WorkflowAttestation:
    """
    Build a WorkflowAttestation from a chain of capsules.

    Each capsule dict should have:
    - capsule_id: str
    - content_hash: str
    - step_name: str (optional, defaults to "step_{i}")
    - prev_hash: str (optional, links to previous)
    """
    from src.attestation.policy import PERMISSIVE_POLICY

    workflow = WorkflowAttestation(
        workflow_id=workflow_id,
        policy=policy or PERMISSIVE_POLICY,
    )

    for i, capsule in enumerate(capsule_chain):
        step_name = capsule.get("step_name", f"step_{i}")
        capsule_id = capsule["capsule_id"]
        content_hash = capsule.get("content_hash", "")

        link = LinkAttestation(name=step_name)
        link.add_capsule_product(capsule_id, content_hash)

        # If not first, add previous capsule as material
        if i > 0:
            prev = capsule_chain[i - 1]
            link.add_capsule_material(
                prev["capsule_id"],
                prev.get("content_hash", ""),
            )

        workflow.add_step(link)

    return workflow
