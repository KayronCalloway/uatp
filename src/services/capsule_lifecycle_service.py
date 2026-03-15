"""
CapsuleLifecycleService - Centralized capsule creation with lineage tracking.

This is a minimal implementation providing core capsule lifecycle functionality.
The full lineage graph features from constellations are optional.
"""

import hashlib
import json
import logging
import uuid as uuid_module
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.capsule import CapsuleModel
from src.utils.uatp_envelope import is_envelope_format, wrap_in_uatp_envelope

logger = logging.getLogger(__name__)

# Optional lineage model import
try:
    from src.models.lineage import LineageEdgeModel

    _LINEAGE_MODEL_AVAILABLE = True
except ImportError:
    LineageEdgeModel = None  # type: ignore
    _LINEAGE_MODEL_AVAILABLE = False


def compute_chain_merkle_root(capsule_ids: List[str]) -> str:
    """
    Compute a Merkle root hash from a list of capsule IDs.

    Args:
        capsule_ids: List of capsule IDs in chain order

    Returns:
        Hex-encoded SHA-256 hash representing the chain
    """
    if not capsule_ids:
        return hashlib.sha256(b"empty_chain").hexdigest()

    current_hash = hashlib.sha256(capsule_ids[0].encode()).digest()
    for capsule_id in capsule_ids[1:]:
        combined = current_hash + capsule_id.encode()
        current_hash = hashlib.sha256(combined).digest()

    return current_hash.hex()


class CapsuleLifecycleService:
    """
    Centralized capsule creation with automatic lineage tracking.

    This service ensures every capsule created through it:
    1. Is properly persisted to the database
    2. Has lineage edges registered when parent_capsule_id is provided
    3. Is tracked in chains for sealing
    """

    def __init__(self):
        self._chain_capsules: Dict[str, List[str]] = {}  # chain_id -> [capsule_ids]
        self._lineage_edges: Dict[str, List[str]] = {}  # child_id -> [parent_ids]

    async def create_capsule(
        self,
        capsule_data: Union[Dict[str, Any], Any],
        session: AsyncSession,
        parent_capsule_id: Optional[str] = None,
        chain_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        relationship_type: str = "derived_from",
        attribution_weight: float = 1.0,
    ) -> CapsuleModel:
        """
        Create a capsule with automatic lineage and chain tracking.

        Args:
            capsule_data: Capsule data (dict or Pydantic model)
            session: SQLAlchemy async session
            parent_capsule_id: Optional parent capsule for lineage
            chain_id: Optional chain ID for chain tracking
            owner_id: Optional owner ID for user isolation
            relationship_type: Type of lineage relationship
            attribution_weight: Weight for attribution calculations

        Returns:
            Created CapsuleModel instance
        """
        # Convert Pydantic model to dict if needed
        if hasattr(capsule_data, "model_dump"):
            capsule_dict = capsule_data.model_dump()
        elif hasattr(capsule_data, "dict"):
            capsule_dict = capsule_data.dict()
        else:
            capsule_dict = dict(capsule_data)

        # Extract/generate capsule ID
        capsule_id = capsule_dict.get("capsule_id")
        if not capsule_id:
            content_str = json.dumps(capsule_dict.get("payload", {}), sort_keys=True)
            capsule_id = hashlib.sha256(content_str.encode()).hexdigest()[:16]
            capsule_dict["capsule_id"] = capsule_id

        capsule_type = capsule_dict.get(
            "capsule_type", capsule_dict.get("type", "generic")
        )

        # Parse timestamp
        timestamp = capsule_dict.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.now(timezone.utc)
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Get chain capsule IDs for merkle_root calculation
        chain_capsule_ids = None
        if chain_id:
            chain_capsule_ids = self._chain_capsules.get(chain_id, []).copy()
            chain_capsule_ids.append(capsule_id)

        # Get payload and wrap in UATP envelope
        payload = capsule_dict.get("payload", {})
        if not is_envelope_format(payload):
            parent_capsules = [parent_capsule_id] if parent_capsule_id else []

            merkle_root = None
            if chain_capsule_ids:
                merkle_root = compute_chain_merkle_root(chain_capsule_ids)

            verification = capsule_dict.get("verification", {})
            agent_id = (
                verification.get("signer") if isinstance(verification, dict) else None
            )

            payload = wrap_in_uatp_envelope(
                payload_data=payload,
                capsule_id=capsule_id,
                capsule_type=capsule_type,
                agent_id=agent_id,
                parent_capsules=parent_capsules,
                chain_id=chain_id,
                chain_position=len(chain_capsule_ids) - 1 if chain_capsule_ids else 0,
            )

            if merkle_root and "chain_context" in payload:
                payload["chain_context"]["merkle_root"] = merkle_root

        # Convert owner_id to UUID if provided
        owner_uuid = None
        if owner_id:
            try:
                owner_uuid = uuid_module.UUID(owner_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid owner_id format: {owner_id}")
                owner_uuid = None

        # Create CapsuleModel
        capsule = CapsuleModel(
            capsule_id=capsule_id,
            owner_id=owner_uuid,
            capsule_type=capsule_type,
            version=capsule_dict.get("version", "7.2"),
            timestamp=timestamp,
            status=capsule_dict.get("status", "SEALED"),
            verification=capsule_dict.get("verification", {}),
            payload=payload,
            parent_capsule_id=parent_capsule_id,
            encrypted_payload=capsule_dict.get("encrypted_payload"),
            encryption_metadata=capsule_dict.get("encryption_metadata"),
        )

        # Track lineage in memory
        if parent_capsule_id:
            if capsule_id not in self._lineage_edges:
                self._lineage_edges[capsule_id] = []
            if parent_capsule_id not in self._lineage_edges[capsule_id]:
                self._lineage_edges[capsule_id].append(parent_capsule_id)

            # Persist to database if model available
            if _LINEAGE_MODEL_AVAILABLE and LineageEdgeModel:
                edge = LineageEdgeModel(
                    parent_capsule_id=parent_capsule_id,
                    child_capsule_id=capsule_id,
                    relationship_type=relationship_type,
                    attribution_weight=str(attribution_weight),
                    created_at=timestamp,
                )
                session.add(edge)

        # Track in chain
        if chain_id:
            self._track_capsule_in_chain(chain_id, capsule_id)

        # Save to database
        session.add(capsule)
        await session.commit()
        await session.refresh(capsule)

        logger.info(
            f"Created capsule {capsule_id} "
            f"(type={capsule_type}, parent={parent_capsule_id}, chain={chain_id})"
        )

        return capsule

    def _track_capsule_in_chain(self, chain_id: str, capsule_id: str) -> None:
        """Track a capsule as part of a chain."""
        if chain_id not in self._chain_capsules:
            self._chain_capsules[chain_id] = []

        if capsule_id not in self._chain_capsules[chain_id]:
            self._chain_capsules[chain_id].append(capsule_id)

    def get_chain_capsules(self, chain_id: str) -> List[str]:
        """Get all capsule IDs tracked in a chain."""
        return self._chain_capsules.get(chain_id, []).copy()

    def compute_chain_hash(self, chain_id: str) -> Optional[str]:
        """Compute the merkle root for a chain."""
        capsule_ids = self.get_chain_capsules(chain_id)
        if not capsule_ids:
            return None
        return compute_chain_merkle_root(capsule_ids)

    async def get_ancestors(
        self, capsule_id: str, depth: Optional[int] = None
    ) -> List[str]:
        """Get ancestor capsule IDs from lineage tracking."""
        ancestors = []
        visited = set()
        to_visit = [capsule_id]
        current_depth = 0

        while to_visit and (depth is None or current_depth < depth):
            next_visit = []
            for cid in to_visit:
                if cid in visited:
                    continue
                visited.add(cid)
                parents = self._lineage_edges.get(cid, [])
                for parent in parents:
                    if parent not in visited:
                        ancestors.append(parent)
                        next_visit.append(parent)
            to_visit = next_visit
            current_depth += 1

        return ancestors

    async def get_descendants(
        self, capsule_id: str, depth: Optional[int] = None
    ) -> List[str]:
        """Get descendant capsule IDs from lineage tracking."""
        # Build reverse index
        children_map: Dict[str, List[str]] = {}
        for child, parents in self._lineage_edges.items():
            for parent in parents:
                if parent not in children_map:
                    children_map[parent] = []
                children_map[parent].append(child)

        descendants = []
        visited = set()
        to_visit = [capsule_id]
        current_depth = 0

        while to_visit and (depth is None or current_depth < depth):
            next_visit = []
            for cid in to_visit:
                if cid in visited:
                    continue
                visited.add(cid)
                children = children_map.get(cid, [])
                for child in children:
                    if child not in visited:
                        descendants.append(child)
                        next_visit.append(child)
            to_visit = next_visit
            current_depth += 1

        return descendants

    async def get_lineage(self, capsule_id: str) -> List[str]:
        """Get the full lineage path to genesis."""
        lineage = []
        current = capsule_id
        visited = set()

        while current and current not in visited:
            visited.add(current)
            parents = self._lineage_edges.get(current, [])
            if parents:
                parent = parents[0]  # Follow first parent
                lineage.append(parent)
                current = parent
            else:
                break

        return lineage

    async def load_lineage_from_database(self, session: AsyncSession) -> int:
        """
        Load lineage edges from database into memory.

        Returns:
            Number of edges loaded
        """
        if not _LINEAGE_MODEL_AVAILABLE or not LineageEdgeModel:
            logger.info("LineageEdgeModel not available, skipping lineage load")
            return 0

        try:
            result = await session.execute(select(LineageEdgeModel))
            edges = result.scalars().all()

            for edge in edges:
                child_id = edge.child_capsule_id
                parent_id = edge.parent_capsule_id

                if child_id not in self._lineage_edges:
                    self._lineage_edges[child_id] = []
                if parent_id not in self._lineage_edges[child_id]:
                    self._lineage_edges[child_id].append(parent_id)

            logger.info(f"Loaded {len(edges)} lineage edges from database")
            return len(edges)
        except Exception as e:
            logger.warning(f"Failed to load lineage from database: {e}")
            return 0


# Global singleton instance
capsule_lifecycle_service = CapsuleLifecycleService()
