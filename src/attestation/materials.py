"""
Resource Descriptor - in-toto inspired material/product hashing.

A ResourceDescriptor identifies a piece of data (file, capsule, artifact)
with its cryptographic hash for tamper detection in workflow chains.
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ResourceDescriptor:
    """
    Describes an input (material) or output (product) in a workflow step.

    Based on in-toto's artifact model:
    - uri: Where to find it
    - digest: Content hash for verification
    - name: Human-readable name
    - annotations: Additional metadata
    """

    uri: str  # e.g., "capsule://caps_123" or "file://path/to/file"
    digest: Dict[str, str] = field(default_factory=dict)  # {"sha256": "abc123..."}
    name: Optional[str] = None
    media_type: Optional[str] = None
    annotations: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.name:
            # Extract name from URI
            self.name = self.uri.split("/")[-1] if "/" in self.uri else self.uri

    def __hash__(self) -> int:
        """Hash based on URI and canonical digest for use in sets/dicts."""
        return hash((self.uri, self.canonical_digest()))

    def __repr__(self) -> str:
        """Concise string representation."""
        digest_str = self.canonical_digest() or "no-digest"
        return f"ResourceDescriptor({self.name!r}, {digest_str[:20]}...)"

    @classmethod
    def from_content(
        cls,
        content: bytes,
        uri: str,
        name: Optional[str] = None,
        media_type: Optional[str] = None,
    ) -> "ResourceDescriptor":
        """Create ResourceDescriptor by hashing content."""
        digest = {"sha256": hashlib.sha256(content).hexdigest()}
        return cls(
            uri=uri,
            digest=digest,
            name=name,
            media_type=media_type,
        )

    @classmethod
    def from_capsule_id(
        cls,
        capsule_id: str,
        content_hash: Optional[str] = None,
    ) -> "ResourceDescriptor":
        """Create ResourceDescriptor for a capsule."""
        digest = {}
        if content_hash:
            # content_hash might be "sha256:abc123" or just "abc123"
            if ":" in content_hash:
                alg, value = content_hash.split(":", 1)
                digest[alg] = value
            else:
                digest["sha256"] = content_hash

        return cls(
            uri=f"capsule://{capsule_id}",
            digest=digest,
            name=capsule_id,
            media_type="application/vnd.uatp.capsule.v1+json",
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceDescriptor":
        """Deserialize from dictionary."""
        return cls(
            uri=data["uri"],
            digest=data.get("digest", {}),
            name=data.get("name"),
            media_type=data.get("mediaType"),
            annotations=data.get("annotations", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = {
            "uri": self.uri,
        }
        if self.digest:
            result["digest"] = self.digest
        if self.name:
            result["name"] = self.name
        if self.media_type:
            result["mediaType"] = self.media_type
        if self.annotations:
            result["annotations"] = self.annotations
        return result

    def matches_digest(self, other: "ResourceDescriptor") -> bool:
        """
        Check if this descriptor's digest matches another's.

        Two descriptors match if they share at least one common
        digest algorithm with the same value.
        """
        if not self.digest or not other.digest:
            return False

        for alg, value in self.digest.items():
            if alg in other.digest and other.digest[alg] == value:
                return True

        return False

    def canonical_digest(self) -> Optional[str]:
        """Get canonical digest string (sha256:abc123 format)."""
        if "sha256" in self.digest:
            return f"sha256:{self.digest['sha256']}"
        # Fall back to first available
        for alg, value in self.digest.items():
            return f"{alg}:{value}"
        return None


def compute_digest(data: Any, algorithm: str = "sha256") -> str:
    """
    Compute digest of data.

    Data is canonicalized to JSON if not bytes.
    """
    if isinstance(data, bytes):
        content = data
    elif isinstance(data, str):
        content = data.encode("utf-8")
    else:
        # Canonical JSON (sorted keys, no whitespace)
        content = json.dumps(data, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )

    if algorithm == "sha256":
        return hashlib.sha256(content).hexdigest()
    elif algorithm == "sha384":
        return hashlib.sha384(content).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(content).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
