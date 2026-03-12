"""
Link Attestation - in-toto inspired step attestation.

A LinkAttestation captures a single step in a workflow:
- What went in (materials)
- What came out (products)
- Who did it (signer)
- What ran (command/environment)
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.attestation.materials import ResourceDescriptor, compute_digest


@dataclass
class AttestationValidity:
    """
    Temporal validity window for an attestation.

    Based on Sigstore/in-toto patterns for time-bounded trust.
    """

    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    not_before: Optional[datetime] = None  # Valid starting from
    not_after: Optional[datetime] = None  # Expires at

    def is_valid_at(self, when: Optional[datetime] = None) -> bool:
        """Check if attestation is valid at given time."""
        check_time = when or datetime.now(timezone.utc)

        if self.not_before and check_time < self.not_before:
            return False
        if self.not_after and check_time > self.not_after:
            return False
        return True

    def is_expired(self) -> bool:
        """Check if attestation has expired."""
        if self.not_after:
            return datetime.now(timezone.utc) > self.not_after
        return False

    def remaining_validity_seconds(self) -> Optional[float]:
        """Get seconds until expiration (None if no expiry)."""
        if self.not_after:
            delta = self.not_after - datetime.now(timezone.utc)
            return max(0, delta.total_seconds())
        return None

    @classmethod
    def create_with_ttl(cls, ttl_seconds: int) -> "AttestationValidity":
        """Create validity window with time-to-live."""
        now = datetime.now(timezone.utc)
        return cls(
            issued_at=now,
            not_before=now,
            not_after=now + timedelta(seconds=ttl_seconds),
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {"issuedAt": self.issued_at.isoformat()}
        if self.not_before:
            result["notBefore"] = self.not_before.isoformat()
        if self.not_after:
            result["notAfter"] = self.not_after.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttestationValidity":
        return cls(
            issued_at=datetime.fromisoformat(data["issuedAt"]),
            not_before=datetime.fromisoformat(data["notBefore"])
            if data.get("notBefore")
            else None,
            not_after=datetime.fromisoformat(data["notAfter"])
            if data.get("notAfter")
            else None,
        )


@dataclass
class LinkAttestation:
    """
    A single step in a workflow chain.

    Based on in-toto Link format:
    - materials: Input artifacts (with hashes)
    - products: Output artifacts (with hashes)
    - byproducts: Metadata captured during execution
    - command: What was executed
    """

    # Step identity
    name: str  # e.g., "model_inference", "human_review"
    step_id: Optional[str] = None  # UUID for this specific execution

    # Artifacts
    materials: List[ResourceDescriptor] = field(default_factory=list)
    products: List[ResourceDescriptor] = field(default_factory=list)

    # Execution context
    command: Optional[List[str]] = None  # What ran (if applicable)
    environment: Dict[str, str] = field(default_factory=dict)

    # Byproducts (metadata from execution)
    byproducts: Dict[str, Any] = field(default_factory=dict)

    # Signing
    signed_by: Optional[str] = None  # Key ID of signer
    signature: Optional[str] = None
    signed_at: Optional[datetime] = None

    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.step_id:
            # Generate deterministic ID from name + timestamp
            ts = datetime.now(timezone.utc).isoformat()
            content = f"{self.name}:{ts}"
            self.step_id = hashlib.sha256(content.encode()).hexdigest()[:16]

    def __repr__(self) -> str:
        """Concise string representation for debugging."""
        signed = "signed" if self.signature else "unsigned"
        return f"LinkAttestation(name={self.name!r}, materials={len(self.materials)}, products={len(self.products)}, {signed})"

    def add_material(
        self,
        uri: str,
        digest: Optional[Dict[str, str]] = None,
        name: Optional[str] = None,
    ) -> None:
        """Add an input material."""
        self.materials.append(
            ResourceDescriptor(
                uri=uri,
                digest=digest or {},
                name=name,
            )
        )

    def add_product(
        self,
        uri: str,
        digest: Optional[Dict[str, str]] = None,
        name: Optional[str] = None,
    ) -> None:
        """Add an output product."""
        self.products.append(
            ResourceDescriptor(
                uri=uri,
                digest=digest or {},
                name=name,
            )
        )

    def add_capsule_material(
        self, capsule_id: str, content_hash: Optional[str] = None
    ) -> None:
        """Add a capsule as input material."""
        self.materials.append(
            ResourceDescriptor.from_capsule_id(capsule_id, content_hash)
        )

    def add_capsule_product(
        self, capsule_id: str, content_hash: Optional[str] = None
    ) -> None:
        """Add a capsule as output product."""
        self.products.append(
            ResourceDescriptor.from_capsule_id(capsule_id, content_hash)
        )

    def canonical_bytes(self) -> bytes:
        """
        Get canonical representation for signing.

        Excludes signature fields; deterministic JSON.
        """
        canonical = {
            "name": self.name,
            "step_id": self.step_id,
            "materials": [m.to_dict() for m in self.materials],
            "products": [p.to_dict() for p in self.products],
        }
        if self.command:
            canonical["command"] = self.command
        if self.environment:
            canonical["environment"] = self.environment
        if self.byproducts:
            canonical["byproducts"] = self.byproducts

        return json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )

    def content_hash(self) -> str:
        """Get SHA256 of canonical content."""
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LinkAttestation":
        """Deserialize from dictionary."""
        materials = [ResourceDescriptor.from_dict(m) for m in data.get("materials", [])]
        products = [ResourceDescriptor.from_dict(p) for p in data.get("products", [])]

        link = cls(
            name=data["name"],
            step_id=data.get("stepId"),
            materials=materials,
            products=products,
            command=data.get("command"),
            environment=data.get("environment", {}),
            byproducts=data.get("byproducts", {}),
            signed_by=data.get("signedBy"),
            signature=data.get("signature"),
        )

        if data.get("signedAt"):
            link.signed_at = datetime.fromisoformat(data["signedAt"])
        if data.get("startedAt"):
            link.started_at = datetime.fromisoformat(data["startedAt"])
        if data.get("completedAt"):
            link.completed_at = datetime.fromisoformat(data["completedAt"])

        return link

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = {
            "name": self.name,
            "stepId": self.step_id,
            "materials": [m.to_dict() for m in self.materials],
            "products": [p.to_dict() for p in self.products],
        }

        if self.command:
            result["command"] = self.command
        if self.environment:
            result["environment"] = self.environment
        if self.byproducts:
            result["byproducts"] = self.byproducts
        if self.signed_by:
            result["signedBy"] = self.signed_by
        if self.signature:
            result["signature"] = self.signature
        if self.signed_at:
            result["signedAt"] = self.signed_at.isoformat()
        if self.started_at:
            result["startedAt"] = self.started_at.isoformat()
        if self.completed_at:
            result["completedAt"] = self.completed_at.isoformat()

        return result

    def products_contain(self, descriptor: ResourceDescriptor) -> bool:
        """Check if products contain a matching descriptor."""
        for product in self.products:
            if product.matches_digest(descriptor):
                return True
        return False

    def materials_match_products(self, previous_link: "LinkAttestation") -> bool:
        """
        Check if this link's materials match the previous link's products.

        This is the core chain verification: every material must have
        been produced by the previous step.
        """
        for material in self.materials:
            if not previous_link.products_contain(material):
                return False
        return True
