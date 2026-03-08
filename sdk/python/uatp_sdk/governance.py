"""
UATP Python SDK - Governance Module

Provides democratic governance participation capabilities for UATP network decisions.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ProposalStatus(Enum):
    """Status of a governance proposal."""

    DRAFT = "draft"
    ACTIVE = "active"
    VOTING = "voting"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


class VoteChoice(Enum):
    """Vote choices for governance proposals."""

    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass
class Proposal:
    """A governance proposal in the UATP network."""

    proposal_id: str
    title: str
    description: str
    proposer_id: str
    proposal_type: str  # "constitutional", "economic", "technical", "social"
    status: ProposalStatus
    voting_start: datetime
    voting_end: datetime
    required_quorum: float
    required_majority: float

    # Voting results
    votes_approve: int = 0
    votes_reject: int = 0
    votes_abstain: int = 0
    total_voting_power: float = 0.0

    # Execution details
    execution_data: Optional[Dict[str, Any]] = None
    impact_assessment: Optional[Dict[str, Any]] = None

    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)

    @property
    def total_votes(self) -> int:
        """Total number of votes cast."""
        return self.votes_approve + self.votes_reject + self.votes_abstain

    @property
    def approval_percentage(self) -> float:
        """Percentage of approve votes."""
        if self.total_votes == 0:
            return 0.0
        return (self.votes_approve / self.total_votes) * 100

    @property
    def is_active(self) -> bool:
        """Check if proposal is currently in voting phase."""
        now = datetime.now(timezone.utc)
        return (
            self.status == ProposalStatus.VOTING
            and self.voting_start <= now <= self.voting_end
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "description": self.description,
            "proposer_id": self.proposer_id,
            "proposal_type": self.proposal_type,
            "status": self.status.value,
            "voting_start": self.voting_start.isoformat(),
            "voting_end": self.voting_end.isoformat(),
            "required_quorum": self.required_quorum,
            "required_majority": self.required_majority,
            "votes_approve": self.votes_approve,
            "votes_reject": self.votes_reject,
            "votes_abstain": self.votes_abstain,
            "total_voting_power": self.total_voting_power,
            "execution_data": self.execution_data,
            "impact_assessment": self.impact_assessment,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Vote:
    """A vote cast on a governance proposal."""

    vote_id: str
    proposal_id: str
    voter_id: str
    choice: VoteChoice
    voting_power: float
    reasoning: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "vote_id": self.vote_id,
            "proposal_id": self.proposal_id,
            "voter_id": self.voter_id,
            "choice": self.choice.value,
            "voting_power": self.voting_power,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
        }


class GovernanceClient:
    """Client for participating in UATP democratic governance."""

    def __init__(self, client):
        self.client = client
        self.proposal_cache = {}
        self.user_votes = {}
        logger.info(" Governance Client initialized")

    async def get_active_proposals(self) -> List[Proposal]:
        """Get all currently active proposals for voting."""

        try:
            response = await self.client.http_client.get(
                "/api/v1/governance/proposals/active"
            )
            response.raise_for_status()

            data = response.json()
            proposals = []

            for item in data.get("proposals", []):
                proposal = Proposal(
                    proposal_id=item["proposal_id"],
                    title=item["title"],
                    description=item["description"],
                    proposer_id=item["proposer_id"],
                    proposal_type=item["proposal_type"],
                    status=ProposalStatus(item["status"]),
                    voting_start=datetime.fromisoformat(item["voting_start"]),
                    voting_end=datetime.fromisoformat(item["voting_end"]),
                    required_quorum=item["required_quorum"],
                    required_majority=item["required_majority"],
                    votes_approve=item.get("votes_approve", 0),
                    votes_reject=item.get("votes_reject", 0),
                    votes_abstain=item.get("votes_abstain", 0),
                    total_voting_power=item.get("total_voting_power", 0.0),
                    execution_data=item.get("execution_data"),
                    impact_assessment=item.get("impact_assessment"),
                    created_at=datetime.fromisoformat(item["created_at"]),
                    updated_at=datetime.fromisoformat(item["updated_at"]),
                )
                proposals.append(proposal)

                # Cache the proposal
                self.proposal_cache[proposal.proposal_id] = proposal

            logger.info(f"️ Retrieved {len(proposals)} active proposals")
            return proposals

        except Exception as e:
            logger.error(f"[ERROR] Failed to get active proposals: {e}")
            return []

    async def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Get a specific proposal by ID."""

        # Check cache first
        if proposal_id in self.proposal_cache:
            return self.proposal_cache[proposal_id]

        try:
            response = await self.client.http_client.get(
                f"/api/v1/governance/proposals/{proposal_id}"
            )
            response.raise_for_status()

            data = response.json()

            proposal = Proposal(
                proposal_id=data["proposal_id"],
                title=data["title"],
                description=data["description"],
                proposer_id=data["proposer_id"],
                proposal_type=data["proposal_type"],
                status=ProposalStatus(data["status"]),
                voting_start=datetime.fromisoformat(data["voting_start"]),
                voting_end=datetime.fromisoformat(data["voting_end"]),
                required_quorum=data["required_quorum"],
                required_majority=data["required_majority"],
                votes_approve=data.get("votes_approve", 0),
                votes_reject=data.get("votes_reject", 0),
                votes_abstain=data.get("votes_abstain", 0),
                total_voting_power=data.get("total_voting_power", 0.0),
                execution_data=data.get("execution_data"),
                impact_assessment=data.get("impact_assessment"),
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
            )

            # Cache the proposal
            self.proposal_cache[proposal_id] = proposal
            return proposal

        except Exception as e:
            logger.error(f"[ERROR] Failed to get proposal {proposal_id}: {e}")
            return None

    async def cast_vote(
        self,
        proposal_id: str,
        choice: Union[str, VoteChoice],
        reasoning: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cast a vote on a governance proposal.

        Args:
            proposal_id: ID of the proposal to vote on
            choice: Vote choice ("approve", "reject", "abstain")
            reasoning: Optional reasoning for the vote

        Returns:
            Vote confirmation with details
        """

        # Normalize vote choice
        if isinstance(choice, str):
            try:
                choice = VoteChoice(choice.lower())
            except ValueError:
                raise ValueError(
                    f"Invalid vote choice: {choice}. Must be 'approve', 'reject', or 'abstain'"
                )

        vote_request = {
            "proposal_id": proposal_id,
            "choice": choice.value,
            "reasoning": reasoning,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/governance/votes", json=vote_request
            )
            response.raise_for_status()

            result = response.json()

            # Create vote record
            vote = Vote(
                vote_id=result["vote_id"],
                proposal_id=proposal_id,
                voter_id=result["voter_id"],
                choice=choice,
                voting_power=result["voting_power"],
                reasoning=reasoning,
            )

            # Cache user's vote
            if result["voter_id"] not in self.user_votes:
                self.user_votes[result["voter_id"]] = {}
            self.user_votes[result["voter_id"]][proposal_id] = vote

            # Clear proposal cache to force refresh
            if proposal_id in self.proposal_cache:
                del self.proposal_cache[proposal_id]

            logger.info(f"️ Vote cast on proposal {proposal_id}: {choice.value}")
            return {
                "success": True,
                "vote_id": result["vote_id"],
                "voting_power": result["voting_power"],
                "confirmation": result.get("confirmation"),
                "vote": vote.to_dict(),
            }

        except Exception as e:
            logger.error(f"[ERROR] Failed to cast vote on proposal {proposal_id}: {e}")
            return {"success": False, "error": str(e), "vote_id": None}

    async def create_proposal(
        self,
        title: str,
        description: str,
        proposal_type: str,
        execution_data: Optional[Dict[str, Any]] = None,
        voting_duration_hours: int = 168,  # 1 week default
    ) -> Dict[str, Any]:
        """
        Create a new governance proposal.

        Args:
            title: Proposal title
            description: Detailed description
            proposal_type: "constitutional", "economic", "technical", "social"
            execution_data: Data needed for proposal execution
            voting_duration_hours: How long voting should remain open

        Returns:
            Created proposal information
        """

        proposal_request = {
            "title": title,
            "description": description,
            "proposal_type": proposal_type,
            "execution_data": execution_data,
            "voting_duration_hours": voting_duration_hours,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/governance/proposals", json=proposal_request
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f" Created proposal: {result['proposal_id']}")
            return result

        except Exception as e:
            logger.error(f"[ERROR] Failed to create proposal: {e}")
            return {"success": False, "error": str(e), "proposal_id": None}

    async def get_user_votes(self, user_id: str, limit: int = 50) -> List[Vote]:
        """Get voting history for a user."""

        try:
            params = {"user_id": user_id, "limit": limit}

            response = await self.client.http_client.get(
                "/api/v1/governance/votes/user", params=params
            )
            response.raise_for_status()

            data = response.json()
            votes = []

            for item in data.get("votes", []):
                vote = Vote(
                    vote_id=item["vote_id"],
                    proposal_id=item["proposal_id"],
                    voter_id=item["voter_id"],
                    choice=VoteChoice(item["choice"]),
                    voting_power=item["voting_power"],
                    reasoning=item.get("reasoning"),
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                )
                votes.append(vote)

            logger.info(f" Retrieved {len(votes)} votes for user {user_id}")
            return votes

        except Exception as e:
            logger.error(f"[ERROR] Failed to get user votes for {user_id}: {e}")
            return []

    async def get_governance_stats(self) -> Dict[str, Any]:
        """Get overall governance statistics."""

        try:
            response = await self.client.http_client.get("/api/v1/governance/stats")
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"[ERROR] Failed to get governance stats: {e}")
            return {
                "total_proposals": 0,
                "active_proposals": 0,
                "total_voters": 0,
                "participation_rate": 0.0,
                "proposals_by_type": {},
                "error": str(e),
            }

    async def get_voting_power(self, user_id: str) -> Dict[str, Any]:
        """Get a user's voting power and eligibility."""

        try:
            params = {"user_id": user_id}
            response = await self.client.http_client.get(
                "/api/v1/governance/voting-power", params=params
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"[ERROR] Failed to get voting power for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "voting_power": 0.0,
                "eligible": False,
                "requirements": {},
                "error": str(e),
            }

    async def delegate_voting_power(
        self, delegate_to: str, amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Delegate voting power to another user.

        Args:
            delegate_to: User ID to delegate to
            amount: Amount of voting power to delegate (None for all)

        Returns:
            Delegation confirmation
        """

        delegation_request = {
            "delegate_to": delegate_to,
            "amount": amount,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/governance/delegate", json=delegation_request
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f" Delegated voting power to {delegate_to}")
            return result

        except Exception as e:
            logger.error(
                f"[ERROR] Failed to delegate voting power to {delegate_to}: {e}"
            )
            return {"success": False, "error": str(e)}

    async def get_constitutional_framework(self) -> Dict[str, Any]:
        """Get the current constitutional framework of UATP."""

        try:
            response = await self.client.http_client.get(
                "/api/v1/governance/constitution"
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"[ERROR] Failed to get constitutional framework: {e}")
            return {
                "principles": [],
                "articles": {},
                "amendment_process": {},
                "error": str(e),
            }

    def clear_cache(self):
        """Clear all cached governance data."""
        self.proposal_cache.clear()
        self.user_votes.clear()
        logger.info(" Governance cache cleared")
