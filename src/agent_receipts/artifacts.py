"""Content-addressed artifact storage for agent receipt evidence blobs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from src.agent_receipts.events import ArtifactRef
from src.agent_receipts.hashing import canonical_json_bytes


def sha256_bytes_digest(content: bytes) -> str:
    """Return sha256:<hex> for raw artifact bytes."""
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


class ArtifactStore:
    """Local content-addressed store for receipt evidence artifacts."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _relative_path_for_digest(self, digest: str) -> Path:
        hex_digest = digest.removeprefix("sha256:")
        return Path("sha256") / hex_digest[:2] / hex_digest

    def _absolute_path_for_relative(self, relative_path: str | Path) -> Path:
        candidate = (self.root / relative_path).resolve(strict=False)
        if not candidate.is_relative_to(self.root):
            raise ValueError("artifact path escapes store root")
        return candidate

    def store_bytes(
        self,
        content: bytes,
        *,
        media_type: str,
        redaction: dict[str, Any] | None = None,
    ) -> ArtifactRef:
        """Write bytes by content hash and return a JSON-serializable artifact ref."""
        digest = sha256_bytes_digest(content)
        relative_path = self._relative_path_for_digest(digest)
        artifact_path = self._absolute_path_for_relative(relative_path)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        if not artifact_path.exists():
            artifact_path.write_bytes(content)

        return ArtifactRef(
            digest=digest,
            path=relative_path.as_posix(),
            size=len(content),
            media_type=media_type,
            redaction=redaction or {},
        )

    def store_json(
        self,
        value: Any,
        *,
        media_type: str = "application/json",
        redaction: dict[str, Any] | None = None,
    ) -> ArtifactRef:
        """Canonicalize JSON-compatible data, store it as bytes, and return a ref."""
        return self.store_bytes(
            canonical_json_bytes(value),
            media_type=media_type,
            redaction=redaction,
        )


def verify_artifact_ref(root: str | Path, ref: ArtifactRef) -> bool:
    """Verify an artifact ref exists under root with matching digest and size."""
    store = ArtifactStore(root)
    artifact_path = store._absolute_path_for_relative(ref.path)
    if not artifact_path.exists() or not artifact_path.is_file():
        return False

    content = artifact_path.read_bytes()
    return sha256_bytes_digest(content) == ref.digest and len(content) == ref.size
