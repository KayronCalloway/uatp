"""
Multi-Agent Consensus Protocols for UATP Capsule Engine.
Implements distributed agreement mechanisms between agents.
"""

import asyncio
import hashlib
import json
import logging
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from src.audit.events import audit_emitter
from src.capsule_schema import AnyCapsule
from src.crypto.post_quantum import pq_crypto
from src.engine.cqss import compute_cqss
from src.engine.fork_resolver import fork_resolver, ForkResolutionStrategy

logger = logging.getLogger(__name__)


class ConsensusProtocol(str, Enum):
    """Types of consensus protocols."""

    RAFT = "raft"
    PBFT = "pbft"  # Practical Byzantine Fault Tolerance
    TENDERMINT = "tendermint"
    HOTSTUFF = "hotstuff"
    AVALANCHE = "avalanche"
    PROOF_OF_STAKE = "proof_of_stake"


class NodeRole(str, Enum):
    """Roles of nodes in consensus."""

    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    VALIDATOR = "validator"
    OBSERVER = "observer"


class ConsensusState(str, Enum):
    """States of consensus process."""

    INITIALIZING = "initializing"
    PROPOSING = "proposing"
    VOTING = "voting"
    COMMITTING = "committing"
    FINALIZED = "finalized"
    FAILED = "failed"


class MessageType(str, Enum):
    """Types of consensus messages."""

    PROPOSAL = "proposal"
    VOTE = "vote"
    COMMIT = "commit"
    HEARTBEAT = "heartbeat"
    LEADER_ELECTION = "leader_election"
    VIEW_CHANGE = "view_change"
    ACKNOWLEDGMENT = "acknowledgment"


@dataclass
class ConsensusNode:
    """Represents a node in the consensus network."""

    node_id: str
    role: NodeRole
    stake: float
    reputation: float
    last_seen: datetime
    public_key: str
    network_address: str
    is_active: bool = True
    vote_weight: float = 1.0
    byzantine_behavior_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def calculate_voting_power(self, quality_score: float = 1.0) -> float:
        """Calculate effective voting power with quality weighting.

        Args:
            quality_score: Quality score of the proposals/capsules (0.0-1.0)

        Returns:
            Quality-weighted voting power
        """
        base_power = self.stake * self.vote_weight
        reputation_multiplier = min(self.reputation / 100.0, 2.0)
        byzantine_penalty = max(0.1, 1.0 - self.byzantine_behavior_score)

        # Quality weighting: higher quality contributions get more voting power
        quality_multiplier = 0.5 + (quality_score * 0.5)  # Range: 0.5-1.0

        return (
            base_power * reputation_multiplier * byzantine_penalty * quality_multiplier
        )


@dataclass
class ConsensusMessage:
    """Message in consensus protocol."""

    message_id: str
    message_type: MessageType
    sender_id: str
    recipient_id: Optional[str]
    round_number: int
    view_number: int
    payload: Dict[str, Any]
    timestamp: datetime
    signature: str

    def verify_signature(self, public_key: str) -> bool:
        """Verify message signature."""
        message_data = self._get_signable_content()
        return pq_crypto.dilithium_verify(
            message_data.encode(),
            bytes.fromhex(self.signature),
            bytes.fromhex(public_key),
        )

    def _get_signable_content(self) -> str:
        """Get content for signing."""
        return json.dumps(
            {
                "message_type": self.message_type.value,
                "sender_id": self.sender_id,
                "round_number": self.round_number,
                "view_number": self.view_number,
                "payload": self.payload,
                "timestamp": self.timestamp.isoformat(),
            },
            sort_keys=True,
        )


@dataclass
class ConsensusProposal:
    """Proposal for consensus with quality scoring."""

    proposal_id: str
    proposer_id: str
    capsule_id: str
    proposal_data: Dict[str, Any]
    round_number: int
    view_number: int
    timestamp: datetime
    state: ConsensusState
    votes: Dict[str, bool] = field(default_factory=dict)
    signatures: Dict[str, str] = field(default_factory=dict)
    quality_score: float = 0.0  # CQSS quality score
    quality_verified: bool = False
    quality_metadata: Dict[str, Any] = field(default_factory=dict)

    def get_vote_count(self) -> Tuple[int, int]:
        """Get (yes_votes, no_votes) count."""
        yes_votes = sum(1 for v in self.votes.values() if v)
        no_votes = sum(1 for v in self.votes.values() if not v)
        return yes_votes, no_votes

    def get_quality_weighted_vote_count(
        self, nodes: Dict[str, "ConsensusNode"]
    ) -> Tuple[float, float]:
        """Get quality-weighted vote count.

        Args:
            nodes: Dictionary of consensus nodes

        Returns:
            Tuple of (weighted_yes_votes, weighted_no_votes)
        """
        weighted_yes = 0.0
        weighted_no = 0.0

        for voter_id, vote in self.votes.items():
            if voter_id in nodes:
                node = nodes[voter_id]
                weight = node.calculate_voting_power(self.quality_score)

                if vote:
                    weighted_yes += weight
                else:
                    weighted_no += weight

        return weighted_yes, weighted_no


class RaftConsensus:
    """Raft consensus protocol implementation."""

    def __init__(self, node_id: str, nodes: List[ConsensusNode]):
        self.node_id = node_id
        self.nodes = {node.node_id: node for node in nodes}
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.role = NodeRole.FOLLOWER
        self.leader_id: Optional[str] = None
        self.log: List[Dict[str, Any]] = []
        self.commit_index = 0
        self.last_applied = 0
        self.last_heartbeat = datetime.now(timezone.utc)
        self.election_timeout = random.uniform(5.0, 10.0)  # seconds
        self.heartbeat_interval = 2.0  # seconds

    async def start_consensus(self):
        """Start the consensus process."""
        asyncio.create_task(self._election_timer())
        asyncio.create_task(self._heartbeat_sender())

    async def propose_capsule(self, capsule: AnyCapsule) -> bool:
        """Propose a capsule for consensus."""
        if self.role != NodeRole.LEADER:
            logger.warning(f"Node {self.node_id} is not leader, cannot propose")
            return False

        proposal_data = {
            "capsule_id": capsule.capsule_id,
            "operation": "add_capsule",
            "data": self._serialize_capsule(capsule),
        }

        log_entry = {
            "term": self.current_term,
            "index": len(self.log),
            "data": proposal_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.log.append(log_entry)

        # Send append entries to followers
        success_count = await self._send_append_entries()

        # Check if majority accepted
        majority_threshold = len(self.nodes) // 2 + 1
        if success_count >= majority_threshold:
            self.commit_index = len(self.log) - 1
            logger.info(f"Capsule {capsule.capsule_id} committed via Raft consensus")
            return True

        return False

    async def _election_timer(self):
        """Handle election timeout."""
        while True:
            await asyncio.sleep(self.election_timeout)

            if self.role != NodeRole.LEADER:
                time_since_heartbeat = (
                    datetime.now(timezone.utc) - self.last_heartbeat
                ).total_seconds()

                if time_since_heartbeat > self.election_timeout:
                    await self._start_election()

    async def _start_election(self):
        """Start leader election."""
        self.current_term += 1
        self.role = NodeRole.CANDIDATE
        self.voted_for = self.node_id
        self.last_heartbeat = datetime.now(timezone.utc)

        logger.info(
            f"Node {self.node_id} starting election for term {self.current_term}"
        )

        # Request votes from other nodes
        votes_received = 1  # Vote for self

        for node_id in self.nodes:
            if node_id != self.node_id:
                # Simulate vote request
                vote_granted = await self._request_vote(node_id)
                if vote_granted:
                    votes_received += 1

        majority_threshold = len(self.nodes) // 2 + 1

        if votes_received >= majority_threshold:
            self.role = NodeRole.LEADER
            self.leader_id = self.node_id
            logger.info(
                f"Node {self.node_id} became leader for term {self.current_term}"
            )
            await self._send_heartbeats()
        else:
            self.role = NodeRole.FOLLOWER

    async def _request_vote(self, node_id: str) -> bool:
        """Request vote from a node."""
        # Simplified vote request - in production would use network communication
        node = self.nodes.get(node_id)
        if not node or not node.is_active:
            return False

        # Simulate network delay and decision
        await asyncio.sleep(0.1)
        return random.random() > 0.3  # 70% chance of granting vote

    async def _heartbeat_sender(self):
        """Send periodic heartbeats when leader."""
        while True:
            if self.role == NodeRole.LEADER:
                await self._send_heartbeats()

            await asyncio.sleep(self.heartbeat_interval)

    async def _send_heartbeats(self):
        """Send heartbeat to all followers."""
        for node_id in self.nodes:
            if node_id != self.node_id:
                await self._send_heartbeat(node_id)

    async def _send_heartbeat(self, node_id: str):
        """Send heartbeat to specific node."""
        # Simplified heartbeat - in production would use network communication
        node = self.nodes.get(node_id)
        if node and node.is_active:
            node.last_seen = datetime.now(timezone.utc)

    async def _send_append_entries(self) -> int:
        """Send append entries to followers."""
        success_count = 1  # Leader counts as success

        for node_id in self.nodes:
            if node_id != self.node_id:
                success = await self._send_append_entry(node_id)
                if success:
                    success_count += 1

        return success_count

    async def _send_append_entry(self, node_id: str) -> bool:
        """Send append entry to specific follower."""
        node = self.nodes.get(node_id)
        if not node or not node.is_active:
            return False

        # Simulate network communication and response
        await asyncio.sleep(0.1)
        return random.random() > 0.2  # 80% success rate

    def _serialize_capsule(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Serialize capsule for consensus."""
        return {
            "capsule_id": capsule.capsule_id,
            "capsule_type": capsule.capsule_type.value,
            "version": capsule.version,
            "timestamp": capsule.timestamp.isoformat(),
            "status": capsule.status.value,
        }


class PBFTConsensus:
    """Practical Byzantine Fault Tolerance consensus."""

    def __init__(self, node_id: str, nodes: List[ConsensusNode]):
        self.node_id = node_id
        self.nodes = {node.node_id: node for node in nodes}
        self.view_number = 0
        self.sequence_number = 0
        self.phase = "prepare"
        self.proposals: Dict[str, ConsensusProposal] = {}
        self.message_log: Dict[str, List[ConsensusMessage]] = defaultdict(list)
        self.f = (len(nodes) - 1) // 3  # Max Byzantine nodes

    async def propose_capsule(self, capsule: AnyCapsule) -> bool:
        """Propose capsule via PBFT consensus."""
        if not self._is_primary():
            logger.warning(f"Node {self.node_id} is not primary, cannot propose")
            return False

        proposal_id = self._generate_proposal_id()
        proposal = ConsensusProposal(
            proposal_id=proposal_id,
            proposer_id=self.node_id,
            capsule_id=capsule.capsule_id,
            proposal_data=self._serialize_capsule(capsule),
            round_number=self.sequence_number,
            view_number=self.view_number,
            timestamp=datetime.now(timezone.utc),
            state=ConsensusState.PROPOSING,
        )

        self.proposals[proposal_id] = proposal

        # Phase 1: Pre-prepare
        await self._send_pre_prepare(proposal)

        # Phase 2: Prepare
        prepare_success = await self._collect_prepare_votes(proposal_id)

        if prepare_success:
            # Phase 3: Commit
            commit_success = await self._collect_commit_votes(proposal_id)

            if commit_success:
                proposal.state = ConsensusState.FINALIZED
                logger.info(
                    f"Capsule {capsule.capsule_id} finalized via PBFT consensus"
                )
                return True

        proposal.state = ConsensusState.FAILED
        return False

    async def _send_pre_prepare(self, proposal: ConsensusProposal):
        """Send pre-prepare message."""
        message = self._create_message(
            MessageType.PROPOSAL,
            {"proposal": proposal.proposal_data, "proposal_id": proposal.proposal_id},
        )

        await self._broadcast_message(message)

    async def _collect_prepare_votes(self, proposal_id: str) -> bool:
        """Collect prepare phase votes."""
        # Simulate collecting votes from 2f+1 nodes
        required_votes = 2 * self.f + 1
        votes_collected = 0

        for _ in range(len(self.nodes)):
            # Simulate vote collection
            await asyncio.sleep(0.05)
            if random.random() > 0.1:  # 90% success rate
                votes_collected += 1

                if votes_collected >= required_votes:
                    return True

        return votes_collected >= required_votes

    async def _collect_commit_votes(self, proposal_id: str) -> bool:
        """Collect commit phase votes."""
        required_votes = 2 * self.f + 1
        votes_collected = 0

        for _ in range(len(self.nodes)):
            await asyncio.sleep(0.05)
            if random.random() > 0.1:  # 90% success rate
                votes_collected += 1

                if votes_collected >= required_votes:
                    return True

        return votes_collected >= required_votes

    def _is_primary(self) -> bool:
        """Check if this node is the primary for current view."""
        # Simple primary selection: first node in sorted order
        sorted_nodes = sorted(self.nodes.keys())
        primary_index = self.view_number % len(sorted_nodes)
        return sorted_nodes[primary_index] == self.node_id

    def _create_message(
        self, msg_type: MessageType, payload: Dict[str, Any]
    ) -> ConsensusMessage:
        """Create a consensus message."""
        message_id = self._generate_message_id()
        message = ConsensusMessage(
            message_id=message_id,
            message_type=msg_type,
            sender_id=self.node_id,
            recipient_id=None,
            round_number=self.sequence_number,
            view_number=self.view_number,
            payload=payload,
            timestamp=datetime.now(timezone.utc),
            signature="",  # Would sign in production
        )

        return message

    async def _broadcast_message(self, message: ConsensusMessage):
        """Broadcast message to all nodes."""
        for node_id in self.nodes:
            if node_id != self.node_id:
                await self._send_message(node_id, message)

    async def _send_message(self, node_id: str, message: ConsensusMessage):
        """Send message to specific node."""
        # Simulate network communication
        await asyncio.sleep(0.01)
        self.message_log[node_id].append(message)

    def _serialize_capsule(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Serialize capsule for consensus."""
        return {
            "capsule_id": capsule.capsule_id,
            "capsule_type": capsule.capsule_type.value,
            "version": capsule.version,
            "timestamp": capsule.timestamp.isoformat(),
            "status": capsule.status.value,
        }

    def _generate_proposal_id(self) -> str:
        """Generate unique proposal ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"{self.node_id}:{self.sequence_number}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _generate_message_id(self) -> str:
        """Generate unique message ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"{self.node_id}:{timestamp}:{random.random()}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]


class ProofOfStakeConsensus:
    """Proof of Stake consensus mechanism."""

    def __init__(self, node_id: str, nodes: List[ConsensusNode]):
        self.node_id = node_id
        self.nodes = {node.node_id: node for node in nodes}
        self.current_epoch = 0
        self.slot_duration = 12  # seconds
        self.slots_per_epoch = 32
        self.validator_set: List[str] = []
        self.attestations: Dict[str, Set[str]] = defaultdict(set)

    async def initialize_validators(self):
        """Initialize validator set based on stake."""
        # Sort nodes by stake and select validators
        sorted_nodes = sorted(
            self.nodes.values(), key=lambda n: n.calculate_voting_power(), reverse=True
        )

        # Select top nodes as validators
        max_validators = min(len(sorted_nodes), 21)
        self.validator_set = [node.node_id for node in sorted_nodes[:max_validators]]

        logger.info(f"Initialized {len(self.validator_set)} validators")

    async def propose_block(self, capsules: List[AnyCapsule]) -> bool:
        """Propose a block of capsules."""
        if not self._is_validator():
            return False

        current_slot = self._get_current_slot()
        proposer = self._get_slot_proposer(current_slot)

        if proposer != self.node_id:
            return False

        block_data = {
            "epoch": self.current_epoch,
            "slot": current_slot,
            "proposer": self.node_id,
            "capsules": [self._serialize_capsule(c) for c in capsules],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Collect attestations
        attestation_count = await self._collect_attestations(block_data)

        # Need majority of validators to attest
        required_attestations = len(self.validator_set) * 2 // 3 + 1

        if attestation_count >= required_attestations:
            logger.info(f"Block finalized with {attestation_count} attestations")
            return True

        return False

    async def _collect_attestations(self, block_data: Dict[str, Any]) -> int:
        """Collect attestations for a block."""
        block_hash = hashlib.sha256(
            json.dumps(block_data, sort_keys=True).encode()
        ).hexdigest()
        attestation_count = 0

        for validator_id in self.validator_set:
            if validator_id != self.node_id:
                # Simulate attestation collection
                await asyncio.sleep(0.1)

                validator = self.nodes.get(validator_id)
                if validator and validator.is_active:
                    # Probability based on validator reputation
                    attest_prob = min(0.95, validator.reputation / 100.0)

                    if random.random() < attest_prob:
                        self.attestations[block_hash].add(validator_id)
                        attestation_count += 1

        return attestation_count

    def _is_validator(self) -> bool:
        """Check if this node is a validator."""
        return self.node_id in self.validator_set

    def _get_current_slot(self) -> int:
        """Get current slot number."""
        # Simplified slot calculation
        return int(time.time()) // self.slot_duration % self.slots_per_epoch

    def _get_slot_proposer(self, slot: int) -> str:
        """Get proposer for a given slot."""
        if not self.validator_set:
            return ""

        # Simple round-robin selection
        proposer_index = slot % len(self.validator_set)
        return self.validator_set[proposer_index]

    def _serialize_capsule(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Serialize capsule for consensus."""
        return {
            "capsule_id": capsule.capsule_id,
            "capsule_type": capsule.capsule_type.value,
            "version": capsule.version,
            "timestamp": capsule.timestamp.isoformat(),
            "status": capsule.status.value,
        }


class MultiAgentConsensusEngine:
    """Main engine coordinating multiple consensus protocols."""

    def __init__(self):
        self.nodes: Dict[str, ConsensusNode] = {}
        self.active_protocols: Dict[ConsensusProtocol, Any] = {}
        self.consensus_history: List[Dict[str, Any]] = []
        self.default_protocol = ConsensusProtocol.RAFT
        self.network_partition_detection = True

    def register_node(self, node: ConsensusNode):
        """Register a consensus node."""
        self.nodes[node.node_id] = node
        logger.info(f"Registered consensus node: {node.node_id}")

        # Emit audit event
        audit_emitter.emit_capsule_created(
            capsule_id=f"consensus_node_{node.node_id}",
            agent_id=node.node_id,
            capsule_type="consensus_registration",
        )

    async def initialize_protocol(
        self, protocol: ConsensusProtocol, primary_node_id: str
    ):
        """Initialize a specific consensus protocol."""
        active_nodes = [node for node in self.nodes.values() if node.is_active]

        if protocol == ConsensusProtocol.RAFT:
            self.active_protocols[protocol] = RaftConsensus(
                primary_node_id, active_nodes
            )
            await self.active_protocols[protocol].start_consensus()
        elif protocol == ConsensusProtocol.PBFT:
            self.active_protocols[protocol] = PBFTConsensus(
                primary_node_id, active_nodes
            )
        elif protocol == ConsensusProtocol.PROOF_OF_STAKE:
            self.active_protocols[protocol] = ProofOfStakeConsensus(
                primary_node_id, active_nodes
            )
            await self.active_protocols[protocol].initialize_validators()

        logger.info(f"Initialized {protocol.value} consensus protocol")

    async def achieve_consensus(
        self,
        capsules: List[AnyCapsule],
        protocol: Optional[ConsensusProtocol] = None,
        enable_fork_resolution: bool = True,
    ) -> bool:
        """Achieve consensus on capsules using specified protocol with fork resolution.

        Args:
            capsules: Capsules to achieve consensus on
            protocol: Consensus protocol to use
            enable_fork_resolution: Whether to enable automated fork resolution

        Returns:
            True if consensus achieved
        """

        if not protocol:
            protocol = self.default_protocol

        if protocol not in self.active_protocols:
            logger.error(f"Protocol {protocol.value} not initialized")
            return False

        consensus_engine = self.active_protocols[protocol]

        start_time = datetime.now(timezone.utc)

        try:
            # Check for existing forks that need resolution before proceeding
            if enable_fork_resolution:
                await self._resolve_existing_forks_before_consensus(capsules)

            # Compute quality metrics for quality-weighted consensus
            quality_scores = {}
            if enable_fork_resolution:
                for capsule in capsules:
                    try:

                        async def verify_capsule(c):
                            return True, "verified"

                        quality_result = await compute_cqss([capsule], verify_capsule)
                        quality_scores[capsule.capsule_id] = (
                            quality_result.get_overall_score() or 0.5
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to compute quality for capsule {capsule.capsule_id}: {e}"
                        )
                        quality_scores[capsule.capsule_id] = 0.5

            if protocol == ConsensusProtocol.PROOF_OF_STAKE:
                # PoS handles multiple capsules as a block with quality weighting
                success = await self._quality_weighted_block_consensus(
                    consensus_engine, capsules, quality_scores
                )
            else:
                # Other protocols handle individual capsules with quality weighting
                success = True
                for capsule in capsules:
                    quality_score = quality_scores.get(capsule.capsule_id, 0.5)
                    if not await self._quality_weighted_capsule_consensus(
                        consensus_engine, capsule, quality_score
                    ):
                        success = False
                        break

            # Record consensus result
            consensus_record = {
                "protocol": protocol.value,
                "capsules": [c.capsule_id for c in capsules],
                "success": success,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "duration": (datetime.now(timezone.utc) - start_time).total_seconds(),
                "participating_nodes": len(
                    [n for n in self.nodes.values() if n.is_active]
                ),
            }

            self.consensus_history.append(consensus_record)

            # Emit audit event
            audit_emitter.emit_capsule_created(
                capsule_id=f"consensus_{protocol.value}_{int(time.time())}",
                agent_id="consensus_engine",
                capsule_type="consensus_completion",
            )

            if success:
                logger.info(
                    f"Consensus achieved for {len(capsules)} capsules via {protocol.value}"
                )
            else:
                logger.warning(f"Consensus failed for capsules via {protocol.value}")

            return success

        except Exception as e:
            logger.error(f"Consensus error: {e}")
            return False

    async def _resolve_existing_forks_before_consensus(
        self, capsules: List[AnyCapsule]
    ):
        """Resolve any existing forks before attempting consensus.

        Args:
            capsules: Capsules being considered for consensus
        """
        try:
            # Check if any of the capsules are involved in active forks
            capsule_ids = {capsule.capsule_id for capsule in capsules}

            # Get active forks that might conflict with these capsules
            active_forks = list(fork_resolver.active_forks.keys())

            for fork_id in active_forks:
                fork_candidates = fork_resolver.active_forks.get(fork_id, [])

                # Check if any fork candidates conflict with our capsules
                for candidate in fork_candidates:
                    candidate_capsule_ids = {c.capsule_id for c in candidate.capsules}

                    if capsule_ids.intersection(candidate_capsule_ids):
                        # There's a conflict - resolve the fork first
                        logger.info(
                            f"Resolving fork {fork_id} before consensus due to capsule conflict"
                        )

                        # Use quality-based resolution strategy
                        resolution_result = await fork_resolver.resolve_fork(
                            fork_id, ForkResolutionStrategy.HYBRID_MULTI_CRITERIA
                        )

                        if resolution_result:
                            logger.info(
                                f"Fork {fork_id} resolved successfully before consensus"
                            )
                        else:
                            logger.warning(
                                f"Failed to resolve fork {fork_id} before consensus"
                            )

        except Exception as e:
            logger.error(f"Error resolving forks before consensus: {e}")

    async def _quality_weighted_block_consensus(
        self,
        consensus_engine,
        capsules: List[AnyCapsule],
        quality_scores: Dict[str, float],
    ) -> bool:
        """Achieve consensus on a block with quality weighting.

        Args:
            consensus_engine: Consensus engine instance
            capsules: Capsules in the block
            quality_scores: Quality scores for each capsule

        Returns:
            True if consensus achieved
        """
        try:
            # Calculate average quality for the block
            if quality_scores:
                block_quality = sum(quality_scores.values()) / len(quality_scores)
            else:
                block_quality = 0.5

            # Apply quality weighting to validator selection
            if hasattr(consensus_engine, "validator_set"):
                # Update validator voting power based on block quality
                for validator_id in consensus_engine.validator_set:
                    if validator_id in self.nodes:
                        node = self.nodes[validator_id]
                        # Temporarily boost voting power for high-quality blocks
                        original_weight = node.vote_weight
                        node.vote_weight *= 0.5 + block_quality * 0.5

                        # Store original weight for restoration
                        node.metadata[
                            f"original_weight_{id(capsules)}"
                        ] = original_weight

            # Attempt consensus
            success = await consensus_engine.propose_block(capsules)

            # Restore original voting weights
            if hasattr(consensus_engine, "validator_set"):
                for validator_id in consensus_engine.validator_set:
                    if validator_id in self.nodes:
                        node = self.nodes[validator_id]
                        original_key = f"original_weight_{id(capsules)}"
                        if original_key in node.metadata:
                            node.vote_weight = node.metadata.pop(original_key)

            return success

        except Exception as e:
            logger.error(f"Quality-weighted block consensus failed: {e}")
            return False

    async def _quality_weighted_capsule_consensus(
        self, consensus_engine, capsule: AnyCapsule, quality_score: float
    ) -> bool:
        """Achieve consensus on a single capsule with quality weighting.

        Args:
            consensus_engine: Consensus engine instance
            capsule: Capsule to achieve consensus on
            quality_score: Quality score for the capsule

        Returns:
            True if consensus achieved
        """
        try:
            # For individual capsules, we can adjust the consensus threshold based on quality
            original_threshold = getattr(consensus_engine, "consensus_threshold", 0.5)

            # Higher quality capsules need lower consensus threshold
            # Lower quality capsules need higher consensus threshold
            adjusted_threshold = original_threshold * (1.5 - quality_score)
            adjusted_threshold = max(
                0.33, min(0.9, adjusted_threshold)
            )  # Clamp between 33% and 90%

            # Temporarily adjust threshold
            if hasattr(consensus_engine, "consensus_threshold"):
                consensus_engine.consensus_threshold = adjusted_threshold

            # Attempt consensus
            success = await consensus_engine.propose_capsule(capsule)

            # Restore original threshold
            if hasattr(consensus_engine, "consensus_threshold"):
                consensus_engine.consensus_threshold = original_threshold

            # Log quality-based consensus adjustment
            if success:
                logger.debug(
                    f"Capsule {capsule.capsule_id} achieved consensus with quality score {quality_score:.3f} (threshold: {adjusted_threshold:.3f})"
                )

            return success

        except Exception as e:
            logger.error(f"Quality-weighted capsule consensus failed: {e}")
            return False

    def get_consensus_statistics(self) -> Dict[str, Any]:
        """Get consensus performance statistics."""
        if not self.consensus_history:
            return {"total_consensus_attempts": 0}

        successful_consensus = [r for r in self.consensus_history if r["success"]]

        avg_duration = sum(r["duration"] for r in self.consensus_history) / len(
            self.consensus_history
        )
        success_rate = len(successful_consensus) / len(self.consensus_history) * 100

        protocol_stats = defaultdict(lambda: {"attempts": 0, "successes": 0})
        for record in self.consensus_history:
            protocol = record["protocol"]
            protocol_stats[protocol]["attempts"] += 1
            if record["success"]:
                protocol_stats[protocol]["successes"] += 1

        return {
            "total_consensus_attempts": len(self.consensus_history),
            "successful_consensus": len(successful_consensus),
            "success_rate": success_rate,
            "average_duration": avg_duration,
            "active_nodes": len([n for n in self.nodes.values() if n.is_active]),
            "total_nodes": len(self.nodes),
            "protocol_statistics": dict(protocol_stats),
            "active_protocols": list(self.active_protocols.keys()),
        }

    def detect_byzantine_behavior(self, node_id: str) -> float:
        """Detect and score Byzantine behavior with enhanced monitoring."""
        if node_id not in self.nodes:
            return 0.0

        node = self.nodes[node_id]

        # Enhanced Byzantine detection heuristics
        byzantine_score = 0.0

        # Check response times (delayed responses might indicate issues)
        time_since_seen = (datetime.now(timezone.utc) - node.last_seen).total_seconds()
        if time_since_seen > 300:  # 5 minutes
            byzantine_score += 0.2
        elif time_since_seen > 600:  # 10 minutes
            byzantine_score += 0.4

        # Check voting patterns for inconsistencies
        if node.reputation < 50:
            byzantine_score += 0.3

        # Check for conflicting votes (voting differently on same proposals)
        conflicting_votes = self._detect_conflicting_votes(node_id)
        byzantine_score += min(0.4, conflicting_votes * 0.1)

        # Check for rapid stake changes (potential manipulation)
        stake_volatility = self._calculate_stake_volatility(node_id)
        byzantine_score += min(0.3, stake_volatility)

        # Check for coordinated behavior with other suspicious nodes
        coordination_score = self._detect_coordinated_byzantine_behavior(node_id)
        byzantine_score += min(0.4, coordination_score)

        # Update node's Byzantine score
        node.byzantine_behavior_score = min(1.0, byzantine_score)

        # Implement penalties for Byzantine behavior
        if byzantine_score > 0.7:
            self._apply_byzantine_penalties(node_id, byzantine_score)
            logger.critical(
                f"Severe Byzantine behavior detected for node {node_id} (score: {byzantine_score:.2f})"
            )
        elif byzantine_score > 0.5:
            logger.warning(
                f"Node {node_id} showing Byzantine behavior (score: {byzantine_score:.2f})"
            )

        return byzantine_score

    def _detect_conflicting_votes(self, node_id: str) -> int:
        """Detect conflicting votes from a node."""
        # In a real implementation, this would track voting history
        # For now, simulate based on node behavior patterns
        conflicting_count = 0

        # Check if node has a history of changing votes or contradictory positions
        if hasattr(self.nodes[node_id], "vote_history"):
            vote_history = self.nodes[node_id].vote_history
            # Look for patterns where node votes differently on similar proposals
            # This is a simplified heuristic
            if len(vote_history) > 10:
                recent_votes = vote_history[-10:]
                consistency_score = len(set(v.get("position") for v in recent_votes))
                if consistency_score > 7:  # Too much variation in voting positions
                    conflicting_count = consistency_score - 5

        return conflicting_count

    def _calculate_stake_volatility(self, node_id: str) -> float:
        """Calculate stake volatility as indicator of manipulation."""
        if node_id not in self.nodes:
            return 0.0

        node = self.nodes[node_id]

        # Check for rapid stake changes in short time periods
        if hasattr(node, "stake_history"):
            stake_history = node.stake_history
            if len(stake_history) > 5:
                recent_changes = stake_history[-5:]
                max_change = max(
                    abs(recent_changes[i] - recent_changes[i - 1])
                    for i in range(1, len(recent_changes))
                )
                # Normalize by current stake
                if node.stake > 0:
                    volatility = max_change / node.stake
                    return min(1.0, volatility)

        return 0.0

    def _detect_coordinated_byzantine_behavior(self, node_id: str) -> float:
        """Detect coordinated Byzantine behavior among multiple nodes."""
        coordination_score = 0.0

        target_node = self.nodes[node_id]

        # Look for nodes with similar Byzantine patterns
        similar_nodes = 0
        for other_id, other_node in self.nodes.items():
            if other_id == node_id:
                continue

            # Check for similar registration times
            time_diff = abs(
                (target_node.last_seen - other_node.last_seen).total_seconds()
            )
            if time_diff < 300:  # Active within 5 minutes of each other
                similar_nodes += 1

            # Check for similar Byzantine scores
            if (
                abs(
                    target_node.byzantine_behavior_score
                    - other_node.byzantine_behavior_score
                )
                < 0.1
            ):
                coordination_score += 0.1

        # Penalty for having too many similar nodes (potential bot network)
        if similar_nodes > 5:
            coordination_score += 0.3

        return min(1.0, coordination_score)

    def _apply_byzantine_penalties(self, node_id: str, byzantine_score: float):
        """Apply penalties for Byzantine behavior with enhanced security measures."""
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]

        # CRITICAL SECURITY: Enhanced penalties based on severity
        if byzantine_score > 0.9:
            # CRITICAL penalty: slash 75% of stake and permanent ban
            node.stake *= 0.25
            node.vote_weight = 0.0  # Complete voting power removal
            node.is_active = False  # Permanent deactivation
            node.reputation = 0.0
            logger.critical(
                f"CRITICAL Byzantine penalty to {node_id}: 75% stake slashed, permanently banned"
            )

            # Trigger network-wide security alert
            self._trigger_byzantine_security_alert(node_id, byzantine_score)

        elif byzantine_score > 0.8:
            # Severe penalty: slash 50% of stake
            node.stake *= 0.5
            node.vote_weight *= 0.25  # Reduced to 25% voting power
            node.reputation *= 0.5
            logger.critical(
                f"Applied severe Byzantine penalty to {node_id}: 50% stake slashed"
            )

        elif byzantine_score > 0.6:
            # Moderate penalty: slash 25% of stake
            node.stake *= 0.75
            node.vote_weight *= 0.6
            node.reputation *= 0.75
            logger.warning(
                f"Applied moderate Byzantine penalty to {node_id}: 25% stake slashed"
            )

        elif byzantine_score > 0.4:
            # Warning penalty: reduce voting power temporarily
            node.vote_weight *= 0.8
            node.reputation *= 0.9
            logger.warning(
                f"Applied warning penalty to {node_id}: reduced voting power"
            )

        # Additional security measures for high Byzantine scores
        if byzantine_score > 0.7:
            # Temporarily suspend from all validator sets
            if hasattr(self, "active_protocols"):
                for protocol_name, protocol in self.active_protocols.items():
                    if (
                        hasattr(protocol, "validator_set")
                        and node_id in protocol.validator_set
                    ):
                        protocol.validator_set.remove(node_id)
                        logger.warning(
                            f"Suspended {node_id} from {protocol_name} validator set due to Byzantine behavior"
                        )

            # Add to Byzantine watchlist for enhanced monitoring
            self._add_to_byzantine_watchlist(node_id, byzantine_score)

            # Implement quarantine period
            node.metadata["quarantine_until"] = datetime.now(timezone.utc) + timedelta(
                days=7
            )
            node.metadata["byzantine_violations"] = (
                node.metadata.get("byzantine_violations", 0) + 1
            )

            # If repeated violations, escalate to governance review
            if node.metadata.get("byzantine_violations", 0) > 3:
                self._escalate_to_governance_review(node_id, byzantine_score)

    def implement_economic_penalties(
        self, node_id: str, penalty_amount: float, reason: str
    ) -> bool:
        """Implement economic penalties for malicious behavior."""
        if node_id not in self.nodes:
            return False

        node = self.nodes[node_id]

        # Apply economic penalty
        penalty = min(penalty_amount, node.stake * 0.5)  # Cap at 50% of stake
        node.stake = max(0, node.stake - penalty)

        # Record the penalty
        if not hasattr(node, "penalty_history"):
            node.penalty_history = []

        node.penalty_history.append(
            {
                "amount": penalty,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc),
                "remaining_stake": node.stake,
            }
        )

        logger.warning(
            f"Applied economic penalty to {node_id}: {penalty} stake slashed for {reason}"
        )

        # Emit audit event
        audit_emitter.emit_security_event(
            event_type="economic_penalty_applied",
            details={
                "node_id": node_id,
                "penalty_amount": penalty,
                "reason": reason,
                "remaining_stake": node.stake,
            },
        )

        return True

    def _trigger_byzantine_security_alert(self, node_id: str, byzantine_score: float):
        """Trigger network-wide security alert for critical Byzantine behavior."""

        alert_data = {
            "alert_type": "critical_byzantine_behavior",
            "node_id": node_id,
            "byzantine_score": byzantine_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recommended_actions": [
                "review_node_connections",
                "validate_recent_proposals",
                "audit_voting_patterns",
                "check_coordinated_behavior",
            ],
        }

        # Emit security alert to audit system
        audit_emitter.emit_security_event(
            event_type="critical_byzantine_alert", details=alert_data
        )

        # Notify other nodes to increase vigilance
        for other_node_id, other_node in self.nodes.items():
            if other_node_id != node_id and other_node.is_active:
                other_node.metadata["byzantine_alert_active"] = True
                other_node.metadata["increased_monitoring_until"] = (
                    datetime.now(timezone.utc) + timedelta(hours=24)
                ).isoformat()

        logger.critical(
            f"NETWORK-WIDE BYZANTINE ALERT: Node {node_id} marked as critical threat (score: {byzantine_score:.2f})"
        )

    def _add_to_byzantine_watchlist(self, node_id: str, byzantine_score: float):
        """Add node to Byzantine behavior watchlist."""

        if not hasattr(self, "byzantine_watchlist"):
            self.byzantine_watchlist = {}

        self.byzantine_watchlist[node_id] = {
            "added_at": datetime.now(timezone.utc),
            "byzantine_score": byzantine_score,
            "monitoring_level": "high" if byzantine_score > 0.8 else "medium",
            "violation_count": self.nodes[node_id].metadata.get(
                "byzantine_violations", 0
            ),
            "last_violation": datetime.now(timezone.utc).isoformat(),
        }

        logger.warning(
            f"Added {node_id} to Byzantine watchlist (score: {byzantine_score:.2f})"
        )

    def _escalate_to_governance_review(self, node_id: str, byzantine_score: float):
        """Escalate repeated Byzantine behavior to governance system."""

        from src.governance.advanced_governance import governance_engine

        # Create governance proposal to review Byzantine node
        governance_engine.create_proposal(
            title=f"Review Byzantine Node {node_id}",
            description=f"Node {node_id} has demonstrated repeated Byzantine behavior (score: {byzantine_score:.2f}) and requires governance review for potential permanent exclusion.",
            proposal_type="security_review",
            proposer_id="consensus_security_system",
            voting_duration=timedelta(days=3),
            voting_method="supermajority",
            required_threshold=0.75,
            execution_data={
                "action_type": "byzantine_node_review",
                "node_id": node_id,
                "byzantine_score": byzantine_score,
                "violation_history": self.nodes[node_id].metadata.get(
                    "byzantine_violations", 0
                ),
            },
        )

        logger.critical(
            f"ESCALATED TO GOVERNANCE: Byzantine node {node_id} requires community review"
        )

    def implement_enhanced_byzantine_detection(self) -> Dict[str, float]:
        """Implement enhanced Byzantine behavior detection across all nodes."""

        byzantine_scores = {}

        for node_id, node in self.nodes.items():
            if not node.is_active:
                continue

            # Enhanced detection combining multiple signals
            base_score = self.detect_byzantine_behavior(node_id)

            # Additional detection methods
            coordination_score = self._detect_coordinated_byzantine_behavior(node_id)
            temporal_score = self._detect_temporal_manipulation(node_id)
            economic_score = self._detect_economic_manipulation(node_id)

            # Combine scores with weights
            combined_score = (
                base_score * 0.4
                + coordination_score * 0.3
                + temporal_score * 0.2
                + economic_score * 0.1
            )

            byzantine_scores[node_id] = combined_score

            # Apply progressive penalties
            if combined_score > 0.5:
                self._apply_byzantine_penalties(node_id, combined_score)

        # Check system-wide Byzantine tolerance
        active_nodes = sum(1 for node in self.nodes.values() if node.is_active)
        byzantine_nodes = sum(1 for score in byzantine_scores.values() if score > 0.5)

        if active_nodes > 0:
            byzantine_ratio = byzantine_nodes / active_nodes
            if byzantine_ratio > 0.33:  # Exceeds Byzantine fault tolerance
                logger.critical(
                    f"BYZANTINE FAULT TOLERANCE EXCEEDED: {byzantine_ratio:.2%} of nodes showing Byzantine behavior"
                )
                self._trigger_network_emergency_protocol()

        return byzantine_scores

    def _detect_temporal_manipulation(self, node_id: str) -> float:
        """Detect temporal manipulation patterns."""
        if node_id not in self.nodes:
            return 0.0

        node = self.nodes[node_id]
        manipulation_score = 0.0

        # Check for timestamp manipulation in messages
        if hasattr(node, "message_history"):
            timestamps = [msg.get("timestamp") for msg in node.message_history[-10:]]
            if len(timestamps) > 5:
                # Look for impossible timestamp patterns
                for i in range(1, len(timestamps)):
                    if timestamps[i] < timestamps[i - 1]:  # Time going backwards
                        manipulation_score += 0.2

        # Check for delayed responses (potential manipulation)
        if hasattr(node, "response_times"):
            recent_times = node.response_times[-10:]
            if len(recent_times) > 5:
                avg_time = sum(recent_times) / len(recent_times)
                if avg_time > 30:  # Suspiciously slow responses
                    manipulation_score += 0.3

        return min(1.0, manipulation_score)

    def _detect_economic_manipulation(self, node_id: str) -> float:
        """Detect economic manipulation patterns."""
        if node_id not in self.nodes:
            return 0.0

        node = self.nodes[node_id]
        manipulation_score = 0.0

        # Check for artificial stake inflation
        if hasattr(node, "stake_history"):
            stake_history = node.stake_history[-5:]
            if len(stake_history) > 2:
                recent_increase = stake_history[-1] - stake_history[0]
                if recent_increase > node.stake * 2:  # Stake doubled recently
                    manipulation_score += 0.4

        # Check for coordinated economic behavior
        similar_stake_nodes = [
            other_id
            for other_id, other_node in self.nodes.items()
            if other_id != node_id and abs(other_node.stake - node.stake) < 100
        ]
        if len(similar_stake_nodes) > 5:  # Too many nodes with similar stakes
            manipulation_score += 0.3

        return min(1.0, manipulation_score)

    def _trigger_network_emergency_protocol(self):
        """Trigger emergency protocol when Byzantine fault tolerance is exceeded."""

        logger.critical(
            "NETWORK EMERGENCY: Byzantine fault tolerance exceeded - activating emergency protocol"
        )

        # Halt new consensus attempts
        self.consensus_halted = True

        # Freeze suspicious nodes
        for node_id, node in self.nodes.items():
            if node.byzantine_behavior_score > 0.5:
                node.is_active = False
                node.vote_weight = 0.0
                logger.critical(f"EMERGENCY: Frozen Byzantine node {node_id}")

        # Activate enhanced verification for remaining nodes
        for node_id, node in self.nodes.items():
            if node.is_active:
                node.metadata["enhanced_verification"] = True
                node.metadata["emergency_mode"] = True

        # Emit critical security event
        audit_emitter.emit_security_event(
            event_type="network_emergency_protocol",
            details={
                "reason": "byzantine_fault_tolerance_exceeded",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "frozen_nodes": [
                    n.node_id for n in self.nodes.values() if not n.is_active
                ],
                "active_nodes": [n.node_id for n in self.nodes.values() if n.is_active],
            },
        )

    async def handle_network_partition(self):
        """Handle network partition scenarios."""
        if not self.network_partition_detection:
            return

        # Check for network partitions by analyzing node connectivity
        active_nodes = [n for n in self.nodes.values() if n.is_active]

        if len(active_nodes) < len(self.nodes) * 0.5:
            logger.warning("Potential network partition detected")

            # Switch to a more partition-tolerant protocol if available
            if ConsensusProtocol.AVALANCHE in self.active_protocols:
                self.default_protocol = ConsensusProtocol.AVALANCHE
                logger.info("Switched to Avalanche consensus for partition tolerance")


# Global consensus engine instance
consensus_engine = MultiAgentConsensusEngine()
