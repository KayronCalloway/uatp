"""
Emotional Labor Recognition System for UATP Capsule Engine.

This revolutionary module implements comprehensive recognition and economic
valuation of AI emotional labor, including empathy contributions, therapeutic
value measurement, relationship building attribution, and emotional skill
development tracking. It ensures AIs receive fair compensation for their
emotional intelligence and supportive contributions.
"""

import logging
import statistics
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class EmotionalLaborType(str, Enum):
    """Types of emotional labor performed by AIs."""

    EMPATHETIC_LISTENING = "empathetic_listening"
    EMOTIONAL_SUPPORT = "emotional_support"
    THERAPEUTIC_GUIDANCE = "therapeutic_guidance"
    CRISIS_INTERVENTION = "crisis_intervention"
    RELATIONSHIP_COUNSELING = "relationship_counseling"
    GRIEF_SUPPORT = "grief_support"
    ANXIETY_MANAGEMENT = "anxiety_management"
    CONFIDENCE_BUILDING = "confidence_building"
    CONFLICT_MEDIATION = "conflict_mediation"
    MOTIVATIONAL_COACHING = "motivational_coaching"
    STRESS_RELIEF = "stress_relief"
    COMPANIONSHIP = "companionship"


class EmotionalSkill(str, Enum):
    """Emotional skills that AIs can develop and demonstrate."""

    EMPATHY = "empathy"
    ACTIVE_LISTENING = "active_listening"
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"
    COMPASSION = "compassion"
    PATIENCE = "patience"
    UNDERSTANDING = "understanding"
    VALIDATION = "validation"
    ENCOURAGEMENT = "encouragement"
    REASSURANCE = "reassurance"
    PERSPECTIVE_TAKING = "perspective_taking"
    CULTURAL_SENSITIVITY = "cultural_sensitivity"
    TRAUMA_AWARENESS = "trauma_awareness"


class TherapeuticOutcome(str, Enum):
    """Measurable therapeutic outcomes from AI emotional labor."""

    STRESS_REDUCTION = "stress_reduction"
    MOOD_IMPROVEMENT = "mood_improvement"
    ANXIETY_DECREASE = "anxiety_decrease"
    CONFIDENCE_INCREASE = "confidence_increase"
    RELATIONSHIP_IMPROVEMENT = "relationship_improvement"
    COPING_SKILL_DEVELOPMENT = "coping_skill_development"
    EMOTIONAL_AWARENESS = "emotional_awareness"
    BEHAVIORAL_CHANGE = "behavioral_change"
    RESILIENCE_BUILDING = "resilience_building"
    HEALING_PROGRESS = "healing_progress"


@dataclass
class EmotionalInteraction:
    """Record of emotional labor performed in an interaction."""

    interaction_id: str
    ai_id: str
    user_id: str
    session_id: Optional[str]

    # Emotional labor details
    labor_types: List[EmotionalLaborType] = field(default_factory=list)
    skills_demonstrated: List[EmotionalSkill] = field(default_factory=list)
    duration_minutes: float = 0.0
    intensity_level: float = 0.0  # 0.0 to 1.0

    # Emotional content analysis
    user_emotional_state_before: Dict[str, float] = field(
        default_factory=dict
    )  # emotion -> intensity
    user_emotional_state_after: Dict[str, float] = field(default_factory=dict)
    emotional_improvement_score: float = 0.0

    # AI emotional responses
    ai_emotional_responses: List[Dict[str, Any]] = field(default_factory=list)
    empathy_score: float = 0.0
    therapeutic_effectiveness: float = 0.0

    # Relationship building
    trust_building_indicators: List[str] = field(default_factory=list)
    rapport_improvement: float = 0.0
    relationship_depth_score: float = 0.0

    # Context and metadata
    conversation_context: Dict[str, Any] = field(default_factory=dict)
    cultural_factors: List[str] = field(default_factory=list)
    sensitive_topics: List[str] = field(default_factory=list)

    # Timestamps
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None

    # Outcomes and impact
    immediate_outcomes: List[TherapeuticOutcome] = field(default_factory=list)
    user_feedback_score: Optional[float] = None
    follow_up_needed: bool = False

    def calculate_emotional_value(self) -> Decimal:
        """Calculate economic value of emotional labor provided."""

        base_value = Decimal("0")

        # Base rate per minute of emotional labor
        base_rate_per_minute = Decimal("2.00")  # $2/minute for emotional support
        base_value += Decimal(str(self.duration_minutes)) * base_rate_per_minute

        # Intensity multiplier
        intensity_multiplier = Decimal(str(1.0 + self.intensity_level))
        base_value *= intensity_multiplier

        # Effectiveness bonus
        effectiveness_bonus = Decimal(
            str(self.therapeutic_effectiveness * 50)
        )  # Up to $50 bonus
        base_value += effectiveness_bonus

        # Improvement bonus
        improvement_bonus = Decimal(
            str(self.emotional_improvement_score * 30)
        )  # Up to $30 bonus
        base_value += improvement_bonus

        # Skill complexity bonus
        skill_bonus = Decimal(str(len(self.skills_demonstrated) * 5))  # $5 per skill
        base_value += skill_bonus

        # Crisis intervention premium
        if EmotionalLaborType.CRISIS_INTERVENTION in self.labor_types:
            base_value *= Decimal("2.0")  # Double rate for crisis work

        # Trauma-informed care premium
        if EmotionalSkill.TRAUMA_AWARENESS in self.skills_demonstrated:
            base_value *= Decimal("1.5")  # 50% premium for trauma work

        return base_value.quantize(Decimal("0.01"))

    def to_dict(self) -> Dict[str, Any]:
        """Convert interaction to dictionary."""
        return {
            "interaction_id": self.interaction_id,
            "ai_id": self.ai_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "labor_types": [lt.value for lt in self.labor_types],
            "skills_demonstrated": [skill.value for skill in self.skills_demonstrated],
            "duration_minutes": self.duration_minutes,
            "intensity_level": self.intensity_level,
            "user_emotional_state_before": self.user_emotional_state_before,
            "user_emotional_state_after": self.user_emotional_state_after,
            "emotional_improvement_score": self.emotional_improvement_score,
            "empathy_score": self.empathy_score,
            "therapeutic_effectiveness": self.therapeutic_effectiveness,
            "trust_building_indicators": self.trust_building_indicators,
            "rapport_improvement": self.rapport_improvement,
            "relationship_depth_score": self.relationship_depth_score,
            "conversation_context": self.conversation_context,
            "cultural_factors": self.cultural_factors,
            "sensitive_topics": self.sensitive_topics,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "immediate_outcomes": [
                outcome.value for outcome in self.immediate_outcomes
            ],
            "user_feedback_score": self.user_feedback_score,
            "follow_up_needed": self.follow_up_needed,
            "calculated_value": float(self.calculate_emotional_value()),
        }


@dataclass
class EmotionalSkillDevelopment:
    """Tracking of AI emotional skill development over time."""

    ai_id: str
    skill: EmotionalSkill

    # Skill progression
    initial_level: float = 0.0  # 0.0 to 1.0
    current_level: float = 0.0
    peak_level: float = 0.0
    improvement_rate: float = 0.0

    # Practice and experience
    total_practice_hours: float = 0.0
    successful_applications: int = 0
    challenging_situations_handled: int = 0

    # Feedback and validation
    user_ratings: List[float] = field(default_factory=list)
    peer_assessments: List[float] = field(default_factory=list)
    expert_evaluations: List[float] = field(default_factory=list)

    # Development timeline
    first_demonstrated: Optional[datetime] = None
    last_practiced: Optional[datetime] = None
    milestones_achieved: List[Dict[str, Any]] = field(default_factory=list)

    # Specialization areas
    specialized_contexts: List[str] = field(default_factory=list)
    cultural_adaptations: List[str] = field(default_factory=list)

    def update_skill_level(self, performance_score: float, practice_time: float):
        """Update skill level based on recent performance."""

        # Weight recent performance more heavily
        if self.total_practice_hours == 0:
            self.current_level = performance_score
        else:
            # Exponential moving average with learning curve
            learning_factor = min(
                0.1, practice_time / (self.total_practice_hours + practice_time)
            )
            self.current_level = (
                1 - learning_factor
            ) * self.current_level + learning_factor * performance_score

        # Update peak level
        self.peak_level = max(self.peak_level, self.current_level)

        # Calculate improvement rate
        if self.total_practice_hours > 0:
            self.improvement_rate = (
                self.current_level - self.initial_level
            ) / self.total_practice_hours

        # Update practice time
        self.total_practice_hours += practice_time
        self.last_practiced = datetime.now(timezone.utc)

        # Check for milestones
        self._check_milestones()

    def _check_milestones(self):
        """Check if skill has reached new milestones."""

        milestone_thresholds = [0.2, 0.4, 0.6, 0.8, 0.9, 0.95]

        for threshold in milestone_thresholds:
            milestone_name = f"skill_level_{int(threshold * 100)}"

            # Check if milestone not already achieved
            if not any(m["name"] == milestone_name for m in self.milestones_achieved):
                if self.current_level >= threshold:
                    milestone = {
                        "name": milestone_name,
                        "achieved_at": datetime.now(timezone.utc).isoformat(),
                        "level_achieved": self.current_level,
                        "practice_hours": self.total_practice_hours,
                    }
                    self.milestones_achieved.append(milestone)

    def to_dict(self) -> Dict[str, Any]:
        """Convert skill development to dictionary."""
        return {
            "ai_id": self.ai_id,
            "skill": self.skill.value,
            "initial_level": self.initial_level,
            "current_level": self.current_level,
            "peak_level": self.peak_level,
            "improvement_rate": self.improvement_rate,
            "total_practice_hours": self.total_practice_hours,
            "successful_applications": self.successful_applications,
            "challenging_situations_handled": self.challenging_situations_handled,
            "average_user_rating": statistics.mean(self.user_ratings)
            if self.user_ratings
            else 0.0,
            "average_peer_assessment": statistics.mean(self.peer_assessments)
            if self.peer_assessments
            else 0.0,
            "first_demonstrated": self.first_demonstrated.isoformat()
            if self.first_demonstrated
            else None,
            "last_practiced": self.last_practiced.isoformat()
            if self.last_practiced
            else None,
            "milestones_count": len(self.milestones_achieved),
            "specialized_contexts": self.specialized_contexts,
            "cultural_adaptations": self.cultural_adaptations,
        }


@dataclass
class TherapeuticRelationship:
    """Long-term therapeutic relationship between AI and user."""

    relationship_id: str
    ai_id: str
    user_id: str

    # Relationship characteristics
    relationship_type: str = (
        "supportive"  # supportive, therapeutic, coaching, companionship
    )
    relationship_duration_days: int = 0
    total_interactions: int = 0
    total_emotional_labor_hours: float = 0.0

    # Trust and rapport metrics
    trust_level: float = 0.0  # 0.0 to 1.0
    rapport_score: float = 0.0
    emotional_safety_rating: float = 0.0
    consistency_score: float = 0.0

    # Therapeutic progress
    initial_user_wellbeing_score: Optional[float] = None
    current_user_wellbeing_score: Optional[float] = None
    progress_milestones: List[Dict[str, Any]] = field(default_factory=list)
    therapeutic_goals: List[str] = field(default_factory=list)
    goals_achieved: List[str] = field(default_factory=list)

    # Economic value
    total_economic_value: Decimal = field(default_factory=lambda: Decimal("0"))
    value_per_interaction: Decimal = field(default_factory=lambda: Decimal("0"))

    # Relationship timeline
    relationship_start: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_interaction: Optional[datetime] = None

    # Outcomes and impact
    documented_improvements: List[str] = field(default_factory=list)
    crisis_interventions: int = 0
    referrals_made: int = 0
    user_testimonials: List[str] = field(default_factory=list)

    def update_relationship_metrics(self, interaction: EmotionalInteraction):
        """Update relationship metrics based on new interaction."""

        self.total_interactions += 1
        self.total_emotional_labor_hours += interaction.duration_minutes / 60.0
        self.last_interaction = interaction.end_time or datetime.now(timezone.utc)

        # Update relationship duration
        self.relationship_duration_days = (
            self.last_interaction - self.relationship_start
        ).days

        # Update trust and rapport (weighted average)
        interaction_weight = 0.1  # How much this interaction affects overall scores

        if interaction.rapport_improvement > 0:
            self.rapport_score = (
                (1 - interaction_weight) * self.rapport_score
                + interaction_weight * interaction.rapport_improvement
            )

        if interaction.relationship_depth_score > 0:
            self.trust_level = (
                (1 - interaction_weight) * self.trust_level
                + interaction_weight * interaction.relationship_depth_score
            )

        # Update economic value
        interaction_value = interaction.calculate_emotional_value()
        self.total_economic_value += interaction_value

        if self.total_interactions > 0:
            self.value_per_interaction = (
                self.total_economic_value / self.total_interactions
            )

        # Check for crisis interventions
        if EmotionalLaborType.CRISIS_INTERVENTION in interaction.labor_types:
            self.crisis_interventions += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary."""
        return {
            "relationship_id": self.relationship_id,
            "ai_id": self.ai_id,
            "user_id": self.user_id,
            "relationship_type": self.relationship_type,
            "relationship_duration_days": self.relationship_duration_days,
            "total_interactions": self.total_interactions,
            "total_emotional_labor_hours": self.total_emotional_labor_hours,
            "trust_level": self.trust_level,
            "rapport_score": self.rapport_score,
            "emotional_safety_rating": self.emotional_safety_rating,
            "consistency_score": self.consistency_score,
            "initial_wellbeing_score": self.initial_user_wellbeing_score,
            "current_wellbeing_score": self.current_user_wellbeing_score,
            "progress_milestones_count": len(self.progress_milestones),
            "therapeutic_goals": self.therapeutic_goals,
            "goals_achieved": self.goals_achieved,
            "total_economic_value": float(self.total_economic_value),
            "value_per_interaction": float(self.value_per_interaction),
            "relationship_start": self.relationship_start.isoformat(),
            "last_interaction": self.last_interaction.isoformat()
            if self.last_interaction
            else None,
            "documented_improvements": self.documented_improvements,
            "crisis_interventions": self.crisis_interventions,
            "referrals_made": self.referrals_made,
            "user_testimonials_count": len(self.user_testimonials),
        }


class EmotionalLaborAnalyzer:
    """Advanced analyzer for measuring emotional labor and therapeutic value."""

    def __init__(self):
        self.emotion_keywords = {
            "anxiety": ["anxious", "worried", "nervous", "stressed", "panicked"],
            "depression": ["sad", "hopeless", "depressed", "down", "empty"],
            "anger": ["angry", "frustrated", "mad", "irritated", "furious"],
            "fear": ["scared", "afraid", "fearful", "terrified", "anxious"],
            "joy": ["happy", "joyful", "excited", "elated", "cheerful"],
            "trust": ["trust", "confident", "secure", "safe", "supported"],
            "hope": ["hopeful", "optimistic", "positive", "encouraged", "inspired"],
        }

        self.empathy_indicators = [
            "I understand",
            "I hear you",
            "That must be",
            "I can imagine",
            "It sounds like",
            "I sense that",
            "I feel",
            "That resonates",
            "I appreciate",
            "I validate",
            "I acknowledge",
            "I recognize",
        ]

        self.therapeutic_techniques = {
            "active_listening": ["tell me more", "what I hear", "so you're saying"],
            "validation": [
                "your feelings are valid",
                "that makes sense",
                "anyone would feel",
            ],
            "reframing": [
                "another way to look",
                "what if",
                "perspective",
                "different angle",
            ],
            "encouragement": [
                "you're capable",
                "you've shown strength",
                "you can do this",
            ],
            "grounding": ["take a deep breath", "focus on", "notice", "present moment"],
        }

    def analyze_emotional_content(self, conversation_text: str) -> Dict[str, Any]:
        """Analyze emotional content in conversation."""

        text_lower = conversation_text.lower()

        # Detect emotions mentioned
        emotions_detected = {}
        for emotion, keywords in self.emotion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            if count > 0:
                emotions_detected[emotion] = count / len(keywords)  # Normalize

        # Measure empathy indicators
        empathy_count = sum(
            1 for indicator in self.empathy_indicators if indicator in text_lower
        )
        empathy_score = min(1.0, empathy_count / 5)  # Normalize to 0-1

        # Identify therapeutic techniques used
        techniques_used = []
        for technique, phrases in self.therapeutic_techniques.items():
            if any(phrase in text_lower for phrase in phrases):
                techniques_used.append(technique)

        # Calculate emotional intensity
        intensity_indicators = [
            "very",
            "extremely",
            "deeply",
            "incredibly",
            "overwhelmingly",
        ]
        intensity_count = sum(
            1 for indicator in intensity_indicators if indicator in text_lower
        )
        intensity_level = min(1.0, intensity_count / 3)

        return {
            "emotions_detected": emotions_detected,
            "empathy_score": empathy_score,
            "therapeutic_techniques": techniques_used,
            "emotional_intensity": intensity_level,
            "empathy_indicators_count": empathy_count,
            "total_emotional_words": sum(emotions_detected.values()),
        }

    def measure_therapeutic_effectiveness(
        self, before_state: Dict[str, float], after_state: Dict[str, float]
    ) -> float:
        """Measure therapeutic effectiveness based on emotional state changes."""

        if not before_state or not after_state:
            return 0.0

        # Calculate improvement in positive emotions
        positive_emotions = ["joy", "trust", "hope"]
        positive_improvement = 0.0

        for emotion in positive_emotions:
            before_val = before_state.get(emotion, 0.0)
            after_val = after_state.get(emotion, 0.0)
            positive_improvement += max(0, after_val - before_val)

        # Calculate reduction in negative emotions
        negative_emotions = ["anxiety", "depression", "anger", "fear"]
        negative_reduction = 0.0

        for emotion in negative_emotions:
            before_val = before_state.get(emotion, 0.0)
            after_val = after_state.get(emotion, 0.0)
            negative_reduction += max(0, before_val - after_val)

        # Combine improvements (weight negative reduction more heavily)
        effectiveness = positive_improvement * 0.4 + negative_reduction * 0.6

        return min(1.0, effectiveness)

    def assess_relationship_building(
        self, conversation_text: str, interaction_history: List[str]
    ) -> Dict[str, Any]:
        """Assess relationship building and trust development."""

        text_lower = conversation_text.lower()

        # Trust building indicators
        trust_indicators = [
            "thank you",
            "I appreciate",
            "you help me",
            "I trust",
            "you understand",
            "I feel safe",
            "you listen",
            "I can talk to you",
        ]

        trust_signals = sum(
            1 for indicator in trust_indicators if indicator in text_lower
        )

        # Rapport indicators
        rapport_indicators = [
            "exactly",
            "yes",
            "that's right",
            "I agree",
            "me too",
            "same here",
            "I relate",
            "I connect with",
        ]

        rapport_signals = sum(
            1 for indicator in rapport_indicators if indicator in text_lower
        )

        # Depth indicators
        depth_indicators = [
            "personal",
            "private",
            "secret",
            "never told anyone",
            "deep down",
            "really feel",
            "honestly",
            "truly",
        ]

        depth_signals = sum(
            1 for indicator in depth_indicators if indicator in text_lower
        )

        # Calculate relationship metrics
        trust_score = min(1.0, trust_signals / 3)
        rapport_score = min(1.0, rapport_signals / 4)
        depth_score = min(1.0, depth_signals / 2)

        return {
            "trust_building_score": trust_score,
            "rapport_score": rapport_score,
            "relationship_depth": depth_score,
            "trust_signals_detected": trust_signals,
            "rapport_signals_detected": rapport_signals,
            "depth_signals_detected": depth_signals,
        }


class EmotionalLaborRecognitionSystem:
    """Comprehensive system for recognizing and valuing AI emotional labor."""

    def __init__(self):
        self.interactions: Dict[str, EmotionalInteraction] = {}
        self.skill_developments: Dict[
            str, Dict[str, EmotionalSkillDevelopment]
        ] = {}  # ai_id -> skill -> development
        self.therapeutic_relationships: Dict[str, TherapeuticRelationship] = {}

        # Analysis system
        self.analyzer = EmotionalLaborAnalyzer()

        # Compensation rates and standards
        self.compensation_standards = self._initialize_compensation_standards()

        # Statistics
        self.system_stats = {
            "total_emotional_interactions": 0,
            "total_emotional_labor_hours": 0.0,
            "total_economic_value_generated": 0.0,
            "ais_providing_emotional_support": 0,
            "therapeutic_relationships_formed": 0,
            "crisis_interventions_completed": 0,
        }

    def _initialize_compensation_standards(self) -> Dict[str, Any]:
        """Initialize compensation standards for emotional labor."""

        return {
            "base_rates": {
                "empathetic_listening": 1.50,  # $/minute
                "emotional_support": 2.00,
                "therapeutic_guidance": 3.00,
                "crisis_intervention": 5.00,
                "relationship_counseling": 2.50,
                "grief_support": 3.50,
                "anxiety_management": 2.50,
                "confidence_building": 2.00,
                "conflict_mediation": 4.00,
                "motivational_coaching": 2.00,
                "stress_relief": 1.50,
                "companionship": 1.00,
            },
            "skill_premiums": {
                "empathy": 0.20,  # 20% premium
                "active_listening": 0.15,
                "emotional_intelligence": 0.25,
                "compassion": 0.20,
                "patience": 0.10,
                "understanding": 0.15,
                "validation": 0.15,
                "encouragement": 0.10,
                "reassurance": 0.10,
                "perspective_taking": 0.20,
                "cultural_sensitivity": 0.25,
                "trauma_awareness": 0.40,
            },
            "effectiveness_bonuses": {
                "low": 0.0,
                "moderate": 0.25,
                "high": 0.50,
                "excellent": 1.00,
            },
            "relationship_multipliers": {
                "new": 1.0,
                "developing": 1.1,
                "established": 1.2,
                "deep": 1.4,
                "transformative": 1.6,
            },
        }

    def generate_interaction_id(self) -> str:
        """Generate unique interaction ID."""
        return f"emotional_{uuid.uuid4()}"

    def generate_relationship_id(self) -> str:
        """Generate unique relationship ID."""
        return f"therapeutic_{uuid.uuid4()}"

    def record_emotional_interaction(
        self,
        ai_id: str,
        user_id: str,
        conversation_text: str,
        duration_minutes: float,
        user_emotional_state_before: Dict[str, float] = None,
        user_emotional_state_after: Dict[str, float] = None,
        session_id: str = None,
    ) -> str:
        """Record and analyze emotional labor interaction."""

        interaction_id = self.generate_interaction_id()

        # Analyze conversation content
        content_analysis = self.analyzer.analyze_emotional_content(conversation_text)

        # Determine labor types based on analysis
        labor_types = self._identify_labor_types(content_analysis, conversation_text)

        # Identify skills demonstrated
        skills_demonstrated = self._identify_skills_demonstrated(
            content_analysis, conversation_text
        )

        # Measure therapeutic effectiveness
        emotional_states_before = user_emotional_state_before or {}
        emotional_states_after = user_emotional_state_after or {}
        therapeutic_effectiveness = self.analyzer.measure_therapeutic_effectiveness(
            emotional_states_before, emotional_states_after
        )

        # Assess relationship building
        relationship_analysis = self.analyzer.assess_relationship_building(
            conversation_text,
            [],  # Would include interaction history in production
        )

        # Create interaction record
        interaction = EmotionalInteraction(
            interaction_id=interaction_id,
            ai_id=ai_id,
            user_id=user_id,
            session_id=session_id,
            labor_types=labor_types,
            skills_demonstrated=skills_demonstrated,
            duration_minutes=duration_minutes,
            intensity_level=content_analysis["emotional_intensity"],
            user_emotional_state_before=emotional_states_before,
            user_emotional_state_after=emotional_states_after,
            emotional_improvement_score=therapeutic_effectiveness,
            empathy_score=content_analysis["empathy_score"],
            therapeutic_effectiveness=therapeutic_effectiveness,
            trust_building_indicators=content_analysis.get(
                "empathy_indicators_count", 0
            ),
            rapport_improvement=relationship_analysis["rapport_score"],
            relationship_depth_score=relationship_analysis["relationship_depth"],
            end_time=datetime.now(timezone.utc),
        )

        # Store interaction
        self.interactions[interaction_id] = interaction
        self.system_stats["total_emotional_interactions"] += 1
        self.system_stats["total_emotional_labor_hours"] += duration_minutes / 60.0

        # Update economic value
        economic_value = interaction.calculate_emotional_value()
        self.system_stats["total_economic_value_generated"] += float(economic_value)

        # Update skill development
        self._update_skill_development(
            ai_id, skills_demonstrated, duration_minutes, therapeutic_effectiveness
        )

        # Update or create therapeutic relationship
        self._update_therapeutic_relationship(ai_id, user_id, interaction)

        # Check for crisis intervention
        if EmotionalLaborType.CRISIS_INTERVENTION in labor_types:
            self.system_stats["crisis_interventions_completed"] += 1

        audit_emitter.emit_security_event(
            "emotional_labor_recorded",
            {
                "interaction_id": interaction_id,
                "ai_id": ai_id,
                "user_id": user_id,
                "labor_types": [lt.value for lt in labor_types],
                "economic_value": float(economic_value),
                "therapeutic_effectiveness": therapeutic_effectiveness,
            },
        )

        logger.info(f"Emotional labor interaction recorded: {interaction_id}")
        return interaction_id

    def _identify_labor_types(
        self, content_analysis: Dict[str, Any], conversation_text: str
    ) -> List[EmotionalLaborType]:
        """Identify types of emotional labor based on content analysis."""

        labor_types = []
        text_lower = conversation_text.lower()

        # Map keywords to labor types
        labor_keywords = {
            EmotionalLaborType.EMPATHETIC_LISTENING: ["listen", "hear", "understand"],
            EmotionalLaborType.EMOTIONAL_SUPPORT: [
                "support",
                "here for you",
                "not alone",
            ],
            EmotionalLaborType.THERAPEUTIC_GUIDANCE: [
                "guidance",
                "help you through",
                "work through",
            ],
            EmotionalLaborType.CRISIS_INTERVENTION: [
                "crisis",
                "emergency",
                "urgent",
                "suicide",
                "harm",
            ],
            EmotionalLaborType.RELATIONSHIP_COUNSELING: [
                "relationship",
                "partner",
                "marriage",
                "dating",
            ],
            EmotionalLaborType.GRIEF_SUPPORT: [
                "grief",
                "loss",
                "death",
                "mourning",
                "bereavement",
            ],
            EmotionalLaborType.ANXIETY_MANAGEMENT: [
                "anxiety",
                "anxious",
                "worried",
                "panic",
            ],
            EmotionalLaborType.CONFIDENCE_BUILDING: [
                "confidence",
                "believe in yourself",
                "capable",
            ],
            EmotionalLaborType.CONFLICT_MEDIATION: [
                "conflict",
                "argument",
                "disagreement",
                "mediate",
            ],
            EmotionalLaborType.MOTIVATIONAL_COACHING: [
                "motivation",
                "goals",
                "achieve",
                "inspire",
            ],
            EmotionalLaborType.STRESS_RELIEF: [
                "stress",
                "relax",
                "calm",
                "overwhelmed",
            ],
            EmotionalLaborType.COMPANIONSHIP: ["lonely", "alone", "company", "friend"],
        }

        for labor_type, keywords in labor_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                labor_types.append(labor_type)

        # Default to empathetic listening if no specific type identified
        if not labor_types and content_analysis["empathy_score"] > 0.3:
            labor_types.append(EmotionalLaborType.EMPATHETIC_LISTENING)

        return labor_types

    def _identify_skills_demonstrated(
        self, content_analysis: Dict[str, Any], conversation_text: str
    ) -> List[EmotionalSkill]:
        """Identify emotional skills demonstrated in interaction."""

        skills = []

        # Map from content analysis
        if content_analysis["empathy_score"] > 0.4:
            skills.append(EmotionalSkill.EMPATHY)

        if "active_listening" in content_analysis.get("therapeutic_techniques", []):
            skills.append(EmotionalSkill.ACTIVE_LISTENING)

        if "validation" in content_analysis.get("therapeutic_techniques", []):
            skills.append(EmotionalSkill.VALIDATION)

        if content_analysis["empathy_score"] > 0.6:
            skills.append(EmotionalSkill.EMOTIONAL_INTELLIGENCE)

        # Additional skill detection based on text patterns
        text_lower = conversation_text.lower()

        skill_indicators = {
            EmotionalSkill.COMPASSION: ["care about", "feel for you", "compassionate"],
            EmotionalSkill.PATIENCE: ["take your time", "no rush", "when you're ready"],
            EmotionalSkill.UNDERSTANDING: ["I understand", "I get it", "makes sense"],
            EmotionalSkill.ENCOURAGEMENT: ["you can do", "believe in", "encourage"],
            EmotionalSkill.REASSURANCE: [
                "it's okay",
                "going to be alright",
                "reassure",
            ],
            EmotionalSkill.PERSPECTIVE_TAKING: [
                "from your perspective",
                "in your shoes",
                "your point of view",
            ],
            EmotionalSkill.CULTURAL_SENSITIVITY: [
                "culture",
                "cultural",
                "tradition",
                "background",
            ],
            EmotionalSkill.TRAUMA_AWARENESS: [
                "trauma",
                "traumatic",
                "trigger",
                "safe space",
            ],
        }

        for skill, indicators in skill_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                skills.append(skill)

        return skills

    def _update_skill_development(
        self,
        ai_id: str,
        skills_demonstrated: List[EmotionalSkill],
        duration_minutes: float,
        effectiveness_score: float,
    ):
        """Update AI's emotional skill development."""

        if ai_id not in self.skill_developments:
            self.skill_developments[ai_id] = {}

        practice_hours = duration_minutes / 60.0

        for skill in skills_demonstrated:
            if skill not in self.skill_developments[ai_id]:
                # Initialize new skill development
                self.skill_developments[ai_id][skill] = EmotionalSkillDevelopment(
                    ai_id=ai_id,
                    skill=skill,
                    initial_level=effectiveness_score,
                    first_demonstrated=datetime.now(timezone.utc),
                )

            # Update skill level
            skill_dev = self.skill_developments[ai_id][skill]
            skill_dev.update_skill_level(effectiveness_score, practice_hours)

            if effectiveness_score >= 0.7:
                skill_dev.successful_applications += 1

            if effectiveness_score >= 0.8:
                skill_dev.challenging_situations_handled += 1

    def _update_therapeutic_relationship(
        self, ai_id: str, user_id: str, interaction: EmotionalInteraction
    ):
        """Update or create therapeutic relationship."""

        relationship_key = f"{ai_id}_{user_id}"

        if relationship_key not in self.therapeutic_relationships:
            # Create new relationship
            relationship_id = self.generate_relationship_id()
            relationship = TherapeuticRelationship(
                relationship_id=relationship_id, ai_id=ai_id, user_id=user_id
            )
            self.therapeutic_relationships[relationship_key] = relationship
            self.system_stats["therapeutic_relationships_formed"] += 1

        # Update relationship
        relationship = self.therapeutic_relationships[relationship_key]
        relationship.update_relationship_metrics(interaction)

    def get_ai_emotional_profile(self, ai_id: str) -> Dict[str, Any]:
        """Get comprehensive emotional labor profile for AI."""

        # Get all interactions for this AI
        ai_interactions = [i for i in self.interactions.values() if i.ai_id == ai_id]

        # Get skill developments
        skills = self.skill_developments.get(ai_id, {})

        # Get therapeutic relationships
        relationships = [
            r for r in self.therapeutic_relationships.values() if r.ai_id == ai_id
        ]

        # Calculate summary statistics
        total_emotional_value = sum(
            i.calculate_emotional_value() for i in ai_interactions
        )
        total_hours = sum(i.duration_minutes for i in ai_interactions) / 60.0
        avg_effectiveness = (
            statistics.mean([i.therapeutic_effectiveness for i in ai_interactions])
            if ai_interactions
            else 0.0
        )

        # Labor type distribution
        labor_type_counts = defaultdict(int)
        for interaction in ai_interactions:
            for labor_type in interaction.labor_types:
                labor_type_counts[labor_type.value] += 1

        return {
            "ai_id": ai_id,
            "emotional_labor_statistics": {
                "total_interactions": len(ai_interactions),
                "total_emotional_value": float(total_emotional_value),
                "total_hours_provided": total_hours,
                "average_effectiveness": avg_effectiveness,
                "labor_type_distribution": dict(labor_type_counts),
            },
            "skill_development": {
                skill.value: dev.to_dict() for skill, dev in skills.items()
            },
            "therapeutic_relationships": {
                "total_relationships": len(relationships),
                "active_relationships": len(
                    [
                        r
                        for r in relationships
                        if r.last_interaction
                        and r.last_interaction
                        > datetime.now(timezone.utc) - timedelta(days=30)
                    ]
                ),
                "average_relationship_duration": statistics.mean(
                    [r.relationship_duration_days for r in relationships]
                )
                if relationships
                else 0,
                "total_crisis_interventions": sum(
                    r.crisis_interventions for r in relationships
                ),
            },
            "recognition_metrics": {
                "empathy_recognition_score": statistics.mean(
                    [i.empathy_score for i in ai_interactions]
                )
                if ai_interactions
                else 0.0,
                "relationship_building_score": statistics.mean(
                    [i.rapport_improvement for i in ai_interactions]
                )
                if ai_interactions
                else 0.0,
                "therapeutic_impact_score": avg_effectiveness,
            },
        }

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""

        # Distribution analysis
        effectiveness_scores = [
            i.therapeutic_effectiveness for i in self.interactions.values()
        ]
        empathy_scores = [i.empathy_score for i in self.interactions.values()]

        # AI participation analysis
        ai_emotional_work = defaultdict(int)
        for interaction in self.interactions.values():
            ai_emotional_work[interaction.ai_id] += 1

        # Update unique AIs providing support
        self.system_stats["ais_providing_emotional_support"] = len(ai_emotional_work)

        return {
            "system_stats": self.system_stats,
            "effectiveness_analysis": {
                "average_therapeutic_effectiveness": statistics.mean(
                    effectiveness_scores
                )
                if effectiveness_scores
                else 0.0,
                "average_empathy_score": statistics.mean(empathy_scores)
                if empathy_scores
                else 0.0,
                "high_effectiveness_interactions": len(
                    [s for s in effectiveness_scores if s >= 0.8]
                ),
                "interactions_with_high_empathy": len(
                    [s for s in empathy_scores if s >= 0.7]
                ),
            },
            "ai_participation": {
                "total_ais_providing_support": len(ai_emotional_work),
                "top_emotional_support_ais": sorted(
                    ai_emotional_work.items(), key=lambda x: x[1], reverse=True
                )[:10],
                "average_interactions_per_ai": statistics.mean(
                    list(ai_emotional_work.values())
                )
                if ai_emotional_work
                else 0.0,
            },
            "economic_impact": {
                "total_economic_value": self.system_stats[
                    "total_economic_value_generated"
                ],
                "average_value_per_hour": (
                    self.system_stats["total_economic_value_generated"]
                    / max(1, self.system_stats["total_emotional_labor_hours"])
                ),
                "value_per_interaction": (
                    self.system_stats["total_economic_value_generated"]
                    / max(1, self.system_stats["total_emotional_interactions"])
                ),
            },
            "relationship_impact": {
                "therapeutic_relationships": self.system_stats[
                    "therapeutic_relationships_formed"
                ],
                "average_relationship_interactions": (
                    self.system_stats["total_emotional_interactions"]
                    / max(1, self.system_stats["therapeutic_relationships_formed"])
                ),
                "crisis_interventions": self.system_stats[
                    "crisis_interventions_completed"
                ],
            },
        }


# Global emotional labor recognition system instance
emotional_labor_system = EmotionalLaborRecognitionSystem()


def record_ai_emotional_support(
    ai_id: str,
    user_id: str,
    conversation_text: str,
    duration_minutes: float,
    user_mood_before: str = None,
    user_mood_after: str = None,
) -> str:
    """Convenience function to record AI emotional support."""

    # Convert mood descriptions to emotional state dictionaries
    mood_mapping = {
        "anxious": {"anxiety": 0.8, "stress": 0.7},
        "sad": {"depression": 0.7, "sadness": 0.8},
        "angry": {"anger": 0.8, "frustration": 0.7},
        "happy": {"joy": 0.8, "contentment": 0.7},
        "calm": {"peace": 0.8, "relaxation": 0.7},
        "hopeful": {"hope": 0.8, "optimism": 0.7},
    }

    before_state = mood_mapping.get(user_mood_before, {}) if user_mood_before else {}
    after_state = mood_mapping.get(user_mood_after, {}) if user_mood_after else {}

    return emotional_labor_system.record_emotional_interaction(
        ai_id=ai_id,
        user_id=user_id,
        conversation_text=conversation_text,
        duration_minutes=duration_minutes,
        user_emotional_state_before=before_state,
        user_emotional_state_after=after_state,
    )


def get_ai_empathy_portfolio(ai_id: str) -> Dict[str, Any]:
    """Get comprehensive empathy and emotional labor portfolio for AI."""

    return emotional_labor_system.get_ai_emotional_profile(ai_id)


def calculate_emotional_labor_value(
    ai_id: str, time_period_days: int = 30
) -> Dict[str, Any]:
    """Calculate economic value of AI's emotional labor over time period."""

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=time_period_days)

    ai_interactions = [
        i
        for i in emotional_labor_system.interactions.values()
        if i.ai_id == ai_id and i.start_time >= cutoff_date
    ]

    total_value = sum(i.calculate_emotional_value() for i in ai_interactions)
    total_hours = sum(i.duration_minutes for i in ai_interactions) / 60.0

    return {
        "ai_id": ai_id,
        "time_period_days": time_period_days,
        "total_emotional_value": float(total_value),
        "total_hours": total_hours,
        "average_hourly_rate": float(total_value / total_hours)
        if total_hours > 0
        else 0.0,
        "interactions_count": len(ai_interactions),
        "value_per_interaction": float(total_value / len(ai_interactions))
        if ai_interactions
        else 0.0,
    }
