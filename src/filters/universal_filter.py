"""
Universal UATP Filter System
============================

This is the central filter that ALL AI interactions must pass through.
It determines what gets encapsulated based on significance analysis.

Flow:
1. All AI interactions → Universal Filter
2. Filter analyzes significance
3. If significant → Create capsule
4. If not significant → Log and discard

Configuration:
- Significance threshold (default: 0.6)
- User-specific preferences
- Platform-specific rules
- Content type filtering
"""

import asyncio
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.reasoning.analyzer import analyze_conversation_significance

# from src.engine.capsule_engine import CapsuleEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FilterDecision(Enum):
    """Possible filter decisions."""

    ENCAPSULATE = "encapsulate"
    DISCARD = "discard"
    DEFER = "defer"  # Wait for more context
    REVIEW = "review"  # Needs manual review


@dataclass
class FilterConfig:
    """Configuration for the universal filter."""

    significance_threshold: float = 0.6
    min_conversation_length: int = 2
    max_conversation_length: int = 100
    require_user_interaction: bool = True

    # Platform-specific settings
    platform_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "openai": 1.0,
            "claude": 1.0,
            "anthropic": 1.0,
            "claude_code": 1.2,  # Slightly higher weight for code interactions
            "windsurf": 1.1,
            "cursor": 1.0,
        }
    )

    # Content type weights
    content_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "code_generation": 1.3,
            "problem_solving": 1.2,
            "learning": 1.1,
            "casual_chat": 0.8,
            "debugging": 1.4,
            "architecture": 1.5,
        }
    )

    # User-specific preferences
    user_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FilterResult:
    """Result of filtering an AI interaction."""

    decision: FilterDecision
    confidence: float
    significance_score: float
    reasoning: List[str]
    metadata: Dict[str, Any]
    should_encapsulate: bool
    capsule_type: str = "reasoning_trace"

    def to_dict(self) -> Dict:
        return {
            "decision": self.decision.value,
            "confidence": self.confidence,
            "significance_score": self.significance_score,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "should_encapsulate": self.should_encapsulate,
            "capsule_type": self.capsule_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class UniversalFilter:
    """
    Universal filter that processes ALL AI interactions to determine encapsulation.

    This is the single point of decision-making for the entire UATP system.
    """

    def __init__(
        self, config: Optional[FilterConfig] = None, engine: Optional[Any] = None
    ):
        self.config = config or FilterConfig()
        self.engine = engine  # Will be set up later when needed

        # Statistics
        self.total_processed = 0
        self.total_encapsulated = 0
        self.total_discarded = 0

        # Callbacks for different decisions
        self.callbacks: Dict[FilterDecision, List[Callable]] = {
            FilterDecision.ENCAPSULATE: [],
            FilterDecision.DISCARD: [],
            FilterDecision.DEFER: [],
            FilterDecision.REVIEW: [],
        }

        logger.info(
            f" Universal Filter initialized with threshold {self.config.significance_threshold}"
        )

    async def process_interaction(
        self, interaction_data: Dict[str, Any], user_id: str, platform: str
    ) -> FilterResult:
        """
        Process an AI interaction through the universal filter.

        Args:
            interaction_data: The interaction data (messages, context, etc.)
            user_id: ID of the user
            platform: Platform where interaction occurred

        Returns:
            FilterResult with decision and metadata
        """

        self.total_processed += 1

        try:
            # Extract messages and context
            messages = interaction_data.get("messages", [])
            context = interaction_data.get("context", {})
            context.update(
                {
                    "user_id": user_id,
                    "platform": platform,
                    "conversation_length": len(messages),
                }
            )

            # Basic validation
            if not self._validate_interaction(messages, context):
                return FilterResult(
                    decision=FilterDecision.DISCARD,
                    confidence=0.9,
                    significance_score=0.0,
                    reasoning=["Failed basic validation"],
                    metadata={"validation_failed": True},
                    should_encapsulate=False,
                )

            # Analyze significance
            significance_result = await analyze_conversation_significance(
                messages, context
            )

            # Apply platform and content weights
            weighted_score = self._apply_weights(
                significance_result, platform, messages
            )

            # Make decision
            decision = self._make_decision(weighted_score, significance_result, context)

            # Create result
            result = FilterResult(
                decision=decision,
                confidence=significance_result.get("confidence", 0.8),
                significance_score=weighted_score,
                reasoning=significance_result.get("factors", []),
                metadata={
                    "platform": platform,
                    "user_id": user_id,
                    "original_score": significance_result.get("score", 0.0),
                    "weighted_score": weighted_score,
                    "analysis_details": significance_result,
                },
                should_encapsulate=(decision == FilterDecision.ENCAPSULATE),
            )

            # Execute callbacks
            await self._execute_callbacks(decision, result, interaction_data)

            # Log decision
            self._log_decision(result)

            return result

        except Exception as e:
            logger.error(f"Error processing interaction: {e}")
            return FilterResult(
                decision=FilterDecision.DISCARD,
                confidence=0.0,
                significance_score=0.0,
                reasoning=[f"Processing error: {str(e)}"],
                metadata={"error": str(e)},
                should_encapsulate=False,
            )

    def _validate_interaction(self, messages: List[Dict], context: Dict) -> bool:
        """Validate that the interaction meets basic requirements."""

        # Must have messages
        if not messages:
            return False

        # Must meet minimum length requirement
        if len(messages) < self.config.min_conversation_length:
            return False

        # Must not exceed maximum length
        if len(messages) > self.config.max_conversation_length:
            return False

        # Must have user interaction if required
        if self.config.require_user_interaction:
            has_user_message = any(msg.get("role") == "user" for msg in messages)
            if not has_user_message:
                return False

        return True

    def _apply_weights(
        self, significance_result: Dict, platform: str, messages: List[Dict]
    ) -> float:
        """Apply platform and content weights to the significance score."""

        base_score = significance_result.get("score", 0.0)

        # Apply platform weight
        platform_weight = self.config.platform_weights.get(platform.lower(), 1.0)
        weighted_score = base_score * platform_weight

        # Apply content type weights
        content_types = self._detect_content_types(messages)
        for content_type in content_types:
            content_weight = self.config.content_weights.get(content_type, 1.0)
            weighted_score *= content_weight

        return weighted_score

    def _detect_content_types(self, messages: List[Dict]) -> List[str]:
        """Detect content types in the messages."""

        content_types = []
        combined_text = " ".join(msg.get("content", "") for msg in messages).lower()

        # Code generation
        if any(
            marker in combined_text
            for marker in ["```", "def ", "class ", "function", "import"]
        ):
            content_types.append("code_generation")

        # Problem solving
        if any(
            word in combined_text
            for word in ["problem", "issue", "error", "bug", "fix", "solve"]
        ):
            content_types.append("problem_solving")

        # Learning
        if any(
            word in combined_text
            for word in ["how to", "explain", "tutorial", "guide", "learn"]
        ):
            content_types.append("learning")

        # Debugging
        if any(
            word in combined_text for word in ["debug", "trace", "exception", "stack"]
        ):
            content_types.append("debugging")

        # Architecture
        if any(
            word in combined_text
            for word in ["architecture", "design", "pattern", "system"]
        ):
            content_types.append("architecture")

        # Default to casual chat if no specific type detected
        if not content_types:
            content_types.append("casual_chat")

        return content_types

    def _make_decision(
        self, weighted_score: float, significance_result: Dict, context: Dict
    ) -> FilterDecision:
        """Make the final decision about encapsulation."""

        # Check significance threshold
        if weighted_score >= self.config.significance_threshold:
            return FilterDecision.ENCAPSULATE

        # Check if it's close to threshold (defer for more context)
        if weighted_score >= (self.config.significance_threshold * 0.8):
            return FilterDecision.DEFER

        # Check if it needs manual review
        if weighted_score >= (self.config.significance_threshold * 0.5):
            return FilterDecision.REVIEW

        # Otherwise discard
        return FilterDecision.DISCARD

    async def _execute_callbacks(
        self, decision: FilterDecision, result: FilterResult, interaction_data: Dict
    ):
        """Execute callbacks for the decision."""

        callbacks = self.callbacks.get(decision, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(result, interaction_data)
                else:
                    callback(result, interaction_data)
            except Exception as e:
                logger.error(f"Error executing callback: {e}")

    def _log_decision(self, result: FilterResult):
        """Log the filter decision."""

        if result.decision == FilterDecision.ENCAPSULATE:
            self.total_encapsulated += 1
            logger.info(
                f"[OK] ENCAPSULATE - Score: {result.significance_score:.2f} - {result.reasoning[:2]}"
            )
        elif result.decision == FilterDecision.DISCARD:
            self.total_discarded += 1
            logger.debug(f"[ERROR] DISCARD - Score: {result.significance_score:.2f}")
        elif result.decision == FilterDecision.DEFER:
            logger.info(
                f"⏳ DEFER - Score: {result.significance_score:.2f} - Waiting for more context"
            )
        elif result.decision == FilterDecision.REVIEW:
            logger.info(
                f"️ REVIEW - Score: {result.significance_score:.2f} - Manual review needed"
            )

    def add_callback(self, decision: FilterDecision, callback: Callable):
        """Add a callback for a specific decision type."""
        self.callbacks[decision].append(callback)

    def get_stats(self) -> Dict[str, Any]:
        """Get filter statistics."""
        return {
            "total_processed": self.total_processed,
            "total_encapsulated": self.total_encapsulated,
            "total_discarded": self.total_discarded,
            "encapsulation_rate": self.total_encapsulated
            / max(self.total_processed, 1),
            "discard_rate": self.total_discarded / max(self.total_processed, 1),
            "config": {
                "significance_threshold": self.config.significance_threshold,
                "min_conversation_length": self.config.min_conversation_length,
                "max_conversation_length": self.config.max_conversation_length,
            },
        }

    def update_config(self, new_config: Dict[str, Any]):
        """Update filter configuration."""
        for key, value in new_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f" Updated filter config: {key} = {value}")


# Global filter instance
_universal_filter = None


def get_universal_filter() -> UniversalFilter:
    """Get the global universal filter instance."""
    global _universal_filter
    if _universal_filter is None:
        _universal_filter = UniversalFilter()
    return _universal_filter


# Convenience functions
async def filter_interaction(
    interaction_data: Dict[str, Any], user_id: str, platform: str
) -> FilterResult:
    """Filter an AI interaction through the universal filter."""
    filter_instance = get_universal_filter()
    return await filter_instance.process_interaction(
        interaction_data, user_id, platform
    )


def should_encapsulate(
    interaction_data: Dict[str, Any], user_id: str, platform: str
) -> bool:
    """Quick check if an interaction should be encapsulated."""
    # This is a synchronous version for simple checks
    filter_instance = get_universal_filter()

    # Simple heuristic for sync check
    messages = interaction_data.get("messages", [])
    if len(messages) < filter_instance.config.min_conversation_length:
        return False

    # For full analysis, use filter_interaction async
    return True
