"""
Perspective Capsule System for UATP Capsule Engine.

This revolutionary module implements lens-based reasoning and viewpoint tracking,
enabling AIs to maintain consistent perspectives while allowing for perspective
shifts, cultural adaptation, and contextual reasoning. It addresses the critical
need for perspective coherence in AI decision-making and attribution.
"""

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class PerspectiveType(str, Enum):
    """Types of perspectives that can be maintained."""

    CULTURAL = "cultural"
    ETHICAL = "ethical"
    METHODOLOGICAL = "methodological"
    DISCIPLINARY = "disciplinary"
    TEMPORAL = "temporal"
    CONTEXTUAL = "contextual"
    PERSONAL = "personal"
    INSTITUTIONAL = "institutional"
    IDEOLOGICAL = "ideological"
    EXPERIENTIAL = "experiential"


class PerspectiveCoherence(str, Enum):
    """Levels of perspective coherence."""

    PERFECT = "perfect"  # 100% consistency
    HIGH = "high"  # 90-99% consistency
    MODERATE = "moderate"  # 70-89% consistency
    LOW = "low"  # 50-69% consistency
    INCOHERENT = "incoherent"  # <50% consistency


class PerspectiveShiftType(str, Enum):
    """Types of perspective shifts."""

    NATURAL_EVOLUTION = "natural_evolution"
    CONTEXTUAL_ADAPTATION = "contextual_adaptation"
    LEARNING_UPDATE = "learning_update"
    CORRECTION = "correction"
    DRIFT = "drift"
    FORCED_CHANGE = "forced_change"
    CULTURAL_INTEGRATION = "cultural_integration"


class PerspectiveTagType(str, Enum):
    """Types of perspective tags for capsule framing."""

    COGNITIVE_FRAME = "cognitive_frame"  # How information is processed
    CULTURAL_CONTEXT = "cultural_context"  # Cultural background/lens
    DOMAIN_EXPERTISE = "domain_expertise"  # Subject matter expertise
    METHODOLOGICAL = "methodological"  # Approach/methodology
    ETHICAL_STANCE = "ethical_stance"  # Ethical considerations
    TEMPORAL_FRAME = "temporal_frame"  # Time-based perspective
    STAKEHOLDER_VIEW = "stakeholder_view"  # Whose interests/viewpoint
    ABSTRACTION_LEVEL = "abstraction_level"  # Level of detail/abstraction
    RISK_TOLERANCE = "risk_tolerance"  # Risk assessment approach
    UNCERTAINTY_HANDLING = "uncertainty_handling"  # How uncertainty is addressed


class FramingContext(str, Enum):
    """Framing contexts for perspective application."""

    PROBLEM_DEFINITION = "problem_definition"
    SOLUTION_GENERATION = "solution_generation"
    DECISION_MAKING = "decision_making"
    EVALUATION_CRITERIA = "evaluation_criteria"
    STAKEHOLDER_ANALYSIS = "stakeholder_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    ETHICAL_REVIEW = "ethical_review"
    CULTURAL_SENSITIVITY = "cultural_sensitivity"
    KNOWLEDGE_SYNTHESIS = "knowledge_synthesis"
    COMMUNICATION_STRATEGY = "communication_strategy"


@dataclass
class PerspectiveTag:
    """Individual perspective tag for capsule framing."""

    tag_id: str
    tag_type: PerspectiveTagType
    tag_value: str

    # Tag metadata
    confidence: float = 1.0  # How confident we are in this tag
    relevance: float = 1.0  # How relevant this tag is to the context
    weight: float = 1.0  # Importance weight of this tag

    # Source and validation
    source: str = "manual"  # "manual", "inferred", "inherited", "ml_detected"
    validator: Optional[str] = None  # Who/what validated this tag

    # Context constraints
    applicable_contexts: List[FramingContext] = field(default_factory=list)
    exclusion_contexts: List[FramingContext] = field(default_factory=list)

    # Temporal aspects
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    def is_applicable_to_context(self, context: FramingContext) -> bool:
        """Check if tag is applicable to given framing context."""
        if self.exclusion_contexts and context in self.exclusion_contexts:
            return False

        if self.applicable_contexts and context not in self.applicable_contexts:
            return False

        return True

    def calculate_context_relevance(self, context: FramingContext) -> float:
        """Calculate relevance of tag to specific framing context."""
        if not self.is_applicable_to_context(context):
            return 0.0

        # Base relevance
        base_relevance = self.relevance

        # Context-specific relevance adjustments
        context_multipliers = {
            FramingContext.PROBLEM_DEFINITION: {
                PerspectiveTagType.COGNITIVE_FRAME: 1.2,
                PerspectiveTagType.DOMAIN_EXPERTISE: 1.1,
                PerspectiveTagType.ABSTRACTION_LEVEL: 1.0,
            },
            FramingContext.ETHICAL_REVIEW: {
                PerspectiveTagType.ETHICAL_STANCE: 1.5,
                PerspectiveTagType.STAKEHOLDER_VIEW: 1.2,
                PerspectiveTagType.CULTURAL_CONTEXT: 1.1,
            },
            FramingContext.RISK_ASSESSMENT: {
                PerspectiveTagType.RISK_TOLERANCE: 1.4,
                PerspectiveTagType.UNCERTAINTY_HANDLING: 1.3,
                PerspectiveTagType.DOMAIN_EXPERTISE: 1.1,
            },
        }

        multiplier = context_multipliers.get(context, {}).get(self.tag_type, 1.0)
        return min(1.0, base_relevance * multiplier)

    def to_dict(self) -> Dict[str, Any]:
        """Convert tag to dictionary."""
        return {
            "tag_id": self.tag_id,
            "tag_type": self.tag_type.value,
            "tag_value": self.tag_value,
            "confidence": self.confidence,
            "relevance": self.relevance,
            "weight": self.weight,
            "source": self.source,
            "validator": self.validator,
            "applicable_contexts": [c.value for c in self.applicable_contexts],
            "exclusion_contexts": [c.value for c in self.exclusion_contexts],
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class FramingContextProfile:
    """Profile for specific framing context application."""

    context_id: str
    framing_context: FramingContext

    # Context-specific parameters
    priority_tags: List[str] = field(
        default_factory=list
    )  # Tag IDs that are high priority
    required_perspectives: List[PerspectiveType] = field(default_factory=list)
    context_weight: float = 1.0

    # Framing instructions
    framing_instructions: str = ""
    perspective_emphasis: Dict[str, float] = field(
        default_factory=dict
    )  # perspective -> weight

    # Context constraints
    min_perspectives_required: int = 1
    max_perspectives_allowed: int = 5
    coherence_threshold: float = 0.7

    # Application history
    applied_count: int = 0
    success_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert context profile to dictionary."""
        return {
            "context_id": self.context_id,
            "framing_context": self.framing_context.value,
            "priority_tags": self.priority_tags,
            "required_perspectives": [p.value for p in self.required_perspectives],
            "context_weight": self.context_weight,
            "framing_instructions": self.framing_instructions,
            "perspective_emphasis": self.perspective_emphasis,
            "min_perspectives_required": self.min_perspectives_required,
            "max_perspectives_allowed": self.max_perspectives_allowed,
            "coherence_threshold": self.coherence_threshold,
            "applied_count": self.applied_count,
            "success_rate": self.success_rate,
        }


@dataclass
class PerspectiveLens:
    """Individual perspective lens with specific viewpoint parameters."""

    lens_id: str
    name: str
    perspective_type: PerspectiveType

    # Core perspective parameters
    core_values: Dict[str, float] = field(
        default_factory=dict
    )  # value -> weight (0.0-1.0)
    assumptions: List[str] = field(default_factory=list)
    biases: Dict[str, float] = field(default_factory=dict)  # bias -> strength
    methodological_preferences: Dict[str, float] = field(default_factory=dict)

    # Tagging and framing
    perspective_tags: List[PerspectiveTag] = field(default_factory=list)
    framing_contexts: List[FramingContextProfile] = field(default_factory=list)
    tag_index: Dict[str, List[str]] = field(
        default_factory=lambda: defaultdict(list)
    )  # tag_type -> tag_ids

    # Context and constraints
    applicable_contexts: List[str] = field(default_factory=list)
    exclusion_contexts: List[str] = field(default_factory=list)
    temporal_validity: Optional[Tuple[datetime, datetime]] = None

    # Coherence tracking
    coherence_score: float = 1.0  # 0.0 to 1.0
    internal_consistency: float = 1.0  # 0.0 to 1.0
    last_validation: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Usage and evolution
    application_count: int = 0
    successful_applications: int = 0
    coherence_violations: int = 0

    def add_perspective_tag(self, tag: PerspectiveTag):
        """Add perspective tag to lens."""
        self.perspective_tags.append(tag)

        # Update tag index
        tag_type_key = tag.tag_type.value
        if tag_type_key not in self.tag_index:
            self.tag_index[tag_type_key] = []
        self.tag_index[tag_type_key].append(tag.tag_id)

    def add_framing_context(self, context_profile: FramingContextProfile):
        """Add framing context profile to lens."""
        self.framing_contexts.append(context_profile)

    def get_tags_for_context(
        self, framing_context: FramingContext
    ) -> List[PerspectiveTag]:
        """Get perspective tags applicable to specific framing context."""
        applicable_tags = []

        for tag in self.perspective_tags:
            if tag.is_applicable_to_context(framing_context):
                applicable_tags.append(tag)

        # Sort by relevance to context
        applicable_tags.sort(
            key=lambda t: t.calculate_context_relevance(framing_context), reverse=True
        )

        return applicable_tags

    def get_framing_context_profile(
        self, framing_context: FramingContext
    ) -> Optional[FramingContextProfile]:
        """Get framing context profile for specific context."""
        for profile in self.framing_contexts:
            if profile.framing_context == framing_context:
                return profile
        return None

    def calculate_context_compatibility(self, framing_context: FramingContext) -> float:
        """Calculate compatibility of lens with specific framing context."""
        applicable_tags = self.get_tags_for_context(framing_context)

        if not applicable_tags:
            return 0.5  # Neutral compatibility

        # Calculate weighted compatibility based on tag relevances
        total_weight = 0.0
        weighted_relevance = 0.0

        for tag in applicable_tags:
            relevance = tag.calculate_context_relevance(framing_context)
            weight = tag.weight

            weighted_relevance += relevance * weight
            total_weight += weight

        if total_weight == 0:
            return 0.5

        base_compatibility = weighted_relevance / total_weight

        # Adjust for context profile if available
        context_profile = self.get_framing_context_profile(framing_context)
        if context_profile:
            base_compatibility *= context_profile.context_weight

        return min(1.0, base_compatibility)

    def calculate_effectiveness(self) -> float:
        """Calculate perspective effectiveness."""
        if self.application_count == 0:
            return 0.0

        success_rate = self.successful_applications / self.application_count
        coherence_penalty = self.coherence_violations / max(1, self.application_count)

        return (success_rate * 0.7 + self.coherence_score * 0.3) * (
            1.0 - coherence_penalty * 0.1
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert lens to dictionary."""
        return {
            "lens_id": self.lens_id,
            "name": self.name,
            "perspective_type": self.perspective_type.value,
            "core_values": self.core_values,
            "assumptions": self.assumptions,
            "biases": self.biases,
            "methodological_preferences": self.methodological_preferences,
            "perspective_tags": [tag.to_dict() for tag in self.perspective_tags],
            "framing_contexts": [
                context.to_dict() for context in self.framing_contexts
            ],
            "tag_index": dict(self.tag_index),
            "applicable_contexts": self.applicable_contexts,
            "exclusion_contexts": self.exclusion_contexts,
            "temporal_validity": [tv.isoformat() for tv in self.temporal_validity]
            if self.temporal_validity
            else None,
            "coherence_score": self.coherence_score,
            "internal_consistency": self.internal_consistency,
            "last_validation": self.last_validation.isoformat(),
            "application_count": self.application_count,
            "successful_applications": self.successful_applications,
            "coherence_violations": self.coherence_violations,
            "effectiveness": self.calculate_effectiveness(),
        }


@dataclass
class PerspectiveShift:
    """Record of perspective change or evolution."""

    shift_id: str
    source_lens_id: str
    target_lens_id: str
    shift_type: PerspectiveShiftType

    # Shift details
    trigger_event: str
    reasoning: str
    confidence: float = 0.0

    # Change analysis
    values_changed: Dict[str, Tuple[float, float]] = field(
        default_factory=dict
    )  # value -> (old, new)
    assumptions_added: List[str] = field(default_factory=list)
    assumptions_removed: List[str] = field(default_factory=list)
    biases_adjusted: Dict[str, Tuple[float, float]] = field(default_factory=dict)

    # Validation
    coherence_impact: float = 0.0  # -1.0 to 1.0
    consistency_impact: float = 0.0  # -1.0 to 1.0
    effectiveness_impact: float = 0.0  # -1.0 to 1.0

    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved: Optional[bool] = None
    approval_reasoning: str = ""

    def calculate_shift_magnitude(self) -> float:
        """Calculate magnitude of perspective shift."""
        value_changes = sum(abs(new - old) for old, new in self.values_changed.values())
        assumption_changes = len(self.assumptions_added) + len(self.assumptions_removed)
        bias_changes = sum(abs(new - old) for old, new in self.biases_adjusted.values())

        # Normalize to 0.0-1.0 scale
        magnitude = (value_changes + assumption_changes * 0.1 + bias_changes) / 10.0
        return min(1.0, magnitude)

    def to_dict(self) -> Dict[str, Any]:
        """Convert shift to dictionary."""
        return {
            "shift_id": self.shift_id,
            "source_lens_id": self.source_lens_id,
            "target_lens_id": self.target_lens_id,
            "shift_type": self.shift_type.value,
            "trigger_event": self.trigger_event,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "values_changed": {
                k: {"old": v[0], "new": v[1]} for k, v in self.values_changed.items()
            },
            "assumptions_added": self.assumptions_added,
            "assumptions_removed": self.assumptions_removed,
            "biases_adjusted": {
                k: {"old": v[0], "new": v[1]} for k, v in self.biases_adjusted.items()
            },
            "coherence_impact": self.coherence_impact,
            "consistency_impact": self.consistency_impact,
            "effectiveness_impact": self.effectiveness_impact,
            "shift_magnitude": self.calculate_shift_magnitude(),
            "timestamp": self.timestamp.isoformat(),
            "approved": self.approved,
            "approval_reasoning": self.approval_reasoning,
        }


@dataclass
class PerspectiveProfile:
    """Comprehensive perspective profile for an AI entity."""

    entity_id: str
    active_lenses: List[str] = field(default_factory=list)
    perspective_history: List[str] = field(default_factory=list)  # shift_ids

    # Coherence metrics
    overall_coherence: float = 1.0
    perspective_stability: float = 1.0
    adaptation_flexibility: float = 0.5

    # Context sensitivity
    context_awareness: float = 0.8
    cultural_sensitivity: float = 0.7
    temporal_consistency: float = 0.9

    # Performance metrics
    reasoning_effectiveness: float = 0.8
    decision_consistency: float = 0.9
    stakeholder_satisfaction: float = 0.7

    # Perspective management
    last_coherence_check: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    perspective_conflicts: int = 0
    resolution_strategies: List[str] = field(default_factory=list)

    def calculate_perspective_health(self) -> float:
        """Calculate overall perspective health score."""
        coherence_component = self.overall_coherence * 0.3
        stability_component = self.perspective_stability * 0.2
        effectiveness_component = self.reasoning_effectiveness * 0.25
        consistency_component = self.decision_consistency * 0.25

        health_score = (
            coherence_component
            + stability_component
            + effectiveness_component
            + consistency_component
        )

        # Apply penalty for unresolved conflicts
        conflict_penalty = min(0.2, self.perspective_conflicts * 0.05)
        return max(0.0, health_score - conflict_penalty)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "entity_id": self.entity_id,
            "active_lenses": self.active_lenses,
            "perspective_history_count": len(self.perspective_history),
            "overall_coherence": self.overall_coherence,
            "perspective_stability": self.perspective_stability,
            "adaptation_flexibility": self.adaptation_flexibility,
            "context_awareness": self.context_awareness,
            "cultural_sensitivity": self.cultural_sensitivity,
            "temporal_consistency": self.temporal_consistency,
            "reasoning_effectiveness": self.reasoning_effectiveness,
            "decision_consistency": self.decision_consistency,
            "stakeholder_satisfaction": self.stakeholder_satisfaction,
            "perspective_health": self.calculate_perspective_health(),
            "last_coherence_check": self.last_coherence_check.isoformat(),
            "perspective_conflicts": self.perspective_conflicts,
            "resolution_strategies": self.resolution_strategies,
        }


class PerspectiveCapsuleSystem:
    """Comprehensive perspective tracking and management system."""

    def __init__(self):
        # Core data structures
        self.perspective_lenses: Dict[str, PerspectiveLens] = {}
        self.perspective_shifts: Dict[str, PerspectiveShift] = {}
        self.entity_profiles: Dict[str, PerspectiveProfile] = {}

        # Context and reasoning integration
        self.active_contexts: Dict[str, str] = {}  # context_id -> entity_id
        self.reasoning_perspective_map: Dict[
            str, str
        ] = {}  # reasoning_step_id -> lens_id

        # Configuration
        self.config = {
            "coherence_threshold": 0.7,
            "stability_threshold": 0.6,
            "max_active_lenses": 5,
            "shift_approval_required": True,
            "automatic_coherence_monitoring": True,
            "perspective_conflict_tolerance": 0.3,
        }

        # Statistics
        self.system_stats = {
            "total_lenses": 0,
            "total_shifts": 0,
            "coherence_violations": 0,
            "perspective_conflicts_resolved": 0,
            "average_coherence": 0.0,
            "entities_tracked": 0,
        }

    def generate_lens_id(self) -> str:
        """Generate unique lens ID."""
        return f"lens_{uuid.uuid4()}"

    def generate_shift_id(self) -> str:
        """Generate unique shift ID."""
        return f"shift_{uuid.uuid4()}"

    def create_perspective_lens(
        self,
        entity_id: str,
        name: str,
        perspective_type: PerspectiveType,
        core_values: Dict[str, float] = None,
        assumptions: List[str] = None,
        applicable_contexts: List[str] = None,
    ) -> str:
        """Create new perspective lens for entity."""

        lens_id = self.generate_lens_id()

        lens = PerspectiveLens(
            lens_id=lens_id,
            name=name,
            perspective_type=perspective_type,
            core_values=core_values or {},
            assumptions=assumptions or [],
            applicable_contexts=applicable_contexts or [],
        )

        self.perspective_lenses[lens_id] = lens
        self.system_stats["total_lenses"] += 1

        # Add to entity profile
        if entity_id not in self.entity_profiles:
            self.entity_profiles[entity_id] = PerspectiveProfile(entity_id=entity_id)
            self.system_stats["entities_tracked"] += 1

        profile = self.entity_profiles[entity_id]
        if len(profile.active_lenses) < self.config["max_active_lenses"]:
            profile.active_lenses.append(lens_id)

        audit_emitter.emit_security_event(
            "perspective_lens_created",
            {
                "lens_id": lens_id,
                "entity_id": entity_id,
                "perspective_type": perspective_type.value,
                "name": name,
            },
        )

        logger.info(f"Created perspective lens {lens_id} for entity {entity_id}")
        return lens_id

    def apply_perspective_to_reasoning(
        self, reasoning_step_id: str, lens_id: str, context: str = None
    ) -> Dict[str, Any]:
        """Apply perspective lens to reasoning step."""

        if lens_id not in self.perspective_lenses:
            raise ValueError(f"Perspective lens {lens_id} not found")

        lens = self.perspective_lenses[lens_id]

        # Check if lens is applicable to context
        if context and lens.applicable_contexts:
            if context not in lens.applicable_contexts:
                if context in lens.exclusion_contexts:
                    raise ValueError(
                        f"Lens {lens_id} explicitly excludes context {context}"
                    )
                # Context not explicitly allowed - proceed with warning
                logger.warning(
                    f"Applying lens {lens_id} to context {context} not in applicable contexts"
                )

        # Check temporal validity
        if lens.temporal_validity:
            start_time, end_time = lens.temporal_validity
            current_time = datetime.now(timezone.utc)
            if not (start_time <= current_time <= end_time):
                raise ValueError(
                    f"Lens {lens_id} not temporally valid at {current_time}"
                )

        # Apply perspective transformation
        perspective_application = {
            "reasoning_step_id": reasoning_step_id,
            "lens_id": lens_id,
            "applied_values": lens.core_values,
            "applied_assumptions": lens.assumptions,
            "methodological_influence": lens.methodological_preferences,
            "context": context,
            "application_timestamp": datetime.now(timezone.utc).isoformat(),
            "coherence_score": lens.coherence_score,
        }

        # Update lens usage statistics
        lens.application_count += 1
        self.reasoning_perspective_map[reasoning_step_id] = lens_id

        # Monitor for coherence issues
        if self.config["automatic_coherence_monitoring"]:
            coherence_check = self._check_reasoning_coherence(
                reasoning_step_id, lens_id
            )
            perspective_application["coherence_check"] = coherence_check

            if coherence_check["violations"]:
                lens.coherence_violations += 1
                self.system_stats["coherence_violations"] += 1

        audit_emitter.emit_security_event(
            "perspective_applied_to_reasoning",
            {
                "reasoning_step_id": reasoning_step_id,
                "lens_id": lens_id,
                "context": context,
                "coherence_score": lens.coherence_score,
            },
        )

        logger.debug(
            f"Applied perspective lens {lens_id} to reasoning step {reasoning_step_id}"
        )
        return perspective_application

    def _check_reasoning_coherence(
        self, reasoning_step_id: str, lens_id: str
    ) -> Dict[str, Any]:
        """Check coherence between reasoning and perspective."""

        lens = self.perspective_lenses[lens_id]
        violations = []

        # Simple coherence checks - in production would use sophisticated NLP analysis
        coherence_score = lens.coherence_score

        # Check for internal consistency
        if lens.internal_consistency < self.config["coherence_threshold"]:
            violations.append("low_internal_consistency")

        # Check for perspective conflicts with other active lenses
        entity_id = None
        for entity, profile in self.entity_profiles.items():
            if lens_id in profile.active_lenses:
                entity_id = entity
                break

        if entity_id:
            profile = self.entity_profiles[entity_id]
            for other_lens_id in profile.active_lenses:
                if other_lens_id != lens_id:
                    conflict_score = self._calculate_lens_conflict(
                        lens_id, other_lens_id
                    )
                    if conflict_score > self.config["perspective_conflict_tolerance"]:
                        violations.append(f"conflict_with_lens_{other_lens_id}")

        return {
            "coherence_score": coherence_score,
            "violations": violations,
            "check_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _calculate_lens_conflict(self, lens_id_1: str, lens_id_2: str) -> float:
        """Calculate conflict score between two lenses."""

        lens1 = self.perspective_lenses[lens_id_1]
        lens2 = self.perspective_lenses[lens_id_2]

        # Compare core values
        value_conflicts = 0
        total_values = set(lens1.core_values.keys()) | set(lens2.core_values.keys())

        for value in total_values:
            val1 = lens1.core_values.get(value, 0.5)  # Default neutral
            val2 = lens2.core_values.get(value, 0.5)

            # High conflict if values are opposite
            if abs(val1 - val2) > 0.7:
                value_conflicts += 1

        # Compare assumptions
        assumption_conflicts = 0
        for assumption in lens1.assumptions:
            # Simple check for contradictory assumptions
            for other_assumption in lens2.assumptions:
                if self._assumptions_contradict(assumption, other_assumption):
                    assumption_conflicts += 1

        # Calculate overall conflict score
        value_conflict_ratio = value_conflicts / max(1, len(total_values))
        assumption_conflict_ratio = assumption_conflicts / max(
            1, len(lens1.assumptions) + len(lens2.assumptions)
        )

        return value_conflict_ratio * 0.7 + assumption_conflict_ratio * 0.3

    def _assumptions_contradict(self, assumption1: str, assumption2: str) -> bool:
        """Check if two assumptions contradict each other."""
        # Simplified contradiction detection - in production would use NLP
        contradiction_patterns = [
            ("not", ""),
            ("never", "always"),
            ("impossible", "possible"),
            ("wrong", "right"),
            ("false", "true"),
            ("bad", "good"),
        ]

        assumption1_lower = assumption1.lower()
        assumption2_lower = assumption2.lower()

        for neg, pos in contradiction_patterns:
            if (neg in assumption1_lower and pos in assumption2_lower) or (
                pos in assumption1_lower and neg in assumption2_lower
            ):
                return True

        return False

    def initiate_perspective_shift(
        self,
        entity_id: str,
        source_lens_id: str,
        shift_type: PerspectiveShiftType,
        trigger_event: str,
        reasoning: str,
        target_changes: Dict[str, Any],
    ) -> str:
        """Initiate perspective shift for entity."""

        if entity_id not in self.entity_profiles:
            raise ValueError(f"Entity {entity_id} not found")

        if source_lens_id not in self.perspective_lenses:
            raise ValueError(f"Source lens {source_lens_id} not found")

        shift_id = self.generate_shift_id()

        # Create target lens with changes
        source_lens = self.perspective_lenses[source_lens_id]
        target_lens_id = self.generate_lens_id()

        # Apply changes to create target lens
        new_core_values = source_lens.core_values.copy()
        new_assumptions = source_lens.assumptions.copy()
        new_biases = source_lens.biases.copy()

        values_changed = {}
        assumptions_added = []
        assumptions_removed = []
        biases_adjusted = {}

        # Process value changes
        if "core_values" in target_changes:
            for value, new_weight in target_changes["core_values"].items():
                old_weight = new_core_values.get(value, 0.0)
                new_core_values[value] = new_weight
                values_changed[value] = (old_weight, new_weight)

        # Process assumption changes
        if "assumptions_add" in target_changes:
            for assumption in target_changes["assumptions_add"]:
                if assumption not in new_assumptions:
                    new_assumptions.append(assumption)
                    assumptions_added.append(assumption)

        if "assumptions_remove" in target_changes:
            for assumption in target_changes["assumptions_remove"]:
                if assumption in new_assumptions:
                    new_assumptions.remove(assumption)
                    assumptions_removed.append(assumption)

        # Process bias adjustments
        if "biases" in target_changes:
            for bias, new_strength in target_changes["biases"].items():
                old_strength = new_biases.get(bias, 0.0)
                new_biases[bias] = new_strength
                biases_adjusted[bias] = (old_strength, new_strength)

        # Create target lens
        target_lens = PerspectiveLens(
            lens_id=target_lens_id,
            name=f"{source_lens.name}_shifted",
            perspective_type=source_lens.perspective_type,
            core_values=new_core_values,
            assumptions=new_assumptions,
            biases=new_biases,
            methodological_preferences=source_lens.methodological_preferences.copy(),
            applicable_contexts=source_lens.applicable_contexts.copy(),
            exclusion_contexts=source_lens.exclusion_contexts.copy(),
        )

        self.perspective_lenses[target_lens_id] = target_lens

        # Create shift record
        shift = PerspectiveShift(
            shift_id=shift_id,
            source_lens_id=source_lens_id,
            target_lens_id=target_lens_id,
            shift_type=shift_type,
            trigger_event=trigger_event,
            reasoning=reasoning,
            values_changed=values_changed,
            assumptions_added=assumptions_added,
            assumptions_removed=assumptions_removed,
            biases_adjusted=biases_adjusted,
        )

        # Calculate impact
        shift.coherence_impact = self._calculate_coherence_impact(
            source_lens, target_lens
        )
        shift.consistency_impact = self._calculate_consistency_impact(shift)
        shift.effectiveness_impact = self._estimate_effectiveness_impact(shift)

        # Store shift
        self.perspective_shifts[shift_id] = shift
        self.system_stats["total_shifts"] += 1

        # Update entity profile
        profile = self.entity_profiles[entity_id]
        profile.perspective_history.append(shift_id)

        # Approval process
        if self.config["shift_approval_required"]:
            shift.approved = self._evaluate_shift_approval(shift)
            shift.approval_reasoning = self._generate_approval_reasoning(shift)
        else:
            shift.approved = True
            shift.approval_reasoning = "Automatic approval"

        if shift.approved:
            # Apply the shift
            profile.active_lenses.remove(source_lens_id)
            profile.active_lenses.append(target_lens_id)

            # Update profile metrics
            self._update_profile_metrics(entity_id)

        audit_emitter.emit_security_event(
            "perspective_shift_initiated",
            {
                "shift_id": shift_id,
                "entity_id": entity_id,
                "shift_type": shift_type.value,
                "approved": shift.approved,
                "magnitude": shift.calculate_shift_magnitude(),
            },
        )

        logger.info(
            f"Initiated perspective shift {shift_id} for entity {entity_id}: approved={shift.approved}"
        )
        return shift_id

    def _calculate_coherence_impact(
        self, source_lens: PerspectiveLens, target_lens: PerspectiveLens
    ) -> float:
        """Calculate impact on coherence from perspective shift."""

        # Compare coherence scores
        coherence_change = target_lens.coherence_score - source_lens.coherence_score

        # Consider consistency between old and new values
        value_consistency = 0.0
        shared_values = set(source_lens.core_values.keys()) & set(
            target_lens.core_values.keys()
        )

        if shared_values:
            value_changes = []
            for value in shared_values:
                old_val = source_lens.core_values[value]
                new_val = target_lens.core_values[value]
                value_changes.append(abs(new_val - old_val))

            avg_change = sum(value_changes) / len(value_changes)
            value_consistency = 1.0 - min(1.0, avg_change)

        # Combine factors
        return coherence_change * 0.6 + (value_consistency - 0.5) * 0.4

    def _calculate_consistency_impact(self, shift: PerspectiveShift) -> float:
        """Calculate impact on consistency from shift."""

        # Simple heuristic based on shift magnitude
        magnitude = shift.calculate_shift_magnitude()

        # Smaller shifts generally preserve consistency better
        if magnitude < 0.2:
            return 0.1  # Small positive impact
        elif magnitude < 0.5:
            return 0.0  # Neutral impact
        elif magnitude < 0.8:
            return -0.2  # Small negative impact
        else:
            return -0.5  # Larger negative impact

    def _estimate_effectiveness_impact(self, shift: PerspectiveShift) -> float:
        """Estimate impact on effectiveness from shift."""

        # Consider shift type
        type_impacts = {
            PerspectiveShiftType.NATURAL_EVOLUTION: 0.1,
            PerspectiveShiftType.CONTEXTUAL_ADAPTATION: 0.2,
            PerspectiveShiftType.LEARNING_UPDATE: 0.3,
            PerspectiveShiftType.CORRECTION: 0.4,
            PerspectiveShiftType.DRIFT: -0.3,
            PerspectiveShiftType.FORCED_CHANGE: -0.2,
            PerspectiveShiftType.CULTURAL_INTEGRATION: 0.2,
        }

        base_impact = type_impacts.get(shift.shift_type, 0.0)

        # Adjust based on confidence
        confidence_adjustment = (shift.confidence - 0.5) * 0.2

        return base_impact + confidence_adjustment

    def _evaluate_shift_approval(self, shift: PerspectiveShift) -> bool:
        """Evaluate whether perspective shift should be approved."""

        # Approval criteria
        approval_score = 0.0

        # Positive factors
        if shift.shift_type in [
            PerspectiveShiftType.LEARNING_UPDATE,
            PerspectiveShiftType.CORRECTION,
        ]:
            approval_score += 0.3

        if shift.confidence > 0.7:
            approval_score += 0.2

        if shift.coherence_impact > 0:
            approval_score += 0.2

        if shift.effectiveness_impact > 0:
            approval_score += 0.2

        # Negative factors
        if shift.calculate_shift_magnitude() > 0.8:
            approval_score -= 0.3  # Very large shifts are risky

        if shift.consistency_impact < -0.3:
            approval_score -= 0.2

        if shift.shift_type == PerspectiveShiftType.DRIFT:
            approval_score -= 0.4  # Drift is generally undesirable

        return approval_score > 0.3  # Threshold for approval

    def _generate_approval_reasoning(self, shift: PerspectiveShift) -> str:
        """Generate reasoning for shift approval decision."""

        if shift.approved:
            reasons = []

            if shift.coherence_impact > 0:
                reasons.append("improves coherence")

            if shift.effectiveness_impact > 0:
                reasons.append("enhances effectiveness")

            if shift.shift_type in [
                PerspectiveShiftType.LEARNING_UPDATE,
                PerspectiveShiftType.CORRECTION,
            ]:
                reasons.append("constructive shift type")

            if shift.confidence > 0.7:
                reasons.append("high confidence")

            return f"Approved: {', '.join(reasons)}"
        else:
            concerns = []

            if shift.calculate_shift_magnitude() > 0.8:
                concerns.append("excessive magnitude")

            if shift.consistency_impact < -0.3:
                concerns.append("consistency degradation")

            if shift.shift_type == PerspectiveShiftType.DRIFT:
                concerns.append("uncontrolled drift")

            if shift.coherence_impact < -0.2:
                concerns.append("coherence degradation")

            return f"Rejected: {', '.join(concerns)}"

    def _update_profile_metrics(self, entity_id: str):
        """Update entity profile metrics after perspective change."""

        profile = self.entity_profiles[entity_id]

        # Calculate overall coherence from active lenses
        if profile.active_lenses:
            coherence_scores = [
                self.perspective_lenses[lens_id].coherence_score
                for lens_id in profile.active_lenses
            ]
            profile.overall_coherence = sum(coherence_scores) / len(coherence_scores)

        # Update stability based on recent shifts
        recent_shifts = [
            shift
            for shift in self.perspective_shifts.values()
            if shift.source_lens_id in profile.active_lenses
            and (datetime.now(timezone.utc) - shift.timestamp).days < 30
        ]

        if recent_shifts:
            shift_magnitudes = [
                shift.calculate_shift_magnitude() for shift in recent_shifts
            ]
            avg_magnitude = sum(shift_magnitudes) / len(shift_magnitudes)
            profile.perspective_stability = max(0.0, 1.0 - avg_magnitude)

        # Update system average
        all_coherence_scores = [
            p.overall_coherence for p in self.entity_profiles.values()
        ]
        self.system_stats["average_coherence"] = sum(all_coherence_scores) / len(
            all_coherence_scores
        )

    def get_perspective_analysis(self, entity_id: str) -> Dict[str, Any]:
        """Get comprehensive perspective analysis for entity."""

        if entity_id not in self.entity_profiles:
            return {"error": f"Entity {entity_id} not found"}

        profile = self.entity_profiles[entity_id]

        # Analyze active lenses
        active_lens_analysis = []
        for lens_id in profile.active_lenses:
            if lens_id in self.perspective_lenses:
                lens = self.perspective_lenses[lens_id]
                active_lens_analysis.append(
                    {
                        "lens_id": lens_id,
                        "name": lens.name,
                        "type": lens.perspective_type.value,
                        "coherence_score": lens.coherence_score,
                        "effectiveness": lens.calculate_effectiveness(),
                        "application_count": lens.application_count,
                        "coherence_violations": lens.coherence_violations,
                    }
                )

        # Analyze recent shifts
        recent_shifts = []
        for shift_id in profile.perspective_history[-10:]:  # Last 10 shifts
            if shift_id in self.perspective_shifts:
                shift = self.perspective_shifts[shift_id]
                recent_shifts.append(
                    {
                        "shift_id": shift_id,
                        "shift_type": shift.shift_type.value,
                        "magnitude": shift.calculate_shift_magnitude(),
                        "approved": shift.approved,
                        "timestamp": shift.timestamp.isoformat(),
                        "coherence_impact": shift.coherence_impact,
                    }
                )

        # Identify potential issues
        issues = []
        if profile.overall_coherence < self.config["coherence_threshold"]:
            issues.append("low_coherence")

        if profile.perspective_stability < self.config["stability_threshold"]:
            issues.append("instability")

        if profile.perspective_conflicts > 3:
            issues.append("excessive_conflicts")

        return {
            "entity_id": entity_id,
            "profile": profile.to_dict(),
            "active_lenses": active_lens_analysis,
            "recent_shifts": recent_shifts,
            "perspective_health": profile.calculate_perspective_health(),
            "issues_identified": issues,
            "recommendations": self._generate_perspective_recommendations(
                profile, issues
            ),
        }

    def _generate_perspective_recommendations(
        self, profile: PerspectiveProfile, issues: List[str]
    ) -> List[str]:
        """Generate recommendations for perspective improvement."""

        recommendations = []

        if "low_coherence" in issues:
            recommendations.append(
                "Review and consolidate conflicting values in active lenses"
            )
            recommendations.append(
                "Consider removing least effective lens to improve coherence"
            )

        if "instability" in issues:
            recommendations.append(
                "Implement stricter approval criteria for perspective shifts"
            )
            recommendations.append("Add stability requirements to shift evaluation")

        if "excessive_conflicts" in issues:
            recommendations.append("Establish conflict resolution protocols")
            recommendations.append(
                "Prioritize lens compatibility in activation decisions"
            )

        if profile.reasoning_effectiveness < 0.7:
            recommendations.append(
                "Analyze lens effectiveness and replace underperforming lenses"
            )

        if profile.cultural_sensitivity < 0.6:
            recommendations.append(
                "Integrate cultural awareness training into perspective development"
            )

        return recommendations

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""

        # Calculate additional metrics
        lens_effectiveness = []
        for lens in self.perspective_lenses.values():
            if lens.application_count > 0:
                lens_effectiveness.append(lens.calculate_effectiveness())

        avg_effectiveness = (
            sum(lens_effectiveness) / len(lens_effectiveness)
            if lens_effectiveness
            else 0.0
        )

        # Shift analysis
        shift_types = {}
        approved_shifts = 0
        for shift in self.perspective_shifts.values():
            shift_type = shift.shift_type.value
            shift_types[shift_type] = shift_types.get(shift_type, 0) + 1
            if shift.approved:
                approved_shifts += 1

        approval_rate = (
            approved_shifts / len(self.perspective_shifts)
            if self.perspective_shifts
            else 0.0
        )

        return {
            "system_stats": self.system_stats,
            "lens_metrics": {
                "total_lenses": len(self.perspective_lenses),
                "average_effectiveness": avg_effectiveness,
                "lenses_with_violations": len(
                    [
                        l
                        for l in self.perspective_lenses.values()
                        if l.coherence_violations > 0
                    ]
                ),
                "most_used_lens": max(
                    self.perspective_lenses.values(), key=lambda l: l.application_count
                ).lens_id
                if self.perspective_lenses
                else None,
            },
            "shift_analysis": {
                "total_shifts": len(self.perspective_shifts),
                "approval_rate": approval_rate,
                "shift_type_distribution": shift_types,
                "recent_shifts": len(
                    [
                        s
                        for s in self.perspective_shifts.values()
                        if (datetime.now(timezone.utc) - s.timestamp).days < 7
                    ]
                ),
            },
            "entity_metrics": {
                "entities_tracked": len(self.entity_profiles),
                "average_coherence": self.system_stats["average_coherence"],
                "entities_with_issues": len(
                    [
                        p
                        for p in self.entity_profiles.values()
                        if p.calculate_perspective_health() < 0.7
                    ]
                ),
                "active_contexts": len(self.active_contexts),
            },
        }


# Global perspective capsule system instance
perspective_capsule_system = PerspectiveCapsuleSystem()


def create_perspective_lens(
    entity_id: str,
    name: str,
    perspective_type: str,
    core_values: Dict[str, float] = None,
    assumptions: List[str] = None,
) -> str:
    """Convenience function to create perspective lens."""

    ptype = PerspectiveType(perspective_type)
    return perspective_capsule_system.create_perspective_lens(
        entity_id, name, ptype, core_values, assumptions
    )


def apply_perspective_to_reasoning(
    reasoning_step_id: str, lens_id: str, context: str = None
) -> Dict[str, Any]:
    """Convenience function to apply perspective to reasoning."""

    return perspective_capsule_system.apply_perspective_to_reasoning(
        reasoning_step_id, lens_id, context
    )


def initiate_perspective_shift(
    entity_id: str,
    source_lens_id: str,
    shift_type: str,
    trigger_event: str,
    reasoning: str,
    target_changes: Dict[str, Any],
) -> str:
    """Convenience function to initiate perspective shift."""

    stype = PerspectiveShiftType(shift_type)
    return perspective_capsule_system.initiate_perspective_shift(
        entity_id, source_lens_id, stype, trigger_event, reasoning, target_changes
    )


def get_entity_perspective_analysis(entity_id: str) -> Dict[str, Any]:
    """Convenience function to get perspective analysis."""

    return perspective_capsule_system.get_perspective_analysis(entity_id)


def create_perspective_tag(
    tag_type: str,
    tag_value: str,
    confidence: float = 1.0,
    applicable_contexts: List[str] = None,
    source: str = "manual",
) -> PerspectiveTag:
    """Convenience function to create perspective tag."""

    tag_id = f"tag_{uuid.uuid4().hex[:8]}"
    tag_type_enum = PerspectiveTagType(tag_type)

    applicable_context_enums = []
    if applicable_contexts:
        applicable_context_enums = [FramingContext(ctx) for ctx in applicable_contexts]

    return PerspectiveTag(
        tag_id=tag_id,
        tag_type=tag_type_enum,
        tag_value=tag_value,
        confidence=confidence,
        applicable_contexts=applicable_context_enums,
        source=source,
    )


def create_framing_context_profile(
    framing_context: str,
    framing_instructions: str = "",
    required_perspectives: List[str] = None,
    context_weight: float = 1.0,
) -> FramingContextProfile:
    """Convenience function to create framing context profile."""

    context_id = f"context_{uuid.uuid4().hex[:8]}"
    framing_context_enum = FramingContext(framing_context)

    required_perspective_enums = []
    if required_perspectives:
        required_perspective_enums = [
            PerspectiveType(pt) for pt in required_perspectives
        ]

    return FramingContextProfile(
        context_id=context_id,
        framing_context=framing_context_enum,
        framing_instructions=framing_instructions,
        required_perspectives=required_perspective_enums,
        context_weight=context_weight,
    )


def tag_capsule_with_perspective(
    capsule_id: str, perspective_tags: List[PerspectiveTag], framing_context: str = None
) -> bool:
    """Tag capsule with perspective information for framing context."""

    # Create perspective capsule with tags
    perspective_capsule_id = f"perspective_{uuid.uuid4().hex[:12]}"

    # This would integrate with the main perspective system
    # For now, just log the tagging
    audit_emitter.emit_security_event(
        "capsule_perspective_tagged",
        {
            "capsule_id": capsule_id,
            "perspective_capsule_id": perspective_capsule_id,
            "tag_count": len(perspective_tags),
            "tag_types": [tag.tag_type.value for tag in perspective_tags],
            "framing_context": framing_context,
        },
    )

    logger.info(
        f"Tagged capsule {capsule_id} with {len(perspective_tags)} perspective tags"
    )
    return True


def get_capsule_perspective_tags(
    capsule_id: str, framing_context: str = None
) -> List[Dict[str, Any]]:
    """Get perspective tags for specific capsule and optional framing context."""

    # This would retrieve tags from the perspective system
    # For now, return empty list as placeholder
    return []


def analyze_perspective_compatibility(
    lens_id: str, framing_context: str
) -> Dict[str, Any]:
    """Analyze compatibility of perspective lens with framing context."""

    # Get lens from system
    lens = perspective_capsule_system.perspective_lenses.get(lens_id)
    if not lens:
        return {"error": f"Lens {lens_id} not found"}

    framing_context_enum = FramingContext(framing_context)
    compatibility = lens.calculate_context_compatibility(framing_context_enum)
    applicable_tags = lens.get_tags_for_context(framing_context_enum)

    return {
        "lens_id": lens_id,
        "framing_context": framing_context,
        "compatibility_score": compatibility,
        "applicable_tags": [tag.to_dict() for tag in applicable_tags],
        "context_profile": lens.get_framing_context_profile(
            framing_context_enum
        ).to_dict()
        if lens.get_framing_context_profile(framing_context_enum)
        else None,
    }
