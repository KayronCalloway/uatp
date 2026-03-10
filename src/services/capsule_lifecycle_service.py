"""
CapsuleLifecycleService - Centralized capsule creation with lineage and chain integration.

UATP 7.2: This service provides a single entry point for capsule creation that
automatically handles:
1. Database persistence
2. Lineage edge registration (in-memory graph + database)
3. Chain tracking for sealing
4. UATP envelope wrapping with computed merkle_root

Design Decision:
    Centralizing capsule creation ensures consistent lineage tracking and
    eliminates the problem of "orphaned" capsules that exist in the database
    but aren't tracked in the lineage graph.
"""

import hashlib
import json
import logging
import uuid as uuid_module
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.capsule_schema import AnyCapsule
from src.capsules.lineage_system import capsule_lineage_system
from src.constellations import get_graph_store
from src.models.capsule import CapsuleModel
from src.models.lineage import LineageEdgeModel
from src.utils.uatp_envelope import is_envelope_format, wrap_in_uatp_envelope

logger = logging.getLogger(__name__)


def compute_chain_merkle_root(capsule_ids: List[str]) -> str:
    """
    Compute a Merkle root hash from a list of capsule IDs.

    This provides a compact cryptographic commitment to the chain contents.
    For simplicity, we use a linear hash chain (not a true Merkle tree),
    which is sufficient for chains under ~1000 capsules.

    Args:
        capsule_ids: List of capsule IDs in chain order

    Returns:
        Hex-encoded SHA-256 hash representing the chain
    """
    if not capsule_ids:
        return hashlib.sha256(b"empty_chain").hexdigest()

    # Build hash chain: H(H(...H(H(id0) || id1) || id2)... || idN)
    current_hash = hashlib.sha256(capsule_ids[0].encode()).digest()
    for capsule_id in capsule_ids[1:]:
        combined = current_hash + capsule_id.encode()
        current_hash = hashlib.sha256(combined).digest()

    return current_hash.hex()


class CapsuleLifecycleService:
    """
    Centralized capsule creation with automatic lineage and chain integration.

    This service ensures that every capsule created through it:
    1. Is properly persisted to the database
    2. Has lineage edges registered when parent_capsule_id is provided
    3. Is tracked in chains for sealing
    4. Has a properly computed merkle_root in the UATP envelope
    """

    def __init__(self):
        self._graph_store = get_graph_store()
        self._chain_capsules: Dict[str, List[str]] = {}  # chain_id -> [capsule_ids]

    async def create_capsule(
        self,
        capsule_data: Union[Dict[str, Any], AnyCapsule],
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
            attribution_weight: Weight for temporal justice calculations

        Returns:
            Created CapsuleModel instance

        Flow:
            1. Create CapsuleModel from data
            2. If parent_capsule_id: add lineage edge (graph + database)
            3. If chain_id: track for chain sealing
            4. Wrap payload in UATP envelope with computed merkle_root
            5. Save to database
            6. Return model
        """
        # Convert Pydantic model to dict if needed
        if hasattr(capsule_data, "model_dump"):
            capsule_dict = capsule_data.model_dump()
        elif hasattr(capsule_data, "dict"):
            capsule_dict = capsule_data.dict()
        else:
            capsule_dict = dict(capsule_data)

        # Extract key fields
        capsule_id = capsule_dict.get("capsule_id")
        if not capsule_id:
            # Generate capsule ID from content hash
            content_str = json.dumps(capsule_dict.get("payload", {}), sort_keys=True)
            capsule_id = hashlib.sha256(content_str.encode()).hexdigest()[:16]
            capsule_dict["capsule_id"] = capsule_id

        capsule_type = capsule_dict.get(
            "capsule_type", capsule_dict.get("type", "generic")
        )
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
            # Build parent capsules list
            parent_capsules = []
            if parent_capsule_id:
                parent_capsules.append(parent_capsule_id)

            # Compute merkle_root if we have chain data
            merkle_root = None
            if chain_capsule_ids:
                merkle_root = compute_chain_merkle_root(chain_capsule_ids)

            # Get agent_id from verification if available
            verification = capsule_dict.get("verification", {})
            agent_id = (
                verification.get("signer") if isinstance(verification, dict) else None
            )

            # Wrap payload
            payload = wrap_in_uatp_envelope(
                payload_data=payload,
                capsule_id=capsule_id,
                capsule_type=capsule_type,
                agent_id=agent_id,
                parent_capsules=parent_capsules,
                chain_id=chain_id,
                chain_position=len(chain_capsule_ids) - 1 if chain_capsule_ids else 0,
            )

            # Inject computed merkle_root into chain_context
            if merkle_root and "chain_context" in payload:
                payload["chain_context"]["merkle_root"] = merkle_root

        # Convert owner_id string to UUID object if provided
        owner_uuid = None
        if owner_id:
            try:
                owner_uuid = uuid_module.UUID(owner_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid owner_id format: {owner_id}, setting to None")
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

        # Handle lineage registration
        if parent_capsule_id:
            await self._register_lineage_edge(
                session=session,
                parent_capsule_id=parent_capsule_id,
                child_capsule_id=capsule_id,
                capsule_type=capsule_type,
                relationship_type=relationship_type,
                attribution_weight=attribution_weight,
                timestamp=timestamp,
            )

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

    async def _register_lineage_edge(
        self,
        session: AsyncSession,
        parent_capsule_id: str,
        child_capsule_id: str,
        capsule_type: str,
        relationship_type: str = "derived_from",
        attribution_weight: float = 1.0,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Register a lineage edge in both the in-memory graph and database.

        Args:
            session: SQLAlchemy async session
            parent_capsule_id: Parent (source) capsule ID
            child_capsule_id: Child (target) capsule ID
            capsule_type: Type of the child capsule
            relationship_type: Type of relationship
            attribution_weight: Weight for temporal justice
            timestamp: Creation timestamp
        """
        timestamp = timestamp or datetime.now(timezone.utc)

        # 1. Add edge to in-memory Constellations graph
        self._graph_store.add_edge(
            parent_id=parent_capsule_id,
            child_id=child_capsule_id,
            relationship_type=relationship_type,
            attribution_weight=attribution_weight,
            created_at=timestamp.isoformat(),
        )

        # 2. Register in lineage system for temporal justice
        try:
            capsule_lineage_system.register_capsule_node(
                capsule_id=child_capsule_id,
                creator_id="system",  # Would be extracted from auth context
                capsule_type=capsule_type,
                base_value=Decimal("100.0"),
                parent_capsule_ids=[parent_capsule_id],
            )
        except Exception as e:
            # Log but don't fail - lineage system is supplementary
            logger.warning(f"Failed to register capsule in lineage system: {e}")

        # 3. Persist edge to database
        edge = LineageEdgeModel(
            parent_capsule_id=parent_capsule_id,
            child_capsule_id=child_capsule_id,
            relationship_type=relationship_type,
            attribution_weight=str(attribution_weight),
            created_at=timestamp,
        )
        session.add(edge)

        logger.debug(
            f"Registered lineage edge: {parent_capsule_id} → {child_capsule_id} "
            f"(type={relationship_type}, weight={attribution_weight})"
        )

    def _track_capsule_in_chain(self, chain_id: str, capsule_id: str) -> None:
        """Track a capsule as part of a chain for sealing."""
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
        """Get ancestor capsule IDs from the lineage graph."""
        return self._graph_store.ancestors(capsule_id, depth)

    async def get_descendants(
        self, capsule_id: str, depth: Optional[int] = None
    ) -> List[str]:
        """Get descendant capsule IDs from the lineage graph."""
        return self._graph_store.descendants(capsule_id, depth)

    async def get_lineage(self, capsule_id: str) -> List[str]:
        """Get the lineage path from genesis to this capsule."""
        return self._graph_store.lineage(capsule_id)

    async def load_lineage_from_database(self, session: AsyncSession) -> int:
        """
        Load lineage edges from database into the in-memory graph.

        This should be called on application startup to restore
        the lineage graph from persisted data.

        Returns:
            Number of edges loaded
        """
        result = await session.execute(select(LineageEdgeModel))
        edges = result.scalars().all()

        for edge in edges:
            self._graph_store.add_edge(
                parent_id=edge.parent_capsule_id,
                child_id=edge.child_capsule_id,
                relationship_type=edge.relationship_type,
                attribution_weight=float(edge.attribution_weight),
                created_at=edge.created_at.isoformat() if edge.created_at else None,
            )

        logger.info(f"Loaded {len(edges)} lineage edges from database")
        return len(edges)


# Global singleton instance
capsule_lifecycle_service = CapsuleLifecycleService()
