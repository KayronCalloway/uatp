"""
Centralized color palette for the UATP Visualizer.
"""

# Standard UATP Capsule Type Colors
CAPSULE_TYPE_COLORS = {
    # UATP 6.0 Capsule Types
    "Refusal": "#e57373",  # Red
    "Introspective": "#64b5f6",  # Blue
    "Joint": "#81c784",  # Green
    "Meta": "#9575cd",  # Deep Purple
    "Influence": "#ff8a65",  # Deep Orange
    "Perspective": "#ba68c8",  # Purple
    "Lifecycle": "#4dd0e1",  # Cyan
    "Embodied": "#ffd54f",  # Amber
    "AncestralKnowledge": "#a1887f",  # Brown
    "Merge": "#ffb74d",  # Orange
    # UATP 7.0 Capsule Types (snake_case for schema compatibility)
    "reasoning_trace": "#64b5f6",  # Blue
    "economic_transaction": "#9ccc65",  # Light Green
    "governance_vote": "#78909c",  # Blue Grey
    "ethics_trigger": "#ef5350",  # Red
    "post_quantum_signature": "#26a69a",  # Teal
    "consent": "#42a5f5",  # Blue
    "remix": "#7e57c2",  # Deep Purple
    "trust_renewal": "#ffa726",  # Orange
    "simulated_malice": "#ef5350",  # Red
    "implicit_consent": "#5c6bc0",  # Indigo
    "temporal_justice": "#4dd0e1",  # Cyan
    "uncertainty": "#ffb74d",  # Orange
    "conflict_resolution": "#9575cd",  # Deep Purple
    "perspective": "#ba68c8",  # Purple
    "feedback_assimilation": "#81c784",  # Green
    "knowledge_expiry": "#8d6e63",  # Brown
    "emotional_load": "#ec407a",  # Pink
    "manipulation_attempt": "#e57373",  # Red
    "compute_footprint": "#a1887f",  # Brown
    "hand_off": "#ff8a65",  # Deep Orange
    "retirement": "#90a4ae",  # Grey
    "audit": "#ffd54f",  # Amber
    "refusal": "#e57373",  # Red
    "cloning_rights": "#66bb6a",  # Green
    "evolution": "#7e57c2",  # Deep Purple
    "dividend_bond": "#9ccc65",  # Light Green
    "citizenship": "#42a5f5",  # Blue
    # Legacy PascalCase for backward compatibility
    "Remix": "#7e57c2",  # Deep Purple
    "TemporalSignature": "#26a69a",  # Teal
    "ValueInception": "#66bb6a",  # Green
    "SimulatedMalice": "#ef5350",  # Red
    "ImplicitConsent": "#5c6bc0",  # Indigo
    "SelfHallucination": "#ec407a",  # Pink
    "Consent": "#42a5f5",  # Blue
    "TrustRenewal": "#ffa726",  # Orange
    "CapsuleExpiration": "#8d6e63",  # Brown
    "Governance": "#78909c",  # Blue Grey
    "Economic": "#9ccc65",  # Light Green
    "Base": "#90a4ae",  # Grey (for test data)
    "DEFAULT": "#90a4ae",  # Grey
}


# CQSS Score Color Scale (e.g., for gauges, text)
def get_cqss_color(score: float, max_score: int = 100) -> str:
    """Returns a color based on the CQSS score."""
    normalized_score = score / max_score
    if normalized_score > 0.7:
        return "#4caf50"  # Green
    elif normalized_score > 0.4:
        return "#ff9800"  # Orange
    else:
        return "#f44336"  # Red
