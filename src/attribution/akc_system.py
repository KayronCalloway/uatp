"""
Attribution Key Clustering (AKC) System

This module implements the Attribution Key Clustering system for tracking
ancestral knowledge lineage and enabling post-labor economics through
transparent attribution of knowledge sources.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import CapsuleModel, Attribution
from ..database.connection import get_async_session
from ..economic.fcde_engine import FCDEEngine
from ..economic.common_attribution_fund import CommonAttributionFund

logger = logging.getLogger(__name__)


class KnowledgeSourceType(str, Enum):
    """Types of knowledge sources that can be attributed"""

    ACADEMIC_PAPER = "academic_paper"
    BOOK = "book"
    CODE_REPOSITORY = "code_repository"
    DATASET = "dataset"
    DOCUMENTATION = "documentation"
    BLOG_POST = "blog_post"
    PATENT = "patent"
    CONVERSATION = "conversation"
    TRAINING_DATA = "training_data"
    EXPERT_KNOWLEDGE = "expert_knowledge"
    CULTURAL_KNOWLEDGE = "cultural_knowledge"
    HISTORICAL_RECORD = "historical_record"


class VerificationStatus(str, Enum):
    """Verification status of knowledge sources"""

    VERIFIED = "verified"
    PENDING = "pending"
    DISPUTED = "disputed"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


@dataclass
class KnowledgeSource:
    """Represents a source of knowledge with attribution metadata"""

    id: str
    type: KnowledgeSourceType
    title: str
    authors: List[str]
    publication_date: Optional[datetime] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    repository_url: Optional[str] = None
    license: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    confidence_score: float = 0.0
    usage_count: int = 0
    last_verified: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "authors": self.authors,
            "publication_date": self.publication_date.isoformat()
            if self.publication_date
            else None,
            "url": self.url,
            "doi": self.doi,
            "isbn": self.isbn,
            "repository_url": self.repository_url,
            "license": self.license,
            "verification_status": self.verification_status.value,
            "confidence_score": self.confidence_score,
            "usage_count": self.usage_count,
            "last_verified": self.last_verified.isoformat()
            if self.last_verified
            else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeSource":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            type=KnowledgeSourceType(data["type"]),
            title=data["title"],
            authors=data["authors"],
            publication_date=datetime.fromisoformat(data["publication_date"])
            if data["publication_date"]
            else None,
            url=data.get("url"),
            doi=data.get("doi"),
            isbn=data.get("isbn"),
            repository_url=data.get("repository_url"),
            license=data.get("license"),
            verification_status=VerificationStatus(
                data.get("verification_status", "unknown")
            ),
            confidence_score=data.get("confidence_score", 0.0),
            usage_count=data.get("usage_count", 0),
            last_verified=datetime.fromisoformat(data["last_verified"])
            if data.get("last_verified")
            else None,
            metadata=data.get("metadata", {}),
        )


@dataclass
class KnowledgeCluster:
    """Represents a cluster of related knowledge sources"""

    id: str
    name: str
    description: str
    sources: List[KnowledgeSource] = field(default_factory=list)
    cluster_hash: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        self.update_cluster_hash()

    def update_cluster_hash(self):
        """Update the cluster hash based on source content"""
        content = json.dumps([s.to_dict() for s in self.sources], sort_keys=True)
        self.cluster_hash = hashlib.sha256(content.encode()).hexdigest()
        self.updated_at = datetime.now(timezone.utc)

    def add_source(self, source: KnowledgeSource):
        """Add a knowledge source to the cluster"""
        self.sources.append(source)
        self.update_cluster_hash()

    def remove_source(self, source_id: str):
        """Remove a knowledge source from the cluster"""
        self.sources = [s for s in self.sources if s.id != source_id]
        self.update_cluster_hash()

    def get_total_usage(self) -> int:
        """Get total usage count across all sources in cluster"""
        return sum(s.usage_count for s in self.sources)

    def get_primary_contributors(self) -> List[str]:
        """Get list of primary contributors (authors) from all sources"""
        contributors = set()
        for source in self.sources:
            contributors.update(source.authors)
        return list(contributors)


class AKCSystem:
    """Attribution Key Clustering System for tracking knowledge lineage"""

    def __init__(self, fcde_engine: FCDEEngine, caf: CommonAttributionFund):
        self.fcde_engine = fcde_engine
        self.caf = caf
        self.knowledge_sources: Dict[str, KnowledgeSource] = {}
        self.knowledge_clusters: Dict[str, KnowledgeCluster] = {}
        self.source_registry: Dict[
            str, Set[str]
        ] = {}  # Maps content hash to source IDs

    async def initialize(self):
        """Initialize the AKC system"""
        await self._load_knowledge_sources()
        await self._load_knowledge_clusters()
        logger.info("AKC System initialized")

    async def _load_knowledge_sources(self):
        """Load knowledge sources from database"""
        async with get_async_session() as session:
            stmt = select(CapsuleModel).where(CapsuleModel.type == "akc")
            result = await session.execute(stmt)
            capsules = result.scalars().all()

            for capsule in capsules:
                if capsule.payload and "knowledge_source" in capsule.payload:
                    source_data = capsule.payload["knowledge_source"]
                    source = KnowledgeSource.from_dict(source_data)
                    self.knowledge_sources[source.id] = source

    async def _load_knowledge_clusters(self):
        """Load knowledge clusters from database"""
        async with get_async_session() as session:
            stmt = select(CapsuleModel).where(CapsuleModel.type == "akc_cluster")
            result = await session.execute(stmt)
            capsules = result.scalars().all()

            for capsule in capsules:
                if capsule.payload and "knowledge_cluster" in capsule.payload:
                    cluster_data = capsule.payload["knowledge_cluster"]
                    cluster = KnowledgeCluster(
                        id=cluster_data["id"],
                        name=cluster_data["name"],
                        description=cluster_data["description"],
                        sources=[
                            self.knowledge_sources.get(
                                source_id, KnowledgeSource.from_dict(source_data)
                            )
                            for source_id, source_data in cluster_data.get(
                                "sources", {}
                            ).items()
                        ],
                    )
                    self.knowledge_clusters[cluster.id] = cluster

    async def register_knowledge_source(
        self,
        source_type: KnowledgeSourceType,
        title: str,
        authors: List[str],
        content_hash: Optional[str] = None,
        **kwargs,
    ) -> KnowledgeSource:
        """Register a new knowledge source"""
        source = KnowledgeSource(
            id=str(uuid.uuid4()),
            type=source_type,
            title=title,
            authors=authors,
            **kwargs,
        )

        # Store in memory registry
        self.knowledge_sources[source.id] = source

        # Add to content hash registry if provided
        if content_hash:
            if content_hash not in self.source_registry:
                self.source_registry[content_hash] = set()
            self.source_registry[content_hash].add(source.id)

        # Persist to database
        await self._save_knowledge_source(source)

        logger.info(
            f"Registered knowledge source: {source.title} by {', '.join(authors)}"
        )
        return source

    async def _save_knowledge_source(self, source: KnowledgeSource):
        """Save knowledge source to database as AKC capsule"""
        async with get_async_session() as session:
            capsule = CapsuleModel(
                id=str(uuid.uuid4()),
                type="akc",
                payload={
                    "knowledge_source": source.to_dict(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                agent_id="akc_system",
                reasoning_trace="Knowledge source registration",
                created_at=datetime.now(timezone.utc),
            )
            session.add(capsule)
            await session.commit()

    async def discover_sources_from_content(
        self, content: str
    ) -> List[KnowledgeSource]:
        """Discover knowledge sources that may have contributed to content"""
        discovered_sources = []

        # Hash the content for lookup
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check if we have direct matches
        if content_hash in self.source_registry:
            source_ids = self.source_registry[content_hash]
            discovered_sources.extend(
                [
                    self.knowledge_sources[source_id]
                    for source_id in source_ids
                    if source_id in self.knowledge_sources
                ]
            )

        # Use heuristic discovery methods
        discovered_sources.extend(await self._heuristic_source_discovery(content))

        return discovered_sources

    async def _heuristic_source_discovery(self, content: str) -> List[KnowledgeSource]:
        """Use heuristic methods to discover potential knowledge sources"""
        potential_sources = []

        # Look for citations, DOIs, URLs, etc.
        import re

        # DOI pattern
        doi_pattern = r"10\.\d{4,}/[^\s]+"
        dois = re.findall(doi_pattern, content)

        # URL pattern
        url_pattern = r"https?://[^\s]+"
        urls = re.findall(url_pattern, content)

        # Look for sources that match these patterns
        for source in self.knowledge_sources.values():
            if source.doi and any(source.doi in content for doi in dois):
                potential_sources.append(source)
            elif source.url and any(source.url in content for url in urls):
                potential_sources.append(source)
            elif any(author.lower() in content.lower() for author in source.authors):
                # Author name appears in content
                potential_sources.append(source)

        return potential_sources

    async def create_knowledge_cluster(
        self, name: str, description: str, source_ids: List[str]
    ) -> KnowledgeCluster:
        """Create a new knowledge cluster"""
        sources = [
            self.knowledge_sources[source_id]
            for source_id in source_ids
            if source_id in self.knowledge_sources
        ]

        cluster = KnowledgeCluster(
            id=str(uuid.uuid4()), name=name, description=description, sources=sources
        )

        self.knowledge_clusters[cluster.id] = cluster
        await self._save_knowledge_cluster(cluster)

        logger.info(f"Created knowledge cluster: {name} with {len(sources)} sources")
        return cluster

    async def _save_knowledge_cluster(self, cluster: KnowledgeCluster):
        """Save knowledge cluster to database"""
        async with get_async_session() as session:
            capsule = CapsuleModel(
                id=str(uuid.uuid4()),
                type="akc_cluster",
                payload={
                    "knowledge_cluster": {
                        "id": cluster.id,
                        "name": cluster.name,
                        "description": cluster.description,
                        "sources": {s.id: s.to_dict() for s in cluster.sources},
                        "cluster_hash": cluster.cluster_hash,
                        "created_at": cluster.created_at.isoformat(),
                        "updated_at": cluster.updated_at.isoformat(),
                    }
                },
                agent_id="akc_system",
                reasoning_trace="Knowledge cluster creation",
                created_at=datetime.now(timezone.utc),
            )
            session.add(capsule)
            await session.commit()

    async def track_knowledge_usage(
        self, source_ids: List[str], usage_context: str, capsule_id: str
    ):
        """Track usage of knowledge sources"""
        for source_id in source_ids:
            if source_id in self.knowledge_sources:
                source = self.knowledge_sources[source_id]
                source.usage_count += 1

                # Update verification status based on usage
                if (
                    source.usage_count > 10
                    and source.verification_status == VerificationStatus.UNKNOWN
                ):
                    source.verification_status = VerificationStatus.PENDING

                # Save updated source
                await self._save_knowledge_source(source)

                # Record attribution for potential payouts
                await self._record_attribution(source, usage_context, capsule_id)

    async def _record_attribution(
        self, source: KnowledgeSource, usage_context: str, capsule_id: str
    ):
        """Record attribution for potential dividend payouts"""
        async with get_async_session() as session:
            attribution = Attribution(
                id=str(uuid.uuid4()),
                capsule_id=capsule_id,
                contributor_id=f"akc_source_{source.id}",
                contribution_type="knowledge_source",
                contribution_value=source.confidence_score,
                usage_context=usage_context,
                created_at=datetime.now(timezone.utc),
            )
            session.add(attribution)
            await session.commit()

    async def calculate_ancestral_dividends(
        self, total_revenue: float, capsule_id: str
    ) -> Dict[str, float]:
        """Calculate dividend payouts for ancestral knowledge contributors"""
        dividends = {}

        # Get all attributions for this capsule
        async with get_async_session() as session:
            stmt = select(Attribution).where(Attribution.capsule_id == capsule_id)
            result = await session.execute(stmt)
            attributions = result.scalars().all()

            # Calculate total contribution value
            total_contribution = sum(attr.contribution_value for attr in attributions)

            if total_contribution > 0:
                # Distribute dividends proportionally
                for attribution in attributions:
                    if attribution.contributor_id.startswith("akc_source_"):
                        source_id = attribution.contributor_id.replace(
                            "akc_source_", ""
                        )
                        if source_id in self.knowledge_sources:
                            source = self.knowledge_sources[source_id]

                            # Calculate dividend based on contribution value
                            dividend_percentage = (
                                attribution.contribution_value / total_contribution
                            )
                            dividend_amount = total_revenue * dividend_percentage

                            # Distribute among authors
                            author_count = len(source.authors)
                            if author_count > 0:
                                per_author_dividend = dividend_amount / author_count
                                for author in source.authors:
                                    if author in dividends:
                                        dividends[author] += per_author_dividend
                                    else:
                                        dividends[author] = per_author_dividend

        return dividends

    async def verify_knowledge_source(
        self,
        source_id: str,
        verifier_id: str,
        verification_status: VerificationStatus,
        confidence_score: float,
    ):
        """Verify a knowledge source"""
        if source_id not in self.knowledge_sources:
            raise ValueError(f"Knowledge source {source_id} not found")

        source = self.knowledge_sources[source_id]
        source.verification_status = verification_status
        source.confidence_score = confidence_score
        source.last_verified = datetime.now(timezone.utc)

        await self._save_knowledge_source(source)

        logger.info(
            f"Verified knowledge source {source.title}: {verification_status.value}"
        )

    async def get_knowledge_lineage(self, capsule_id: str) -> Dict[str, Any]:
        """Get complete knowledge lineage for a capsule"""
        lineage = {
            "capsule_id": capsule_id,
            "sources": [],
            "clusters": [],
            "total_sources": 0,
            "verified_sources": 0,
            "total_usage": 0,
        }

        # Get attributions for this capsule
        async with get_async_session() as session:
            stmt = select(Attribution).where(Attribution.capsule_id == capsule_id)
            result = await session.execute(stmt)
            attributions = result.scalars().all()

            for attribution in attributions:
                if attribution.contributor_id.startswith("akc_source_"):
                    source_id = attribution.contributor_id.replace("akc_source_", "")
                    if source_id in self.knowledge_sources:
                        source = self.knowledge_sources[source_id]
                        lineage["sources"].append(source.to_dict())
                        lineage["total_sources"] += 1
                        lineage["total_usage"] += source.usage_count

                        if source.verification_status == VerificationStatus.VERIFIED:
                            lineage["verified_sources"] += 1

        return lineage

    async def search_knowledge_sources(
        self,
        query: str,
        source_type: Optional[KnowledgeSourceType] = None,
        verified_only: bool = False,
    ) -> List[KnowledgeSource]:
        """Search knowledge sources"""
        results = []

        for source in self.knowledge_sources.values():
            # Filter by type if specified
            if source_type and source.type != source_type:
                continue

            # Filter by verification status if specified
            if (
                verified_only
                and source.verification_status != VerificationStatus.VERIFIED
            ):
                continue

            # Simple text search
            if (
                query.lower() in source.title.lower()
                or any(query.lower() in author.lower() for author in source.authors)
                or (source.url and query.lower() in source.url.lower())
            ):
                results.append(source)

        # Sort by usage count and confidence score
        results.sort(key=lambda s: (s.usage_count, s.confidence_score), reverse=True)

        return results

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get AKC system statistics"""
        stats = {
            "total_sources": len(self.knowledge_sources),
            "total_clusters": len(self.knowledge_clusters),
            "verified_sources": sum(
                1
                for s in self.knowledge_sources.values()
                if s.verification_status == VerificationStatus.VERIFIED
            ),
            "total_usage": sum(s.usage_count for s in self.knowledge_sources.values()),
            "source_types": {},
            "top_contributors": [],
        }

        # Count by source type
        for source in self.knowledge_sources.values():
            source_type = source.type.value
            if source_type in stats["source_types"]:
                stats["source_types"][source_type] += 1
            else:
                stats["source_types"][source_type] = 1

        # Get top contributors
        contributor_usage = {}
        for source in self.knowledge_sources.values():
            for author in source.authors:
                if author in contributor_usage:
                    contributor_usage[author] += source.usage_count
                else:
                    contributor_usage[author] = source.usage_count

        stats["top_contributors"] = sorted(
            contributor_usage.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return stats
