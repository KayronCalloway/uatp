"""UATP 7.0 Economic Engine

This module implements the economic layer for UATP 7.0, including:
- Token economics for incentivizing trust verification
- Value attribution and distribution mechanisms
- Economic activity tracking and dividend calculation
- Stake-based reputation systems
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from src.capsules.specialized_capsules import EconomicCapsule
from src.utils.timezone_utils import utc_now

# from engine.specialized_engine import SpecializedCapsuleEngine  # Not needed for demo

logger = logging.getLogger(__name__)


class EconomicTransactionType:
    """Constants for different economic transaction types."""

    VALUE_CREATION = "value_creation"
    VALUE_TRANSFER = "value_transfer"
    VERIFICATION_REWARD = "verification_reward"
    STAKE_DEPOSIT = "stake_deposit"
    STAKE_WITHDRAWAL = "stake_withdrawal"
    DIVIDEND_DISTRIBUTION = "dividend_distribution"
    PENALTY = "penalty"
    BOUNTY_REWARD = "bounty_reward"
    ATTRIBUTION_PAYMENT = "attribution_payment"
    COMMONS_CONTRIBUTION = "commons_contribution"
    EMERGENCE_BONUS = "emergence_bonus"
    TEMPORAL_DECAY_ADJUSTMENT = "temporal_decay_adjustment"


class AttributionConfidence(Enum):
    """Attribution confidence levels for pragmatic attribution."""

    HIGH = "high"  # >0.8 confidence - direct attribution
    MEDIUM = "medium"  # 0.5-0.8 confidence - weighted attribution
    LOW = "low"  # 0.2-0.5 confidence - mostly to commons
    UNKNOWN = "unknown"  # <0.2 confidence - all to commons


@dataclass
class AttributionResult:
    """Result of attribution analysis."""

    source_id: str
    confidence: float
    attribution_basis: str
    semantic_similarity: float
    temporal_relevance: float
    training_data_influence: float
    conversation_influence: float

    @property
    def confidence_level(self) -> AttributionConfidence:
        """Get the confidence level enum based on confidence score."""
        if self.confidence >= 0.8:
            return AttributionConfidence.HIGH
        elif self.confidence >= 0.5:
            return AttributionConfidence.MEDIUM
        elif self.confidence >= 0.2:
            return AttributionConfidence.LOW
        else:
            return AttributionConfidence.UNKNOWN


@dataclass
class PragmaticDistribution:
    """Result of pragmatic attribution distribution."""

    direct_attributions: Dict[str, float]  # contributor_id -> amount
    commons_contribution: float
    emergence_bonus: float
    total_distributed: float
    attribution_confidence: float
    distribution_method: str


class UatpEconomicEngine:
    """Economic engine for UATP 7.0 with pragmatic attribution.

    This engine extends the capabilities of the standard capsule engine
    with economic functions including token economics, incentives,
    pragmatic attribution, and Universal Basic Attribution.

    Key principles:
    - What we can attribute → direct compensation
    - What we can't attribute → commons fund until we can
    - Gradual improvement of attribution capabilities
    - Universal Basic Attribution (15% to global commons)
    """

    def __init__(self, base_engine=None):
        """Initialize the economic engine.

        Args:
            base_engine: The base capsule engine for creating and managing capsules (optional for demo)
        """
        self.base_engine = base_engine
        self.agent_id = base_engine.agent_id if base_engine else "demo-agent"

        # Core economic state
        self.agent_balances: Dict[str, float] = {}  # Agent ID -> balance
        self.agent_stakes: Dict[str, float] = {}  # Agent ID -> staked amount
        self.agent_reputation: Dict[str, float] = {}  # Agent ID -> reputation score

        # Attribution and commons tracking
        self.commons_fund_balance: float = 0.0
        self.attribution_history: List[AttributionResult] = []
        self.conversation_registry: Dict[str, Dict] = {}  # conversation_id -> metadata
        self.training_data_registry: Dict[str, Dict] = {}  # data_id -> metadata

        # Pragmatic attribution settings
        self.uba_percentage: float = 0.15  # Universal Basic Attribution
        self.attribution_confidence_threshold: float = 0.5
        self.temporal_decay_rate: float = 0.95  # 5% decay per year
        self.emergence_detection_threshold: float = (
            1.2  # 20% more value than sum of inputs
        )

        # Load existing economic state if available
        self._load_economic_state()

    def register_conversation(
        self,
        conversation_id: str,
        participant_id: str,
        content_summary: str,
        timestamp: datetime,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Register a conversation for future attribution.

        Args:
            conversation_id: Unique identifier for the conversation
            participant_id: ID of the human participant
            content_summary: Summary of conversation content for semantic analysis
            timestamp: When the conversation occurred
            metadata: Optional additional metadata
        """
        self.conversation_registry[conversation_id] = {
            "participant_id": participant_id,
            "content_summary": content_summary,
            "timestamp": timestamp.isoformat(),
            "semantic_embedding": None,  # To be populated by semantic analysis
            "attribution_count": 0,
            "total_value_attributed": 0.0,
            "metadata": metadata or {},
        }

        logger.info(
            f"Registered conversation {conversation_id} for participant {participant_id}"
        )

    def analyze_semantic_similarity(
        self, ai_output: str, conversation_content: str
    ) -> float:
        """Analyze semantic similarity between AI output and conversation content.

        This is a placeholder for advanced semantic analysis. In production,
        this would use sophisticated NLP models like sentence transformers.

        Args:
            ai_output: The AI-generated content
            conversation_content: The human conversation content

        Returns:
            Similarity score from 0.0 to 1.0
        """
        # Placeholder implementation - in production would use actual semantic analysis
        # Simple word overlap as basic similarity measure
        ai_words = set(ai_output.lower().split())
        conv_words = set(conversation_content.lower().split())

        if not ai_words or not conv_words:
            return 0.0

        overlap = len(ai_words.intersection(conv_words))
        union = len(ai_words.union(conv_words))

        return overlap / union if union > 0 else 0.0

    def calculate_temporal_decay(
        self, timestamp: datetime, current_time: Optional[datetime] = None
    ) -> float:
        """Calculate temporal decay factor for attribution value.

        Args:
            timestamp: When the original contribution was made
            current_time: Current time (defaults to now)

        Returns:
            Decay factor from 0.0 to 1.0
        """
        if current_time is None:
            current_time = utc_now()

        # Calculate years elapsed
        time_diff = current_time - timestamp
        years_elapsed = time_diff.total_seconds() / (365.25 * 24 * 3600)

        # Apply exponential decay
        decay_factor = self.temporal_decay_rate**years_elapsed

        return max(0.0, min(1.0, decay_factor))

    def attribute_ai_output(
        self, ai_output: str, value_amount: float, context: Optional[Dict] = None
    ) -> List[AttributionResult]:
        """Analyze AI output and determine attribution to human contributors.

        This implements the core of the pragmatic attribution system:
        - Attempts to find attributable sources
        - Calculates confidence levels
        - Returns attribution results for distribution

        Args:
            ai_output: The AI-generated content to analyze
            value_amount: Total economic value generated
            context: Optional context about the AI output

        Returns:
            List of attribution results sorted by confidence
        """
        attribution_results = []
        current_time = utc_now()

        # Analyze against conversation registry
        for conv_id, conv_data in self.conversation_registry.items():
            # Calculate semantic similarity
            semantic_sim = self.analyze_semantic_similarity(
                ai_output, conv_data["content_summary"]
            )

            # Calculate temporal relevance
            conv_timestamp = datetime.fromisoformat(conv_data["timestamp"])
            temporal_relevance = self.calculate_temporal_decay(
                conv_timestamp, current_time
            )

            # For now, set training_data_influence and conversation_influence as placeholders
            # In production, these would be calculated by sophisticated analysis
            training_data_influence = semantic_sim * 0.3  # Simplified
            conversation_influence = semantic_sim * 0.7  # Simplified

            # Calculate overall confidence
            confidence = (
                semantic_sim * 0.4
                + temporal_relevance * 0.2
                + training_data_influence * 0.2
                + conversation_influence * 0.2
            )

            # Only include if confidence meets minimum threshold
            if confidence > 0.1:  # Very low threshold for inclusion
                attribution_result = AttributionResult(
                    source_id=conv_data["participant_id"],
                    confidence=confidence,
                    attribution_basis=f"Conversation {conv_id}",
                    semantic_similarity=semantic_sim,
                    temporal_relevance=temporal_relevance,
                    training_data_influence=training_data_influence,
                    conversation_influence=conversation_influence,
                )
                attribution_results.append(attribution_result)

        # Sort by confidence (highest first)
        attribution_results.sort(key=lambda x: x.confidence, reverse=True)

        # Store in history for analytics
        self.attribution_history.extend(attribution_results)

        logger.info(
            f"Attribution analysis found {len(attribution_results)} potential sources"
        )
        return attribution_results

    def calculate_pragmatic_distribution(
        self, attribution_results: List[AttributionResult], total_value: float
    ) -> PragmaticDistribution:
        """Calculate pragmatic distribution based on attribution confidence.

        This is the core of the pragmatic approach:
        - High confidence → direct attribution
        - Low confidence → commons fund
        - Always reserve 15% for Universal Basic Attribution

        Args:
            attribution_results: Results from attribution analysis
            total_value: Total value to distribute

        Returns:
            Distribution plan
        """
        # Reserve UBA percentage for commons immediately
        uba_amount = total_value * self.uba_percentage
        distributable_value = total_value - uba_amount

        direct_attributions = {}
        commons_contribution = uba_amount  # Start with UBA amount
        emergence_bonus = 0.0

        # Calculate total weighted confidence for normalization
        total_weighted_confidence = 0.0
        high_confidence_results = []

        for result in attribution_results:
            if result.confidence >= self.attribution_confidence_threshold:
                high_confidence_results.append(result)
                # Weight by confidence and temporal decay
                weight = result.confidence * result.temporal_relevance
                total_weighted_confidence += weight

        if high_confidence_results and total_weighted_confidence > 0:
            # Distribute to high-confidence attributions
            attributable_percentage = min(
                0.85, len(high_confidence_results) * 0.2
            )  # Max 85%
            attributable_value = distributable_value * attributable_percentage
            unattributable_value = distributable_value - attributable_value

            # Add unattributable value to commons
            commons_contribution += unattributable_value

            # Distribute attributable value
            for result in high_confidence_results:
                weight = (
                    result.confidence * result.temporal_relevance
                ) / total_weighted_confidence
                attribution_amount = attributable_value * weight

                # Apply temporal decay - degraded value goes to commons
                if result.temporal_relevance < 1.0:
                    decay_loss = attribution_amount * (1.0 - result.temporal_relevance)
                    attribution_amount -= decay_loss
                    commons_contribution += (
                        decay_loss  # KEY INSIGHT: degraded value to commons
                    )

                if result.source_id not in direct_attributions:
                    direct_attributions[result.source_id] = 0.0
                direct_attributions[result.source_id] += attribution_amount

            distribution_method = "weighted_attribution"
            overall_confidence = sum(
                r.confidence for r in high_confidence_results
            ) / len(high_confidence_results)
        else:
            # No high-confidence attributions - everything to commons
            commons_contribution += distributable_value
            distribution_method = "commons_fallback"
            overall_confidence = 0.0

        # Detect emergence value (1+1=3 scenarios)
        expected_value = sum(direct_attributions.values())
        if (
            expected_value > 0
            and total_value > expected_value * self.emergence_detection_threshold
        ):
            emergence_value = total_value - expected_value
            emergence_bonus = (
                emergence_value * 0.1
            )  # 10% goes to emergence research fund
            # Note: The emergence distribution formula from our discussion would be applied here

        return PragmaticDistribution(
            direct_attributions=direct_attributions,
            commons_contribution=commons_contribution,
            emergence_bonus=emergence_bonus,
            total_distributed=sum(direct_attributions.values())
            + commons_contribution
            + emergence_bonus,
            attribution_confidence=overall_confidence,
            distribution_method=distribution_method,
        )

    def _load_economic_state(self):
        """Load existing economic state from chain."""
        if not self.base_engine:
            return  # Skip loading in demo mode

        chain = self.base_engine.get_chain()

        # Extract economic state from existing economic capsules
        for capsule in chain:
            if isinstance(capsule, EconomicCapsule):
                self._process_economic_capsule(capsule)

    def _process_economic_capsule(self, capsule: EconomicCapsule):
        """Process an economic capsule to update internal state."""
        if capsule.economic_event_type == EconomicTransactionType.VALUE_TRANSFER:
            # Update balances based on transfers
            for recipient, amount in capsule.value_recipients.items():
                if recipient not in self.agent_balances:
                    self.agent_balances[recipient] = 0
                self.agent_balances[recipient] += amount * capsule.value_amount

        elif capsule.economic_event_type == EconomicTransactionType.STAKE_DEPOSIT:
            # Update staked amounts
            for agent, amount in capsule.value_recipients.items():
                if agent not in self.agent_stakes:
                    self.agent_stakes[agent] = 0
                self.agent_stakes[agent] += amount * capsule.value_amount

                # Deduct from balance
                if agent in self.agent_balances:
                    self.agent_balances[agent] -= amount * capsule.value_amount

        elif capsule.economic_event_type == EconomicTransactionType.STAKE_WITHDRAWAL:
            # Return staked amounts to balance
            for agent, amount in capsule.value_recipients.items():
                if (
                    agent in self.agent_stakes
                    and self.agent_stakes[agent] >= amount * capsule.value_amount
                ):
                    self.agent_stakes[agent] -= amount * capsule.value_amount

                    if agent not in self.agent_balances:
                        self.agent_balances[agent] = 0
                    self.agent_balances[agent] += amount * capsule.value_amount

    def get_agent_balance(self, agent_id: str) -> float:
        """Get the current balance for an agent.

        Args:
            agent_id: The ID of the agent

        Returns:
            Current balance
        """
        return self.agent_balances.get(agent_id, 0.0)

    def get_agent_stake(self, agent_id: str) -> float:
        """Get the current staked amount for an agent.

        Args:
            agent_id: The ID of the agent

        Returns:
            Current staked amount
        """
        return self.agent_stakes.get(agent_id, 0.0)

    def get_agent_reputation(self, agent_id: str) -> float:
        """Get the current reputation score for an agent.

        Args:
            agent_id: The ID of the agent

        Returns:
            Current reputation score (0.0-1.0)
        """
        return self.agent_reputation.get(agent_id, 0.5)  # Default to neutral reputation

    def create_value_transfer(
        self,
        source_agent_id: str,
        recipients: Dict[str, float],
        amount: float,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EconomicCapsule:
        """Create a value transfer between agents.

        Args:
            source_agent_id: ID of the agent sending value
            recipients: Dict mapping recipient agent IDs to their share (0.0-1.0)
            amount: Total amount of value to transfer
            description: Description of the transfer
            metadata: Optional additional metadata

        Returns:
            Created economic capsule

        Raises:
            ValueError: If source agent has insufficient balance
        """
        # Validate inputs
        if sum(recipients.values()) != 1.0:
            raise ValueError("Recipient shares must sum to 1.0")

        if source_agent_id not in self.agent_balances:
            self.agent_balances[source_agent_id] = 0.0

        if self.agent_balances[source_agent_id] < amount:
            raise ValueError(
                f"Insufficient balance: {self.agent_balances[source_agent_id]} < {amount}"
            )

        # Create the capsule
        capsule = self.base_engine.create_economic_capsule(
            transaction_type=EconomicTransactionType.VALUE_TRANSFER,
            resource_allocation={"source": source_agent_id, "amount": amount},
            value_recipients=recipients,
            calculation_method="direct_transfer",
            content=description,
            dividend_distribution=recipients,
            economic_value={
                "transaction_type": "transfer",
                "timestamp": utc_now().isoformat(),
                **(metadata or {}),
            },
        )

        # Update internal state
        self.agent_balances[source_agent_id] -= amount
        for recipient, share in recipients.items():
            if recipient not in self.agent_balances:
                self.agent_balances[recipient] = 0.0
            self.agent_balances[recipient] += amount * share

        return capsule

    def create_stake_deposit(
        self,
        agent_id: str,
        amount: float,
        purpose: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EconomicCapsule:
        """Create a stake deposit for an agent.

        Args:
            agent_id: ID of the agent staking
            amount: Amount to stake
            purpose: Purpose of the stake
            metadata: Optional additional metadata

        Returns:
            Created economic capsule

        Raises:
            ValueError: If agent has insufficient balance
        """
        if agent_id not in self.agent_balances:
            self.agent_balances[agent_id] = 0.0

        if self.agent_balances[agent_id] < amount:
            raise ValueError(
                f"Insufficient balance for staking: {self.agent_balances[agent_id]} < {amount}"
            )

        # Create the capsule
        capsule = self.base_engine.create_economic_capsule(
            transaction_type=EconomicTransactionType.STAKE_DEPOSIT,
            resource_allocation={"source": agent_id, "amount": amount},
            value_recipients={agent_id: 1.0},
            calculation_method="direct_stake",
            content=f"Stake deposit: {purpose}",
            dividend_distribution={agent_id: 1.0},
            economic_value={
                "transaction_type": "stake",
                "purpose": purpose,
                "timestamp": utc_now().isoformat(),
                **(metadata or {}),
            },
        )

        # Update internal state
        self.agent_balances[agent_id] -= amount
        if agent_id not in self.agent_stakes:
            self.agent_stakes[agent_id] = 0.0
        self.agent_stakes[agent_id] += amount

        return capsule

    def create_verification_reward(
        self,
        agent_id: str,
        verified_capsule_id: str,
        reward_amount: float,
        quality_score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EconomicCapsule:
        """Create a verification reward for an agent.

        Args:
            agent_id: ID of the agent being rewarded
            verified_capsule_id: ID of the capsule that was verified
            reward_amount: Amount of reward
            quality_score: Quality score of the verification (0.0-1.0)
            metadata: Optional additional metadata

        Returns:
            Created economic capsule
        """
        # Create the capsule
        capsule = self.base_engine.create_economic_capsule(
            transaction_type=EconomicTransactionType.VERIFICATION_REWARD,
            resource_allocation={
                "verified_capsule_id": verified_capsule_id,
                "quality_score": quality_score,
                "amount": reward_amount,
            },
            value_recipients={agent_id: 1.0},
            calculation_method="verification_quality",
            content=f"Verification reward for capsule {verified_capsule_id}",
            dividend_distribution={agent_id: 1.0},
            economic_value={
                "transaction_type": "reward",
                "verified_capsule_id": verified_capsule_id,
                "quality_score": quality_score,
                "timestamp": utc_now().isoformat(),
                **(metadata or {}),
            },
        )

        # Update internal state
        if agent_id not in self.agent_balances:
            self.agent_balances[agent_id] = 0.0
        self.agent_balances[agent_id] += reward_amount

        # Update reputation based on quality
        if agent_id not in self.agent_reputation:
            self.agent_reputation[agent_id] = 0.5  # Start at neutral

        # Update reputation (weighted average with new quality score)
        current_rep = self.agent_reputation[agent_id]
        self.agent_reputation[agent_id] = (current_rep * 0.9) + (quality_score * 0.1)

        return capsule

    def calculate_value_distribution(
        self,
        value_amount: float,
        contributors: Dict[str, float],
        stake_weight: float = 0.2,
        reputation_weight: float = 0.3,
    ) -> Dict[str, float]:
        """Calculate fair distribution of value based on contribution, stake, and reputation.

        Args:
            value_amount: Total value to distribute
            contributors: Dict mapping contributor agent IDs to their contribution share (0.0-1.0)
            stake_weight: Weight to give to stake in calculation (0.0-1.0)
            reputation_weight: Weight to give to reputation in calculation (0.0-1.0)

        Returns:
            Dict mapping agent IDs to their value share
        """
        # Validate inputs
        if sum(contributors.values()) != 1.0:
            raise ValueError("Contributor shares must sum to 1.0")

        # Calculate total stake of all contributors
        total_stake = sum(
            self.agent_stakes.get(agent_id, 0.0) for agent_id in contributors.keys()
        )

        # Calculate weighted distribution
        contribution_weight = 1.0 - stake_weight - reputation_weight
        distribution = {}

        for agent_id, contribution_share in contributors.items():
            # Get stake and reputation factors
            stake_share = (
                self.agent_stakes.get(agent_id, 0.0) / total_stake
                if total_stake > 0
                else 0
            )
            reputation = self.agent_reputation.get(agent_id, 0.5)

            # Calculate weighted score
            weighted_score = (
                (contribution_share * contribution_weight)
                + (stake_share * stake_weight)
                + (reputation * reputation_weight)
            )

            distribution[agent_id] = weighted_score

        # Normalize to sum to 1.0
        total_score = sum(distribution.values())
        if total_score > 0:
            for agent_id in distribution:
                distribution[agent_id] /= total_score

        return distribution

    def create_dividend_distribution(
        self,
        value_source: str,
        value_amount: float,
        contributors: Dict[str, float],
        description: str,
        stake_weight: float = 0.2,
        reputation_weight: float = 0.3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EconomicCapsule:
        """Create a dividend distribution based on contribution, stake, and reputation.

        Args:
            value_source: Description of value source
            value_amount: Total value amount to distribute
            contributors: Dict mapping contributor agent IDs to their contribution share (0.0-1.0)
            description: Description of the distribution
            stake_weight: Weight to give to stake in calculation
            reputation_weight: Weight to give to reputation in calculation
            metadata: Optional additional metadata

        Returns:
            Created economic capsule
        """
        # Calculate distribution
        distribution = self.calculate_value_distribution(
            value_amount=value_amount,
            contributors=contributors,
            stake_weight=stake_weight,
            reputation_weight=reputation_weight,
        )

        # Create the capsule
        capsule = self.base_engine.create_economic_capsule(
            transaction_type=EconomicTransactionType.DIVIDEND_DISTRIBUTION,
            resource_allocation={
                "source": value_source,
                "amount": value_amount,
                "stake_weight": stake_weight,
                "reputation_weight": reputation_weight,
            },
            value_recipients=contributors,
            calculation_method="weighted_distribution",
            content=description,
            dividend_distribution=distribution,
            economic_value={
                "transaction_type": "dividend",
                "contributors": contributors,
                "distribution": distribution,
                "timestamp": utc_now().isoformat(),
                **(metadata or {}),
            },
        )

        # Update internal state
        for agent_id, share in distribution.items():
            if agent_id not in self.agent_balances:
                self.agent_balances[agent_id] = 0.0
            self.agent_balances[agent_id] += value_amount * share

        return capsule

    def calculate_verification_reward(
        self,
        verification_quality: float,
        capsule_value: float,
        stake_amount: float,
        base_reward: float = 0.01,
    ) -> float:
        """Calculate verification reward based on quality, value, and stake.

        Args:
            verification_quality: Quality score of verification (0.0-1.0)
            capsule_value: Value of the capsule being verified
            stake_amount: Amount staked by verifier
            base_reward: Base reward rate

        Returns:
            Reward amount
        """
        # Basic reward calculation formula:
        # reward = base_reward + (verification_quality * capsule_value * 0.01) + (stake_amount * 0.001)
        reward = base_reward
        reward += verification_quality * capsule_value * 0.01
        reward += stake_amount * 0.001

        return reward

    def apply_penalty(
        self,
        agent_id: str,
        violation_type: str,
        penalty_amount: float,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EconomicCapsule:
        """Apply an economic penalty to an agent.

        Args:
            agent_id: ID of the agent being penalized
            violation_type: Type of violation
            penalty_amount: Amount of penalty
            description: Description of the penalty
            metadata: Optional additional metadata

        Returns:
            Created economic capsule
        """
        # Determine if penalty comes from balance or stake
        balance = self.agent_balances.get(agent_id, 0.0)
        stake = self.agent_stakes.get(agent_id, 0.0)

        from_balance = min(balance, penalty_amount)
        from_stake = min(stake, penalty_amount - from_balance)
        actual_penalty = from_balance + from_stake

        # Create the capsule
        capsule = self.base_engine.create_economic_capsule(
            transaction_type=EconomicTransactionType.PENALTY,
            resource_allocation={
                "agent_id": agent_id,
                "violation_type": violation_type,
                "from_balance": from_balance,
                "from_stake": from_stake,
            },
            value_recipients={"system": 1.0},
            calculation_method="direct_penalty",
            content=description,
            dividend_distribution={"system": 1.0},
            economic_value={
                "transaction_type": "penalty",
                "violation_type": violation_type,
                "amount": actual_penalty,
                "timestamp": utc_now().isoformat(),
                **(metadata or {}),
            },
        )

        # Update internal state
        if agent_id in self.agent_balances:
            self.agent_balances[agent_id] -= from_balance

        if agent_id in self.agent_stakes:
            self.agent_stakes[agent_id] -= from_stake

        # Update reputation
        if agent_id not in self.agent_reputation:
            self.agent_reputation[agent_id] = 0.5

        # Reputation decreases based on severity of penalty
        severity = actual_penalty / 10.0  # Scale factor
        reputation_impact = min(
            severity, 0.5
        )  # Cap at 0.5 to prevent instant zero reputation
        self.agent_reputation[agent_id] = max(
            0, self.agent_reputation[agent_id] - reputation_impact
        )

        return capsule

    def get_economic_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of the current economic state.

        Returns:
            Dict containing economic summary information including attribution data
        """
        total_balance = sum(self.agent_balances.values())
        total_staked = sum(self.agent_stakes.values())
        total_economic_value = total_balance + total_staked + self.commons_fund_balance

        # Get top agents by balance
        top_by_balance = sorted(
            self.agent_balances.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Get top agents by stake
        top_by_stake = sorted(
            self.agent_stakes.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Get top agents by reputation
        top_by_reputation = sorted(
            self.agent_reputation.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Calculate attribution metrics
        attribution_analytics = self.get_attribution_analytics()

        return {
            "total_balance": total_balance,
            "total_staked": total_staked,
            "commons_fund_balance": self.commons_fund_balance,
            "total_economic_value": total_economic_value,
            "agent_count": len(self.agent_balances),
            "top_by_balance": dict(top_by_balance),
            "top_by_stake": dict(top_by_stake),
            "top_by_reputation": dict(top_by_reputation),
            "attribution_analytics": attribution_analytics,
            "pragmatic_settings": {
                "uba_percentage": self.uba_percentage,
                "attribution_confidence_threshold": self.attribution_confidence_threshold,
                "temporal_decay_rate": self.temporal_decay_rate,
                "emergence_detection_threshold": self.emergence_detection_threshold,
            },
            "registered_conversations": len(self.conversation_registry),
            "timestamp": utc_now().isoformat(),
        }

    def save_state(self, filepath: str) -> None:
        """Save the current economic state to a file.

        Args:
            filepath: Path to save the state to
        """
        state = {
            "agent_balances": self.agent_balances,
            "agent_stakes": self.agent_stakes,
            "agent_reputation": self.agent_reputation,
            "timestamp": utc_now().isoformat(),
        }

        with open(filepath, "w") as f:
            json.dump(state, f)

    def load_state(self, filepath: str) -> None:
        """Load economic state from a file.

        Args:
            filepath: Path to load the state from
        """
        try:
            with open(filepath) as f:
                state = json.load(f)

            self.agent_balances = state.get("agent_balances", {})
            self.agent_stakes = state.get("agent_stakes", {})
            self.agent_reputation = state.get("agent_reputation", {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load economic state: {e}")

    def create_pragmatic_attribution_payment(
        self,
        ai_output: str,
        total_value: float,
        description: str,
        context: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> EconomicCapsule:
        """Create a pragmatic attribution payment for AI-generated value.

        This is the main entry point for the pragmatic attribution system.
        It analyzes the AI output, determines attribution, and creates payments.

        Args:
            ai_output: The AI-generated content
            total_value: Total economic value generated
            description: Description of the value creation
            context: Optional context about the AI output
            metadata: Optional additional metadata

        Returns:
            Created economic capsule documenting the attribution
        """
        # Perform attribution analysis
        attribution_results = self.attribute_ai_output(ai_output, total_value, context)

        # Calculate pragmatic distribution
        distribution = self.calculate_pragmatic_distribution(
            attribution_results, total_value
        )

        # Update agent balances based on distribution
        for agent_id, amount in distribution.direct_attributions.items():
            if agent_id not in self.agent_balances:
                self.agent_balances[agent_id] = 0.0
            self.agent_balances[agent_id] += amount

        # Add to commons fund
        self.commons_fund_balance += distribution.commons_contribution

        # Create the economic capsule
        capsule = self.base_engine.create_economic_capsule(
            transaction_type=EconomicTransactionType.ATTRIBUTION_PAYMENT,
            resource_allocation={
                "total_value": total_value,
                "attribution_method": "pragmatic_analysis",
                "confidence_threshold": self.attribution_confidence_threshold,
                "uba_percentage": self.uba_percentage,
            },
            value_recipients=distribution.direct_attributions,
            calculation_method=distribution.distribution_method,
            content=description,
            dividend_distribution=distribution.direct_attributions,
            economic_value={
                "transaction_type": "pragmatic_attribution",
                "ai_output_hash": hash(ai_output),  # For reference
                "total_value": total_value,
                "direct_attributions": distribution.direct_attributions,
                "commons_contribution": distribution.commons_contribution,
                "emergence_bonus": distribution.emergence_bonus,
                "attribution_confidence": distribution.attribution_confidence,
                "attribution_count": len(attribution_results),
                "timestamp": utc_now().isoformat(),
                "context": context or {},
                **(metadata or {}),
            },
        )

        logger.info(
            f"Created pragmatic attribution payment: "
            f"{len(distribution.direct_attributions)} direct attributions, "
            f"${distribution.commons_contribution:.2f} to commons, "
            f"confidence: {distribution.attribution_confidence:.2f}"
        )

        return capsule

    def distribute_commons_fund(
        self, recipients: Dict[str, float], distribution_reason: str
    ) -> EconomicCapsule:
        """Distribute Universal Basic Attribution from commons fund.

        Args:
            recipients: Dict mapping recipient IDs to their share (0.0-1.0)
            distribution_reason: Reason for the distribution

        Returns:
            Created economic capsule
        """
        if sum(recipients.values()) != 1.0:
            raise ValueError("Recipient shares must sum to 1.0")

        if self.commons_fund_balance <= 0:
            raise ValueError("Commons fund is empty")

        distribution_amount = self.commons_fund_balance

        # Create the capsule
        capsule = self.base_engine.create_economic_capsule(
            transaction_type=EconomicTransactionType.COMMONS_CONTRIBUTION,
            resource_allocation={
                "source": "commons_fund",
                "amount": distribution_amount,
                "recipient_count": len(recipients),
            },
            value_recipients=recipients,
            calculation_method="universal_basic_attribution",
            content=f"Universal Basic Attribution distribution: {distribution_reason}",
            dividend_distribution=recipients,
            economic_value={
                "transaction_type": "uba_distribution",
                "distribution_amount": distribution_amount,
                "recipient_count": len(recipients),
                "distribution_reason": distribution_reason,
                "timestamp": utc_now().isoformat(),
            },
        )

        # Update balances
        for recipient_id, share in recipients.items():
            amount = distribution_amount * share
            if recipient_id not in self.agent_balances:
                self.agent_balances[recipient_id] = 0.0
            self.agent_balances[recipient_id] += amount

        # Clear commons fund
        self.commons_fund_balance = 0.0

        logger.info(
            f"Distributed ${distribution_amount:.2f} from commons fund to {len(recipients)} recipients"
        )

        return capsule

    def get_attribution_analytics(self) -> Dict[str, Any]:
        """Get analytics about attribution performance.

        Returns:
            Dict with attribution analytics
        """
        if not self.attribution_history:
            return {
                "total_attributions": 0,
                "average_confidence": 0.0,
                "confidence_distribution": {},
                "commons_fund_balance": self.commons_fund_balance,
            }

        total_attributions = len(self.attribution_history)
        average_confidence = (
            sum(a.confidence for a in self.attribution_history) / total_attributions
        )

        # Count by confidence level
        confidence_distribution = {
            "high": sum(
                1
                for a in self.attribution_history
                if a.confidence_level == AttributionConfidence.HIGH
            ),
            "medium": sum(
                1
                for a in self.attribution_history
                if a.confidence_level == AttributionConfidence.MEDIUM
            ),
            "low": sum(
                1
                for a in self.attribution_history
                if a.confidence_level == AttributionConfidence.LOW
            ),
            "unknown": sum(
                1
                for a in self.attribution_history
                if a.confidence_level == AttributionConfidence.UNKNOWN
            ),
        }

        # Top contributors by attribution count
        contributor_counts = {}
        for attribution in self.attribution_history:
            contributor_counts[attribution.source_id] = (
                contributor_counts.get(attribution.source_id, 0) + 1
            )

        top_contributors = sorted(
            contributor_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "total_attributions": total_attributions,
            "average_confidence": average_confidence,
            "confidence_distribution": confidence_distribution,
            "top_contributors": dict(top_contributors),
            "commons_fund_balance": self.commons_fund_balance,
            "temporal_decay_rate": self.temporal_decay_rate,
            "attribution_confidence_threshold": self.attribution_confidence_threshold,
            "uba_percentage": self.uba_percentage,
        }
