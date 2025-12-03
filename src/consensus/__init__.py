"""
Consensus module for UATP Capsule Engine.
Provides multi-agent consensus protocols for distributed agreement.
"""

from .multi_agent_consensus import (
    ConsensusMessage,
    ConsensusNode,
    ConsensusProposal,
    ConsensusProtocol,
    ConsensusState,
    MessageType,
    MultiAgentConsensusEngine,
    NodeRole,
    PBFTConsensus,
    ProofOfStakeConsensus,
    RaftConsensus,
    consensus_engine,
)

__all__ = [
    "MultiAgentConsensusEngine",
    "ConsensusProtocol",
    "NodeRole",
    "ConsensusState",
    "MessageType",
    "ConsensusNode",
    "ConsensusMessage",
    "ConsensusProposal",
    "RaftConsensus",
    "PBFTConsensus",
    "ProofOfStakeConsensus",
    "consensus_engine",
]
