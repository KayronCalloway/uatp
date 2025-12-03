"""
Legacy CapsuleEngine for compatibility with existing visualizer and examples.
This provides a simple file-based capsule engine that works with the existing interface.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.capsule_schema import AnyCapsule, CapsuleStatus

# Import crypto utils with fallback
try:
    from src.crypto_utils import (
        get_verify_key_from_signing_key,
        hash_for_signature,
        sign_capsule,
    )

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class LegacyCapsuleEngine:
    """
    Legacy capsule engine that works with file-based storage.
    Compatible with the existing visualizer and examples.
    """

    def __init__(self, agent_id: str, storage_path: str = "capsule_chain.jsonl"):
        self.agent_id = agent_id
        self.storage_path = storage_path
        # Use a valid hex key for demo or check environment
        demo_key = "a" * 64  # 64 character hex string for demo
        self.signing_key = os.environ.get("UATP_SIGNING_KEY", demo_key)

        # Create storage directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(storage_path)), exist_ok=True)

        # Initialize empty chain file if it doesn't exist
        if not os.path.exists(storage_path):
            with open(storage_path, "w") as f:
                pass  # Create empty file

    def create_capsule(
        self,
        capsule_type: str,
        confidence: float,
        reasoning_trace: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        previous_capsule_id: Optional[str] = None,
    ) -> AnyCapsule:
        """
        Create a new capsule with the given parameters.
        """
        capsule_id = str(uuid.uuid4())

        # Create a basic capsule structure
        capsule_data = {
            "capsule_id": capsule_id,
            "capsule_type": capsule_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": CapsuleStatus.SEALED,
            "agent_id": self.agent_id,
            "confidence": confidence,
            "reasoning_trace": reasoning_trace,
            "metadata": metadata or {},
            "previous_capsule_id": previous_capsule_id,
            "verification": {
                "signer": self.agent_id,
                "verify_key": get_verify_key_from_signing_key(self.signing_key),
                "hash": "",
                "signature": "",
            },
        }

        # Use simple dictionary approach for visualizer compatibility
        # The visualizer expects a simple object with basic attributes
        class SimpleCapsule:
            def __init__(self, data):
                self.capsule_id = data.get("capsule_id", "")
                self.capsule_type = data.get("capsule_type", "unknown")
                self.agent_id = data.get("agent_id", "")
                self.timestamp = data.get("timestamp", "")
                self.confidence = data.get("confidence", 0.0)
                self.reasoning_trace = data.get("reasoning_trace", [])
                self.metadata = data.get("metadata", {})
                self.previous_capsule_id = data.get("previous_capsule_id")
                self.signature = data.get("verification", {}).get(
                    "signature", f"demo-sig-{self.capsule_id[:8]}"
                )
                self.verification = data.get("verification", {})

        return SimpleCapsule(capsule_data)

    def log_capsule(self, capsule: AnyCapsule):
        """
        Log a capsule to the chain file.
        """
        with open(self.storage_path, "a") as f:
            if hasattr(capsule, "model_dump"):
                capsule_json = capsule.model_dump()
            elif hasattr(capsule, "dict"):
                capsule_json = capsule.dict()
            elif hasattr(capsule, "__dict__"):
                # Convert SimpleCapsule to dict
                capsule_json = {
                    "capsule_id": capsule.capsule_id,
                    "capsule_type": capsule.capsule_type,
                    "agent_id": capsule.agent_id,
                    "timestamp": capsule.timestamp,
                    "confidence": capsule.confidence,
                    "reasoning_trace": capsule.reasoning_trace,
                    "metadata": capsule.metadata,
                    "previous_capsule_id": capsule.previous_capsule_id,
                    "verification": capsule.verification,
                }
            else:
                capsule_json = capsule

            f.write(json.dumps(capsule_json) + "\n")

    def load_chain(self) -> List[AnyCapsule]:
        """
        Load all capsules from the chain file.
        """
        capsules = []

        if not os.path.exists(self.storage_path):
            return capsules

        try:
            with open(self.storage_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            capsule_data = json.loads(line)
                            # Convert back to proper capsule if possible
                            capsules.append(self._dict_to_capsule(capsule_data))
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass

        return capsules

    def _dict_to_capsule(self, capsule_data: Dict[str, Any]) -> AnyCapsule:
        """
        Convert a dictionary back to a capsule object.
        """

        # Create a simple capsule-like object for the visualizer
        class SimpleCapsule:
            def __init__(self, data):
                self.capsule_id = data.get("capsule_id", "")
                self.capsule_type = data.get("capsule_type", "unknown")
                self.agent_id = data.get("agent_id", "")
                self.timestamp = data.get("timestamp", "")
                self.confidence = data.get("confidence", 0.0)
                self.reasoning_trace = data.get("reasoning_trace", [])
                self.metadata = data.get("metadata", {})
                self.previous_capsule_id = data.get("previous_capsule_id")
                self.signature = data.get("verification", {}).get("signature", "")
                self.verification = data.get("verification", {})

        return SimpleCapsule(capsule_data)

    def verify_capsule(self, capsule: AnyCapsule) -> bool:
        """
        Verify a capsule's signature.
        """
        # Basic verification - just check if signature exists
        if hasattr(capsule, "signature") and capsule.signature:
            return len(capsule.signature) > 0
        elif hasattr(capsule, "verification") and capsule.verification:
            return bool(capsule.verification.get("signature"))
        return False
