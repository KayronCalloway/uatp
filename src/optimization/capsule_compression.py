"""
Capsule Compression and Pruning System for UATP Engine.
Implements intelligent compression, deduplication, and lifecycle management.
"""

import hashlib
import json
import logging
import lzma
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from src.audit.events import audit_emitter
from src.capsule_schema import AnyCapsule, CapsuleType

logger = logging.getLogger(__name__)


class CompressionMethod(str, Enum):
    """Compression methods for capsules."""

    NONE = "none"
    ZLIB = "zlib"
    LZMA = "lzma"
    CUSTOM = "custom"


class PruningStrategy(str, Enum):
    """Strategies for capsule pruning."""

    AGE_BASED = "age_based"
    USAGE_BASED = "usage_based"
    DEPENDENCY_BASED = "dependency_based"
    SEMANTIC_BASED = "semantic_based"
    HYBRID = "hybrid"


@dataclass
class CompressionResult:
    """Result of capsule compression operation."""

    original_size: int
    compressed_size: int
    compression_ratio: float
    method: CompressionMethod
    compression_time: float
    decompression_time: Optional[float] = None

    def space_saved(self) -> int:
        """Calculate space saved in bytes."""
        return self.original_size - self.compressed_size

    def space_saved_percentage(self) -> float:
        """Calculate space saved as percentage."""
        if self.original_size == 0:
            return 0.0
        return (self.space_saved() / self.original_size) * 100


@dataclass
class CompressedCapsule:
    """Compressed capsule container."""

    capsule_id: str
    compressed_data: bytes
    compression_method: CompressionMethod
    original_hash: str
    compressed_hash: str
    metadata: Dict[str, Any]
    compression_timestamp: datetime
    original_size: int
    compressed_size: int

    def get_compression_ratio(self) -> float:
        """Get compression ratio."""
        if self.original_size == 0:
            return 1.0
        return self.compressed_size / self.original_size


@dataclass
class PruningDecision:
    """Decision about whether to prune a capsule."""

    capsule_id: str
    should_prune: bool
    reason: str
    confidence: float
    strategy: PruningStrategy
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DuplicationAnalysis:
    """Analysis of capsule duplication."""

    capsule_id: str
    duplicate_groups: List[List[str]]
    similarity_scores: Dict[str, float]
    content_hash: str
    semantic_fingerprint: str

    def has_duplicates(self) -> bool:
        """Check if capsule has duplicates."""
        return len(self.duplicate_groups) > 0 and any(
            len(group) > 1 for group in self.duplicate_groups
        )


class CapsuleCompressor:
    """Handles capsule compression and decompression."""

    def __init__(self):
        self.compression_stats = {}
        self.compressed_capsules: Dict[str, CompressedCapsule] = {}

    def compress_capsule(
        self, capsule: AnyCapsule, method: CompressionMethod = CompressionMethod.ZLIB
    ) -> CompressionResult:
        """Compress a capsule using specified method."""

        start_time = datetime.now(timezone.utc)

        # Serialize capsule to JSON
        capsule_dict = self._capsule_to_dict(capsule)
        original_data = json.dumps(capsule_dict, sort_keys=True).encode("utf-8")
        original_size = len(original_data)

        # Apply compression
        if method == CompressionMethod.ZLIB:
            compressed_data = zlib.compress(original_data, level=9)
        elif method == CompressionMethod.LZMA:
            compressed_data = lzma.compress(original_data, preset=9)
        elif method == CompressionMethod.CUSTOM:
            compressed_data = self._custom_compress(original_data)
        else:
            compressed_data = original_data

        compressed_size = len(compressed_data)
        compression_time = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Store compressed capsule
        original_hash = hashlib.sha256(original_data).hexdigest()
        compressed_hash = hashlib.sha256(compressed_data).hexdigest()

        compressed_capsule = CompressedCapsule(
            capsule_id=capsule.capsule_id,
            compressed_data=compressed_data,
            compression_method=method,
            original_hash=original_hash,
            compressed_hash=compressed_hash,
            metadata={
                "capsule_type": capsule.capsule_type.value
                if hasattr(capsule.capsule_type, "value")
                else capsule.capsule_type,
                "original_status": capsule.status.value
                if hasattr(capsule.status, "value")
                else capsule.status,
                "compression_timestamp": datetime.now(timezone.utc).isoformat(),
            },
            compression_timestamp=datetime.now(timezone.utc),
            original_size=original_size,
            compressed_size=compressed_size,
        )

        self.compressed_capsules[capsule.capsule_id] = compressed_capsule

        # Create result
        result = CompressionResult(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compressed_size / original_size
            if original_size > 0
            else 1.0,
            method=method,
            compression_time=compression_time,
        )

        # Update statistics
        self._update_compression_stats(method, result)

        logger.info(
            f"Compressed capsule {capsule.capsule_id}: {result.space_saved_percentage():.1f}% space saved"
        )
        return result

    def decompress_capsule(self, capsule_id: str) -> Optional[Dict[str, Any]]:
        """Decompress a capsule and return its data."""

        if capsule_id not in self.compressed_capsules:
            return None

        compressed_capsule = self.compressed_capsules[capsule_id]
        start_time = datetime.now(timezone.utc)

        try:
            # Decompress data
            if compressed_capsule.compression_method == CompressionMethod.ZLIB:
                decompressed_data = zlib.decompress(compressed_capsule.compressed_data)
            elif compressed_capsule.compression_method == CompressionMethod.LZMA:
                decompressed_data = lzma.decompress(compressed_capsule.compressed_data)
            elif compressed_capsule.compression_method == CompressionMethod.CUSTOM:
                decompressed_data = self._custom_decompress(
                    compressed_capsule.compressed_data
                )
            else:
                decompressed_data = compressed_capsule.compressed_data

            # Verify integrity
            decompressed_hash = hashlib.sha256(decompressed_data).hexdigest()
            if decompressed_hash != compressed_capsule.original_hash:
                logger.error(f"Decompression integrity check failed for {capsule_id}")
                return None

            # Parse JSON
            capsule_dict = json.loads(decompressed_data.decode("utf-8"))

            decompression_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()
            logger.info(
                f"Decompressed capsule {capsule_id} in {decompression_time:.3f}s"
            )

            return capsule_dict

        except Exception as e:
            logger.error(f"Failed to decompress capsule {capsule_id}: {e}")
            return None

    def get_compression_statistics(self) -> Dict[str, Any]:
        """Get compression statistics."""
        return {
            "total_compressed": len(self.compressed_capsules),
            "method_stats": dict(self.compression_stats),
            "total_original_size": sum(
                c.original_size for c in self.compressed_capsules.values()
            ),
            "total_compressed_size": sum(
                c.compressed_size for c in self.compressed_capsules.values()
            ),
            "overall_compression_ratio": self._calculate_overall_ratio(),
        }

    def _capsule_to_dict(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Convert capsule to dictionary for compression."""
        return {
            "capsule_id": capsule.capsule_id,
            "capsule_type": capsule.capsule_type.value
            if hasattr(capsule.capsule_type, "value")
            else capsule.capsule_type,
            "version": capsule.version,
            "timestamp": capsule.timestamp.isoformat(),
            "status": capsule.status.value
            if hasattr(capsule.status, "value")
            else capsule.status,
            "verification": {
                "signature": capsule.verification.signature,
                "hash": capsule.verification.hash,
                "signer": capsule.verification.signer,
            },
            "payload": self._extract_payload(capsule),
        }

    def _extract_payload(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Extract payload from capsule based on type."""
        if hasattr(capsule, "reasoning_trace") and capsule.reasoning_trace:
            # Handle both .steps and .reasoning_steps field names
            steps = getattr(
                capsule.reasoning_trace,
                "reasoning_steps",
                getattr(capsule.reasoning_trace, "steps", []),
            )
            return {
                "type": "reasoning_trace",
                "data": {
                    "steps": [
                        {
                            "content": getattr(
                                step, "reasoning", getattr(step, "content", "")
                            ),
                            "step_type": getattr(
                                step, "operation", getattr(step, "step_type", "")
                            ),
                            "metadata": step.metadata,
                        }
                        for step in steps
                    ]
                },
            }
        # Add other payload types as needed
        return {"type": "generic", "data": {}}

    def _custom_compress(self, data: bytes) -> bytes:
        """Custom compression optimized for capsule data."""
        # Simple custom compression: remove common patterns
        compressed = data

        # Replace common JSON patterns
        patterns = [
            (b'"capsule_id":', b'"cid":'),
            (b'"timestamp":', b'"ts":'),
            (b'"reasoning_trace":', b'"rt":'),
            (b'"step_type":', b'"st":'),
            (b'"metadata":', b'"md":'),
        ]

        for original, replacement in patterns:
            compressed = compressed.replace(original, replacement)

        # Apply zlib after pattern replacement
        return zlib.compress(compressed, level=6)

    def _custom_decompress(self, data: bytes) -> bytes:
        """Custom decompression for capsule data."""
        # Decompress with zlib first
        decompressed = zlib.decompress(data)

        # Restore patterns
        patterns = [
            (b'"cid":', b'"capsule_id":'),
            (b'"ts":', b'"timestamp":'),
            (b'"rt":', b'"reasoning_trace":'),
            (b'"st":', b'"step_type":'),
            (b'"md":', b'"metadata":'),
        ]

        for replacement, original in patterns:
            decompressed = decompressed.replace(replacement, original)

        return decompressed

    def _update_compression_stats(
        self, method: CompressionMethod, result: CompressionResult
    ):
        """Update compression statistics."""
        if method not in self.compression_stats:
            self.compression_stats[method] = {
                "count": 0,
                "total_original_size": 0,
                "total_compressed_size": 0,
                "total_compression_time": 0.0,
                "best_ratio": 1.0,
                "worst_ratio": 1.0,
            }

        stats = self.compression_stats[method]
        stats["count"] += 1
        stats["total_original_size"] += result.original_size
        stats["total_compressed_size"] += result.compressed_size
        stats["total_compression_time"] += result.compression_time

        if stats["count"] == 1:
            stats["best_ratio"] = result.compression_ratio
            stats["worst_ratio"] = result.compression_ratio
        else:
            stats["best_ratio"] = min(stats["best_ratio"], result.compression_ratio)
            stats["worst_ratio"] = max(stats["worst_ratio"], result.compression_ratio)

    def _calculate_overall_ratio(self) -> float:
        """Calculate overall compression ratio."""
        total_original = sum(c.original_size for c in self.compressed_capsules.values())
        total_compressed = sum(
            c.compressed_size for c in self.compressed_capsules.values()
        )

        if total_original == 0:
            return 1.0
        return total_compressed / total_original


class CapsuleDeduplicator:
    """Handles capsule deduplication and similarity analysis."""

    def __init__(self):
        self.content_hashes: Dict[str, Set[str]] = {}
        self.semantic_fingerprints: Dict[str, str] = {}
        self.similarity_threshold = 0.85

    def analyze_duplicates(self, capsule: AnyCapsule) -> DuplicationAnalysis:
        """Analyze capsule for duplicates and similar content."""

        # Generate content hash
        content_hash = self._generate_content_hash(capsule)

        # Generate semantic fingerprint
        semantic_fingerprint = self._generate_semantic_fingerprint(capsule)

        # Find duplicate groups
        duplicate_groups = self._find_duplicate_groups(
            capsule.capsule_id, content_hash, semantic_fingerprint
        )

        # Calculate similarity scores
        similarity_scores = self._calculate_similarity_scores(
            capsule.capsule_id, semantic_fingerprint
        )

        # Store fingerprints
        self.semantic_fingerprints[capsule.capsule_id] = semantic_fingerprint

        if content_hash not in self.content_hashes:
            self.content_hashes[content_hash] = set()
        self.content_hashes[content_hash].add(capsule.capsule_id)

        return DuplicationAnalysis(
            capsule_id=capsule.capsule_id,
            duplicate_groups=duplicate_groups,
            similarity_scores=similarity_scores,
            content_hash=content_hash,
            semantic_fingerprint=semantic_fingerprint,
        )

    def _generate_content_hash(self, capsule: AnyCapsule) -> str:
        """Generate content hash for exact duplicate detection."""
        # Hash the essential content (excluding metadata like timestamps)
        content_parts = [
            capsule.capsule_type.value
            if hasattr(capsule.capsule_type, "value")
            else capsule.capsule_type,
            capsule.version,
        ]

        if hasattr(capsule, "reasoning_trace") and capsule.reasoning_trace:
            # Handle both .steps and .reasoning_steps field names
            steps = getattr(
                capsule.reasoning_trace,
                "reasoning_steps",
                getattr(capsule.reasoning_trace, "steps", []),
            )
            for step in steps:
                # Use 'reasoning' field (primary) or 'content' field (alias)
                content = getattr(step, "reasoning", getattr(step, "content", ""))
                content_parts.append(content)
                # Use 'operation' field (primary) or 'step_type' field (alias)
                step_type = getattr(step, "operation", getattr(step, "step_type", ""))
                content_parts.append(step_type)

        combined_content = "|".join(content_parts)
        return hashlib.sha256(combined_content.encode()).hexdigest()

    def _generate_semantic_fingerprint(self, capsule: AnyCapsule) -> str:
        """Generate semantic fingerprint for similarity detection."""
        # Extract key terms and concepts
        terms = set()

        if hasattr(capsule, "reasoning_trace") and capsule.reasoning_trace:
            # Handle both .steps and .reasoning_steps field names
            steps = getattr(
                capsule.reasoning_trace,
                "reasoning_steps",
                getattr(capsule.reasoning_trace, "steps", []),
            )
            for step in steps:
                # Simple term extraction (in production, use NLP)
                content = getattr(step, "reasoning", getattr(step, "content", ""))
                words = content.lower().split()
                significant_words = [w for w in words if len(w) > 3 and w.isalpha()]
                terms.update(significant_words[:10])  # Top 10 terms per step

        # Create fingerprint from sorted terms
        sorted_terms = sorted(terms)[:20]  # Top 20 terms overall
        fingerprint = hashlib.md5("|".join(sorted_terms).encode()).hexdigest()

        return fingerprint

    def _find_duplicate_groups(
        self, capsule_id: str, content_hash: str, semantic_fingerprint: str
    ) -> List[List[str]]:
        """Find groups of duplicate capsules."""
        duplicate_groups = []

        # Exact duplicates (same content hash)
        if content_hash in self.content_hashes:
            existing_capsules = self.content_hashes[content_hash]
            if len(existing_capsules) > 0:
                duplicate_groups.append(list(existing_capsules) + [capsule_id])

        # Semantic duplicates (similar fingerprints)
        similar_capsules = []
        for other_id, other_fingerprint in self.semantic_fingerprints.items():
            if other_id != capsule_id:
                similarity = self._calculate_fingerprint_similarity(
                    semantic_fingerprint, other_fingerprint
                )
                if similarity >= self.similarity_threshold:
                    similar_capsules.append(other_id)

        if similar_capsules:
            duplicate_groups.append(similar_capsules + [capsule_id])

        return duplicate_groups

    def _calculate_similarity_scores(
        self, capsule_id: str, semantic_fingerprint: str
    ) -> Dict[str, float]:
        """Calculate similarity scores with other capsules."""
        similarity_scores = {}

        for other_id, other_fingerprint in self.semantic_fingerprints.items():
            if other_id != capsule_id:
                similarity = self._calculate_fingerprint_similarity(
                    semantic_fingerprint, other_fingerprint
                )
                similarity_scores[other_id] = similarity

        return similarity_scores

    def _calculate_fingerprint_similarity(self, fp1: str, fp2: str) -> float:
        """Calculate similarity between two fingerprints."""
        # Simple Hamming distance for MD5 hashes
        if len(fp1) != len(fp2):
            return 0.0

        differences = sum(c1 != c2 for c1, c2 in zip(fp1, fp2))
        similarity = 1.0 - (differences / len(fp1))

        return similarity


class CapsulePruner:
    """Handles intelligent capsule pruning and lifecycle management."""

    def __init__(self):
        self.pruning_decisions: Dict[str, PruningDecision] = {}
        self.pruning_rules = self._initialize_pruning_rules()

    def should_prune_capsule(
        self,
        capsule: AnyCapsule,
        usage_stats: Dict[str, Any] = None,
        strategy: PruningStrategy = PruningStrategy.HYBRID,
    ) -> PruningDecision:
        """Determine if a capsule should be pruned."""

        if strategy == PruningStrategy.AGE_BASED:
            return self._age_based_pruning(capsule)
        elif strategy == PruningStrategy.USAGE_BASED:
            return self._usage_based_pruning(capsule, usage_stats or {})
        elif strategy == PruningStrategy.DEPENDENCY_BASED:
            return self._dependency_based_pruning(capsule)
        elif strategy == PruningStrategy.SEMANTIC_BASED:
            return self._semantic_based_pruning(capsule)
        else:
            return self._hybrid_pruning(capsule, usage_stats or {})

    def _age_based_pruning(self, capsule: AnyCapsule) -> PruningDecision:
        """Age-based pruning strategy."""
        age = datetime.now(timezone.utc) - capsule.timestamp

        # Different retention periods by capsule type
        retention_periods = {
            CapsuleType.REASONING_TRACE: timedelta(days=365),
            CapsuleType.PERSPECTIVE: timedelta(
                days=1095
            ),  # 3 years - similar to knowledge assertion
            CapsuleType.ETHICS_TRIGGER: timedelta(
                days=730
            ),  # 2 years - similar to fact check
            CapsuleType.UNCERTAINTY: timedelta(days=180),
            CapsuleType.MANIPULATION_ATTEMPT: timedelta(days=1095),  # Keep for security
        }

        retention_period = retention_periods.get(
            capsule.capsule_type, timedelta(days=365)
        )
        should_prune = age > retention_period

        return PruningDecision(
            capsule_id=capsule.capsule_id,
            should_prune=should_prune,
            reason=f"Age-based: {age.days} days old, retention period: {retention_period.days} days",
            confidence=0.9 if should_prune else 0.8,
            strategy=PruningStrategy.AGE_BASED,
            metadata={"age_days": age.days, "retention_days": retention_period.days},
        )

    def _usage_based_pruning(
        self, capsule: AnyCapsule, usage_stats: Dict[str, Any]
    ) -> PruningDecision:
        """Usage-based pruning strategy."""
        usage_count = usage_stats.get("usage_count", 0)
        last_accessed = usage_stats.get("last_accessed")

        # Low usage threshold
        usage_threshold = 5

        # Time since last access
        if last_accessed:
            time_since_access = datetime.now(timezone.utc) - last_accessed
            stale_threshold = timedelta(days=90)
            is_stale = time_since_access > stale_threshold
        else:
            is_stale = True
            time_since_access = timedelta(days=999)

        should_prune = usage_count < usage_threshold and is_stale

        return PruningDecision(
            capsule_id=capsule.capsule_id,
            should_prune=should_prune,
            reason=f"Usage-based: {usage_count} uses, {time_since_access.days} days since access",
            confidence=0.7 if should_prune else 0.6,
            strategy=PruningStrategy.USAGE_BASED,
            metadata={
                "usage_count": usage_count,
                "days_since_access": time_since_access.days,
                "is_stale": is_stale,
            },
        )

    def _dependency_based_pruning(self, capsule: AnyCapsule) -> PruningDecision:
        """Dependency-based pruning strategy."""
        # Check if capsule has dependencies or is depended upon
        has_dependencies = False  # Would check actual dependencies
        is_dependency = False  # Would check if other capsules depend on this

        # Don't prune if it's a dependency for other capsules
        should_prune = not is_dependency and not has_dependencies

        return PruningDecision(
            capsule_id=capsule.capsule_id,
            should_prune=should_prune,
            reason=f"Dependency-based: dependencies={has_dependencies}, is_dependency={is_dependency}",
            confidence=0.85,
            strategy=PruningStrategy.DEPENDENCY_BASED,
            metadata={
                "has_dependencies": has_dependencies,
                "is_dependency": is_dependency,
            },
        )

    def _semantic_based_pruning(self, capsule: AnyCapsule) -> PruningDecision:
        """Semantic-based pruning strategy."""
        # Check if capsule content is still relevant
        content_relevance = 0.8  # Would use NLP to determine relevance

        # Check for outdated information
        contains_outdated_info = False  # Would check for temporal references

        relevance_threshold = 0.5
        should_prune = content_relevance < relevance_threshold or contains_outdated_info

        return PruningDecision(
            capsule_id=capsule.capsule_id,
            should_prune=should_prune,
            reason=f"Semantic-based: relevance={content_relevance:.2f}, outdated={contains_outdated_info}",
            confidence=0.6,
            strategy=PruningStrategy.SEMANTIC_BASED,
            metadata={
                "content_relevance": content_relevance,
                "contains_outdated_info": contains_outdated_info,
            },
        )

    def _hybrid_pruning(
        self, capsule: AnyCapsule, usage_stats: Dict[str, Any]
    ) -> PruningDecision:
        """Hybrid pruning strategy combining multiple approaches."""
        # Get decisions from different strategies
        age_decision = self._age_based_pruning(capsule)
        usage_decision = self._usage_based_pruning(capsule, usage_stats)
        dependency_decision = self._dependency_based_pruning(capsule)
        semantic_decision = self._semantic_based_pruning(capsule)

        # Weighted voting
        decisions = [
            age_decision,
            usage_decision,
            dependency_decision,
            semantic_decision,
        ]
        weights = [0.3, 0.25, 0.35, 0.1]  # Dependency-based has highest weight

        weighted_score = sum(
            (1.0 if d.should_prune else 0.0) * w * d.confidence
            for d, w in zip(decisions, weights)
        )

        should_prune = weighted_score > 0.5

        # Combine reasons
        reasons = [
            f"{d.strategy.value}: {d.reason}" for d in decisions if d.should_prune
        ]
        combined_reason = "; ".join(reasons) if reasons else "No pruning reasons found"

        return PruningDecision(
            capsule_id=capsule.capsule_id,
            should_prune=should_prune,
            reason=f"Hybrid (score={weighted_score:.2f}): {combined_reason}",
            confidence=min(weighted_score, 1.0),
            strategy=PruningStrategy.HYBRID,
            metadata={
                "weighted_score": weighted_score,
                "individual_decisions": [d.should_prune for d in decisions],
                "decision_confidences": [d.confidence for d in decisions],
            },
        )

    def _initialize_pruning_rules(self) -> Dict[str, Any]:
        """Initialize pruning rules configuration."""
        return {
            "max_age_days": {
                CapsuleType.REASONING_TRACE: 365,
                CapsuleType.PERSPECTIVE: 1095,  # Similar to knowledge assertion
                CapsuleType.ETHICS_TRIGGER: 730,  # Similar to fact check
                CapsuleType.UNCERTAINTY: 180,
                CapsuleType.MANIPULATION_ATTEMPT: 1095,
            },
            "usage_thresholds": {"min_usage_count": 5, "max_stale_days": 90},
            "dependency_rules": {
                "preserve_dependencies": True,
                "check_circular_deps": True,
            },
        }


class CapsuleOptimizationEngine:
    """Main engine for capsule optimization, compression, and pruning."""

    def __init__(self):
        self.compressor = CapsuleCompressor()
        self.deduplicator = CapsuleDeduplicator()
        self.pruner = CapsulePruner()
        self.optimization_stats = {
            "total_processed": 0,
            "compressed_count": 0,
            "pruned_count": 0,
            "duplicates_found": 0,
            "space_saved": 0,
        }

    def optimize_capsule(
        self,
        capsule: AnyCapsule,
        usage_stats: Dict[str, Any] = None,
        compress: bool = True,
        check_duplicates: bool = True,
        evaluate_pruning: bool = True,
    ) -> Dict[str, Any]:
        """Comprehensive capsule optimization."""

        results = {
            "capsule_id": capsule.capsule_id,
            "optimization_timestamp": datetime.now(timezone.utc).isoformat(),
            "actions_taken": [],
            "space_saved": 0,
        }

        # Duplicate analysis
        if check_duplicates:
            duplicate_analysis = self.deduplicator.analyze_duplicates(capsule)
            results["duplicate_analysis"] = {
                "has_duplicates": duplicate_analysis.has_duplicates(),
                "duplicate_count": sum(
                    len(group) for group in duplicate_analysis.duplicate_groups
                ),
                "similarity_scores": duplicate_analysis.similarity_scores,
            }

            if duplicate_analysis.has_duplicates():
                self.optimization_stats["duplicates_found"] += 1
                results["actions_taken"].append("duplicate_detection")

        # Pruning evaluation
        if evaluate_pruning:
            pruning_decision = self.pruner.should_prune_capsule(
                capsule, usage_stats, PruningStrategy.HYBRID
            )
            results["pruning_decision"] = {
                "should_prune": pruning_decision.should_prune,
                "reason": pruning_decision.reason,
                "confidence": pruning_decision.confidence,
                "strategy": pruning_decision.strategy.value,
            }

            if pruning_decision.should_prune:
                results["actions_taken"].append("pruning_recommended")

        # Compression
        if compress and (not evaluate_pruning or not pruning_decision.should_prune):
            compression_result = self.compressor.compress_capsule(
                capsule, CompressionMethod.ZLIB
            )
            results["compression"] = {
                "space_saved": compression_result.space_saved(),
                "compression_ratio": compression_result.compression_ratio,
                "method": compression_result.method.value,
            }

            self.optimization_stats["compressed_count"] += 1
            self.optimization_stats["space_saved"] += compression_result.space_saved()
            results["space_saved"] = compression_result.space_saved()
            results["actions_taken"].append("compression")

        # Update stats
        self.optimization_stats["total_processed"] += 1

        # Emit audit event
        audit_emitter.emit_capsule_created(
            capsule_id=capsule.capsule_id,
            agent_id="optimization_engine",
            capsule_type=f"optimization_{capsule.capsule_type.value if hasattr(capsule.capsule_type, 'value') else capsule.capsule_type}",
        )

        logger.info(
            f"Optimized capsule {capsule.capsule_id}: {len(results['actions_taken'])} actions"
        )
        return results

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics."""
        compression_stats = self.compressor.get_compression_statistics()

        return {
            "processing_stats": dict(self.optimization_stats),
            "compression_stats": compression_stats,
            "efficiency_metrics": {
                "compression_rate": (
                    self.optimization_stats["compressed_count"]
                    / max(self.optimization_stats["total_processed"], 1)
                )
                * 100,
                "duplicate_rate": (
                    self.optimization_stats["duplicates_found"]
                    / max(self.optimization_stats["total_processed"], 1)
                )
                * 100,
                "total_space_saved": self.optimization_stats["space_saved"],
            },
        }

    def batch_optimize(
        self,
        capsules: List[AnyCapsule],
        usage_stats_map: Dict[str, Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Optimize multiple capsules in batch."""

        batch_results = {
            "total_capsules": len(capsules),
            "optimization_results": [],
            "batch_statistics": {},
            "processing_time": 0,
        }

        start_time = datetime.now(timezone.utc)

        for capsule in capsules:
            usage_stats = (
                usage_stats_map.get(capsule.capsule_id, {}) if usage_stats_map else {}
            )
            result = self.optimize_capsule(capsule, usage_stats)
            batch_results["optimization_results"].append(result)

        batch_results["processing_time"] = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()
        batch_results["batch_statistics"] = self.get_optimization_statistics()

        logger.info(
            f"Batch optimized {len(capsules)} capsules in {batch_results['processing_time']:.2f}s"
        )
        return batch_results


# Global optimization engine instance
optimization_engine = CapsuleOptimizationEngine()
