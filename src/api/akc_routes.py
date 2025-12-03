"""
AKC (Attribution Key Clustering) API Routes

This module provides REST API endpoints for managing knowledge sources,
clusters, and ancestral attribution tracking.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4

from quart import Blueprint, request, jsonify, current_app
from pydantic import BaseModel, Field, ValidationError

from ..attribution.akc_system import (
    AKCSystem,
    KnowledgeSource,
    KnowledgeSourceType,
    VerificationStatus,
)
from ..attribution.knowledge_discovery import KnowledgeDiscovery
from ..economic.fcde_engine import FCDEEngine
from ..economic.common_attribution_fund import CommonAttributionFund
from ..api.utils import validate_json_request, handle_async_error
from ..api.dependencies import get_current_user

logger = logging.getLogger(__name__)

# Create blueprint
akc_bp = Blueprint("akc", __name__, url_prefix="/api/akc")

# Initialize AKC system (will be properly initialized in app startup)
akc_system: Optional[AKCSystem] = None
knowledge_discovery: Optional[KnowledgeDiscovery] = None


class KnowledgeSourceCreateRequest(BaseModel):
    """Request model for creating a knowledge source"""

    source_type: KnowledgeSourceType
    title: str
    authors: List[str]
    publication_date: Optional[datetime] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    repository_url: Optional[str] = None
    license: Optional[str] = None
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeClusterCreateRequest(BaseModel):
    """Request model for creating a knowledge cluster"""

    name: str
    description: str
    source_ids: List[str]


class KnowledgeDiscoveryRequest(BaseModel):
    """Request model for knowledge discovery from content"""

    content: str
    auto_verify: bool = False


class KnowledgeVerificationRequest(BaseModel):
    """Request model for verifying a knowledge source"""

    source_id: str
    verification_status: VerificationStatus
    confidence_score: float = Field(ge=0, le=1)


class KnowledgeUsageTrackingRequest(BaseModel):
    """Request model for tracking knowledge usage"""

    source_ids: List[str]
    usage_context: str
    capsule_id: str


class KnowledgeSearchRequest(BaseModel):
    """Request model for searching knowledge sources"""

    query: str
    source_type: Optional[KnowledgeSourceType] = None
    verified_only: bool = False
    limit: int = Field(default=50, le=100)


async def initialize_akc_system():
    """Initialize the AKC system components"""
    global akc_system, knowledge_discovery

    if akc_system is None:
        # Initialize dependencies
        fcde_engine = FCDEEngine()
        caf = CommonAttributionFund()

        # Initialize AKC system
        akc_system = AKCSystem(fcde_engine, caf)
        await akc_system.initialize()

        # Initialize knowledge discovery
        knowledge_discovery = KnowledgeDiscovery()

        logger.info("AKC system initialized successfully")


@akc_bp.before_app_serving
async def setup_akc_system():
    """Setup AKC system before app starts serving"""
    await initialize_akc_system()


@akc_bp.route("/sources", methods=["POST"])
async def create_knowledge_source():
    """Create a new knowledge source"""
    try:
        if not akc_system:
            await initialize_akc_system()

        # Validate request
        data = await validate_json_request(KnowledgeSourceCreateRequest)

        # Create knowledge source
        source = await akc_system.register_knowledge_source(
            source_type=data.source_type,
            title=data.title,
            authors=data.authors,
            publication_date=data.publication_date,
            url=data.url,
            doi=data.doi,
            isbn=data.isbn,
            repository_url=data.repository_url,
            license=data.license,
            content_hash=data.content_hash,
            metadata=data.metadata,
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Knowledge source created successfully",
                    "source": source.to_dict(),
                }
            ),
            201,
        )

    except ValidationError as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid request data",
                    "errors": e.errors(),
                }
            ),
            400,
        )
    except Exception as e:
        return await handle_async_error(e, "Failed to create knowledge source")


@akc_bp.route("/sources/<source_id>", methods=["GET"])
async def get_knowledge_source(source_id: str):
    """Get a specific knowledge source"""
    try:
        if not akc_system:
            await initialize_akc_system()

        # Check if source exists
        if source_id not in akc_system.knowledge_sources:
            return (
                jsonify({"status": "error", "message": "Knowledge source not found"}),
                404,
            )

        source = akc_system.knowledge_sources[source_id]

        return jsonify({"status": "success", "source": source.to_dict()})

    except Exception as e:
        return await handle_async_error(e, "Failed to get knowledge source")


@akc_bp.route("/sources", methods=["GET"])
async def list_knowledge_sources():
    """List all knowledge sources with optional filtering"""
    try:
        if not akc_system:
            await initialize_akc_system()

        # Get query parameters
        source_type = request.args.get("source_type")
        verified_only = request.args.get("verified_only", "false").lower() == "true"
        limit = int(request.args.get("limit", 50))

        # Filter sources
        sources = list(akc_system.knowledge_sources.values())

        if source_type:
            try:
                source_type_enum = KnowledgeSourceType(source_type)
                sources = [s for s in sources if s.type == source_type_enum]
            except ValueError:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"Invalid source type: {source_type}",
                        }
                    ),
                    400,
                )

        if verified_only:
            sources = [
                s
                for s in sources
                if s.verification_status == VerificationStatus.VERIFIED
            ]

        # Apply limit
        sources = sources[:limit]

        return jsonify(
            {
                "status": "success",
                "sources": [s.to_dict() for s in sources],
                "total": len(sources),
            }
        )

    except Exception as e:
        return await handle_async_error(e, "Failed to list knowledge sources")


@akc_bp.route("/sources/search", methods=["POST"])
async def search_knowledge_sources():
    """Search knowledge sources"""
    try:
        if not akc_system:
            await initialize_akc_system()

        # Validate request
        data = await validate_json_request(KnowledgeSearchRequest)

        # Search sources
        results = await akc_system.search_knowledge_sources(
            query=data.query,
            source_type=data.source_type,
            verified_only=data.verified_only,
        )

        # Apply limit
        results = results[: data.limit]

        return jsonify(
            {
                "status": "success",
                "results": [s.to_dict() for s in results],
                "total": len(results),
            }
        )

    except ValidationError as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid request data",
                    "errors": e.errors(),
                }
            ),
            400,
        )
    except Exception as e:
        return await handle_async_error(e, "Failed to search knowledge sources")


@akc_bp.route("/sources/discover", methods=["POST"])
async def discover_knowledge_sources():
    """Discover knowledge sources from content"""
    try:
        if not akc_system or not knowledge_discovery:
            await initialize_akc_system()

        # Validate request
        data = await validate_json_request(KnowledgeDiscoveryRequest)

        # Discover sources
        async with knowledge_discovery as kd:
            discovered_sources = await kd.discover_from_content(data.content)

            # Auto-verify if requested
            if data.auto_verify:
                for source in discovered_sources:
                    status, confidence = await kd.verify_source_external(source)
                    source.verification_status = status
                    source.confidence_score = confidence

            # Register discovered sources
            registered_sources = []
            for source in discovered_sources:
                if source.id not in akc_system.knowledge_sources:
                    akc_system.knowledge_sources[source.id] = source
                    await akc_system._save_knowledge_source(source)
                    registered_sources.append(source)

        return jsonify(
            {
                "status": "success",
                "message": f"Discovered {len(registered_sources)} new knowledge sources",
                "sources": [s.to_dict() for s in registered_sources],
            }
        )

    except ValidationError as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid request data",
                    "errors": e.errors(),
                }
            ),
            400,
        )
    except Exception as e:
        return await handle_async_error(e, "Failed to discover knowledge sources")


@akc_bp.route("/sources/<source_id>/verify", methods=["POST"])
async def verify_knowledge_source(source_id: str):
    """Verify a knowledge source"""
    try:
        if not akc_system:
            await initialize_akc_system()

        # Validate request
        data = await validate_json_request(KnowledgeVerificationRequest)

        # Get current user for verification tracking
        user = await get_current_user()
        verifier_id = user.get("id", "anonymous") if user else "anonymous"

        # Verify source
        await akc_system.verify_knowledge_source(
            source_id=source_id,
            verifier_id=verifier_id,
            verification_status=data.verification_status,
            confidence_score=data.confidence_score,
        )

        return jsonify(
            {"status": "success", "message": "Knowledge source verified successfully"}
        )

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except ValidationError as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid request data",
                    "errors": e.errors(),
                }
            ),
            400,
        )
    except Exception as e:
        return await handle_async_error(e, "Failed to verify knowledge source")


@akc_bp.route("/clusters", methods=["POST"])
async def create_knowledge_cluster():
    """Create a new knowledge cluster"""
    try:
        if not akc_system:
            await initialize_akc_system()

        # Validate request
        data = await validate_json_request(KnowledgeClusterCreateRequest)

        # Create cluster
        cluster = await akc_system.create_knowledge_cluster(
            name=data.name, description=data.description, source_ids=data.source_ids
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Knowledge cluster created successfully",
                    "cluster": {
                        "id": cluster.id,
                        "name": cluster.name,
                        "description": cluster.description,
                        "source_count": len(cluster.sources),
                        "cluster_hash": cluster.cluster_hash,
                        "created_at": cluster.created_at.isoformat(),
                        "updated_at": cluster.updated_at.isoformat(),
                    },
                }
            ),
            201,
        )

    except ValidationError as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid request data",
                    "errors": e.errors(),
                }
            ),
            400,
        )
    except Exception as e:
        return await handle_async_error(e, "Failed to create knowledge cluster")


@akc_bp.route("/clusters/<cluster_id>", methods=["GET"])
async def get_knowledge_cluster(cluster_id: str):
    """Get a specific knowledge cluster"""
    try:
        if not akc_system:
            await initialize_akc_system()

        # Check if cluster exists
        if cluster_id not in akc_system.knowledge_clusters:
            return (
                jsonify({"status": "error", "message": "Knowledge cluster not found"}),
                404,
            )

        cluster = akc_system.knowledge_clusters[cluster_id]

        return jsonify(
            {
                "status": "success",
                "cluster": {
                    "id": cluster.id,
                    "name": cluster.name,
                    "description": cluster.description,
                    "sources": [s.to_dict() for s in cluster.sources],
                    "cluster_hash": cluster.cluster_hash,
                    "total_usage": cluster.get_total_usage(),
                    "primary_contributors": cluster.get_primary_contributors(),
                    "created_at": cluster.created_at.isoformat(),
                    "updated_at": cluster.updated_at.isoformat(),
                },
            }
        )

    except Exception as e:
        return await handle_async_error(e, "Failed to get knowledge cluster")


@akc_bp.route("/clusters", methods=["GET"])
async def list_knowledge_clusters():
    """List all knowledge clusters"""
    try:
        if not akc_system:
            await initialize_akc_system()

        # Get query parameters
        limit = int(request.args.get("limit", 50))

        # Get clusters
        clusters = list(akc_system.knowledge_clusters.values())[:limit]

        return jsonify(
            {
                "status": "success",
                "clusters": [
                    {
                        "id": cluster.id,
                        "name": cluster.name,
                        "description": cluster.description,
                        "source_count": len(cluster.sources),
                        "total_usage": cluster.get_total_usage(),
                        "created_at": cluster.created_at.isoformat(),
                        "updated_at": cluster.updated_at.isoformat(),
                    }
                    for cluster in clusters
                ],
                "total": len(clusters),
            }
        )

    except Exception as e:
        return await handle_async_error(e, "Failed to list knowledge clusters")


@akc_bp.route("/usage/track", methods=["POST"])
async def track_knowledge_usage():
    """Track usage of knowledge sources"""
    try:
        if not akc_system:
            await initialize_akc_system()

        # Validate request
        data = await validate_json_request(KnowledgeUsageTrackingRequest)

        # Track usage
        await akc_system.track_knowledge_usage(
            source_ids=data.source_ids,
            usage_context=data.usage_context,
            capsule_id=data.capsule_id,
        )

        return jsonify(
            {"status": "success", "message": "Knowledge usage tracked successfully"}
        )

    except ValidationError as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Invalid request data",
                    "errors": e.errors(),
                }
            ),
            400,
        )
    except Exception as e:
        return await handle_async_error(e, "Failed to track knowledge usage")


@akc_bp.route("/lineage/<capsule_id>", methods=["GET"])
async def get_knowledge_lineage(capsule_id: str):
    """Get knowledge lineage for a capsule"""
    try:
        if not akc_system:
            await initialize_akc_system()

        # Get lineage
        lineage = await akc_system.get_knowledge_lineage(capsule_id)

        return jsonify({"status": "success", "lineage": lineage})

    except Exception as e:
        return await handle_async_error(e, "Failed to get knowledge lineage")


@akc_bp.route("/dividends/calculate", methods=["POST"])
async def calculate_ancestral_dividends():
    """Calculate ancestral dividends for a capsule"""
    try:
        if not akc_system:
            await initialize_akc_system()

        # Get request data
        data = await request.get_json()
        total_revenue = data.get("total_revenue", 0)
        capsule_id = data.get("capsule_id")

        if not capsule_id:
            return (
                jsonify({"status": "error", "message": "capsule_id is required"}),
                400,
            )

        # Calculate dividends
        dividends = await akc_system.calculate_ancestral_dividends(
            total_revenue=total_revenue, capsule_id=capsule_id
        )

        return jsonify(
            {
                "status": "success",
                "dividends": dividends,
                "total_distributed": sum(dividends.values()),
            }
        )

    except Exception as e:
        return await handle_async_error(e, "Failed to calculate ancestral dividends")


@akc_bp.route("/stats", methods=["GET"])
async def get_akc_stats():
    """Get AKC system statistics"""
    try:
        if not akc_system:
            await initialize_akc_system()

        # Get stats
        stats = await akc_system.get_system_stats()

        return jsonify({"status": "success", "stats": stats})

    except Exception as e:
        return await handle_async_error(e, "Failed to get AKC statistics")


@akc_bp.route("/health", methods=["GET"])
async def health_check():
    """Health check endpoint"""
    try:
        if not akc_system:
            await initialize_akc_system()

        return jsonify(
            {
                "status": "healthy",
                "service": "AKC System",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ),
            503,
        )
