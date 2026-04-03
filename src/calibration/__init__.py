"""
UATP Calibration System
=======================

Measures the gap between model self-assessment and actual outcomes.

Key principle: The learning happens in the comparison, not the reflection.
"""

from .metrics import CalibrationMetrics, calculate_calibration
from .queries import CalibrationQueries

__all__ = ["CalibrationMetrics", "calculate_calibration", "CalibrationQueries"]
