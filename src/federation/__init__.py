"""
UATP Federation Layer - Global Coordination Infrastructure

This module provides the federation protocol that enables global coordination
across thousands of UATP nodes worldwide for civilization-scale AI attribution.
"""

from .federation_protocol import global_federation, GlobalFederationProtocol

__all__ = ["global_federation", "GlobalFederationProtocol"]
