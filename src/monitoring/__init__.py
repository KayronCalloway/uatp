"""
UATP Monitoring Module
======================

Provides health monitoring for various system components:
- ML pipeline metrics (embedding coverage, outcome tracking)
- System performance metrics
- Alert generation
"""

from .ml_metrics import MLMetricsMonitor, get_ml_monitor

__all__ = ["MLMetricsMonitor", "get_ml_monitor"]
