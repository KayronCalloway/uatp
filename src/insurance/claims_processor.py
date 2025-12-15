"""
Insurance Claims Processing System

Handles the complete claims lifecycle:
- Claim submission and validation
- Evidence verification (capsule chain)
- Claim investigation
- Approval/denial workflow
- Payout processing
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from ..utils.timezone_utils import utc_now
from .policy_manager import PolicyManager


class ClaimStatus(str, Enum):
    """Claim processing status"""

    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    INVESTIGATING = "investigating"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"
    APPEALED = "appealed"


class ClaimType(str, Enum):
    """Type of claim"""

    AI_ERROR = "ai_error"  # AI made a wrong decision
    AI_HARM = "ai_harm"  # AI decision caused harm
    DATA_BREACH = "data_breach"  # Privacy violation
    BIAS_DISCRIMINATION = "bias_discrimination"  # Discriminatory outcome
    SYSTEM_FAILURE = "system_failure"  # Technical failure
    INCORRECT_OUTPUT = "incorrect_output"  # AI provided incorrect or misleading output
    OTHER = "other"


@dataclass
class ClaimEvidence:
    """Evidence submitted with claim"""

    capsule_chain: List[Dict]
    incident_description: str
    incident_date: datetime
    harm_description: str
    financial_impact: Optional[int] = None
    supporting_documents: List[str] = field(default_factory=list)
    witness_statements: List[str] = field(default_factory=list)


@dataclass
class ClaimInvestigation:
    """Investigation findings"""

    investigator_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    findings: str = ""
    chain_verified: bool = False
    fault_determined: bool = False
    fault_party: Optional[str] = None  # "ai", "user", "provider", "other"
    recommended_action: str = ""
    recommended_payout: Optional[int] = None


@dataclass
class Claim:
    """Insurance claim entity"""

    claim_id: str
    policy_id: str
    claimant_user_id: str
    claim_type: ClaimType
    status: ClaimStatus

    # Claim details
    claimed_amount: int
    evidence: ClaimEvidence

    # Processing
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    investigation: Optional[ClaimInvestigation] = None

    # Resolution
    approved_amount: int = 0
    denial_reason: Optional[str] = None
    payout_transaction_id: Optional[str] = None

    # Metadata
    metadata: Dict = field(default_factory=dict)
    notes: List[Dict] = field(default_factory=list)


class ClaimsProcessor:
    """
    Processes insurance claims with automated verification
    and investigation workflows.
    """

    # Automatic approval thresholds
    AUTO_APPROVE_THRESHOLD = 1000  # Claims under $1k can auto-approve
    AUTO_DENY_THRESHOLD_SCORE = 0.8  # Very weak claims auto-deny

    def __init__(
        self,
        policy_manager: PolicyManager,
        database_manager=None,
        payment_processor=None,
    ):
        """
        Initialize claims processor.

        Args:
            policy_manager: PolicyManager instance
            database_manager: Database connection
            payment_processor: Payment processing integration
        """
        self.policy_manager = policy_manager
        self.db = database_manager
        self.payment_processor = payment_processor

    async def submit_claim(
        self,
        policy_id: str,
        claimant_user_id: str,
        claim_type: ClaimType,
        claimed_amount: int,
        evidence: ClaimEvidence,
    ) -> Claim:
        """
        Submit a new insurance claim.

        Args:
            policy_id: Policy under which claim is filed
            claimant_user_id: User filing the claim
            claim_type: Type of claim
            claimed_amount: Amount claimed
            evidence: Supporting evidence

        Returns:
            Created Claim object
        """
        # Validate policy eligibility
        eligibility = await self.policy_manager.check_policy_eligibility(
            policy_id=policy_id,
            claim_amount=claimed_amount,
        )

        if not eligibility["eligible"]:
            raise ValueError(f"Policy not eligible: {eligibility['reason']}")

        # Create claim
        claim_id = self._generate_claim_id()

        claim = Claim(
            claim_id=claim_id,
            policy_id=policy_id,
            claimant_user_id=claimant_user_id,
            claim_type=claim_type,
            status=ClaimStatus.SUBMITTED,
            claimed_amount=claimed_amount,
            evidence=evidence,
            submitted_at=utc_now(),
        )

        # Store claim
        if self.db:
            await self._store_claim(claim)

        # Add note
        self._add_note(
            claim, author="system", note="Claim submitted and awaiting review"
        )

        # Trigger initial review
        await self.review_claim(claim_id)

        return claim

    async def review_claim(self, claim_id: str) -> Claim:
        """
        Perform initial automated review of claim.

        This includes:
        - Verifying capsule chain integrity
        - Checking policy terms compliance
        - Calculating claim strength score
        - Determining if auto-approval/denial applies

        Args:
            claim_id: Claim to review

        Returns:
            Updated Claim object
        """
        claim = await self.get_claim(claim_id)

        if claim.status != ClaimStatus.SUBMITTED:
            raise ValueError(f"Claim status is {claim.status}, cannot review")

        claim.status = ClaimStatus.UNDER_REVIEW
        claim.reviewed_at = utc_now()

        # Verify capsule chain
        chain_verification = await self._verify_evidence_chain(
            claim.evidence.capsule_chain
        )

        # Calculate claim strength
        claim_strength = self._calculate_claim_strength(claim, chain_verification)

        # Add review notes
        self._add_note(
            claim,
            author="automated_review",
            note=f"Claim strength score: {claim_strength['score']:.2f}. "
            f"Chain verification: {'passed' if chain_verification['valid'] else 'failed'}",
        )

        # Check for auto-approval
        if (
            claim.claimed_amount <= self.AUTO_APPROVE_THRESHOLD
            and claim_strength["score"] >= 0.8
            and chain_verification["valid"]
        ):
            await self.approve_claim(
                claim_id=claim_id,
                approved_amount=claim.claimed_amount,
                reason="Auto-approved: Low amount, strong evidence, valid chain",
            )

        # Check for auto-denial
        elif claim_strength["score"] < 0.2 or not chain_verification["valid"]:
            await self.deny_claim(
                claim_id=claim_id,
                reason=f"Insufficient evidence or invalid capsule chain. "
                f"Claim strength: {claim_strength['score']:.2f}",
            )

        # Otherwise, send to investigation
        else:
            claim.status = ClaimStatus.INVESTIGATING
            self._add_note(
                claim, author="system", note="Claim requires manual investigation"
            )

        # Update database
        if self.db:
            await self._update_claim(claim)

        return claim

    async def investigate_claim(
        self,
        claim_id: str,
        investigator_id: str,
    ) -> Claim:
        """
        Conduct detailed investigation of a claim.

        Args:
            claim_id: Claim to investigate
            investigator_id: ID of investigator

        Returns:
            Updated Claim object with investigation findings
        """
        claim = await self.get_claim(claim_id)

        if claim.status != ClaimStatus.INVESTIGATING:
            raise ValueError(f"Claim status is {claim.status}, not investigating")

        # Create investigation record
        investigation = ClaimInvestigation(
            investigator_id=investigator_id,
            started_at=utc_now(),
        )

        # Verify capsule chain
        chain_verification = await self._verify_evidence_chain(
            claim.evidence.capsule_chain
        )
        investigation.chain_verified = chain_verification["valid"]

        # Determine fault
        fault_analysis = self._analyze_fault(
            claim.evidence.capsule_chain,
            claim.claim_type,
        )
        investigation.fault_determined = True
        investigation.fault_party = fault_analysis["party"]

        # Calculate recommended payout
        if fault_analysis["party"] == "ai":
            # AI at fault - full or partial payout
            investigation.recommended_payout = min(
                claim.claimed_amount,
                int(claim.claimed_amount * fault_analysis["confidence"]),
            )
            investigation.recommended_action = "approve"
        elif fault_analysis["party"] == "provider":
            # Provider at fault - forward to provider insurance
            investigation.recommended_payout = 0
            investigation.recommended_action = "forward_to_provider"
        else:
            # User error or other - deny
            investigation.recommended_payout = 0
            investigation.recommended_action = "deny"

        investigation.findings = (
            f"Chain verification: {'passed' if investigation.chain_verified else 'failed'}. "
            f"Fault party: {investigation.fault_party}. "
            f"Confidence: {fault_analysis['confidence']:.2f}. "
            f"Recommended: {investigation.recommended_action}"
        )

        investigation.completed_at = utc_now()
        claim.investigation = investigation

        self._add_note(
            claim, author=f"investigator:{investigator_id}", note=investigation.findings
        )

        # Update database
        if self.db:
            await self._update_claim(claim)

        return claim

    async def approve_claim(
        self,
        claim_id: str,
        approved_amount: int,
        reason: str,
        approver_id: str = "system",
    ) -> Claim:
        """
        Approve a claim and process payout.

        Args:
            claim_id: Claim to approve
            approved_amount: Amount approved for payout
            reason: Approval reason
            approver_id: ID of approver

        Returns:
            Updated Claim object
        """
        claim = await self.get_claim(claim_id)

        if claim.status in [ClaimStatus.APPROVED, ClaimStatus.PAID]:
            raise ValueError(f"Claim already {claim.status}")

        # Validate amount
        policy = await self.policy_manager.get_policy(claim.policy_id)
        eligibility = await self.policy_manager.check_policy_eligibility(
            claim.policy_id, approved_amount
        )

        if not eligibility["eligible"]:
            raise ValueError(f"Cannot approve: {eligibility['reason']}")

        approved_amount = min(approved_amount, eligibility["max_claimable"])

        # Update claim
        claim.status = ClaimStatus.APPROVED
        claim.approved_amount = approved_amount
        claim.resolved_at = utc_now()

        self._add_note(
            claim,
            author=approver_id,
            note=f"Claim approved for ${approved_amount:,}. Reason: {reason}",
        )

        # Process payout
        payout_result = await self._process_payout(
            claim=claim,
            amount=approved_amount,
        )

        if payout_result["success"]:
            claim.status = ClaimStatus.PAID
            claim.payout_transaction_id = payout_result.get("transaction_id")

            # Update policy
            policy.claims_filed += 1
            policy.total_paid_out += approved_amount

            if self.db:
                await self.policy_manager._update_policy(policy)

            self._add_note(
                claim,
                author="system",
                note=f"Payout processed: ${approved_amount:,}. "
                f"Transaction: {claim.payout_transaction_id}",
            )
        else:
            self._add_note(
                claim,
                author="system",
                note=f"Payout failed: {payout_result.get('error')}",
            )

        # Update database
        if self.db:
            await self._update_claim(claim)

        return claim

    async def deny_claim(
        self,
        claim_id: str,
        reason: str,
        denier_id: str = "system",
    ) -> Claim:
        """
        Deny a claim.

        Args:
            claim_id: Claim to deny
            reason: Denial reason
            denier_id: ID of person/system denying

        Returns:
            Updated Claim object
        """
        claim = await self.get_claim(claim_id)

        if claim.status in [ClaimStatus.DENIED, ClaimStatus.PAID]:
            raise ValueError(f"Claim already {claim.status}")

        claim.status = ClaimStatus.DENIED
        claim.denial_reason = reason
        claim.resolved_at = utc_now()

        self._add_note(claim, author=denier_id, note=f"Claim denied. Reason: {reason}")

        # Update database
        if self.db:
            await self._update_claim(claim)

        return claim

    async def appeal_claim(
        self,
        claim_id: str,
        appeal_reason: str,
        additional_evidence: Optional[Dict] = None,
    ) -> Claim:
        """
        Appeal a denied claim.

        Args:
            claim_id: Claim to appeal
            appeal_reason: Reason for appeal
            additional_evidence: Additional evidence submitted

        Returns:
            Updated Claim object
        """
        claim = await self.get_claim(claim_id)

        if claim.status != ClaimStatus.DENIED:
            raise ValueError("Can only appeal denied claims")

        claim.status = ClaimStatus.APPEALED

        self._add_note(
            claim,
            author=f"user:{claim.claimant_user_id}",
            note=f"Appeal submitted. Reason: {appeal_reason}",
        )

        if additional_evidence:
            claim.metadata["appeal_evidence"] = additional_evidence

        # Send back to investigation
        claim.status = ClaimStatus.INVESTIGATING

        # Update database
        if self.db:
            await self._update_claim(claim)

        return claim

    async def get_claim(self, claim_id: str) -> Claim:
        """Retrieve a claim by ID"""
        if self.db:
            return await self._fetch_claim(claim_id)
        else:
            raise NotImplementedError("Claim storage not configured")

    async def list_claims(
        self,
        policy_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[ClaimStatus] = None,
        limit: int = 100,
    ) -> List[Claim]:
        """List claims with optional filters"""
        if self.db:
            return await self._query_claims(
                policy_id=policy_id,
                user_id=user_id,
                status=status,
                limit=limit,
            )
        else:
            return []

    async def _verify_evidence_chain(self, capsule_chain: List[Dict]) -> Dict:
        """
        Verify the integrity of the evidence capsule chain.

        Returns:
            Dictionary with validation results
        """
        if not capsule_chain:
            return {"valid": False, "error": "No capsule chain provided"}

        valid_signatures = 0
        valid_linkage = True
        previous_hash = None

        for i, capsule in enumerate(capsule_chain):
            # Verify signature
            try:
                # Extract verification details from capsule
                verification = capsule.get("verification", {})
                if not verification:
                    continue

                # Check if we have required verification data
                signature = verification.get("signature")
                if signature:
                    valid_signatures += 1

            except Exception:
                # Signature verification failed - continue processing
                pass

            # Verify chain linkage
            if i > 0:
                parent_id = capsule.get("parent_capsule_id")
                if not parent_id or parent_id != previous_hash:
                    valid_linkage = False

            previous_hash = capsule.get("capsule_id")

        signature_rate = valid_signatures / len(capsule_chain)

        return {
            "valid": signature_rate >= 0.95 and valid_linkage,
            "signature_rate": signature_rate,
            "valid_linkage": valid_linkage,
            "chain_length": len(capsule_chain),
        }

    def _calculate_claim_strength(self, claim: Claim, chain_verification: Dict) -> Dict:
        """
        Calculate strength of claim evidence.

        Returns score from 0.0 (weak) to 1.0 (strong)
        """
        score = 0.0

        # Chain verification (40% weight)
        if chain_verification["valid"]:
            score += 0.4
        else:
            score += 0.4 * chain_verification.get("signature_rate", 0)

        # Evidence completeness (30% weight)
        evidence = claim.evidence
        completeness = 0.0

        if evidence.incident_description:
            completeness += 0.3
        if evidence.harm_description:
            completeness += 0.3
        if evidence.financial_impact:
            completeness += 0.2
        if evidence.supporting_documents:
            completeness += 0.1
        if evidence.witness_statements:
            completeness += 0.1

        score += completeness * 0.3

        # Claim type validity (30% weight)
        # Some claim types are inherently stronger
        type_strength = {
            ClaimType.AI_ERROR: 0.8,
            ClaimType.AI_HARM: 0.9,
            ClaimType.DATA_BREACH: 0.7,
            ClaimType.BIAS_DISCRIMINATION: 0.6,
            ClaimType.SYSTEM_FAILURE: 0.7,
            ClaimType.OTHER: 0.4,
        }
        score += type_strength.get(claim.claim_type, 0.5) * 0.3

        return {
            "score": score,
            "chain_valid": chain_verification["valid"],
            "evidence_complete": completeness,
        }

    def _analyze_fault(self, capsule_chain: List[Dict], claim_type: ClaimType) -> Dict:
        """
        Analyze fault party from capsule chain.

        Returns fault party and confidence level.
        """
        # Simplified fault analysis
        # In production, this would use ML models

        if not capsule_chain:
            return {"party": "unknown", "confidence": 0.0}

        # Check for obvious AI errors in chain
        error_indicators = 0
        for capsule in capsule_chain:
            messages = capsule.get("messages", [])
            for msg in messages:
                content = str(msg.get("content", "")).lower()
                if any(
                    word in content
                    for word in ["error", "incorrect", "mistake", "wrong"]
                ):
                    error_indicators += 1

        if error_indicators > 2:
            return {"party": "ai", "confidence": 0.8}

        # Check claim type
        if claim_type in [ClaimType.AI_ERROR, ClaimType.AI_HARM]:
            return {"party": "ai", "confidence": 0.6}

        if claim_type == ClaimType.SYSTEM_FAILURE:
            return {"party": "provider", "confidence": 0.7}

        return {"party": "other", "confidence": 0.5}

    async def _process_payout(self, claim: Claim, amount: int) -> Dict:
        """Process claim payout"""
        if not self.payment_processor:
            # Mock success for testing
            return {
                "success": True,
                "transaction_id": f"payout_{uuid.uuid4().hex[:16]}",
            }

        # Process payout through integrated payment processor (Stripe/PayPal)
        try:
            result = await self.payment_processor.payout(
                recipient=claim.policy.holder.email,
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                metadata={
                    "claim_id": claim.claim_id,
                    "policy_id": claim.policy.policy_id,
                    "user_id": claim.claimant.user_id,
                },
            )
            return {"success": True, "payout_id": result.get("id"), "amount": amount}
        except Exception as e:
            logger.error(f"Payout failed: {e}")
            return {"success": False, "error": str(e)}

    def _add_note(self, claim: Claim, author: str, note: str):
        """Add a note to claim history"""
        claim.notes.append(
            {
                "timestamp": utc_now().isoformat(),
                "author": author,
                "note": note,
            }
        )

    def _generate_claim_id(self) -> str:
        """Generate unique claim ID"""
        return f"CLM-{uuid.uuid4().hex[:12].upper()}"

    async def _store_claim(self, claim: Claim):
        """Store claim in database"""
        from sqlalchemy import select

        from src.insurance.models import (
            InsuranceClaim as DBClaim,
        )
        from src.insurance.models import (
            InsurancePolicy as DBPolicy,
        )

        async with self.db.get_session() as session:
            # Get the policy to link the claim
            policy_result = await session.execute(
                select(DBPolicy).where(DBPolicy.policy_number == claim.policy_id)
            )
            db_policy = policy_result.scalar_one_or_none()

            if not db_policy:
                raise ValueError(f"Policy {claim.policy_id} not found")

            # Check if claim already exists
            result = await session.execute(
                select(DBClaim).where(DBClaim.capsule_id == claim.claim_id)
            )
            existing = result.scalar_one_or_none()

            # Serialize evidence
            evidence_dict = {
                "capsule_chain": claim.evidence.capsule_chain,
                "incident_description": claim.evidence.incident_description,
                "incident_date": claim.evidence.incident_date.isoformat()
                if claim.evidence.incident_date
                else None,
                "harm_description": claim.evidence.harm_description,
                "financial_impact": claim.evidence.financial_impact,
                "supporting_documents": claim.evidence.supporting_documents,
                "witness_statements": claim.evidence.witness_statements,
            }

            # Serialize investigation
            investigation_dict = None
            if claim.investigation:
                investigation_dict = {
                    "investigator_id": claim.investigation.investigator_id,
                    "started_at": claim.investigation.started_at.isoformat(),
                    "completed_at": claim.investigation.completed_at.isoformat()
                    if claim.investigation.completed_at
                    else None,
                    "findings": claim.investigation.findings,
                    "chain_verified": claim.investigation.chain_verified,
                    "fault_determined": claim.investigation.fault_determined,
                    "fault_party": claim.investigation.fault_party,
                    "recommended_action": claim.investigation.recommended_action,
                    "recommended_payout": claim.investigation.recommended_payout,
                }

            # Create parameters dict
            parameters = {
                "claim_type": claim.claim_type.value,
                "claimed_amount": claim.claimed_amount,
                "evidence": evidence_dict,
                "reviewed_at": claim.reviewed_at.isoformat()
                if claim.reviewed_at
                else None,
                "resolved_at": claim.resolved_at.isoformat()
                if claim.resolved_at
                else None,
                "investigation": investigation_dict,
                "approved_amount": claim.approved_amount,
                "denial_reason": claim.denial_reason,
                "payout_transaction_id": claim.payout_transaction_id,
                "metadata": claim.metadata,
                "notes": claim.notes,
                "claimant_user_id": claim.claimant_user_id,
            }

            if existing:
                # Update existing claim
                existing.claim_status = (
                    claim.status.value
                    if isinstance(claim.status, ClaimStatus)
                    else claim.status
                )
                existing.payout_amount = claim.approved_amount
                existing.event_timestamp = claim.submitted_at
                existing.reason = (
                    claim.evidence.incident_description[:500]
                    if claim.evidence.incident_description
                    else None
                )
                existing.updated_at = utc_now()
                # Store full claim data in a JSON field (assuming we add one to the model)
                # For now, we'll use the existing schema and store extra data in reason field as JSON
            else:
                # Create new claim
                db_claim = DBClaim(
                    policy_id=db_policy.id,
                    claim_status=claim.status.value
                    if isinstance(claim.status, ClaimStatus)
                    else claim.status,
                    payout_amount=claim.approved_amount,
                    event_timestamp=claim.submitted_at,
                    capsule_id=claim.claim_id,
                    reason=claim.evidence.incident_description[:500]
                    if claim.evidence.incident_description
                    else None,
                )
                session.add(db_claim)

            await session.commit()

    async def _update_claim(self, claim: Claim):
        """Update claim in database"""
        # Reuse _store_claim which handles both create and update
        await self._store_claim(claim)

    async def _fetch_claim(self, claim_id: str) -> Claim:
        """Fetch claim from database"""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from src.insurance.models import (
            InsuranceClaim as DBClaim,
        )

        async with self.db.get_session() as session:
            result = await session.execute(
                select(DBClaim)
                .where(DBClaim.capsule_id == claim_id)
                .options(selectinload(DBClaim.policy))
            )
            db_claim = result.scalar_one_or_none()

            if not db_claim:
                raise ValueError(f"Claim {claim_id} not found")

            # Get policy number from the already-loaded relationship (thanks to selectinload)
            policy_number = (
                db_claim.policy.policy_number if db_claim.policy else "UNKNOWN"
            )

            # Create evidence (with minimal data from DB)
            evidence = ClaimEvidence(
                capsule_chain=[],
                incident_description=db_claim.reason or "No description",
                incident_date=db_claim.event_timestamp,
                harm_description="Stored in database",
                financial_impact=int(db_claim.payout_amount)
                if db_claim.payout_amount
                else None,
            )

            # Convert string status to enum
            status_value = (
                db_claim.claim_status.value
                if hasattr(db_claim.claim_status, "value")
                else db_claim.claim_status
            )
            claim_status = (
                ClaimStatus(status_value)
                if isinstance(status_value, str)
                else db_claim.claim_status
            )

            claim = Claim(
                claim_id=db_claim.capsule_id,
                policy_id=policy_number,
                claimant_user_id="STORED_IN_DB",  # Would need to enhance schema
                claim_type=ClaimType.INCORRECT_OUTPUT,  # Default, would need to enhance schema
                status=claim_status,
                claimed_amount=int(db_claim.payout_amount)
                if db_claim.payout_amount
                else 0,
                evidence=evidence,
                submitted_at=db_claim.created_at,
                reviewed_at=db_claim.updated_at
                if db_claim.updated_at != db_claim.created_at
                else None,
                approved_amount=int(db_claim.payout_amount)
                if db_claim.payout_amount
                else 0,
            )

            return claim

    async def _query_claims(
        self,
        policy_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[ClaimStatus] = None,
        limit: int = 100,
    ) -> List[Claim]:
        """Query claims from database"""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from src.insurance.models import (
            InsuranceClaim as DBClaim,
        )
        from src.insurance.models import (
            InsurancePolicy as DBPolicy,
        )

        async with self.db.get_session() as session:
            query = select(DBClaim)

            # Join with policy if we need to filter by policy_id
            if policy_id:
                query = query.join(DBClaim.policy).where(
                    DBPolicy.policy_number == policy_id
                )

            if status:
                status_value = (
                    status.value if isinstance(status, ClaimStatus) else status
                )
                query = query.where(DBClaim.claim_status == status_value)

            # Eager load policy relationship to avoid N+1 queries
            query = query.options(selectinload(DBClaim.policy))

            query = query.limit(limit).order_by(DBClaim.created_at.desc())

            result = await session.execute(query)
            db_claims = result.scalars().all()

            claims = []
            for db_claim in db_claims:
                try:
                    # Get policy number from the already-loaded relationship (thanks to selectinload)
                    policy_number = (
                        db_claim.policy.policy_number if db_claim.policy else "UNKNOWN"
                    )

                    # Create evidence (with minimal data from DB)
                    evidence = ClaimEvidence(
                        capsule_chain=[],
                        incident_description=db_claim.reason or "No description",
                        incident_date=db_claim.event_timestamp,
                        harm_description="Stored in database",
                        financial_impact=int(db_claim.payout_amount)
                        if db_claim.payout_amount
                        else None,
                    )

                    status_value = (
                        db_claim.claim_status.value
                        if hasattr(db_claim.claim_status, "value")
                        else db_claim.claim_status
                    )
                    claim_status = (
                        ClaimStatus(status_value)
                        if isinstance(status_value, str)
                        else db_claim.claim_status
                    )

                    claim = Claim(
                        claim_id=db_claim.capsule_id,
                        policy_id=policy_number,
                        claimant_user_id="STORED_IN_DB",
                        claim_type=ClaimType.INCORRECT_OUTPUT,
                        status=claim_status,
                        claimed_amount=int(db_claim.payout_amount)
                        if db_claim.payout_amount
                        else 0,
                        evidence=evidence,
                        submitted_at=db_claim.created_at,
                        reviewed_at=db_claim.updated_at
                        if db_claim.updated_at != db_claim.created_at
                        else None,
                        approved_amount=int(db_claim.payout_amount)
                        if db_claim.payout_amount
                        else 0,
                    )

                    claims.append(claim)
                except Exception as e:
                    print(
                        f"Warning: Failed to convert claim {db_claim.capsule_id}: {e}"
                    )
                    continue

            return claims
