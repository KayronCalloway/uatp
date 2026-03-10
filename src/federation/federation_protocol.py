"""
UATP Global Federation Protocol - Civilization-Scale Coordination Infrastructure

This module implements the distributed federation protocol that enables global
coordination across thousands of UATP nodes worldwide. It establishes the
foundation for planetary-scale AI attribution and economic coordination.

 GLOBAL COORDINATION ARCHITECTURE:
- Continental Nodes (6-12 major regions)
- National Nodes (50+ countries)
- Regional Nodes (1000+ cities)
- Organization Nodes (millions of entities)

 FEDERATION CAPABILITIES:
- Cross-node capsule verification and consensus
- Economic attribution across legal jurisdictions
- Multi-currency support and automatic conversion
- Democratic governance with global participation
- Crisis resilience with distributed authority
- Real-time synchronization of attribution data

This represents the network layer that transforms UATP from a single-system
into civilization-grade infrastructure coordinating human-AI economic cooperation globally.
"""

import asyncio
import logging
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of federation nodes in the global network."""

    CONTINENTAL = "continental"  # 6-12 major continental regions
    NATIONAL = "national"  # 50+ countries/large territories
    REGIONAL = "regional"  # 1000+ cities/regions
    ORGANIZATIONAL = "organizational"  # Millions of organizations
    INDIVIDUAL = "individual"  # Individual participant nodes


class NodeStatus(Enum):
    """Status of federation nodes."""

    ACTIVE = "active"
    SYNCING = "syncing"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    QUARANTINED = "quarantined"  # Temporarily isolated due to issues


class ConsensusAlgorithm(Enum):
    """Consensus algorithms for different decision types."""

    BYZANTINE_FAULT_TOLERANCE = "bft"  # For critical decisions
    PROOF_OF_STAKE = "pos"  # For economic decisions
    DEMOCRATIC_VOTING = "democratic"  # For governance decisions
    REPUTATION_WEIGHTED = "reputation"  # For quality assessments


@dataclass
class FederationNode:
    """A node in the global UATP federation network."""

    node_id: str
    node_type: NodeType
    jurisdiction: str  # ISO country code or region
    operator_organization: str

    # Network connectivity
    endpoint_url: str
    public_key: str
    status: NodeStatus = NodeStatus.SYNCING

    # Capabilities and limits
    max_capsules_per_hour: int = 1000
    supported_currencies: List[str] = field(default_factory=lambda: ["USD"])
    supported_languages: List[str] = field(default_factory=lambda: ["en"])

    # Reputation and stakes
    reputation_score: float = 0.5  # 0.0 to 1.0
    economic_stake: Decimal = field(default_factory=lambda: Decimal("0"))
    governance_weight: float = 0.0

    # Performance metrics
    uptime_percentage: float = 0.0
    average_response_time_ms: float = 0.0
    successful_verifications: int = 0
    failed_verifications: int = 0

    # Federation participation
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    joined_federation: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    peer_connections: Set[str] = field(default_factory=set)

    def calculate_trust_score(self) -> float:
        """Calculate overall trust score for this node."""

        # Base reputation (40% weight)
        reputation_component = self.reputation_score * 0.4

        # Uptime reliability (30% weight)
        uptime_component = (self.uptime_percentage / 100.0) * 0.3

        # Performance component (20% weight)
        max_response_time = 1000.0  # 1 second max desired
        performance_score = max(
            0, 1.0 - (self.average_response_time_ms / max_response_time)
        )
        performance_component = performance_score * 0.2

        # Verification accuracy (10% weight)
        total_verifications = self.successful_verifications + self.failed_verifications
        accuracy_score = (
            (self.successful_verifications / total_verifications)
            if total_verifications > 0
            else 0.5
        )
        accuracy_component = accuracy_score * 0.1

        return (
            reputation_component
            + uptime_component
            + performance_component
            + accuracy_component
        )


@dataclass
class FederationProposal:
    """A proposal for federation-wide changes or decisions."""

    proposal_id: str
    title: str
    description: str
    proposal_type: str  # "protocol_upgrade", "economic_parameter", "node_admission", "governance_change"

    # Proposer information
    proposing_node_id: str
    proposal_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Consensus requirements
    consensus_algorithm: ConsensusAlgorithm = ConsensusAlgorithm.DEMOCRATIC_VOTING
    required_approval_percentage: float = 0.51  # 51% default majority
    minimum_participation: float = 0.40  # 40% participation required

    # Voting period
    voting_start: Optional[datetime] = None
    voting_end: Optional[datetime] = None

    # Vote tallies by node type (weighted differently)
    continental_votes: Dict[str, bool] = field(default_factory=dict)  # High weight
    national_votes: Dict[str, bool] = field(default_factory=dict)  # Medium weight
    regional_votes: Dict[str, bool] = field(default_factory=dict)  # Lower weight
    organizational_votes: Dict[str, bool] = field(default_factory=dict)  # Stake-based

    # Results
    approval_percentage: float = 0.0
    participation_percentage: float = 0.0
    passed: bool = False
    executed: bool = False


@dataclass
class CrossBorderTransaction:
    """A transaction spanning multiple legal jurisdictions."""

    transaction_id: str
    source_jurisdiction: str
    target_jurisdiction: str

    # Economic details
    amount: Decimal
    source_currency: str
    target_currency: str
    exchange_rate: float

    # Attribution details
    attribution_capsule_id: str
    contributor_id: str
    ai_platform: str

    # Legal compliance
    regulatory_clearance: Dict[str, bool] = field(default_factory=dict)
    tax_implications: Dict[str, Decimal] = field(default_factory=dict)

    # Processing status
    initiated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    status: str = "pending"  # "pending", "processing", "completed", "failed"


class GlobalFederationProtocol:
    """
    The global federation protocol that coordinates UATP across civilization.

    This protocol enables thousands of nodes worldwide to participate in
    a unified AI attribution and economic coordination system while respecting
    local sovereignty, legal requirements, and cultural differences.
    """

    def __init__(self, local_node_id: str, local_jurisdiction: str):
        self.local_node_id = local_node_id
        self.local_jurisdiction = local_jurisdiction

        # Federation state
        self.federation_nodes: Dict[str, FederationNode] = {}
        self.federation_proposals: Dict[str, FederationProposal] = {}
        self.cross_border_transactions: Dict[str, CrossBorderTransaction] = {}

        # Consensus and synchronization
        self.consensus_sessions: Dict[str, Dict[str, Any]] = {}
        self.sync_status: Dict[str, datetime] = {}

        # Economic coordination
        self.supported_currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "BTC", "ETH"]
        self.exchange_rates: Dict[str, Dict[str, float]] = {}

        # Crisis and emergency protocols
        self.crisis_mode = False
        self.emergency_coordinators: Set[str] = set()

        logger.info(f" Global Federation Protocol initialized for {local_jurisdiction}")

    async def join_federation(
        self,
        node_type: NodeType,
        operator_organization: str,
        endpoint_url: str,
        public_key: str,
        initial_stake: Decimal = Decimal("1000"),
    ) -> bool:
        """Join the global UATP federation as a new node."""

        # Create local node representation
        local_node = FederationNode(
            node_id=self.local_node_id,
            node_type=node_type,
            jurisdiction=self.local_jurisdiction,
            operator_organization=operator_organization,
            endpoint_url=endpoint_url,
            public_key=public_key,
            economic_stake=initial_stake,
            status=NodeStatus.SYNCING,
        )

        self.federation_nodes[self.local_node_id] = local_node

        # Discover existing federation nodes
        discovered_nodes = await self._discover_federation_nodes()

        for node_id, node_data in discovered_nodes.items():
            if node_id != self.local_node_id:
                node = FederationNode(**node_data)
                self.federation_nodes[node_id] = node

        # Request admission to federation
        admission_success = await self._request_federation_admission(local_node)

        if admission_success:
            local_node.status = NodeStatus.ACTIVE
            await self._start_synchronization()

            logger.info(
                f"[OK] Successfully joined UATP federation as {node_type.value} node"
            )
            return True
        else:
            logger.error("[ERROR] Failed to join UATP federation")
            return False

    async def _discover_federation_nodes(self) -> Dict[str, Dict[str, Any]]:
        """Discover existing nodes in the federation network."""

        # In a real implementation, this would:
        # 1. Query DNS for federation bootstrap nodes
        # 2. Connect to known continental nodes
        # 3. Request peer lists from connected nodes
        # 4. Verify node authenticity with cryptographic signatures

        # For now, simulate discovery
        mock_nodes = {
            "continental_north_america": {
                "node_id": "continental_north_america",
                "node_type": NodeType.CONTINENTAL,
                "jurisdiction": "NAFTA",
                "operator_organization": "North American UATP Consortium",
                "endpoint_url": "https://na.uatp.global",
                "public_key": "pubkey_na_" + secrets.token_hex(32),
                "status": NodeStatus.ACTIVE,
                "uptime_percentage": 99.8,
                "reputation_score": 0.95,
            },
            "continental_europe": {
                "node_id": "continental_europe",
                "node_type": NodeType.CONTINENTAL,
                "jurisdiction": "EU",
                "operator_organization": "European UATP Foundation",
                "endpoint_url": "https://eu.uatp.global",
                "public_key": "pubkey_eu_" + secrets.token_hex(32),
                "status": NodeStatus.ACTIVE,
                "uptime_percentage": 99.5,
                "reputation_score": 0.92,
            },
            "national_usa": {
                "node_id": "national_usa",
                "node_type": NodeType.NATIONAL,
                "jurisdiction": "US",
                "operator_organization": "US Digital Rights Consortium",
                "endpoint_url": "https://us.uatp.global",
                "public_key": "pubkey_us_" + secrets.token_hex(32),
                "status": NodeStatus.ACTIVE,
                "uptime_percentage": 98.9,
                "reputation_score": 0.88,
            },
        }

        logger.info(f" Discovered {len(mock_nodes)} federation nodes")
        return mock_nodes

    async def _request_federation_admission(self, local_node: FederationNode) -> bool:
        """Request admission to the federation from existing nodes."""

        # Create admission proposal
        admission_proposal = FederationProposal(
            proposal_id=f"admission_{self.local_node_id}_{int(time.time())}",
            title=f"Admit {local_node.operator_organization} as {local_node.node_type.value} node",
            description=f"Request to admit new {local_node.node_type.value} node from {local_node.jurisdiction}",
            proposal_type="node_admission",
            proposing_node_id=self.local_node_id,
            consensus_algorithm=ConsensusAlgorithm.REPUTATION_WEIGHTED,
            required_approval_percentage=0.60,  # 60% for node admission
            minimum_participation=0.30,
        )

        # In real implementation, this would submit to existing nodes
        # For now, simulate approval
        admission_proposal.passed = True
        admission_proposal.approval_percentage = 0.75
        admission_proposal.participation_percentage = 0.80

        self.federation_proposals[admission_proposal.proposal_id] = admission_proposal

        logger.info(
            f"[OK] Federation admission approved with {admission_proposal.approval_percentage:.1%} support"
        )
        return True

    async def _start_synchronization(self):
        """Start synchronizing with the federation network."""

        # Begin sync with peer nodes
        for node_id, node in self.federation_nodes.items():
            if node_id != self.local_node_id and node.status == NodeStatus.ACTIVE:
                asyncio.create_task(self._sync_with_node(node_id))
                # Don't await here - let it run in background

        logger.info(" Started federation synchronization")

    async def _sync_with_node(self, peer_node_id: str):
        """Synchronize capsules and state with a specific peer node."""

        if peer_node_id not in self.federation_nodes:
            return

        self.federation_nodes[peer_node_id]

        try:
            # In real implementation, this would:
            # 1. Exchange recent capsule hashes
            # 2. Request missing capsules
            # 3. Verify capsule signatures
            # 4. Update local state
            # 5. Share recent capsules with peer

            # Simulate sync
            await asyncio.sleep(0.1)  # Simulate network delay
            self.sync_status[peer_node_id] = datetime.now(timezone.utc)

            logger.debug(f" Synced with peer node {peer_node_id}")

        except Exception as e:
            logger.error(f"[ERROR] Sync failed with {peer_node_id}: {e}")

    async def create_federation_proposal(
        self,
        title: str,
        description: str,
        proposal_type: str,
        consensus_algorithm: ConsensusAlgorithm = ConsensusAlgorithm.DEMOCRATIC_VOTING,
        required_approval: float = 0.51,
    ) -> FederationProposal:
        """Create a proposal for federation-wide decision."""

        proposal = FederationProposal(
            proposal_id=f"fed_prop_{secrets.token_hex(8)}",
            title=title,
            description=description,
            proposal_type=proposal_type,
            proposing_node_id=self.local_node_id,
            consensus_algorithm=consensus_algorithm,
            required_approval_percentage=required_approval,
        )

        self.federation_proposals[proposal.proposal_id] = proposal

        # Distribute proposal to federation
        await self._distribute_proposal(proposal)

        logger.info(f" Created federation proposal: {title}")
        return proposal

    async def _distribute_proposal(self, proposal: FederationProposal):
        """Distribute proposal to all federation nodes for voting."""

        # In real implementation, this would send the proposal to all active nodes
        # For now, simulate distribution

        for node_id, node in self.federation_nodes.items():
            if node_id != self.local_node_id and node.status == NodeStatus.ACTIVE:
                # Simulate sending proposal
                logger.debug(f" Sent proposal {proposal.proposal_id} to {node_id}")

    async def vote_on_federation_proposal(
        self, proposal_id: str, vote: bool, voting_node_id: Optional[str] = None
    ) -> bool:
        """Cast a vote on a federation proposal."""

        if proposal_id not in self.federation_proposals:
            logger.error(f"Proposal {proposal_id} not found")
            return False

        proposal = self.federation_proposals[proposal_id]
        voter_id = voting_node_id or self.local_node_id

        if voter_id not in self.federation_nodes:
            logger.error(f"Voting node {voter_id} not in federation")
            return False

        voter_node = self.federation_nodes[voter_id]

        # Route vote to appropriate category based on node type
        if voter_node.node_type == NodeType.CONTINENTAL:
            proposal.continental_votes[voter_id] = vote
        elif voter_node.node_type == NodeType.NATIONAL:
            proposal.national_votes[voter_id] = vote
        elif voter_node.node_type == NodeType.REGIONAL:
            proposal.regional_votes[voter_id] = vote
        elif voter_node.node_type == NodeType.ORGANIZATIONAL:
            proposal.organizational_votes[voter_id] = vote

        logger.info(f"️ Vote cast on proposal {proposal_id}: {vote}")
        return True

    def calculate_federation_proposal_result(
        self, proposal_id: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Calculate the result of a federation proposal vote."""

        if proposal_id not in self.federation_proposals:
            return False, {"error": "Proposal not found"}

        proposal = self.federation_proposals[proposal_id]

        # Calculate weighted votes
        total_weight = 0.0
        approval_weight = 0.0

        # Continental nodes have highest weight (40%)
        continental_weight = 0.40
        if proposal.continental_votes:
            for node_id, vote in proposal.continental_votes.items():
                node_weight = continental_weight / len(proposal.continental_votes)
                total_weight += node_weight
                if vote:
                    approval_weight += node_weight

        # National nodes have medium weight (30%)
        national_weight = 0.30
        if proposal.national_votes:
            for node_id, vote in proposal.national_votes.items():
                node_weight = national_weight / len(proposal.national_votes)
                total_weight += node_weight
                if vote:
                    approval_weight += node_weight

        # Regional nodes have lower weight (20%)
        regional_weight = 0.20
        if proposal.regional_votes:
            for node_id, vote in proposal.regional_votes.items():
                node_weight = regional_weight / len(proposal.regional_votes)
                total_weight += node_weight
                if vote:
                    approval_weight += node_weight

        # Organizational nodes have stake-based weight (10%)
        org_weight = 0.10
        if proposal.organizational_votes:
            total_org_stake = sum(
                self.federation_nodes[node_id].economic_stake
                for node_id in proposal.organizational_votes.keys()
                if node_id in self.federation_nodes
            )

            for node_id, vote in proposal.organizational_votes.items():
                if node_id in self.federation_nodes:
                    node_stake = self.federation_nodes[node_id].economic_stake
                    stake_ratio = (
                        float(node_stake / total_org_stake)
                        if total_org_stake > 0
                        else 0
                    )
                    node_weight = org_weight * stake_ratio
                    total_weight += node_weight
                    if vote:
                        approval_weight += node_weight

        # Calculate final percentages
        approval_percentage = (
            (approval_weight / total_weight) if total_weight > 0 else 0
        )
        participation_percentage = total_weight  # Since weights are normalized to 1.0

        # Determine if proposal passes
        passed = (
            approval_percentage >= proposal.required_approval_percentage
            and participation_percentage >= proposal.minimum_participation
        )

        proposal.approval_percentage = approval_percentage
        proposal.participation_percentage = participation_percentage
        proposal.passed = passed

        result = {
            "approval_percentage": approval_percentage,
            "participation_percentage": participation_percentage,
            "required_approval": proposal.required_approval_percentage,
            "minimum_participation": proposal.minimum_participation,
            "passed": passed,
            "vote_breakdown": {
                "continental": len(proposal.continental_votes),
                "national": len(proposal.national_votes),
                "regional": len(proposal.regional_votes),
                "organizational": len(proposal.organizational_votes),
            },
        }

        logger.info(
            f" Federation proposal {proposal_id} result: {'PASSED' if passed else 'FAILED'} ({approval_percentage:.1%} approval)"
        )
        return passed, result

    async def process_cross_border_transaction(
        self,
        contributor_id: str,
        amount: Decimal,
        source_currency: str,
        target_jurisdiction: str,
        target_currency: str,
        attribution_capsule_id: str,
    ) -> CrossBorderTransaction:
        """Process an attribution payment across legal jurisdictions."""

        transaction = CrossBorderTransaction(
            transaction_id=f"xborder_{secrets.token_hex(12)}",
            source_jurisdiction=self.local_jurisdiction,
            target_jurisdiction=target_jurisdiction,
            amount=amount,
            source_currency=source_currency,
            target_currency=target_currency,
            exchange_rate=await self._get_exchange_rate(
                source_currency, target_currency
            ),
            attribution_capsule_id=attribution_capsule_id,
            contributor_id=contributor_id,
            ai_platform="federation_network",
        )

        self.cross_border_transactions[transaction.transaction_id] = transaction

        # Process regulatory clearance
        await self._process_regulatory_clearance(transaction)

        # Execute currency conversion and transfer
        if transaction.status == "cleared":
            await self._execute_cross_border_transfer(transaction)

        logger.info(
            f" Cross-border transaction processed: {transaction.transaction_id}"
        )
        return transaction

    async def _get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get current exchange rate between currencies."""

        # In real implementation, this would query financial APIs
        # For now, simulate reasonable exchange rates
        mock_rates = {
            ("USD", "EUR"): 0.85,
            ("USD", "GBP"): 0.75,
            ("USD", "JPY"): 110.0,
            ("USD", "CNY"): 6.5,
            ("EUR", "USD"): 1.18,
            ("GBP", "USD"): 1.33,
        }

        rate = mock_rates.get((from_currency, to_currency), 1.0)
        logger.debug(f" Exchange rate {from_currency}/{to_currency}: {rate}")
        return rate

    async def _process_regulatory_clearance(self, transaction: CrossBorderTransaction):
        """Process regulatory clearance for cross-border transaction."""

        # Check source jurisdiction compliance
        source_cleared = await self._check_jurisdiction_compliance(
            transaction.source_jurisdiction,
            transaction.amount,
            transaction.source_currency,
        )
        transaction.regulatory_clearance[transaction.source_jurisdiction] = (
            source_cleared
        )

        # Check target jurisdiction compliance
        target_cleared = await self._check_jurisdiction_compliance(
            transaction.target_jurisdiction,
            transaction.amount * Decimal(str(transaction.exchange_rate)),
            transaction.target_currency,
        )
        transaction.regulatory_clearance[transaction.target_jurisdiction] = (
            target_cleared
        )

        # Update status
        if source_cleared and target_cleared:
            transaction.status = "cleared"
        else:
            transaction.status = "compliance_failed"

        logger.info(
            f" Regulatory clearance for {transaction.transaction_id}: {transaction.status}"
        )

    async def _check_jurisdiction_compliance(
        self, jurisdiction: str, amount: Decimal, currency: str
    ) -> bool:
        """Check compliance requirements for a specific jurisdiction."""

        # In real implementation, this would:
        # 1. Check AML/KYC requirements
        # 2. Verify tax reporting obligations
        # 3. Ensure currency transfer limits
        # 4. Validate licensing requirements

        # For now, simulate compliance checks
        await asyncio.sleep(0.1)  # Simulate compliance processing

        # Simple rules for demonstration
        if amount > Decimal("10000"):  # Large transactions need extra approval
            return False
        if jurisdiction in ["sanctions_list"]:  # Sanctioned jurisdictions
            return False

        return True

    async def _execute_cross_border_transfer(self, transaction: CrossBorderTransaction):
        """Execute the actual cross-border monetary transfer."""

        try:
            # Convert currency
            target_amount = transaction.amount * Decimal(str(transaction.exchange_rate))

            # In real implementation, this would:
            # 1. Interface with banking APIs
            # 2. Execute SWIFT transfers
            # 3. Handle crypto transactions
            # 4. Update balances in local systems
            # 5. Generate tax reporting documents

            # Simulate transfer processing
            await asyncio.sleep(0.5)  # Simulate transfer time

            transaction.completed_at = datetime.now(timezone.utc)
            transaction.status = "completed"

            logger.info(
                f"[OK] Cross-border transfer completed: {transaction.amount} {transaction.source_currency} → {target_amount} {transaction.target_currency}"
            )

        except Exception as e:
            transaction.status = "failed"
            logger.error(f"[ERROR] Cross-border transfer failed: {e}")

    def activate_crisis_mode(
        self, crisis_reason: str, coordinator_nodes: Set[str]
    ) -> bool:
        """Activate crisis coordination mode for emergency response."""

        if self.crisis_mode:
            logger.warning("Crisis mode already active")
            return False

        self.crisis_mode = True
        self.emergency_coordinators = coordinator_nodes

        logger.critical(f" CRISIS MODE ACTIVATED: {crisis_reason}")
        logger.critical(f" Emergency coordinators: {list(coordinator_nodes)}")

        return True

    def get_federation_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the federation network."""

        active_nodes = [
            n for n in self.federation_nodes.values() if n.status == NodeStatus.ACTIVE
        ]

        node_type_counts = {}
        for node_type in NodeType:
            count = len([n for n in active_nodes if n.node_type == node_type])
            node_type_counts[node_type.value] = count

        recent_transactions = len(
            [
                t
                for t in self.cross_border_transactions.values()
                if (datetime.now(timezone.utc) - t.initiated_at).days < 7
            ]
        )

        return {
            "federation_health": {
                "total_nodes": len(self.federation_nodes),
                "active_nodes": len(active_nodes),
                "node_types": node_type_counts,
                "crisis_mode": self.crisis_mode,
                "local_node_status": self.federation_nodes.get(
                    self.local_node_id, {}
                ).status
                if self.local_node_id in self.federation_nodes
                else "unknown",
            },
            "economic_coordination": {
                "supported_currencies": len(self.supported_currencies),
                "recent_cross_border_transactions": recent_transactions,
                "total_cross_border_value": float(
                    sum(
                        t.amount
                        for t in self.cross_border_transactions.values()
                        if t.status == "completed"
                    )
                ),
            },
            "governance": {
                "active_proposals": len(
                    [p for p in self.federation_proposals.values() if not p.executed]
                ),
                "total_proposals": len(self.federation_proposals),
                "recent_consensus_decisions": len(
                    [
                        p
                        for p in self.federation_proposals.values()
                        if p.passed
                        and (datetime.now(timezone.utc) - p.proposal_timestamp).days
                        < 30
                    ]
                ),
            },
            "network_performance": {
                "synchronized_nodes": len(self.sync_status),
                "average_node_trust": sum(
                    n.calculate_trust_score() for n in active_nodes
                )
                / len(active_nodes)
                if active_nodes
                else 0,
                "network_uptime": sum(n.uptime_percentage for n in active_nodes)
                / len(active_nodes)
                if active_nodes
                else 0,
            },
        }


# Global federation protocol instance
global_federation = GlobalFederationProtocol(
    local_node_id="local_uatp_node",
    local_jurisdiction="US",  # Default, should be configured based on deployment
)
