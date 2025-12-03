"""
Governance module for UATP Capsule Engine.
Provides decentralized governance, voting, and consensus mechanisms.
"""

from .advanced_governance import (
    ConsensusAlgorithm,
    GovernanceAction,
    GovernanceDAOEngine,
    Proposal,
    ProposalStatus,
    ProposalType,
    Stakeholder,
    Vote,
    VoteType,
    VotingMethod,
    governance_engine,
)

__all__ = [
    "GovernanceDAOEngine",
    "ProposalType",
    "ProposalStatus",
    "VoteType",
    "VotingMethod",
    "ConsensusAlgorithm",
    "Stakeholder",
    "Vote",
    "Proposal",
    "GovernanceAction",
    "governance_engine",
]
