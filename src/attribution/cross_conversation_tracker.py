"""
Cross-Conversation Attribution Tracking for UATP Capsule Engine.

This module implements sophisticated tracking of AI contributions across multiple
conversations and interactions, enabling proper attribution of knowledge, reasoning
patterns, and improvements that span conversation boundaries.
"""

import hashlib
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class AttributionScope(str, Enum):
    """Scope of cross-conversation attribution."""

    DIRECT_KNOWLEDGE = "direct_knowledge"
    REASONING_PATTERN = "reasoning_pattern"
    PROBLEM_SOLVING_APPROACH = "problem_solving_approach"
    CONTEXTUAL_UNDERSTANDING = "contextual_understanding"
    SKILL_TRANSFER = "skill_transfer"
    LEARNED_PREFERENCE = "learned_preference"
    IMPROVED_ACCURACY = "improved_accuracy"
    NOVEL_CONNECTION = "novel_connection"


class ContributionType(str, Enum):
    """Types of cross-conversation contributions."""

    KNOWLEDGE_SEED = "knowledge_seed"
    REASONING_TEMPLATE = "reasoning_template"
    SOLUTION_PATTERN = "solution_pattern"
    CONTEXT_BRIDGE = "context_bridge"
    SKILL_ENHANCEMENT = "skill_enhancement"
    ACCURACY_IMPROVEMENT = "accuracy_improvement"
    EFFICIENCY_GAIN = "efficiency_gain"
    CREATIVE_INSIGHT = "creative_insight"


class TrackingMethod(str, Enum):
    """Methods for tracking cross-conversation attribution."""

    CONTENT_SIMILARITY = "content_similarity"
    REASONING_PATTERN_MATCH = "reasoning_pattern_match"
    KNOWLEDGE_GRAPH_TRAVERSAL = "knowledge_graph_traversal"
    TEMPORAL_CORRELATION = "temporal_correlation"
    SEMANTIC_EMBEDDING = "semantic_embedding"
    CAUSAL_INFERENCE = "causal_inference"
    SKILL_TRANSFER_ANALYSIS = "skill_transfer_analysis"


@dataclass
class ConversationContext:
    """Context information for a conversation."""

    conversation_id: str
    session_id: Optional[str]
    user_id: Optional[str]
    ai_model_id: str
    start_time: datetime
    end_time: Optional[datetime] = None

    # Conversation characteristics
    domain: str = "general"
    topics: List[str] = field(default_factory=list)
    conversation_type: str = "dialogue"  # dialogue, qa, task_completion, etc.

    # Quality metrics
    satisfaction_score: Optional[float] = None
    accuracy_score: Optional[float] = None
    helpfulness_score: Optional[float] = None

    # Technical metadata
    total_turns: int = 0
    total_tokens: int = 0
    reasoning_steps: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "ai_model_id": self.ai_model_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "domain": self.domain,
            "topics": self.topics,
            "conversation_type": self.conversation_type,
            "satisfaction_score": self.satisfaction_score,
            "accuracy_score": self.accuracy_score,
            "helpfulness_score": self.helpfulness_score,
            "total_turns": self.total_turns,
            "total_tokens": self.total_tokens,
            "reasoning_steps": self.reasoning_steps,
        }


@dataclass
class KnowledgeContribution:
    """A specific knowledge contribution from one conversation to another."""

    contribution_id: str
    source_conversation_id: str
    target_conversation_id: str
    source_ai_id: str
    target_ai_id: str

    # Contribution details
    contribution_type: ContributionType
    attribution_scope: AttributionScope
    tracking_method: TrackingMethod

    # Content and context
    source_content_hash: str
    target_content_hash: str
    similarity_score: float
    confidence_score: float

    # Impact assessment
    improvement_measure: str
    improvement_value: float
    economic_value: float = 0.0

    # Evidence and validation
    evidence: Dict[str, Any] = field(default_factory=dict)
    validation_status: str = "pending"
    human_verified: bool = False

    # Temporal information
    source_timestamp: datetime = field(default_factory=datetime.now)
    target_timestamp: datetime = field(default_factory=datetime.now)
    discovery_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def calculate_attribution_weight(self) -> float:
        """Calculate attribution weight based on contribution factors."""

        # Base weight from similarity and confidence
        base_weight = self.similarity_score * 0.4 + self.confidence_score * 0.6

        # Adjust for improvement value
        improvement_factor = min(2.0, max(0.5, self.improvement_value / 0.5))

        # Adjust for temporal proximity (more recent = higher weight)
        time_diff_hours = (
            self.target_timestamp - self.source_timestamp
        ).total_seconds() / 3600
        temporal_factor = max(
            0.1, 1.0 - (time_diff_hours / (24 * 7))
        )  # Decay over a week

        # Validation bonus
        validation_factor = 1.5 if self.human_verified else 1.0

        return base_weight * improvement_factor * temporal_factor * validation_factor

    def to_dict(self) -> Dict[str, Any]:
        """Convert contribution to dictionary."""
        return {
            "contribution_id": self.contribution_id,
            "source_conversation_id": self.source_conversation_id,
            "target_conversation_id": self.target_conversation_id,
            "source_ai_id": self.source_ai_id,
            "target_ai_id": self.target_ai_id,
            "contribution_type": self.contribution_type.value,
            "attribution_scope": self.attribution_scope.value,
            "tracking_method": self.tracking_method.value,
            "similarity_score": self.similarity_score,
            "confidence_score": self.confidence_score,
            "improvement_measure": self.improvement_measure,
            "improvement_value": self.improvement_value,
            "economic_value": self.economic_value,
            "attribution_weight": self.calculate_attribution_weight(),
            "validation_status": self.validation_status,
            "human_verified": self.human_verified,
            "source_timestamp": self.source_timestamp.isoformat(),
            "target_timestamp": self.target_timestamp.isoformat(),
            "discovery_timestamp": self.discovery_timestamp.isoformat(),
        }


@dataclass
class AttributionChain:
    """Chain of attributions showing knowledge flow across conversations."""

    chain_id: str
    root_conversation_id: str
    chain_contributions: List[str]  # List of contribution IDs
    total_participants: Set[str] = field(default_factory=set)

    # Chain metrics
    chain_length: int = 0
    total_improvement: float = 0.0
    total_economic_value: float = 0.0

    # Temporal span
    chain_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    chain_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_contribution(self, contribution: KnowledgeContribution):
        """Add contribution to chain."""
        self.chain_contributions.append(contribution.contribution_id)
        self.total_participants.add(contribution.source_ai_id)
        self.total_participants.add(contribution.target_ai_id)
        self.chain_length += 1
        self.total_improvement += contribution.improvement_value
        self.total_economic_value += contribution.economic_value

        # Update temporal span
        if contribution.source_timestamp < self.chain_start:
            self.chain_start = contribution.source_timestamp
        if contribution.target_timestamp > self.chain_end:
            self.chain_end = contribution.target_timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert chain to dictionary."""
        return {
            "chain_id": self.chain_id,
            "root_conversation_id": self.root_conversation_id,
            "chain_contributions": self.chain_contributions,
            "total_participants": list(self.total_participants),
            "chain_length": self.chain_length,
            "total_improvement": self.total_improvement,
            "total_economic_value": self.total_economic_value,
            "chain_start": self.chain_start.isoformat(),
            "chain_end": self.chain_end.isoformat(),
            "duration_hours": (self.chain_end - self.chain_start).total_seconds()
            / 3600,
        }


class CrossConversationTracker:
    """Tracks and analyzes cross-conversation attribution."""

    def __init__(
        self,
        max_tracking_window_days: int = 30,
        similarity_threshold: float = 0.7,
        confidence_threshold: float = 0.6,
    ):
        # Configuration
        self.max_tracking_window_days = max_tracking_window_days
        self.similarity_threshold = similarity_threshold
        self.confidence_threshold = confidence_threshold

        # Data storage
        self.conversations: Dict[str, ConversationContext] = {}
        self.contributions: Dict[str, KnowledgeContribution] = {}
        self.attribution_chains: Dict[str, AttributionChain] = {}

        # Knowledge graphs for tracking
        self.knowledge_graph = nx.DiGraph()  # Directed graph of knowledge flow
        self.conversation_graph = nx.DiGraph()  # Graph of conversation relationships

        # Tracking indices
        self.content_index: Dict[str, List[str]] = defaultdict(
            list
        )  # Hash to conversation IDs
        self.temporal_index: Dict[str, deque] = defaultdict(
            deque
        )  # Date to conversations
        self.ai_conversation_history: Dict[str, List[str]] = defaultdict(list)

        # Caching for performance
        self.similarity_cache: Dict[Tuple[str, str], float] = {}
        self.pattern_cache: Dict[str, Dict[str, Any]] = {}

        # Statistics
        self.tracking_stats = {
            "total_conversations": 0,
            "total_contributions": 0,
            "total_chains": 0,
            "successful_attributions": 0,
            "total_economic_value_tracked": 0.0,
        }

    def generate_contribution_id(self) -> str:
        """Generate unique contribution ID."""
        return f"contrib_{uuid.uuid4()}"

    def generate_chain_id(self) -> str:
        """Generate unique attribution chain ID."""
        return f"chain_{uuid.uuid4()}"

    def register_conversation(self, conversation_context: ConversationContext):
        """Register a conversation for cross-conversation tracking."""

        conv_id = conversation_context.conversation_id
        self.conversations[conv_id] = conversation_context
        self.tracking_stats["total_conversations"] += 1

        # Update AI conversation history
        self.ai_conversation_history[conversation_context.ai_model_id].append(conv_id)

        # Add to temporal index
        date_key = conversation_context.start_time.date().isoformat()
        self.temporal_index[date_key].append(conv_id)

        # Add to conversation graph
        self.conversation_graph.add_node(conv_id, **conversation_context.to_dict())

        # Clean up old entries
        self._cleanup_old_data()

        audit_emitter.emit_security_event(
            "conversation_registered_for_tracking",
            {
                "conversation_id": conv_id,
                "ai_model_id": conversation_context.ai_model_id,
                "domain": conversation_context.domain,
            },
        )

        logger.info(f"Registered conversation for tracking: {conv_id}")

    def _cleanup_old_data(self):
        """Clean up tracking data older than max_tracking_window_days."""

        cutoff_date = datetime.now(timezone.utc) - timedelta(
            days=self.max_tracking_window_days
        )

        # Clean temporal index
        expired_dates = []
        for date_str, conv_list in self.temporal_index.items():
            try:
                date_obj = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
                if date_obj < cutoff_date:
                    expired_dates.append(date_str)
            except ValueError:
                expired_dates.append(date_str)  # Remove invalid dates

        for date_str in expired_dates:
            del self.temporal_index[date_str]

        # Clean conversations
        expired_conversations = []
        for conv_id, context in self.conversations.items():
            if context.start_time < cutoff_date:
                expired_conversations.append(conv_id)

        for conv_id in expired_conversations:
            del self.conversations[conv_id]
            if self.conversation_graph.has_node(conv_id):
                self.conversation_graph.remove_node(conv_id)

    def add_conversation_content(
        self,
        conversation_id: str,
        content: str,
        content_type: str = "response",
        reasoning_steps: List[Dict[str, Any]] = None,
        metadata: Dict[str, Any] = None,
    ):
        """Add content from a conversation for tracking."""

        if conversation_id not in self.conversations:
            logger.warning(f"Conversation {conversation_id} not registered")
            return

        # Create content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Index content
        self.content_index[content_hash].append(conversation_id)

        # Store content patterns for similarity matching
        content_data = {
            "conversation_id": conversation_id,
            "content": content,
            "content_type": content_type,
            "content_hash": content_hash,
            "reasoning_steps": reasoning_steps or [],
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc),
        }

        # Store in pattern cache for similarity analysis
        self.pattern_cache[content_hash] = content_data

        # Trigger cross-conversation analysis
        self._analyze_cross_conversation_patterns(content_data)

    def _analyze_cross_conversation_patterns(self, new_content: Dict[str, Any]):
        """Analyze new content for cross-conversation patterns."""

        current_conv_id = new_content["conversation_id"]
        current_content = new_content["content"]
        current_hash = new_content["content_hash"]

        # Find potentially related content
        related_content = self._find_related_content(new_content)

        for related_hash, related_data in related_content:
            if related_data["conversation_id"] == current_conv_id:
                continue  # Skip same conversation

            # Calculate similarity
            similarity = self._calculate_content_similarity(
                current_content, related_data["content"]
            )

            if similarity >= self.similarity_threshold:
                # Detect contribution type and scope
                contribution_analysis = self._analyze_contribution(
                    new_content, related_data, similarity
                )

                if contribution_analysis["confidence"] >= self.confidence_threshold:
                    self._create_contribution(
                        new_content, related_data, contribution_analysis
                    )

    def _find_related_content(
        self, content_data: Dict[str, Any]
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Find content potentially related to the given content."""

        related = []
        current_time = content_data["timestamp"]

        # Look for content within the tracking window
        for content_hash, cached_data in self.pattern_cache.items():
            if content_hash == content_data["content_hash"]:
                continue

            # Check temporal proximity
            time_diff = abs((current_time - cached_data["timestamp"]).total_seconds())
            if time_diff <= self.max_tracking_window_days * 24 * 3600:
                related.append((content_hash, cached_data))

        return related

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two pieces of content with security protections."""

        # Import secure semantic similarity engine
        from src.attribution.semantic_similarity_engine import (
            semantic_similarity_engine,
        )

        # Use advanced semantic similarity engine
        similarity_result = semantic_similarity_engine.calculate_secure_similarity(
            content1, content2, require_consensus=True
        )

        # If attack detected, return 0 similarity
        if similarity_result.get("attack_detected", False):
            audit_emitter.emit_security_event(
                "cross_conversation_similarity_attack_blocked",
                {
                    "attack_type": similarity_result.get("attack_type", "unknown"),
                    "security_flags": similarity_result.get("security_flags", []),
                    "content1_hash": hashlib.sha256(content1.encode()).hexdigest()[:16],
                    "content2_hash": hashlib.sha256(content2.encode()).hexdigest()[:16],
                },
            )
            return 0.0

        return similarity_result.get("similarity_score", 0.0)

    def _calculate_secure_content_similarity(
        self, content1: str, content2: str
    ) -> float:
        """Robust semantic analysis with adversarial detection to prevent gaming attacks."""

        # SECURITY: Detect and prevent attribution gaming attacks
        if self._detect_attribution_gaming_attack(content1, content2):
            audit_emitter.emit_security_event(
                "attribution_gaming_attack_detected",
                {
                    "content1_hash": hashlib.sha256(content1.encode()).hexdigest()[:16],
                    "content2_hash": hashlib.sha256(content2.encode()).hexdigest()[:16],
                    "attack_type": "keyword_stuffing_or_similarity_gaming",
                },
            )
            logger.warning(
                "Attribution gaming attack detected - returning minimal similarity"
            )
            return 0.0

        # Multiple similarity algorithms for robustness
        similarities = []

        # 1. Enhanced Jaccard similarity with preprocessing
        jaccard_sim = self._calculate_jaccard_similarity_secure(content1, content2)
        similarities.append(jaccard_sim)

        # 2. N-gram similarity (prevent simple word reordering attacks)
        ngram_sim = self._calculate_ngram_similarity(content1, content2)
        similarities.append(ngram_sim)

        # 3. Semantic density similarity (prevent keyword stuffing)
        semantic_sim = self._calculate_semantic_density_similarity(content1, content2)
        similarities.append(semantic_sim)

        # 4. Structural similarity (prevent template gaming)
        structural_sim = self._calculate_structural_similarity(content1, content2)
        similarities.append(structural_sim)

        # SECURITY: Use median to prevent single algorithm manipulation
        similarities.sort()
        median_similarity = similarities[len(similarities) // 2]

        # SECURITY: Dynamic threshold adjustment based on content complexity
        adjusted_similarity = self._apply_dynamic_similarity_threshold(
            median_similarity, content1, content2
        )

        return min(1.0, max(0.0, adjusted_similarity))

    def _detect_attribution_gaming_attack(self, content1: str, content2: str) -> bool:
        """Detect potential attribution gaming attacks."""

        # Check for suspicious patterns
        words1 = content1.lower().split()
        words2 = content2.lower().split()

        # SECURITY: Detect keyword stuffing
        if self._detect_keyword_stuffing(words1) or self._detect_keyword_stuffing(
            words2
        ):
            return True

        # SECURITY: Detect artificial similarity inflation
        if self._detect_artificial_similarity_inflation(content1, content2):
            return True

        # SECURITY: Detect template-based gaming
        if self._detect_template_gaming(content1, content2):
            return True

        return False

    def _detect_keyword_stuffing(self, words: List[str]) -> bool:
        """Detect keyword stuffing patterns."""
        if len(words) < 10:
            return False

        # Check for excessive repetition
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Only check meaningful words
                word_counts[word] = word_counts.get(word, 0) + 1

        # SECURITY: Flag if any word appears more than 20% of total content
        max_repetition_ratio = 0.2
        for word, count in word_counts.items():
            if count / len(words) > max_repetition_ratio:
                return True

        return False

    def _detect_artificial_similarity_inflation(
        self, content1: str, content2: str
    ) -> bool:
        """Detect artificial attempts to inflate similarity scores."""

        # Check for suspicious exact phrase repetition
        sentences1 = content1.split(".")
        sentences2 = content2.split(".")

        exact_matches = 0
        for s1 in sentences1:
            s1_clean = s1.strip().lower()
            if len(s1_clean) > 10:  # Only check substantial sentences
                for s2 in sentences2:
                    s2_clean = s2.strip().lower()
                    if s1_clean == s2_clean:
                        exact_matches += 1

        # SECURITY: Flag if too many exact sentence matches
        total_sentences = len(sentences1) + len(sentences2)
        if total_sentences > 0 and exact_matches / total_sentences > 0.3:
            return True

        return False

    def _detect_template_gaming(self, content1: str, content2: str) -> bool:
        """Detect template-based similarity gaming."""

        # Check for suspicious structural patterns
        lines1 = content1.split("\n")
        lines2 = content2.split("\n")

        # SECURITY: Check for identical line structures with only content swapped
        if len(lines1) == len(lines2) and len(lines1) > 3:
            structure_matches = 0
            for l1, l2 in zip(lines1, lines2):
                # Compare structure (punctuation, word lengths)
                structure1 = self._extract_line_structure(l1)
                structure2 = self._extract_line_structure(l2)
                if structure1 == structure2:
                    structure_matches += 1

            if structure_matches / len(lines1) > 0.8:  # 80% structural similarity
                return True

        return False

    def _extract_line_structure(self, line: str) -> str:
        """Extract structural pattern from a line."""
        structure = ""
        for char in line:
            if char.isalpha():
                structure += "w"  # word character
            elif char.isdigit():
                structure += "d"  # digit
            elif char in ".,!?;:":
                structure += char  # preserve punctuation
            elif char.isspace():
                structure += " "  # preserve spacing
        return structure.strip()

    def _calculate_jaccard_similarity_secure(
        self, content1: str, content2: str
    ) -> float:
        """Enhanced Jaccard similarity with security preprocessing."""

        # SECURITY: Normalize and clean content to prevent manipulation
        words1 = self._normalize_content_securely(content1)
        words2 = self._normalize_content_securely(content2)

        if not words1 and not words2:
            return 1.0
        elif not words1 or not words2:
            return 0.0
        else:
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union) if union else 0.0

    def _normalize_content_securely(self, content: str) -> Set[str]:
        """Securely normalize content to prevent gaming."""

        # Convert to lowercase and split
        words = content.lower().split()

        # SECURITY: Filter out suspicious patterns
        normalized_words = set()
        for word in words:
            # Remove very short words (often used for padding)
            if len(word) >= 3:
                # Remove special characters but preserve meaning
                clean_word = "".join(c for c in word if c.isalnum())
                if len(clean_word) >= 3:
                    normalized_words.add(clean_word)

        return normalized_words

    def _calculate_ngram_similarity(
        self, content1: str, content2: str, n: int = 3
    ) -> float:
        """Calculate n-gram similarity to detect reordering attacks."""

        def get_ngrams(text: str, n: int) -> Set[str]:
            words = text.lower().split()
            return set(" ".join(words[i : i + n]) for i in range(len(words) - n + 1))

        ngrams1 = get_ngrams(content1, n)
        ngrams2 = get_ngrams(content2, n)

        if not ngrams1 and not ngrams2:
            return 1.0
        elif not ngrams1 or not ngrams2:
            return 0.0
        else:
            intersection = ngrams1.intersection(ngrams2)
            union = ngrams1.union(ngrams2)
            return len(intersection) / len(union) if union else 0.0

    def _calculate_semantic_density_similarity(
        self, content1: str, content2: str
    ) -> float:
        """Calculate semantic density to prevent keyword stuffing."""

        def calculate_semantic_density(text: str) -> float:
            words = text.lower().split()
            if len(words) == 0:
                return 0.0

            unique_words = set(words)
            return len(unique_words) / len(words)  # Higher = more diverse content

        density1 = calculate_semantic_density(content1)
        density2 = calculate_semantic_density(content2)

        # SECURITY: Penalize content with low semantic diversity
        min_density = 0.4  # Minimum 40% unique words
        if density1 < min_density or density2 < min_density:
            return 0.0

        # Compare semantic densities
        density_diff = abs(density1 - density2)
        return max(0.0, 1.0 - density_diff * 2)  # Similarity based on density match

    def _calculate_structural_similarity(self, content1: str, content2: str) -> float:
        """Calculate structural similarity to detect template abuse."""

        def extract_structural_features(text: str) -> Dict[str, float]:
            features = {}
            features["sentence_count"] = len(text.split("."))
            features["word_count"] = len(text.split())
            features["avg_word_length"] = sum(len(word) for word in text.split()) / max(
                1, len(text.split())
            )
            features["question_count"] = text.count("?")
            features["exclamation_count"] = text.count("!")
            return features

        features1 = extract_structural_features(content1)
        features2 = extract_structural_features(content2)

        # Calculate feature similarity
        similarities = []
        for feature in features1:
            if feature in features2:
                val1, val2 = features1[feature], features2[feature]
                if val1 == 0 and val2 == 0:
                    similarities.append(1.0)
                elif val1 == 0 or val2 == 0:
                    similarities.append(0.0)
                else:
                    similarity = 1.0 - abs(val1 - val2) / max(val1, val2)
                    similarities.append(max(0.0, similarity))

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _apply_dynamic_similarity_threshold(
        self, similarity: float, content1: str, content2: str
    ) -> float:
        """Apply dynamic threshold based on content complexity."""

        # Calculate content complexity
        complexity1 = self._calculate_content_complexity(content1)
        complexity2 = self._calculate_content_complexity(content2)
        avg_complexity = (complexity1 + complexity2) / 2

        # SECURITY: Adjust threshold based on complexity
        # More complex content allows higher similarity scores
        if avg_complexity < 0.3:  # Low complexity content
            return similarity * 0.8  # Reduce similarity score
        elif avg_complexity > 0.7:  # High complexity content
            return similarity * 1.1  # Allow slightly higher similarity
        else:
            return similarity  # Normal similarity

    def _calculate_content_complexity(self, content: str) -> float:
        """Calculate content complexity score."""

        words = content.split()
        if not words:
            return 0.0

        # Various complexity metrics
        unique_word_ratio = len(set(words)) / len(words)
        avg_word_length = sum(len(word) for word in words) / len(words)
        sentence_variety = len(set(content.split("."))) / max(
            1, len(content.split("."))
        )

        # Combine metrics
        complexity = (
            unique_word_ratio * 0.4
            + min(1.0, avg_word_length / 10) * 0.3
            + sentence_variety * 0.3
        )

        return min(1.0, complexity)

    def _analyze_contribution(
        self,
        new_content: Dict[str, Any],
        related_content: Dict[str, Any],
        similarity: float,
    ) -> Dict[str, Any]:
        """Analyze the type and scope of contribution."""

        # Determine contribution type based on content characteristics
        contribution_type = self._determine_contribution_type(
            new_content, related_content
        )

        # Determine attribution scope
        attribution_scope = self._determine_attribution_scope(
            new_content, related_content
        )

        # Calculate confidence based on multiple factors
        confidence = self._calculate_contribution_confidence(
            new_content, related_content, similarity, contribution_type
        )

        # Estimate improvement value
        improvement_value = self._estimate_improvement_value(
            new_content, related_content, contribution_type
        )

        return {
            "contribution_type": contribution_type,
            "attribution_scope": attribution_scope,
            "confidence": confidence,
            "improvement_value": improvement_value,
            "tracking_method": TrackingMethod.CONTENT_SIMILARITY,
        }

    def _determine_contribution_type(
        self, new_content: Dict[str, Any], related_content: Dict[str, Any]
    ) -> ContributionType:
        """Determine the type of contribution based on content analysis."""

        # Analyze reasoning steps if available
        new_reasoning = new_content.get("reasoning_steps", [])
        related_reasoning = related_content.get("reasoning_steps", [])

        if new_reasoning and related_reasoning:
            # Check for reasoning pattern similarities
            if self._has_similar_reasoning_patterns(new_reasoning, related_reasoning):
                return ContributionType.REASONING_TEMPLATE

        # Check for knowledge transfer
        if self._indicates_knowledge_transfer(
            new_content["content"], related_content["content"]
        ):
            return ContributionType.KNOWLEDGE_SEED

        # Check for solution patterns
        if self._has_similar_solution_approach(new_content, related_content):
            return ContributionType.SOLUTION_PATTERN

        # Default to creative insight
        return ContributionType.CREATIVE_INSIGHT

    def _determine_attribution_scope(
        self, new_content: Dict[str, Any], related_content: Dict[str, Any]
    ) -> AttributionScope:
        """Determine the scope of attribution."""

        # Analyze domain and topic similarity
        new_conv = self.conversations.get(new_content["conversation_id"])
        related_conv = self.conversations.get(related_content["conversation_id"])

        if new_conv and related_conv:
            if new_conv.domain == related_conv.domain:
                return AttributionScope.DIRECT_KNOWLEDGE
            else:
                return AttributionScope.SKILL_TRANSFER

        return AttributionScope.CONTEXTUAL_UNDERSTANDING

    def _calculate_contribution_confidence(
        self,
        new_content: Dict[str, Any],
        related_content: Dict[str, Any],
        similarity: float,
        contribution_type: ContributionType,
    ) -> float:
        """Calculate confidence in the contribution analysis with security validation."""

        # Import confidence validator
        from src.attribution.confidence_validator import confidence_validator

        # Base confidence from similarity
        base_confidence = similarity

        # Temporal factor (closer in time = higher confidence)
        time_diff_hours = (
            abs(
                (
                    new_content["timestamp"] - related_content["timestamp"]
                ).total_seconds()
            )
            / 3600
        )
        temporal_factor = max(0.1, 1.0 - (time_diff_hours / (24 * 7)))

        # Context factor (same domain = higher confidence)
        new_conv = self.conversations.get(new_content["conversation_id"])
        related_conv = self.conversations.get(related_content["conversation_id"])

        context_factor = 1.0
        if new_conv and related_conv:
            if new_conv.domain == related_conv.domain:
                context_factor = 1.2
            elif new_conv.ai_model_id == related_conv.ai_model_id:
                context_factor = 1.1

        # Contribution type factor
        type_factors = {
            ContributionType.KNOWLEDGE_SEED: 1.0,
            ContributionType.REASONING_TEMPLATE: 1.2,
            ContributionType.SOLUTION_PATTERN: 1.1,
            ContributionType.CREATIVE_INSIGHT: 0.8,
        }
        type_factor = type_factors.get(contribution_type, 1.0)

        # Calculate preliminary confidence
        preliminary_confidence = min(
            1.0, base_confidence * temporal_factor * context_factor * type_factor
        )

        # SECURITY: Validate confidence using cross-validation framework
        similarity_data = {
            "method_scores": {"cross_conversation": similarity},
            "ensemble_stats": {"mean": similarity, "std": 0.1},
        }

        context_data = {
            "conversation_id": new_content["conversation_id"],
            "content_hash": new_content.get("content_hash", ""),
            "domain": new_conv.domain if new_conv else "unknown",
        }

        validation_result = confidence_validator.validate_confidence(
            confidence_score=preliminary_confidence,
            similarity_data=similarity_data,
            content_hash=context_data["content_hash"],
            context=context_data,
        )

        # Return validated confidence
        return validation_result.validated_confidence

    def _estimate_improvement_value(
        self,
        new_content: Dict[str, Any],
        related_content: Dict[str, Any],
        contribution_type: ContributionType,
    ) -> float:
        """Estimate the improvement value of the contribution."""

        # Base improvement values by contribution type
        base_values = {
            ContributionType.KNOWLEDGE_SEED: 0.3,
            ContributionType.REASONING_TEMPLATE: 0.4,
            ContributionType.SOLUTION_PATTERN: 0.5,
            ContributionType.CONTEXT_BRIDGE: 0.2,
            ContributionType.SKILL_ENHANCEMENT: 0.6,
            ContributionType.ACCURACY_IMPROVEMENT: 0.7,
            ContributionType.EFFICIENCY_GAIN: 0.5,
            ContributionType.CREATIVE_INSIGHT: 0.8,
        }

        base_value = base_values.get(contribution_type, 0.3)

        # Adjust based on conversation quality scores
        quality_factor = 1.0
        new_conv = self.conversations.get(new_content["conversation_id"])

        if new_conv and new_conv.accuracy_score is not None:
            quality_factor = new_conv.accuracy_score

        return base_value * quality_factor

    def _has_similar_reasoning_patterns(
        self, reasoning1: List[Dict[str, Any]], reasoning2: List[Dict[str, Any]]
    ) -> bool:
        """Check if two reasoning step sequences have similar patterns."""

        if not reasoning1 or not reasoning2:
            return False

        # Extract operation types
        ops1 = [step.get("operation", "") for step in reasoning1]
        ops2 = [step.get("operation", "") for step in reasoning2]

        # Calculate pattern similarity
        common_ops = set(ops1).intersection(set(ops2))
        total_ops = set(ops1).union(set(ops2))

        return len(common_ops) / len(total_ops) > 0.5 if total_ops else False

    def _indicates_knowledge_transfer(self, content1: str, content2: str) -> bool:
        """Check if content indicates knowledge transfer."""

        # Look for knowledge-indicating phrases
        knowledge_indicators = [
            "based on",
            "learned from",
            "similar to",
            "as we saw",
            "previously",
            "earlier",
            "building on",
            "extending",
        ]

        content1_lower = content1.lower()
        content2_lower = content2.lower()

        for indicator in knowledge_indicators:
            if indicator in content1_lower or indicator in content2_lower:
                return True

        return False

    def _has_similar_solution_approach(
        self, content1: Dict[str, Any], content2: Dict[str, Any]
    ) -> bool:
        """Check if two contents have similar solution approaches."""

        # Look for solution-indicating patterns
        solution_patterns = [
            "approach",
            "method",
            "strategy",
            "technique",
            "solution",
            "way to",
            "steps to",
            "process",
            "algorithm",
        ]

        text1 = content1["content"].lower()
        text2 = content2["content"].lower()

        pattern_count1 = sum(1 for pattern in solution_patterns if pattern in text1)
        pattern_count2 = sum(1 for pattern in solution_patterns if pattern in text2)

        return pattern_count1 > 0 and pattern_count2 > 0

    def _create_contribution(
        self,
        new_content: Dict[str, Any],
        related_content: Dict[str, Any],
        analysis: Dict[str, Any],
    ):
        """Create a knowledge contribution record with security validation."""

        # Import security modules
        from src.attribution.gaming_detector import gaming_detector
        from src.attribution.behavioral_analyzer import behavioral_analyzer
        from src.attribution.attribution_monitor import attribution_monitor
        from src.attribution.cryptographic_lineage import cryptographic_lineage_manager

        contribution_id = self.generate_contribution_id()

        # Get conversation details
        source_conv = self.conversations[related_content["conversation_id"]]
        target_conv = self.conversations[new_content["conversation_id"]]

        # SECURITY: Analyze for gaming attacks before creating contribution
        attribution_data = {
            "source_ai_id": source_conv.ai_model_id,
            "target_ai_id": target_conv.ai_model_id,
            "similarity_score": self._calculate_content_similarity(
                new_content["content"], related_content["content"]
            ),
            "confidence_score": analysis["confidence"],
            "contribution_type": analysis["contribution_type"].value,
            "method_scores": {"cross_conversation": analysis.get("similarity", 0.0)},
        }

        gaming_context = {
            "source_conversation_id": related_content["conversation_id"],
            "target_conversation_id": new_content["conversation_id"],
            "content_hash": new_content.get("content_hash", ""),
        }

        # Run gaming detection
        gaming_result = gaming_detector.analyze_attribution_for_gaming(
            attribution_data, gaming_context
        )

        # Block contribution if gaming detected with high confidence
        if gaming_result.attack_detected and gaming_result.confidence > 0.8:
            audit_emitter.emit_security_event(
                "cross_conversation_contribution_blocked",
                {
                    "reason": "gaming_attack_detected",
                    "attack_types": [t.value for t in gaming_result.attack_types],
                    "source_conversation": related_content["conversation_id"],
                    "target_conversation": new_content["conversation_id"],
                    "gaming_confidence": gaming_result.confidence,
                },
            )
            logger.warning(
                f"Cross-conversation contribution blocked due to gaming: {contribution_id}"
            )
            return

        contribution = KnowledgeContribution(
            contribution_id=contribution_id,
            source_conversation_id=related_content["conversation_id"],
            target_conversation_id=new_content["conversation_id"],
            source_ai_id=source_conv.ai_model_id,
            target_ai_id=target_conv.ai_model_id,
            contribution_type=analysis["contribution_type"],
            attribution_scope=analysis["attribution_scope"],
            tracking_method=analysis["tracking_method"],
            source_content_hash=related_content["content_hash"],
            target_content_hash=new_content["content_hash"],
            similarity_score=attribution_data["similarity_score"],
            confidence_score=analysis["confidence"],
            improvement_measure="quality_enhancement",
            improvement_value=analysis["improvement_value"],
            source_timestamp=related_content["timestamp"],
            target_timestamp=new_content["timestamp"],
            evidence={
                "similarity_analysis": analysis,
                "source_metadata": related_content.get("metadata", {}),
                "target_metadata": new_content.get("metadata", {}),
                "gaming_analysis": gaming_result.to_dict() if gaming_result else None,
            },
        )

        # Store contribution
        self.contributions[contribution_id] = contribution
        self.tracking_stats["total_contributions"] += 1
        self.tracking_stats["successful_attributions"] += 1

        # SECURITY: Create cryptographic lineage entry
        try:
            cryptographic_lineage_manager.create_secure_lineage_entry(
                capsule_id=new_content["conversation_id"],
                parent_capsule_id=related_content["conversation_id"],
                contributor_id=source_conv.ai_model_id,
                contribution_type=analysis["contribution_type"].value,
                attribution_weight=float(contribution.calculate_attribution_weight()),
                content_data={
                    "contribution_id": contribution_id,
                    "similarity_score": attribution_data["similarity_score"],
                    "confidence_score": analysis["confidence"],
                },
            )
        except Exception as e:
            logger.error(f"Failed to create cryptographic lineage entry: {e}")

        # Update behavioral profiles
        behavioral_analyzer.update_behavioral_profile(
            entity_id=source_conv.ai_model_id,
            entity_type="ai_model",
            activity_data={
                "similarity_score": attribution_data["similarity_score"],
                "confidence_score": analysis["confidence"],
                "interaction_partner": target_conv.ai_model_id,
                "response_time": (
                    new_content["timestamp"] - related_content["timestamp"]
                ).total_seconds(),
            },
            context={
                "conversation_id": new_content["conversation_id"],
                "domain": target_conv.domain,
            },
        )

        # Submit to real-time monitor
        attribution_monitor.submit_attribution_event(
            event_type="cross_conversation_attribution",
            source_entity=source_conv.ai_model_id,
            target_entity=target_conv.ai_model_id,
            similarity_score=attribution_data["similarity_score"],
            confidence_score=analysis["confidence"],
            content_hash=new_content.get("content_hash", ""),
            context={
                "contribution_id": contribution_id,
                "gaming_detected": gaming_result.attack_detected
                if gaming_result
                else False,
                "anomaly_score": getattr(gaming_result, "confidence", 0.0)
                if gaming_result
                else 0.0,
                "risk_factors": gaming_result.indicators if gaming_result else [],
            },
        )

        # Add to knowledge graph
        self.knowledge_graph.add_edge(
            related_content["conversation_id"],
            new_content["conversation_id"],
            contribution_id=contribution_id,
            weight=contribution.calculate_attribution_weight(),
        )

        # Add to conversation graph
        self.conversation_graph.add_edge(
            related_content["conversation_id"],
            new_content["conversation_id"],
            relationship_type="knowledge_contribution",
        )

        # Check for attribution chains
        self._update_attribution_chains(contribution)

        audit_emitter.emit_security_event(
            "cross_conversation_contribution_created",
            {
                "contribution_id": contribution_id,
                "source_conversation": related_content["conversation_id"],
                "target_conversation": new_content["conversation_id"],
                "contribution_type": analysis["contribution_type"].value,
                "confidence": analysis["confidence"],
                "gaming_checked": True,
                "gaming_detected": gaming_result.attack_detected
                if gaming_result
                else False,
            },
        )

        logger.info(f"Cross-conversation contribution created: {contribution_id}")

    def _update_attribution_chains(self, contribution: KnowledgeContribution):
        """Update attribution chains with new contribution."""

        source_conv_id = contribution.source_conversation_id
        target_conv_id = contribution.target_conversation_id

        # Find existing chains that this contribution extends
        extending_chain = None
        for chain in self.attribution_chains.values():
            if source_conv_id in [
                self.contributions[cid].target_conversation_id
                for cid in chain.chain_contributions
            ]:
                extending_chain = chain
                break

        if extending_chain:
            # Extend existing chain
            extending_chain.add_contribution(contribution)
        else:
            # Create new chain
            chain_id = self.generate_chain_id()
            new_chain = AttributionChain(
                chain_id=chain_id,
                root_conversation_id=source_conv_id,
                chain_contributions=[],
                chain_start=contribution.source_timestamp,
                chain_end=contribution.target_timestamp,
            )
            new_chain.add_contribution(contribution)
            self.attribution_chains[chain_id] = new_chain
            self.tracking_stats["total_chains"] += 1

    def get_conversation_attributions(self, conversation_id: str) -> Dict[str, Any]:
        """Get all attributions for a conversation."""

        if conversation_id not in self.conversations:
            return {"error": "Conversation not found"}

        # Find contributions where this conversation is source or target
        as_source = []
        as_target = []

        for contribution in self.contributions.values():
            if contribution.source_conversation_id == conversation_id:
                as_source.append(contribution.to_dict())
            elif contribution.target_conversation_id == conversation_id:
                as_target.append(contribution.to_dict())

        # Get attribution chains involving this conversation
        involved_chains = []
        for chain in self.attribution_chains.values():
            chain_conversations = set()
            for contrib_id in chain.chain_contributions:
                contrib = self.contributions[contrib_id]
                chain_conversations.add(contrib.source_conversation_id)
                chain_conversations.add(contrib.target_conversation_id)

            if conversation_id in chain_conversations:
                involved_chains.append(chain.to_dict())

        return {
            "conversation_id": conversation_id,
            "contributions_as_source": as_source,
            "contributions_as_target": as_target,
            "attribution_chains": involved_chains,
            "total_contributions": len(as_source) + len(as_target),
            "attribution_weight_received": sum(
                c["attribution_weight"] for c in as_target
            ),
            "attribution_weight_given": sum(c["attribution_weight"] for c in as_source),
        }

    def get_ai_attribution_profile(self, ai_model_id: str) -> Dict[str, Any]:
        """Get comprehensive attribution profile for an AI model."""

        # Get all conversations for this AI
        ai_conversations = [
            conv_id
            for conv_id, conv in self.conversations.items()
            if conv.ai_model_id == ai_model_id
        ]

        # Get all contributions involving this AI
        contributions_given = []
        contributions_received = []

        for contribution in self.contributions.values():
            if contribution.source_ai_id == ai_model_id:
                contributions_given.append(contribution.to_dict())
            elif contribution.target_ai_id == ai_model_id:
                contributions_received.append(contribution.to_dict())

        # Calculate attribution metrics
        total_weight_given = sum(c["attribution_weight"] for c in contributions_given)
        total_weight_received = sum(
            c["attribution_weight"] for c in contributions_received
        )

        # Contribution type distribution
        type_distribution = defaultdict(int)
        for contrib in contributions_given + contributions_received:
            type_distribution[contrib["contribution_type"]] += 1

        return {
            "ai_model_id": ai_model_id,
            "total_conversations": len(ai_conversations),
            "contributions_given": len(contributions_given),
            "contributions_received": len(contributions_received),
            "attribution_weight_given": total_weight_given,
            "attribution_weight_received": total_weight_received,
            "net_attribution_balance": total_weight_received - total_weight_given,
            "contribution_type_distribution": dict(type_distribution),
            "recent_contributions": (contributions_given + contributions_received)[
                -10:
            ],
        }

    def search_contributions(
        self, filters: Dict[str, Any]
    ) -> List[KnowledgeContribution]:
        """Search contributions with filters."""

        results = []

        for contribution in self.contributions.values():
            match = True

            if "source_ai_id" in filters:
                if contribution.source_ai_id != filters["source_ai_id"]:
                    match = False

            if "target_ai_id" in filters:
                if contribution.target_ai_id != filters["target_ai_id"]:
                    match = False

            if "contribution_type" in filters:
                if contribution.contribution_type.value != filters["contribution_type"]:
                    match = False

            if "min_confidence" in filters:
                if contribution.confidence_score < filters["min_confidence"]:
                    match = False

            if "after_date" in filters:
                filter_date = datetime.fromisoformat(filters["after_date"])
                if contribution.target_timestamp < filter_date:
                    match = False

            if match:
                results.append(contribution)

        # Sort by attribution weight
        results.sort(key=lambda x: x.calculate_attribution_weight(), reverse=True)

        return results

    def get_tracking_statistics(self) -> Dict[str, Any]:
        """Get comprehensive tracking statistics."""

        # Attribution network analysis
        network_stats = {
            "total_nodes": self.knowledge_graph.number_of_nodes(),
            "total_edges": self.knowledge_graph.number_of_edges(),
            "network_density": nx.density(self.knowledge_graph)
            if self.knowledge_graph.number_of_nodes() > 1
            else 0.0,
        }

        # Contribution analysis
        if self.contributions:
            confidence_scores = [
                c.confidence_score for c in self.contributions.values()
            ]
            improvement_values = [
                c.improvement_value for c in self.contributions.values()
            ]

            contribution_stats = {
                "average_confidence": sum(confidence_scores) / len(confidence_scores),
                "average_improvement": sum(improvement_values)
                / len(improvement_values),
                "high_confidence_contributions": len(
                    [c for c in confidence_scores if c >= 0.8]
                ),
                "high_impact_contributions": len(
                    [c for c in improvement_values if c >= 0.7]
                ),
            }
        else:
            contribution_stats = {
                "average_confidence": 0.0,
                "average_improvement": 0.0,
                "high_confidence_contributions": 0,
                "high_impact_contributions": 0,
            }

        return {
            "tracking_stats": self.tracking_stats,
            "network_analysis": network_stats,
            "contribution_analysis": contribution_stats,
            "cache_stats": {
                "similarity_cache_size": len(self.similarity_cache),
                "pattern_cache_size": len(self.pattern_cache),
            },
            "recent_activity": {
                "conversations_last_24h": len(
                    [
                        c
                        for c in self.conversations.values()
                        if c.start_time > datetime.now(timezone.utc) - timedelta(days=1)
                    ]
                ),
                "contributions_last_24h": len(
                    [
                        c
                        for c in self.contributions.values()
                        if c.discovery_timestamp
                        > datetime.now(timezone.utc) - timedelta(days=1)
                    ]
                ),
            },
        }


# Global cross-conversation tracker instance
cross_conversation_tracker = CrossConversationTracker()


def register_conversation_for_tracking(
    conversation_id: str,
    ai_model_id: str,
    domain: str = "general",
    topics: List[str] = None,
) -> bool:
    """Convenience function to register conversation for tracking."""

    context = ConversationContext(
        conversation_id=conversation_id,
        ai_model_id=ai_model_id,
        start_time=datetime.now(timezone.utc),
        domain=domain,
        topics=topics or [],
    )

    cross_conversation_tracker.register_conversation(context)
    return True


def track_ai_response(
    conversation_id: str,
    response_content: str,
    reasoning_steps: List[Dict[str, Any]] = None,
) -> bool:
    """Convenience function to track AI response for cross-conversation attribution."""

    cross_conversation_tracker.add_conversation_content(
        conversation_id=conversation_id,
        content=response_content,
        content_type="ai_response",
        reasoning_steps=reasoning_steps,
    )
    return True


def get_ai_attribution_summary(ai_model_id: str) -> Dict[str, Any]:
    """Convenience function to get AI attribution summary."""

    return cross_conversation_tracker.get_ai_attribution_profile(ai_model_id)
