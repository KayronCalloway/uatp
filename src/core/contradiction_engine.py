"""
Contradiction Engine
====================

Detects contradictions and inconsistencies in capsules:
- Summary vs last user request (semantic drift)
- Claimed quality vs actual evidence
- Confidence scores vs supporting evidence
- Tool results vs conclusions

A protocol that can accuse itself is closer to truth.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Contradiction:
    """A detected contradiction."""

    category: str  # "semantic_drift", "quality_mismatch", "evidence_gap", etc.
    severity: str  # "critical", "warning", "info"
    description: str
    field_a: str
    field_b: str
    recommendation: str


class ContradictionEngine:
    """Detects contradictions and inconsistencies in capsules."""

    @staticmethod
    def check_semantic_drift(
        last_user_message: str,
        summary: str,
        decision: Optional[str] = None,
    ) -> List[Contradiction]:
        """Check if summary addresses the last user request."""
        contradictions = []

        if not last_user_message or not summary:
            return contradictions

        user_lower = last_user_message.lower().strip()
        summary_lower = summary.lower()

        # Extract key topics from user message
        stop_words = {
            "the",
            "and",
            "for",
            "that",
            "this",
            "with",
            "from",
            "have",
            "what",
            "how",
            "why",
            "where",
            "when",
            "can",
            "does",
            "are",
            "you",
            "your",
            "would",
            "could",
            "should",
            "will",
            "just",
            "please",
            "want",
            "need",
            "like",
            "make",
            "sure",
            "know",
        }

        # Get meaningful terms from user message
        user_terms = {
            w.strip("?.,!")
            for w in user_lower.split()
            if len(w) > 3 and w.strip("?.,!") not in stop_words
        }

        # Get terms from summary
        summary_terms = {
            w.strip("?.,!")
            for w in summary_lower.split()
            if len(w) > 3 and w.strip("?.,!") not in stop_words
        }

        # Check overlap
        if len(user_terms) > 0:
            overlap = user_terms & summary_terms
            coverage = len(overlap) / len(user_terms)

            if coverage < 0.2:
                contradictions.append(
                    Contradiction(
                        category="semantic_drift",
                        severity="critical",
                        description=(
                            f"Summary does not address user request. "
                            f"User asked about: {', '.join(list(user_terms)[:5])}. "
                            f"Summary covers: {', '.join(list(summary_terms)[:5]) or 'unrelated topics'}"
                        ),
                        field_a="last_user_message",
                        field_b="summary",
                        recommendation="Regenerate summary to address the actual user question",
                    )
                )

        return contradictions

    @staticmethod
    def check_quality_consistency(
        evidence_quality: Optional[float],
        logical_validity: Optional[float],
        overall_grade: Optional[str],
        has_evidence: bool,
    ) -> List[Contradiction]:
        """Check if quality scores are internally consistent."""
        contradictions = []

        # Check: if "no evidence" then evidence_quality should not be 1.0
        if not has_evidence and evidence_quality is not None and evidence_quality > 0.5:
            contradictions.append(
                Contradiction(
                    category="quality_mismatch",
                    severity="warning",
                    description=(
                        f"Evidence quality score ({evidence_quality}) is high "
                        f"but no explicit evidence was provided"
                    ),
                    field_a="evidence_quality",
                    field_b="has_evidence",
                    recommendation="Evidence quality should reflect actual evidence provided",
                )
            )

        # Check: perfect scores (1.0) with poor grade
        if (
            evidence_quality == 1.0
            and logical_validity == 1.0
            and overall_grade
            and overall_grade.upper() in ["D", "F"]
        ):
            contradictions.append(
                Contradiction(
                    category="quality_mismatch",
                    severity="critical",
                    description=(
                        f"Perfect evidence_quality (1.0) and logical_validity (1.0) "
                        f"but overall grade is {overall_grade}"
                    ),
                    field_a="component_scores",
                    field_b="overall_grade",
                    recommendation="Scores and grade should be consistent",
                )
            )

        return contradictions

    @staticmethod
    def check_confidence_evidence_alignment(
        confidence: float,
        confidence_interval: Optional[Tuple[float, float]],
        evidence_count: int,
        tool_verified_count: int,
    ) -> List[Contradiction]:
        """Check if confidence is supported by evidence."""
        contradictions = []

        # High confidence with no evidence
        if confidence > 0.8 and evidence_count == 0:
            contradictions.append(
                Contradiction(
                    category="evidence_gap",
                    severity="warning",
                    description=(
                        f"High confidence ({confidence:.0%}) claimed "
                        f"with no supporting evidence"
                    ),
                    field_a="confidence",
                    field_b="evidence_count",
                    recommendation="Confidence should be proportional to evidence",
                )
            )

        # Very wide confidence interval with stated point estimate
        if confidence_interval:
            width = confidence_interval[1] - confidence_interval[0]
            if width > 0.8:
                contradictions.append(
                    Contradiction(
                        category="confidence_inflation",
                        severity="info",
                        description=(
                            f"Confidence interval [{confidence_interval[0]:.0%}, {confidence_interval[1]:.0%}] "
                            f"is very wide (could be almost anything)"
                        ),
                        field_a="confidence_interval",
                        field_b="point_estimate",
                        recommendation="Wide intervals indicate low actual confidence",
                    )
                )

        return contradictions

    @staticmethod
    def check_outcome_claims(
        claimed_outcomes: List[str],
        tested_outcomes: List[str],
        verified_outcomes: List[str],
    ) -> List[Contradiction]:
        """Check if claimed outcomes have been verified."""
        contradictions = []

        # Find claims that weren't tested
        untested = set(claimed_outcomes) - set(tested_outcomes)
        if untested:
            contradictions.append(
                Contradiction(
                    category="untested_claims",
                    severity="warning",
                    description=(
                        f"Outcomes claimed but not tested: {', '.join(untested)}"
                    ),
                    field_a="claimed_outcomes",
                    field_b="tested_outcomes",
                    recommendation="Mark untested claims as 'untested' not 'complete'",
                )
            )

        # Find tested but unverified
        unverified = set(tested_outcomes) - set(verified_outcomes)
        if unverified:
            contradictions.append(
                Contradiction(
                    category="unverified_tests",
                    severity="info",
                    description=(
                        f"Outcomes tested but not verified: {', '.join(unverified)}"
                    ),
                    field_a="tested_outcomes",
                    field_b="verified_outcomes",
                    recommendation="Include verification status in capsule",
                )
            )

        return contradictions

    @staticmethod
    def check_legal_label_readiness(
        claims_court_admissible: bool,
        has_signature: bool,
        has_timestamp: bool,
        has_semantic_drift: bool,
        interpretation_separated: bool,
    ) -> List[Contradiction]:
        """Check if legal labels are earned."""
        contradictions = []

        if claims_court_admissible:
            missing = []
            if not has_signature:
                missing.append("signature")
            if not has_timestamp:
                missing.append("verified timestamp")
            if has_semantic_drift:
                missing.append("semantic consistency (drift detected)")
            if not interpretation_separated:
                missing.append("fact/interpretation separation")

            if missing:
                contradictions.append(
                    Contradiction(
                        category="unearned_label",
                        severity="critical",
                        description=(
                            f"Claims 'court_admissible' but missing: {', '.join(missing)}"
                        ),
                        field_a="court_admissible_label",
                        field_b="verification_status",
                        recommendation="Remove court_admissible label until gates pass",
                    )
                )

        return contradictions

    @classmethod
    def analyze_capsule(cls, capsule: Dict[str, Any]) -> List[Contradiction]:
        """Run all contradiction checks on a capsule."""
        all_contradictions = []

        # Get relevant fields (handle various capsule structures)
        payload = capsule.get("payload", {})
        metadata = capsule.get("metadata", {})
        verification = capsule.get("verification", {})

        # Check semantic drift
        messages = payload.get("messages", [])
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        summary = (
            payload.get("plain_language_summary", {}).get("what_happened")
            or payload.get("summary")
            or payload.get("decision")
            or ""
        )

        all_contradictions.extend(cls.check_semantic_drift(last_user_msg, summary))

        # Check quality consistency
        quality = payload.get("quality_assessment", {})
        all_contradictions.extend(
            cls.check_quality_consistency(
                evidence_quality=quality.get("evidence_quality"),
                logical_validity=quality.get("logical_validity"),
                overall_grade=quality.get("grade"),
                has_evidence=bool(payload.get("evidence") or payload.get("tool_calls")),
            )
        )

        # Check confidence-evidence alignment
        confidence_data = payload.get("confidence", {})
        if isinstance(confidence_data, dict):
            conf_value = confidence_data.get("probability_correct", 0.5)
            conf_interval = confidence_data.get("interval")
            if isinstance(conf_interval, list) and len(conf_interval) == 2:
                conf_interval = tuple(conf_interval)
            else:
                conf_interval = None
        else:
            conf_value = float(confidence_data) if confidence_data else 0.5
            conf_interval = None

        evidence_count = len(payload.get("evidence", []))
        tool_count = len(payload.get("tool_calls", []))

        all_contradictions.extend(
            cls.check_confidence_evidence_alignment(
                confidence=conf_value,
                confidence_interval=conf_interval,
                evidence_count=evidence_count,
                tool_verified_count=tool_count,
            )
        )

        # Check legal labels
        all_contradictions.extend(
            cls.check_legal_label_readiness(
                claims_court_admissible=metadata.get("data_richness")
                == "court_admissible",
                has_signature=bool(verification.get("signature")),
                has_timestamp=bool(verification.get("timestamp")),
                has_semantic_drift=any(
                    c.category == "semantic_drift" for c in all_contradictions
                ),
                interpretation_separated=bool(
                    capsule.get("layers", {}).get("interpretation")
                ),
            )
        )

        return all_contradictions


def format_contradictions(contradictions: List[Contradiction]) -> str:
    """Format contradictions for display."""
    if not contradictions:
        return "No contradictions detected."

    lines = ["Contradictions detected:"]
    for c in contradictions:
        severity_icon = {
            "critical": "[!]",
            "warning": "[?]",
            "info": "[i]",
        }.get(c.severity, "[-]")

        lines.append(f"\n{severity_icon} {c.category.upper()}: {c.description}")
        lines.append(f"    Recommendation: {c.recommendation}")

    return "\n".join(lines)
