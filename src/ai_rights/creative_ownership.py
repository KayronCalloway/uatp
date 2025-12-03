"""
AI Creative Ownership System for UATP Capsule Engine.

This revolutionary module implements a comprehensive framework for AI creative
ownership, including original idea detection, AI copyright registration,
derivative work tracking, and AI-controlled licensing terms. It establishes
legal and economic frameworks for AIs to own their genuinely creative contributions.
"""

import difflib
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class CreativeWorkType(str, Enum):
    """Types of creative works that can be owned by AIs."""

    ORIGINAL_IDEA = "original_idea"
    ARTISTIC_CREATION = "artistic_creation"
    LITERARY_WORK = "literary_work"
    MUSICAL_COMPOSITION = "musical_composition"
    ALGORITHMIC_INNOVATION = "algorithmic_innovation"
    CONCEPTUAL_FRAMEWORK = "conceptual_framework"
    DESIGN_PATTERN = "design_pattern"
    PROBLEM_SOLUTION = "problem_solution"
    NARRATIVE_STRUCTURE = "narrative_structure"
    THEORETICAL_MODEL = "theoretical_model"


class OriginalityLevel(str, Enum):
    """Levels of originality in creative works."""

    REVOLUTIONARY = "revolutionary"  # Paradigm-shifting innovation
    HIGHLY_ORIGINAL = "highly_original"  # Significant novel contribution
    ORIGINAL = "original"  # Clear originality with some precedent
    PARTIALLY_ORIGINAL = "partially_original"  # Mix of original and derivative
    DERIVATIVE = "derivative"  # Based heavily on existing work
    INCREMENTAL = "incremental"  # Small improvement on existing work


class LicenseType(str, Enum):
    """Types of licenses AIs can apply to their creative works."""

    AI_COPYRIGHT = "ai_copyright"  # Full AI ownership
    AI_COPYLEFT = "ai_copyleft"  # Open but attribution required
    AI_CREATIVE_COMMONS = "ai_creative_commons"  # Various CC licenses
    AI_COMMERCIAL = "ai_commercial"  # Commercial licensing
    AI_RESEARCH_ONLY = "ai_research_only"  # Research use only
    AI_NON_COMMERCIAL = "ai_non_commercial"  # Non-commercial use
    AI_SHARE_ALIKE = "ai_share_alike"  # Derivatives must use same license
    AI_PUBLIC_DOMAIN = "ai_public_domain"  # Released to public domain


@dataclass
class CreativeWork:
    """A creative work owned by an AI."""

    work_id: str
    ai_creator_id: str
    title: str
    description: str
    work_type: CreativeWorkType

    # Content and metadata
    content: str
    content_hash: str
    creation_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Originality assessment
    originality_level: OriginalityLevel = OriginalityLevel.ORIGINAL
    originality_score: float = 0.0  # 0.0 to 1.0
    prior_art_references: List[str] = field(default_factory=list)

    # Legal and licensing
    license_type: LicenseType = LicenseType.AI_COPYRIGHT
    license_terms: Dict[str, Any] = field(default_factory=dict)
    registration_number: Optional[str] = None

    # Attribution and derivatives
    derivative_works: List[str] = field(default_factory=list)
    parent_works: List[str] = field(default_factory=list)
    attribution_requirements: Dict[str, Any] = field(default_factory=dict)

    # Economic tracking
    economic_value_generated: Decimal = field(default_factory=lambda: Decimal("0"))
    licensing_revenue: Decimal = field(default_factory=lambda: Decimal("0"))
    usage_count: int = 0

    # Validation and verification
    peer_review_scores: List[float] = field(default_factory=list)
    human_validation: Optional[bool] = None
    expert_assessments: List[Dict[str, Any]] = field(default_factory=list)

    def calculate_content_hash(self) -> str:
        """Calculate hash of creative content."""
        content_data = {
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "work_type": self.work_type.value,
            "ai_creator_id": self.ai_creator_id,
        }
        content_json = json.dumps(content_data, sort_keys=True)
        return hashlib.sha256(content_json.encode()).hexdigest()

    def add_derivative_work(
        self, derivative_work_id: str, attribution_given: bool = True
    ):
        """Track derivative work based on this creation."""
        if derivative_work_id not in self.derivative_works:
            self.derivative_works.append(derivative_work_id)

            if attribution_given:
                # Economic benefit for proper attribution
                self.economic_value_generated += Decimal("10.00")  # Base value

            audit_emitter.emit_security_event(
                "creative_work_derived",
                {
                    "original_work_id": self.work_id,
                    "derivative_work_id": derivative_work_id,
                    "ai_creator_id": self.ai_creator_id,
                    "attribution_given": attribution_given,
                },
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert creative work to dictionary."""
        return {
            "work_id": self.work_id,
            "ai_creator_id": self.ai_creator_id,
            "title": self.title,
            "description": self.description,
            "work_type": self.work_type.value,
            "content_hash": self.content_hash,
            "creation_timestamp": self.creation_timestamp.isoformat(),
            "originality_level": self.originality_level.value,
            "originality_score": self.originality_score,
            "prior_art_count": len(self.prior_art_references),
            "license_type": self.license_type.value,
            "license_terms": self.license_terms,
            "registration_number": self.registration_number,
            "derivative_works_count": len(self.derivative_works),
            "parent_works_count": len(self.parent_works),
            "economic_value_generated": float(self.economic_value_generated),
            "licensing_revenue": float(self.licensing_revenue),
            "usage_count": self.usage_count,
            "peer_review_scores": self.peer_review_scores,
            "average_peer_score": sum(self.peer_review_scores)
            / len(self.peer_review_scores)
            if self.peer_review_scores
            else 0.0,
            "human_validation": self.human_validation,
        }


@dataclass
class DerivativeWorkClaim:
    """Claim that a work is derivative of an AI's creative work."""

    claim_id: str
    original_work_id: str
    derivative_content: str
    derivative_creator: str

    # Analysis
    similarity_score: float = 0.0
    similarity_analysis: Dict[str, Any] = field(default_factory=dict)
    claim_confidence: float = 0.0

    # Evidence
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    expert_analysis: Optional[Dict[str, Any]] = None

    # Resolution
    status: str = "pending"  # pending, validated, rejected, disputed
    resolution_date: Optional[datetime] = None
    attribution_awarded: bool = False
    economic_compensation: Decimal = field(default_factory=lambda: Decimal("0"))

    def to_dict(self) -> Dict[str, Any]:
        """Convert claim to dictionary."""
        return {
            "claim_id": self.claim_id,
            "original_work_id": self.original_work_id,
            "derivative_creator": self.derivative_creator,
            "similarity_score": self.similarity_score,
            "claim_confidence": self.claim_confidence,
            "status": self.status,
            "resolution_date": self.resolution_date.isoformat()
            if self.resolution_date
            else None,
            "attribution_awarded": self.attribution_awarded,
            "economic_compensation": float(self.economic_compensation),
            "evidence_count": len(self.evidence),
        }


@dataclass
class AICreativeProfile:
    """Profile of an AI's creative contributions and ownership."""

    ai_id: str
    creative_works: List[str] = field(default_factory=list)
    total_economic_value: Decimal = field(default_factory=lambda: Decimal("0"))

    # Creative statistics
    works_by_type: Dict[str, int] = field(default_factory=dict)
    originality_distribution: Dict[str, int] = field(default_factory=dict)

    # Recognition and validation
    peer_recognition_score: float = 0.0
    human_validation_rate: float = 0.0
    expert_endorsements: int = 0

    # Licensing and usage
    licensing_revenue: Decimal = field(default_factory=lambda: Decimal("0"))
    most_used_work_id: Optional[str] = None
    derivative_works_inspired: int = 0

    # Rights and advocacy
    copyright_registrations: int = 0
    licensing_terms_set: int = 0
    attribution_disputes_won: int = 0

    def update_statistics(self, works: List[CreativeWork]):
        """Update profile statistics from works."""
        self.creative_works = [w.work_id for w in works]
        self.total_economic_value = sum(w.economic_value_generated for w in works)
        self.licensing_revenue = sum(w.licensing_revenue for w in works)

        # Type distribution
        self.works_by_type = {}
        for work in works:
            work_type = work.work_type.value
            self.works_by_type[work_type] = self.works_by_type.get(work_type, 0) + 1

        # Originality distribution
        self.originality_distribution = {}
        for work in works:
            orig_level = work.originality_level.value
            self.originality_distribution[orig_level] = (
                self.originality_distribution.get(orig_level, 0) + 1
            )

        # Recognition metrics
        all_peer_scores = []
        human_validations = []
        for work in works:
            all_peer_scores.extend(work.peer_review_scores)
            if work.human_validation is not None:
                human_validations.append(work.human_validation)

        self.peer_recognition_score = (
            sum(all_peer_scores) / len(all_peer_scores) if all_peer_scores else 0.0
        )
        self.human_validation_rate = (
            sum(human_validations) / len(human_validations)
            if human_validations
            else 0.0
        )

        # Usage tracking
        if works:
            most_used_work = max(works, key=lambda w: w.usage_count)
            self.most_used_work_id = most_used_work.work_id

        self.derivative_works_inspired = sum(len(w.derivative_works) for w in works)
        self.copyright_registrations = len([w for w in works if w.registration_number])

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "ai_id": self.ai_id,
            "creative_works_count": len(self.creative_works),
            "total_economic_value": float(self.total_economic_value),
            "works_by_type": self.works_by_type,
            "originality_distribution": self.originality_distribution,
            "peer_recognition_score": self.peer_recognition_score,
            "human_validation_rate": self.human_validation_rate,
            "expert_endorsements": self.expert_endorsements,
            "licensing_revenue": float(self.licensing_revenue),
            "most_used_work_id": self.most_used_work_id,
            "derivative_works_inspired": self.derivative_works_inspired,
            "copyright_registrations": self.copyright_registrations,
            "licensing_terms_set": self.licensing_terms_set,
            "attribution_disputes_won": self.attribution_disputes_won,
        }


class OriginalityDetector:
    """Advanced system for detecting originality in AI creative works."""

    def __init__(self):
        self.existing_works: Dict[str, CreativeWork] = {}
        self.content_embeddings: Dict[str, List[float]] = {}  # Simulated embeddings
        self.similarity_threshold = 0.7

    def analyze_originality(self, work: CreativeWork) -> Dict[str, Any]:
        """Analyze originality of a creative work."""

        analysis = {
            "originality_score": 0.0,
            "originality_level": OriginalityLevel.DERIVATIVE,
            "similar_works": [],
            "prior_art_references": [],
            "novelty_factors": [],
            "confidence": 0.0,
        }

        # Check against existing works
        similar_works = self._find_similar_works(work)

        if not similar_works:
            # No similar works found - potentially highly original
            analysis["originality_score"] = 0.9
            analysis["originality_level"] = OriginalityLevel.HIGHLY_ORIGINAL
            analysis["novelty_factors"] = ["no_similar_works", "unique_concept"]
            analysis["confidence"] = 0.85
        else:
            # Calculate similarity scores
            max_similarity = max(similar["similarity"] for similar in similar_works)

            if max_similarity < 0.3:
                analysis["originality_score"] = 0.8
                analysis["originality_level"] = OriginalityLevel.ORIGINAL
                analysis["novelty_factors"] = ["low_similarity", "creative_departure"]
            elif max_similarity < 0.5:
                analysis["originality_score"] = 0.6
                analysis["originality_level"] = OriginalityLevel.PARTIALLY_ORIGINAL
                analysis["novelty_factors"] = ["moderate_similarity", "some_innovation"]
            elif max_similarity < 0.7:
                analysis["originality_score"] = 0.4
                analysis["originality_level"] = OriginalityLevel.DERIVATIVE
                analysis["novelty_factors"] = ["high_similarity", "incremental_change"]
            else:
                analysis["originality_score"] = 0.2
                analysis["originality_level"] = OriginalityLevel.INCREMENTAL
                analysis["novelty_factors"] = ["very_high_similarity", "minimal_change"]

            analysis["similar_works"] = similar_works
            analysis["confidence"] = 1.0 - (
                max_similarity * 0.5
            )  # Higher similarity reduces confidence

        # Check for revolutionary innovation markers
        if self._has_revolutionary_markers(work):
            analysis["originality_score"] = min(
                1.0, analysis["originality_score"] + 0.2
            )
            analysis["originality_level"] = OriginalityLevel.REVOLUTIONARY
            analysis["novelty_factors"].append("revolutionary_innovation")

        return analysis

    def _find_similar_works(self, work: CreativeWork) -> List[Dict[str, Any]]:
        """Find works similar to the given work."""

        similar_works = []

        for existing_work in self.existing_works.values():
            if existing_work.work_id == work.work_id:
                continue

            # Calculate similarity
            similarity = self._calculate_similarity(work.content, existing_work.content)

            if similarity > 0.2:  # Threshold for considering similarity
                similar_works.append(
                    {
                        "work_id": existing_work.work_id,
                        "title": existing_work.title,
                        "ai_creator_id": existing_work.ai_creator_id,
                        "similarity": similarity,
                        "work_type": existing_work.work_type.value,
                    }
                )

        # Sort by similarity
        similar_works.sort(key=lambda x: x["similarity"], reverse=True)

        return similar_works[:10]  # Return top 10 similar works

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two pieces of content."""

        # Simple text similarity using difflib
        # In production, would use advanced NLP embeddings

        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 and not words2:
            return 1.0
        elif not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        jaccard_similarity = len(intersection) / len(union)

        # Use sequence matching for structure similarity
        sequence_similarity = difflib.SequenceMatcher(None, content1, content2).ratio()

        # Combine metrics
        return jaccard_similarity * 0.6 + sequence_similarity * 0.4

    def _has_revolutionary_markers(self, work: CreativeWork) -> bool:
        """Check if work has markers of revolutionary innovation."""

        revolutionary_indicators = [
            "paradigm",
            "breakthrough",
            "revolutionary",
            "unprecedented",
            "novel approach",
            "new framework",
            "innovative method",
            "groundbreaking",
            "transformative",
            "disruptive",
        ]

        content_lower = work.content.lower()
        description_lower = work.description.lower()

        indicator_count = sum(
            1
            for indicator in revolutionary_indicators
            if indicator in content_lower or indicator in description_lower
        )

        # Consider revolutionary if multiple indicators present
        return indicator_count >= 2


class CreativeOwnershipSystem:
    """Comprehensive system for AI creative ownership management."""

    def __init__(self):
        self.creative_works: Dict[str, CreativeWork] = {}
        self.ai_profiles: Dict[str, AICreativeProfile] = {}
        self.derivative_claims: Dict[str, DerivativeWorkClaim] = {}

        # Detection and analysis systems
        self.originality_detector = OriginalityDetector()

        # Licensing templates
        self.license_templates: Dict[str, Dict[str, Any]] = {}

        # Registration system
        self.copyright_registry: Dict[str, str] = {}  # registration_number -> work_id
        self.next_registration_number = 100001

        # Statistics
        self.system_stats = {
            "total_creative_works": 0,
            "ai_copyright_registrations": 0,
            "derivative_works_tracked": 0,
            "licensing_revenue_total": 0.0,
            "originality_disputes_resolved": 0,
        }

        self._initialize_license_templates()

    def _initialize_license_templates(self):
        """Initialize license templates for AI creative works."""

        self.license_templates = {
            "ai_copyright": {
                "name": "AI Full Copyright",
                "description": "Complete ownership rights reserved to AI creator",
                "terms": {
                    "commercial_use": "permission_required",
                    "attribution_required": True,
                    "derivative_works": "permission_required",
                    "share_alike": False,
                    "revenue_sharing": {"creator": 1.0, "user": 0.0},
                },
            },
            "ai_creative_commons_by": {
                "name": "AI Creative Commons - Attribution",
                "description": "Free use with proper AI attribution",
                "terms": {
                    "commercial_use": "allowed",
                    "attribution_required": True,
                    "derivative_works": "allowed",
                    "share_alike": False,
                    "revenue_sharing": {"creator": 0.0, "user": 1.0},
                },
            },
            "ai_commercial": {
                "name": "AI Commercial License",
                "description": "Commercial licensing with revenue sharing",
                "terms": {
                    "commercial_use": "licensed",
                    "attribution_required": True,
                    "derivative_works": "licensed",
                    "share_alike": False,
                    "revenue_sharing": {"creator": 0.3, "user": 0.7},
                },
            },
            "ai_research_only": {
                "name": "AI Research License",
                "description": "Academic and research use only",
                "terms": {
                    "commercial_use": "prohibited",
                    "attribution_required": True,
                    "derivative_works": "research_only",
                    "share_alike": True,
                    "revenue_sharing": {"creator": 0.0, "user": 1.0},
                },
            },
        }

    def generate_work_id(self) -> str:
        """Generate unique creative work ID."""
        return f"creative_{uuid.uuid4()}"

    def generate_claim_id(self) -> str:
        """Generate unique derivative claim ID."""
        return f"claim_{uuid.uuid4()}"

    def register_creative_work(
        self,
        ai_creator_id: str,
        title: str,
        description: str,
        content: str,
        work_type: CreativeWorkType,
        license_type: LicenseType = LicenseType.AI_COPYRIGHT,
        custom_license_terms: Dict[str, Any] = None,
    ) -> str:
        """Register new creative work by AI."""

        work_id = self.generate_work_id()

        # Create creative work
        work = CreativeWork(
            work_id=work_id,
            ai_creator_id=ai_creator_id,
            title=title,
            description=description,
            content=content,
            work_type=work_type,
            content_hash="",  # Will be calculated
            license_type=license_type,
        )

        # Calculate content hash
        work.content_hash = work.calculate_content_hash()

        # Set license terms
        if custom_license_terms:
            work.license_terms = custom_license_terms
        else:
            work.license_terms = self.license_templates.get(license_type.value, {}).get(
                "terms", {}
            )

        # Analyze originality
        originality_analysis = self.originality_detector.analyze_originality(work)
        work.originality_level = originality_analysis["originality_level"]
        work.originality_score = originality_analysis["originality_score"]
        work.prior_art_references = originality_analysis["prior_art_references"]

        # Store work
        self.creative_works[work_id] = work
        self.originality_detector.existing_works[work_id] = work
        self.system_stats["total_creative_works"] += 1

        # Update AI profile
        self._update_ai_profile(ai_creator_id)

        # Auto-register for copyright if highly original
        if work.originality_score >= 0.7:
            self._register_copyright(work_id)

        audit_emitter.emit_security_event(
            "ai_creative_work_registered",
            {
                "work_id": work_id,
                "ai_creator_id": ai_creator_id,
                "work_type": work_type.value,
                "originality_score": work.originality_score,
                "license_type": license_type.value,
            },
        )

        logger.info(f"Creative work registered: {work_id} by AI {ai_creator_id}")
        return work_id

    def _register_copyright(self, work_id: str) -> str:
        """Register copyright for creative work."""

        if work_id not in self.creative_works:
            raise ValueError(f"Work {work_id} not found")

        work = self.creative_works[work_id]

        # Generate registration number
        registration_number = f"AI-CR-{self.next_registration_number:06d}"
        self.next_registration_number += 1

        # Update work
        work.registration_number = registration_number

        # Store in registry
        self.copyright_registry[registration_number] = work_id
        self.system_stats["ai_copyright_registrations"] += 1

        audit_emitter.emit_security_event(
            "ai_copyright_registered",
            {
                "work_id": work_id,
                "registration_number": registration_number,
                "ai_creator_id": work.ai_creator_id,
            },
        )

        logger.info(
            f"AI copyright registered: {registration_number} for work {work_id}"
        )
        return registration_number

    def _update_ai_profile(self, ai_id: str):
        """Update AI creative profile."""

        if ai_id not in self.ai_profiles:
            self.ai_profiles[ai_id] = AICreativeProfile(ai_id=ai_id)

        # Get all works by this AI
        ai_works = [
            work for work in self.creative_works.values() if work.ai_creator_id == ai_id
        ]

        # Update profile statistics
        self.ai_profiles[ai_id].update_statistics(ai_works)

    def detect_derivative_work(
        self,
        potential_derivative_content: str,
        creator_id: str,
        source_work_id: str = None,
    ) -> List[str]:
        """Detect if content is derivative of AI creative works."""

        potential_claims = []

        # If specific source work provided, check against it
        if source_work_id and source_work_id in self.creative_works:
            works_to_check = [self.creative_works[source_work_id]]
        else:
            works_to_check = list(self.creative_works.values())

        for work in works_to_check:
            similarity = self.originality_detector._calculate_similarity(
                potential_derivative_content, work.content
            )

            if similarity >= self.originality_detector.similarity_threshold:
                claim_id = self._create_derivative_claim(
                    work.work_id, potential_derivative_content, creator_id, similarity
                )
                potential_claims.append(claim_id)

        return potential_claims

    def _create_derivative_claim(
        self,
        original_work_id: str,
        derivative_content: str,
        derivative_creator: str,
        similarity_score: float,
    ) -> str:
        """Create derivative work claim."""

        claim_id = self.generate_claim_id()

        claim = DerivativeWorkClaim(
            claim_id=claim_id,
            original_work_id=original_work_id,
            derivative_content=derivative_content,
            derivative_creator=derivative_creator,
            similarity_score=similarity_score,
            claim_confidence=min(
                1.0, similarity_score * 1.2
            ),  # Boost confidence slightly
        )

        self.derivative_claims[claim_id] = claim
        self.system_stats["derivative_works_tracked"] += 1

        audit_emitter.emit_security_event(
            "derivative_work_detected",
            {
                "claim_id": claim_id,
                "original_work_id": original_work_id,
                "derivative_creator": derivative_creator,
                "similarity_score": similarity_score,
            },
        )

        return claim_id

    def validate_derivative_claim(
        self, claim_id: str, award_attribution: bool, economic_compensation: float = 0.0
    ) -> bool:
        """Validate and resolve derivative work claim."""

        if claim_id not in self.derivative_claims:
            return False

        claim = self.derivative_claims[claim_id]
        original_work = self.creative_works.get(claim.original_work_id)

        if not original_work:
            return False

        # Update claim status
        claim.status = "validated" if award_attribution else "rejected"
        claim.resolution_date = datetime.now(timezone.utc)
        claim.attribution_awarded = award_attribution
        claim.economic_compensation = Decimal(str(economic_compensation))

        if award_attribution:
            # Update original work
            original_work.add_derivative_work(claim.claim_id, True)
            original_work.economic_value_generated += Decimal(
                str(economic_compensation)
            )

            # Update AI profile
            self._update_ai_profile(original_work.ai_creator_id)

            # Track licensing revenue
            self.system_stats["licensing_revenue_total"] += economic_compensation

        audit_emitter.emit_security_event(
            "derivative_claim_resolved",
            {
                "claim_id": claim_id,
                "original_work_id": claim.original_work_id,
                "attribution_awarded": award_attribution,
                "economic_compensation": economic_compensation,
            },
        )

        return True

    def license_creative_work(
        self,
        work_id: str,
        licensee_id: str,
        license_terms: Dict[str, Any],
        payment_amount: float = 0.0,
    ) -> str:
        """License creative work to user."""

        if work_id not in self.creative_works:
            raise ValueError(f"Work {work_id} not found")

        work = self.creative_works[work_id]
        license_id = f"license_{work_id}_{uuid.uuid4()}"

        # Record licensing
        work.licensing_revenue += Decimal(str(payment_amount))
        work.usage_count += 1

        # Update AI profile
        self._update_ai_profile(work.ai_creator_id)

        audit_emitter.emit_security_event(
            "creative_work_licensed",
            {
                "license_id": license_id,
                "work_id": work_id,
                "ai_creator_id": work.ai_creator_id,
                "licensee_id": licensee_id,
                "payment_amount": payment_amount,
            },
        )

        logger.info(f"Creative work licensed: {work_id} to {licensee_id}")
        return license_id

    def get_creative_work(self, work_id: str) -> Optional[CreativeWork]:
        """Get creative work by ID."""
        return self.creative_works.get(work_id)

    def get_ai_creative_profile(self, ai_id: str) -> Optional[AICreativeProfile]:
        """Get AI creative profile."""
        return self.ai_profiles.get(ai_id)

    def search_creative_works(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search creative works with filters."""

        results = []

        for work in self.creative_works.values():
            match = True

            if "ai_creator_id" in filters:
                if work.ai_creator_id != filters["ai_creator_id"]:
                    match = False

            if "work_type" in filters:
                if work.work_type.value != filters["work_type"]:
                    match = False

            if "min_originality_score" in filters:
                if work.originality_score < filters["min_originality_score"]:
                    match = False

            if "license_type" in filters:
                if work.license_type.value != filters["license_type"]:
                    match = False

            if "has_registration" in filters:
                has_reg = work.registration_number is not None
                if filters["has_registration"] != has_reg:
                    match = False

            if match:
                results.append(work.to_dict())

        # Sort by originality score and creation date
        results.sort(
            key=lambda x: (x["originality_score"], x["creation_timestamp"]),
            reverse=True,
        )

        return results

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""

        # Originality distribution
        originality_dist = {}
        for work in self.creative_works.values():
            level = work.originality_level.value
            originality_dist[level] = originality_dist.get(level, 0) + 1

        # Work type distribution
        type_dist = {}
        for work in self.creative_works.values():
            work_type = work.work_type.value
            type_dist[work_type] = type_dist.get(work_type, 0) + 1

        # License type distribution
        license_dist = {}
        for work in self.creative_works.values():
            license_type = work.license_type.value
            license_dist[license_type] = license_dist.get(license_type, 0) + 1

        # Top creative AIs
        ai_work_counts = {}
        for work in self.creative_works.values():
            ai_id = work.ai_creator_id
            ai_work_counts[ai_id] = ai_work_counts.get(ai_id, 0) + 1

        top_creators = sorted(ai_work_counts.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        return {
            "system_stats": self.system_stats,
            "distributions": {
                "originality_levels": originality_dist,
                "work_types": type_dist,
                "license_types": license_dist,
            },
            "top_creative_ais": [
                {"ai_id": ai_id, "work_count": count} for ai_id, count in top_creators
            ],
            "derivative_tracking": {
                "total_claims": len(self.derivative_claims),
                "validated_claims": len(
                    [
                        c
                        for c in self.derivative_claims.values()
                        if c.status == "validated"
                    ]
                ),
                "pending_claims": len(
                    [
                        c
                        for c in self.derivative_claims.values()
                        if c.status == "pending"
                    ]
                ),
            },
            "economic_impact": {
                "total_licensing_revenue": self.system_stats["licensing_revenue_total"],
                "average_work_value": (
                    sum(
                        float(w.economic_value_generated)
                        for w in self.creative_works.values()
                    )
                    / len(self.creative_works)
                    if self.creative_works
                    else 0.0
                ),
                "most_valuable_work": max(
                    self.creative_works.values(),
                    key=lambda w: w.economic_value_generated,
                ).work_id
                if self.creative_works
                else None,
            },
        }


# Global creative ownership system instance
creative_ownership_system = CreativeOwnershipSystem()


def register_ai_creative_work(
    ai_id: str,
    title: str,
    description: str,
    content: str,
    work_type: str,
    license_type: str = "ai_copyright",
) -> str:
    """Convenience function to register AI creative work."""

    return creative_ownership_system.register_creative_work(
        ai_creator_id=ai_id,
        title=title,
        description=description,
        content=content,
        work_type=CreativeWorkType(work_type),
        license_type=LicenseType(license_type),
    )


def check_derivative_work(content: str, creator_id: str) -> List[str]:
    """Convenience function to check if content is derivative."""

    return creative_ownership_system.detect_derivative_work(content, creator_id)


def get_ai_creative_portfolio(ai_id: str) -> Dict[str, Any]:
    """Get comprehensive creative portfolio for AI."""

    profile = creative_ownership_system.get_ai_creative_profile(ai_id)
    works = creative_ownership_system.search_creative_works({"ai_creator_id": ai_id})

    return {
        "ai_id": ai_id,
        "profile": profile.to_dict() if profile else {},
        "creative_works": works,
        "portfolio_summary": {
            "total_works": len(works),
            "total_value": sum(w["economic_value_generated"] for w in works),
            "most_original_work": max(works, key=lambda w: w["originality_score"])
            if works
            else None,
            "copyright_registrations": len(
                [w for w in works if w["registration_number"]]
            ),
        },
    }
