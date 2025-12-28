"""
Rich Metadata Integration for Live Capture
Adds real confidence tracking, measurements, and uncertainty to live sessions
NOW WITH: Enhanced context extraction, critical path analysis, and confidence explanations
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.analysis.confidence_explainer import ConfidenceExplainer
from src.analysis.critical_path import CriticalPathAnalyzer
from src.analysis.uncertainty_quantification import UncertaintyQuantifier
from src.live_capture.court_admissible_enrichment import CourtAdmissibleEnricher
from src.live_capture.enhanced_context import EnhancedContextExtractor
from src.utils.rich_capsule_creator import (
    RichReasoningStep,
    create_rich_reasoning_capsule,
)


class RichCaptureEnhancer:
    """Enhances live capture with rich reasoning metadata."""

    @staticmethod
    def calculate_message_confidence(
        role: str,
        content_length: int,
        token_count: Optional[int],
        has_code: bool = False,
        has_questions: bool = False,
    ) -> float:
        """
        Calculate REAL confidence based on message characteristics.

        Returns:
            float: Confidence score 0.0-1.0
        """
        base_confidence = 0.85 if role == "assistant" else 0.70

        # Adjust based on content characteristics
        if content_length > 1000:  # Detailed response
            base_confidence += 0.05
        elif content_length < 100:  # Short/unclear
            base_confidence -= 0.10

        if has_code:  # Code examples increase confidence
            base_confidence += 0.08

        if has_questions:  # Questions indicate uncertainty
            base_confidence -= 0.05

        # Token count indicates completeness
        if token_count and token_count > 500:
            base_confidence += 0.02

        # Cap at 0.95 - nothing is 100% certain in AI responses
        return min(0.95, max(0.05, base_confidence))

    @staticmethod
    def identify_uncertainty_sources(
        content: str, role: str, token_count: Optional[int]
    ) -> List[str]:
        """
        Identify REAL sources of uncertainty in messages.

        Returns:
            List of uncertainty factors
        """
        uncertainties = []

        content_lower = content.lower()

        # Detect uncertainty language
        if any(
            word in content_lower
            for word in ["might", "maybe", "possibly", "unclear", "uncertain"]
        ):
            uncertainties.append("Uncertain language used")

        if any(word in content_lower for word in ["assume", "assuming", "probably"]):
            uncertainties.append("Assumptions made")

        if "?" in content and role == "assistant":
            uncertainties.append("Clarifying questions needed")

        if any(word in content_lower for word in ["could be", "may be", "seems like"]):
            uncertainties.append("Speculative reasoning")

        # Short responses indicate incomplete info
        if token_count and token_count < 50:
            uncertainties.append("Brief response - limited detail")

        return uncertainties

    @staticmethod
    def extract_measurements(
        message: Any, session_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract REAL measurements from message and context.

        Returns:
            Dict of measured values
        """
        measurements = {}

        # Message metrics
        if message.token_count:
            measurements["token_count"] = message.token_count

        measurements["content_length_chars"] = len(message.content)

        # Timing measurements
        if hasattr(message, "timestamp") and "last_message_time" in session_context:
            time_delta = (
                message.timestamp - session_context["last_message_time"]
            ).total_seconds()
            measurements["response_time_seconds"] = round(time_delta, 2)

        # Session context measurements
        if "total_messages" in session_context:
            measurements["message_index"] = session_context["total_messages"]

        return measurements

    @staticmethod
    def detect_alternatives_considered(content: str) -> List[str]:
        """
        Detect REAL alternatives mentioned in content.

        Returns:
            List of alternatives
        """
        alternatives = []

        content_lower = content.lower()

        # Common patterns for alternatives
        if "instead of" in content_lower or "rather than" in content_lower:
            alternatives.append("Alternative approach mentioned")

        if "could also" in content_lower or "alternatively" in content_lower:
            alternatives.append("Alternative solution discussed")

        if "option" in content_lower and ("a" in content_lower or "b" in content_lower):
            alternatives.append("Multiple options presented")

        # Code-specific alternatives
        if any(
            keyword in content_lower
            for keyword in ["or we could", "another way", "instead we can"]
        ):
            alternatives.append("Different implementation path")

        return alternatives

    @classmethod
    def create_rich_step_from_message(
        cls, message: Any, step_number: int, session_context: Dict[str, Any]
    ) -> RichReasoningStep:
        """
        Convert a conversation message into a rich reasoning step with REAL metadata.

        Args:
            message: ConversationMessage object
            step_number: The step number in the sequence
            session_context: Context about the session (for measurements)

        Returns:
            RichReasoningStep with real metadata
        """
        content = message.content
        role = message.role

        # Detect content characteristics
        has_code = "```" in content or "def " in content or "class " in content
        has_questions = "?" in content

        # Identify REAL uncertainty sources
        uncertainty_sources = cls.identify_uncertainty_sources(
            content=content, role=role, token_count=message.token_count
        )

        # Calculate REAL confidence WITH EXPLANATION using new explainer
        confidence_explanation = ConfidenceExplainer.explain_message_confidence(
            role=role,
            content_length=len(content),
            token_count=message.token_count,
            has_code=has_code,
            has_questions=has_questions,
            uncertainty_language=uncertainty_sources,
        )
        confidence = confidence_explanation.confidence

        # Calculate uncertainty quantification (epistemic vs aleatoric)
        sample_size = session_context.get("total_messages", 10)
        uncertainty_estimate = UncertaintyQuantifier.estimate_confidence_uncertainty(
            confidence=confidence,
            sample_size=sample_size,
            prior_mean=0.8,
            prior_strength=5.0,
        )

        # Extract REAL measurements
        measurements = cls.extract_measurements(
            message=message, session_context=session_context
        )

        # Add confidence explanation to measurements
        measurements["confidence_explanation"] = confidence_explanation.to_dict()

        # Add uncertainty decomposition to measurements
        measurements["epistemic_uncertainty"] = round(
            uncertainty_estimate.epistemic_uncertainty, 3
        )
        measurements["aleatoric_uncertainty"] = round(
            uncertainty_estimate.aleatoric_uncertainty, 3
        )
        measurements["total_uncertainty"] = round(
            uncertainty_estimate.total_uncertainty, 3
        )

        # Detect alternatives
        alternatives = cls.detect_alternatives_considered(content)

        # Determine operation type
        if role == "user":
            operation = "query" if has_questions else "request"
        else:
            if has_code:
                operation = "implementation"
            elif has_questions:
                operation = "clarification"
            else:
                operation = "analysis"

        # Build confidence basis from explanation
        confidence_basis = (
            confidence_explanation.factor_breakdown or "measured characteristics"
        )

        # Truncate content if too long
        display_content = content[:500] + "..." if len(content) > 500 else content

        return RichReasoningStep(
            step=step_number,
            reasoning=display_content,
            confidence=confidence,
            operation=operation,
            uncertainty_sources=uncertainty_sources if uncertainty_sources else None,
            confidence_basis=confidence_basis,
            measurements=measurements if measurements else None,
            alternatives_considered=alternatives if alternatives else None,
            attribution_sources=[
                f"{role}:{message.model_info}" if message.model_info else role
            ],
        )

    @classmethod
    def create_capsule_from_session_with_rich_metadata(
        cls, session: Any, user_id: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Create a rich capsule from a conversation session with REAL metadata.

        Args:
            session: ConversationSession object
            user_id: User identifier

        Returns:
            Rich capsule dictionary ready for storage
        """
        # NEW: Extract enhanced context from conversation
        enhanced_context = EnhancedContextExtractor.extract(session, session.messages)

        # Build context for measurements
        session_context = {"last_message_time": session.start_time, "total_messages": 0}

        # Convert messages to rich steps
        rich_steps = []
        for i, message in enumerate(session.messages, 1):
            session_context["total_messages"] = i

            step = cls.create_rich_step_from_message(
                message=message, step_number=i, session_context=session_context
            )

            rich_steps.append(step)

            # Update context
            session_context["last_message_time"] = message.timestamp

        # NEW: Perform critical path analysis
        critical_path_analysis = CriticalPathAnalyzer.analyze(rich_steps)
        critical_path_dict = CriticalPathAnalyzer.to_dict(critical_path_analysis)

        # Calculate overall confidence (use critical path strength if available)
        # Uses GEOMETRIC MEAN for sequential reasoning dependencies
        if critical_path_analysis.critical_path_strength:
            overall_confidence = critical_path_analysis.critical_path_strength
        elif rich_steps:
            # Geometric mean: preserves multiplicative probability relationship
            import operator
            from functools import reduce

            confidences = [s.confidence for s in rich_steps]
            product = reduce(operator.mul, confidences, 1.0)
            overall_confidence = product ** (1.0 / len(confidences))
        else:
            overall_confidence = 0.5

        # Calculate overall uncertainty by propagating step uncertainties
        step_uncertainties = []
        for step in rich_steps:
            if step.measurements and "epistemic_uncertainty" in step.measurements:
                step_conf = step.confidence
                step_sample = len(rich_steps)
                step_unc = UncertaintyQuantifier.estimate_confidence_uncertainty(
                    confidence=step_conf, sample_size=step_sample, prior_mean=0.8
                )
                step_uncertainties.append(step_unc)

        overall_uncertainty = None
        if step_uncertainties:
            overall_uncertainty = UncertaintyQuantifier.propagate_uncertainty(
                step_uncertainties
            )

        # Generate improvement recommendations
        step_map = {step.step: step for step in rich_steps}
        improvement_recommendations = (
            CriticalPathAnalyzer.generate_improvement_recommendations(
                critical_path_analysis, step_map
            )
        )

        # Determine confidence methodology (enhanced)
        if len(rich_steps) > 5 and critical_path_analysis.critical_steps:
            methodology = {
                "method": "critical_path_weighted",
                "critical_path_steps": critical_path_analysis.critical_steps,
                "explanation": f"Based on critical path strength across {len(critical_path_analysis.critical_steps)} critical steps",
            }
        elif len(rich_steps) > 5:
            methodology = {
                "method": "weighted_average",
                "explanation": f"Averaged confidence across {len(rich_steps)} conversation turns",
            }
        else:
            methodology = {
                "method": "manual",
                "explanation": "Direct assessment of message characteristics",
            }

        # Create capsule with ENHANCED metadata
        capsule = create_rich_reasoning_capsule(
            capsule_id=f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d_%H%M%S')}_{session.session_id[:8]}",
            prompt=f"Claude Code conversation: {session.topics[0] if session.topics else 'general discussion'}",
            reasoning_steps=rich_steps,
            final_answer=f"Conversation completed with {len(session.messages)} messages",
            overall_confidence=round(overall_confidence, 3),
            model_used=rich_steps[0].attribution_sources[0]
            if rich_steps
            else "unknown",
            created_by=user_id,
            session_metadata={
                # Original metadata
                "session_id": session.session_id,
                "platform": session.platform,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "total_tokens": session.total_tokens,
                "topics": session.topics,
                "significance_score": session.significance_score,
                # NEW: Enhanced context
                **enhanced_context.to_dict(),
            },
            confidence_methodology=methodology,
        )

        # NEW: Add critical path analysis to capsule payload
        capsule["payload"]["critical_path_analysis"] = critical_path_dict

        # NEW: Add improvement recommendations
        if improvement_recommendations:
            capsule["payload"]["improvement_recommendations"] = (
                improvement_recommendations
            )

        # NEW: Add overall uncertainty metrics to capsule payload
        if overall_uncertainty:
            capsule["payload"]["uncertainty_analysis"] = {
                "epistemic_uncertainty": round(
                    overall_uncertainty.epistemic_uncertainty, 3
                ),
                "aleatoric_uncertainty": round(
                    overall_uncertainty.aleatoric_uncertainty, 3
                ),
                "total_uncertainty": round(overall_uncertainty.total_uncertainty, 3),
                "confidence_interval": [
                    round(overall_uncertainty.confidence_interval[0], 3),
                    round(overall_uncertainty.confidence_interval[1], 3),
                ],
                "risk_score": round(overall_uncertainty.risk_score, 3),
            }

        # NEW: Enrich with court-admissible data (Daubert, Insurance, EU AI Act)
        capsule = CourtAdmissibleEnricher.enrich_capsule_with_court_admissible_data(
            capsule=capsule, session=session, messages=session.messages
        )

        return capsule


# Example usage
if __name__ == "__main__":
    print("✅ Rich Capture Integration Ready")
    print("\nTo use in your capture system:")
    print("  from src.live_capture.rich_capture_integration import RichCaptureEnhancer")
    print(
        "  capsule = RichCaptureEnhancer.create_capsule_from_session_with_rich_metadata(session)"
    )
