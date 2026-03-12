"""
Confidence Facet - AI confidence and uncertainty metrics.

Captures:
- Overall confidence score
- Methodology used
- Uncertainty decomposition
- Calibration status
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.schema.base import RunFacet


@dataclass
class UATPConfidenceRunFacet(RunFacet):
    """
    Confidence and uncertainty metrics for a capsule.

    This facet describes HOW CONFIDENT the AI was.
    """

    # Overall confidence
    confidence: float = 0.0  # 0.0 - 1.0
    confidence_methodology: str = "manual"  # manual, weighted_average, critical_path

    # Uncertainty decomposition
    epistemic_uncertainty: Optional[float] = None  # Reducible uncertainty
    aleatoric_uncertainty: Optional[float] = None  # Irreducible uncertainty
    total_uncertainty: Optional[float] = None

    # Confidence interval
    confidence_interval: Optional[Tuple[float, float]] = None  # (lower, upper)

    # Risk assessment
    risk_score: Optional[float] = None  # 0.0 - 1.0

    # Calibration
    is_calibrated: bool = False
    calibration_method: Optional[str] = None
    calibration_adjustment: Optional[float] = None  # How much confidence was adjusted
    pre_calibration_confidence: Optional[float] = None

    # Historical accuracy (if available)
    historical_accuracy: Optional[float] = None
    historical_sample_size: Optional[int] = None

    # Quality assessment
    quality_grade: Optional[str] = None  # A, B, C, D, F
    quality_score: Optional[float] = None  # 0.0 - 1.0

    # Explanation
    confidence_factors: List[str] = field(
        default_factory=list
    )  # What influenced confidence
    uncertainty_sources: List[str] = field(
        default_factory=list
    )  # What adds uncertainty

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if confidence is above threshold."""
        return self.confidence >= threshold

    def is_calibration_significant(self) -> bool:
        """Check if calibration made significant adjustment."""
        if self.calibration_adjustment is not None:
            return abs(self.calibration_adjustment) > 0.05
        return False
