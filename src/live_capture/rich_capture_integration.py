"""
Rich Metadata Integration for Live Capture
Adds real confidence tracking, measurements, and uncertainty to live sessions
NOW WITH: Enhanced context extraction, critical path analysis, and confidence explanations
         + RFC 3161 trusted timestamps and Ed25519 cryptographic signing
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.analysis.confidence_explainer import ConfidenceExplainer
from src.analysis.critical_path import CriticalPathAnalyzer
from src.analysis.quality_assessment import QualityAssessor
from src.analysis.uncertainty_quantification import UncertaintyQuantifier
from src.live_capture.court_admissible_enrichment import CourtAdmissibleEnricher
from src.live_capture.enhanced_context import EnhancedContextExtractor
from src.live_capture.environment_capture import capture_environment_context
from src.live_capture.outcome_integration import register_capsule_for_tracking
from src.live_capture.tool_calls_capture import capture_tool_calls
from src.ml.calibration_integration import calibrate_capsule_confidence
from src.ml.historical_accuracy import get_historical_accuracy_engine

logger = logging.getLogger(__name__)

# Import crypto for Ed25519 signing with RFC 3161 timestamps
try:
    from src.security.uatp_crypto_v7 import UATPCryptoV7

    _crypto = UATPCryptoV7(key_dir=".uatp_keys", signer_id="rich_capture_v7")
    _CRYPTO_AVAILABLE = _crypto.enabled
except Exception as e:
    logger.warning(f"Crypto not available for rich capture: {e}")
    _crypto = None
    _CRYPTO_AVAILABLE = False

# Import reasoning extractor for AI enrichment
try:
    from src.enrichment.reasoning_extractor import ReasoningExtractor

    _reasoning_extractor = ReasoningExtractor()
except Exception:
    _reasoning_extractor = None

# Import embedder for semantic search
try:
    from src.embeddings.capsule_embedder import CapsuleEmbedder

    _embedder = CapsuleEmbedder()
    _EMBEDDER_AVAILABLE = True
except Exception as e:
    logger.warning(f"Embedder not available: {e}")
    _embedder = None
    _EMBEDDER_AVAILABLE = False
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

        # Keep MORE content for assistant messages (the actual decision/recommendation)
        # User messages can be truncated more aggressively
        if role == "assistant":
            # Keep up to 2000 chars for assistant responses - this is THE DECISION
            display_content = content[:2000] + "..." if len(content) > 2000 else content
        else:
            # User messages - keep up to 500 chars
            display_content = content[:500] + "..." if len(content) > 500 else content

        return RichReasoningStep(
            step=step_number,
            reasoning=display_content,
            confidence=confidence,
            operation=operation,
            role=role,  # NEW: Pass the role for clear user vs assistant distinction
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
            model_used=next(
                (
                    s.attribution_sources[0]
                    for s in rich_steps
                    if s.attribution_sources
                    and "assistant:" in s.attribution_sources[0]
                ),
                rich_steps[0].attribution_sources[0] if rich_steps else "unknown",
            ),
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

        # AI Reasoning Enrichment - extract structured reasoning from conversation
        if _reasoning_extractor and _reasoning_extractor.enabled:
            try:
                # Combine user and assistant messages for enrichment
                user_content = " ".join(
                    [m.content for m in session.messages if m.role == "user"]
                )
                assistant_content = " ".join(
                    [m.content for m in session.messages if m.role == "assistant"]
                )

                # Use local extraction (sync) for efficiency
                enrichment_result = _reasoning_extractor._extract_local(
                    user_content, assistant_content, {"session_id": session.session_id}
                )

                if enrichment_result.get("steps"):
                    capsule["payload"]["ai_enrichment"] = {
                        "reasoning_steps": enrichment_result["steps"],
                        "suggested_score": enrichment_result.get(
                            "suggested_score", 0.0
                        ),
                        "extraction_method": enrichment_result.get(
                            "extraction_method", "local"
                        ),
                        "enriched_at": datetime.now(timezone.utc).isoformat(),
                    }

                    # RECALCULATE trust_score now that we have AI enrichment
                    # This fixes the "richness paradox" identified by antigravity
                    from src.utils.rich_capsule_creator import (
                        calculate_capsule_trust_score,
                    )

                    updated_trust = calculate_capsule_trust_score(
                        reasoning_steps=capsule["payload"].get("reasoning_steps", []),
                        overall_confidence=capsule.get("confidence", 0.7),
                        verified=True,
                        ai_enrichment=capsule["payload"]["ai_enrichment"],
                    )
                    # Update trust_score in verification
                    if "verification" in capsule:
                        capsule["verification"]["trust_score"] = updated_trust
            except Exception:
                # Don't fail capsule creation if enrichment fails
                pass

        # LEGIBILITY ANALYSIS - Track how human-interpretable the reasoning is
        # This is foundational for detecting AI reasoning evolution over time
        try:
            from src.analysis.legibility_analyzer import analyze_legibility
            from src.analysis.legibility_tracker import record_legibility

            # Combine all reasoning content for legibility analysis
            full_reasoning = " ".join(
                [step.reasoning for step in rich_steps if step.reasoning]
            )

            legibility_metrics = analyze_legibility(full_reasoning)
            capsule["payload"]["legibility"] = legibility_metrics.to_dict()

            # Record for historical tracking (singularity early warning)
            model_used = capsule.get("model_used", session.platform)
            alert = record_legibility(
                capsule_id=capsule["capsule_id"],
                platform=session.platform,
                model=model_used,
                legibility_metrics=legibility_metrics.to_dict(),
            )

            if alert:
                logger.warning(f"🚨 Legibility alert: {alert.message}")
                capsule["payload"]["legibility_alert"] = {
                    "severity": alert.severity,
                    "message": alert.message,
                    "baseline": alert.baseline_score,
                }

            logger.debug(
                f"📊 Legibility score: {legibility_metrics.score:.2f} "
                f"(parseable: {legibility_metrics.human_parseable:.2f}, "
                f"novel: {legibility_metrics.novel_concept_ratio:.2f})"
            )
        except Exception as e:
            logger.debug(f"Legibility analysis skipped: {e}")

        # QUALITY ASSESSMENT - Multi-dimensional reasoning quality scoring
        # Evaluates: completeness, coherence, evidence, logic, bias, clarity
        try:
            quality_assessment = QualityAssessor.assess_capsule(capsule)
            capsule["payload"]["quality_assessment"] = {
                "overall_quality": round(quality_assessment.overall_quality, 3),
                "quality_grade": quality_assessment.quality_grade,
                "dimensions": {
                    dim: {
                        "score": round(score.score, 3),
                        "issues": score.issues,
                        "suggestions": score.suggestions[:2],  # Top 2 suggestions
                    }
                    for dim, score in quality_assessment.dimension_scores.items()
                },
                "strengths": quality_assessment.strengths,
                "weaknesses": quality_assessment.weaknesses,
                "improvement_priority": [
                    {"dimension": dim, "impact": round(impact, 3)}
                    for dim, impact in quality_assessment.improvement_priority[:3]
                ],
                "assessed_at": datetime.now(timezone.utc).isoformat(),
            }
            logger.info(
                f"📊 Quality assessment: Grade {quality_assessment.quality_grade} "
                f"({quality_assessment.overall_quality:.2f})"
            )
        except Exception as e:
            logger.debug(f"Quality assessment skipped: {e}")

        # ENVIRONMENT CONTEXT CAPTURE (Gap 4)
        # Captures git state, platform info, and working directory
        try:
            environment_context = capture_environment_context()
            capsule["payload"]["environment"] = environment_context
            logger.info(
                f"🌍 Environment captured: git={environment_context.get('git', {}).get('branch', 'N/A')}, "
                f"commit={environment_context.get('git', {}).get('commit', 'N/A')}"
            )
        except Exception as e:
            logger.debug(f"Environment capture skipped: {e}")

        # TOOL CALLS CAPTURE (Gap 3)
        # Captures tool operations from the Claude Code transcript
        try:
            # Don't filter by session_start - capture all recent tool calls
            # The transcript contains the current session's tool calls
            tool_calls_data = capture_tool_calls(
                session_start=None,  # Capture all available tool calls
                max_calls=100,  # Reasonable limit
            )
            if tool_calls_data.get("tool_calls"):
                capsule["payload"]["tool_calls"] = tool_calls_data["tool_calls"]
                capsule["payload"]["tool_calls_summary"] = tool_calls_data["summary"]
                logger.info(
                    f"🔧 Tool calls captured: {tool_calls_data['summary']['total_calls']} calls, "
                    f"tools: {list(tool_calls_data['summary'].get('by_tool', {}).keys())}"
                )
            else:
                logger.debug("No tool calls found in transcript")
        except Exception as e:
            logger.debug(f"Tool calls capture skipped: {e}")

        # CRYPTOGRAPHIC SIGNING with RFC 3161 trusted timestamp
        # This provides insurance-grade proof of:
        # - WHO signed (Ed25519 key holder)
        # - WHAT was signed (SHA256 hash)
        # - WHEN it existed (RFC 3161 from DigiCert)
        if _CRYPTO_AVAILABLE and _crypto:
            try:
                # Sign with auto timestamp mode (tries online TSA, falls back to local)
                verification = _crypto.sign_capsule(capsule, timestamp_mode="auto")
                capsule["verification"] = verification

                ts_info = verification.get("timestamp", {})
                if ts_info.get("trusted"):
                    logger.info(
                        f"🔐 Capsule {capsule['capsule_id']} signed with RFC 3161 timestamp "
                        f"from {ts_info.get('tsa_url', 'TSA')}"
                    )
                else:
                    logger.info(
                        f"🔐 Capsule {capsule['capsule_id']} signed with Ed25519 "
                        f"(local timestamp fallback)"
                    )
            except Exception as e:
                logger.warning(f"⚠️ Crypto signing failed, capsule unsigned: {e}")
        else:
            logger.debug("Crypto not available, capsule will be unsigned")

        # EMBEDDING for semantic similarity search
        # Generates TF-IDF vector for finding similar capsules
        if _EMBEDDER_AVAILABLE and _embedder:
            try:
                embedding = _embedder.embed_capsule(
                    {"payload": capsule.get("payload", {})}
                )
                capsule["embedding"] = embedding
                capsule["embedding_model"] = _embedder.model_name
                capsule["embedding_created_at"] = datetime.now(timezone.utc).isoformat()
                logger.debug(
                    f"📊 Capsule {capsule['capsule_id']} embedded ({len(embedding)} dims)"
                )

                # HISTORICAL ACCURACY LEARNING (Gap 2)
                # Uses embedding to find similar past capsules and learn from outcomes
                try:
                    historical_engine = get_historical_accuracy_engine()
                    historical_result = historical_engine.analyze_for_capsule(
                        query_embedding=embedding,
                        model_confidence=overall_confidence,
                        capsule_id=capsule["capsule_id"],
                    )

                    # Store historical accuracy analysis
                    capsule["payload"]["historical_accuracy"] = (
                        historical_result.to_dict()
                    )

                    # Update confidence if we have enough historical data
                    if historical_result.sample_size >= 3:
                        # Store both original and adjusted confidence
                        capsule["payload"]["confidence_original"] = overall_confidence
                        capsule["payload"]["confidence"] = (
                            historical_result.adjusted_confidence
                        )

                        logger.info(
                            f"📈 Historical accuracy: {historical_result.sample_size} similar capsules, "
                            f"accuracy={historical_result.historical_accuracy:.0%}, "
                            f"confidence adjusted {overall_confidence:.0%} -> {historical_result.adjusted_confidence:.0%}"
                        )
                    else:
                        logger.debug(
                            f"📊 Historical accuracy: {historical_result.sample_size} similar capsules "
                            f"(need 3+ for confidence adjustment)"
                        )
                except Exception as e:
                    logger.debug(f"Historical accuracy analysis skipped: {e}")

                # CALIBRATION FEEDBACK (Gap 5)
                # Apply calibration based on historical prediction accuracy
                try:
                    current_confidence = capsule["payload"].get(
                        "confidence", overall_confidence
                    )
                    topics = session.topics if hasattr(session, "topics") else []

                    (
                        calibrated_confidence,
                        calibration_info,
                    ) = calibrate_capsule_confidence(
                        raw_confidence=current_confidence,
                        topics=topics,
                    )

                    if calibration_info.get("calibration") == "applied":
                        # Store calibration info
                        capsule["payload"]["calibration"] = calibration_info
                        capsule["payload"]["confidence_pre_calibration"] = (
                            current_confidence
                        )
                        capsule["payload"]["confidence"] = calibrated_confidence

                        logger.info(
                            f"📏 Calibration applied: {current_confidence:.0%} -> {calibrated_confidence:.0%} "
                            f"(adjustment: {calibration_info.get('adjustment', 0):+.1%})"
                        )
                    else:
                        # Not enough data for calibration
                        capsule["payload"]["calibration"] = calibration_info
                        logger.debug(
                            f"Calibration: {calibration_info.get('calibration', 'unknown')}"
                        )
                except Exception as e:
                    logger.debug(f"Calibration skipped: {e}")

            except Exception as e:
                logger.debug(f"Embedding skipped: {e}")

        # OUTCOME TRACKING REGISTRATION (Gap 1)
        # Register this capsule for outcome tracking
        # When a follow-up message comes in, we'll infer whether the recommendation worked
        try:
            # Get the assistant's response for tracking
            assistant_responses = [
                step.reasoning for step in rich_steps if step.role == "assistant"
            ]
            if assistant_responses:
                response_text = assistant_responses[-1]  # Last assistant response
                topics = session.topics if hasattr(session, "topics") else []

                register_capsule_for_tracking(
                    capsule_id=capsule["capsule_id"],
                    response_text=response_text,
                    confidence=capsule["payload"].get("confidence", overall_confidence),
                    topics=topics,
                )
                logger.debug(
                    f"📋 Capsule {capsule['capsule_id']} registered for outcome tracking"
                )
        except Exception as e:
            logger.debug(f"Outcome tracking registration skipped: {e}")

        return capsule


# Example usage
if __name__ == "__main__":
    print("✅ Rich Capture Integration Ready")
    print("\nTo use in your capture system:")
    print("  from src.live_capture.rich_capture_integration import RichCaptureEnhancer")
    print(
        "  capsule = RichCaptureEnhancer.create_capsule_from_session_with_rich_metadata(session)"
    )
