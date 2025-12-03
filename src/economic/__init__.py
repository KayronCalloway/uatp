"""
Economic module for UATP Capsule Engine.
Implements Fair Creator Dividend Engine (FCDE) for economic attribution and rewards.
"""

from .capsule_economics import CapsuleEconomics, capsule_economics
from .fcde_engine import (
    DEFAULT_QUALITY_SCORES,
    AttributionRecord,
    Contribution,
    ContributionType,
    CreatorAccount,
    DividendPool,
    FCDEEngine,
    RewardMetric,
    fcde_engine,
)

__all__ = [
    "FCDEEngine",
    "ContributionType",
    "RewardMetric",
    "Contribution",
    "AttributionRecord",
    "DividendPool",
    "CreatorAccount",
    "fcde_engine",
    "DEFAULT_QUALITY_SCORES",
    "CapsuleEconomics",
    "capsule_economics",
]
