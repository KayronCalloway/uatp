"""
Real-time Governance Security Monitor for UATP System.

This module provides continuous monitoring and alerting for governance
attacks and suspicious activities, enabling rapid response to threats.
"""

import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from src.audit.events import audit_emitter
from src.governance.advanced_governance import governance_engine
from src.governance.constitutional_framework import constitutional_framework
from src.consensus.multi_agent_consensus import consensus_engine

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Severity levels for security threats."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AttackType(str, Enum):
    """Types of governance attacks."""

    STAKE_CONCENTRATION = "stake_concentration"
    SYBIL_ATTACK = "sybil_attack"
    COORDINATED_MANIPULATION = "coordinated_manipulation"
    RAPID_TAKEOVER = "rapid_takeover"
    CONSTITUTIONAL_VIOLATION = "constitutional_violation"
    BYZANTINE_BEHAVIOR = "byzantine_behavior"
    VOTING_MANIPULATION = "voting_manipulation"
    IDENTITY_FRAUD = "identity_fraud"
    PROPOSAL_SPAM = "proposal_spam"
    DELEGATION_ABUSE = "delegation_abuse"


class SecurityAlert:
    """Security alert for governance threats."""

    def __init__(
        self,
        alert_id: str,
        threat_level: ThreatLevel,
        attack_type: AttackType,
        description: str,
        affected_entities: List[str],
        evidence: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ):
        self.alert_id = alert_id
        self.threat_level = threat_level
        self.attack_type = attack_type
        self.description = description
        self.affected_entities = affected_entities
        self.evidence = evidence
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.acknowledged = False
        self.resolved = False
        self.response_actions = []


class GovernanceSecurityMonitor:
    """Real-time security monitor for governance system."""

    def __init__(self):
        self.active_alerts: Dict[str, SecurityAlert] = {}
        self.alert_history: List[SecurityAlert] = []
        self.monitoring_active = False

        # Monitoring configurations
        self.monitoring_intervals = {
            AttackType.STAKE_CONCENTRATION: 300,  # 5 minutes
            AttackType.SYBIL_ATTACK: 180,  # 3 minutes
            AttackType.COORDINATED_MANIPULATION: 600,  # 10 minutes
            AttackType.RAPID_TAKEOVER: 60,  # 1 minute
            AttackType.CONSTITUTIONAL_VIOLATION: 30,  # 30 seconds
            AttackType.BYZANTINE_BEHAVIOR: 120,  # 2 minutes
            AttackType.VOTING_MANIPULATION: 240,  # 4 minutes
            AttackType.PROPOSAL_SPAM: 900,  # 15 minutes
        }

        # Threat detection thresholds
        self.threat_thresholds = {
            "stake_concentration_warning": 0.12,  # 12% individual stake
            "stake_concentration_critical": 0.15,  # 15% individual stake
            "coordinated_group_warning": 0.20,  # 20% coordinated stake
            "coordinated_group_critical": 0.25,  # 25% coordinated stake
            "sybil_similarity_threshold": 0.8,  # 80% behavioral similarity
            "rapid_registration_threshold": 5,  # 5 registrations in 1 hour
            "byzantine_score_warning": 0.6,  # 60% Byzantine score
            "byzantine_score_critical": 0.8,  # 80% Byzantine score
            "proposal_spam_threshold": 10,  # 10 proposals in 1 hour
            "voting_pattern_anomaly": 0.9,  # 90% voting pattern deviation
        }

        # Activity tracking for pattern detection
        self.activity_windows = {
            "registrations": deque(maxlen=100),
            "proposals": deque(maxlen=100),
            "votes": deque(maxlen=500),
            "delegations": deque(maxlen=100),
            "stake_changes": deque(maxlen=100),
        }

        # Alert counters
        self.alert_stats = defaultdict(int)

        logger.info("Governance Security Monitor initialized")

    async def start_monitoring(self):
        """Start continuous security monitoring."""
        if self.monitoring_active:
            logger.warning("Security monitoring already active")
            return

        self.monitoring_active = True
        logger.info("Starting governance security monitoring")

        # Start monitoring tasks for different attack types
        monitoring_tasks = []
        for attack_type, interval in self.monitoring_intervals.items():
            task = asyncio.create_task(self._monitor_attack_type(attack_type, interval))
            monitoring_tasks.append(task)

        # Start general pattern monitoring
        monitoring_tasks.append(asyncio.create_task(self._monitor_general_patterns()))

        # Wait for all monitoring tasks
        try:
            await asyncio.gather(*monitoring_tasks)
        except asyncio.CancelledError:
            logger.info("Security monitoring stopped")
        finally:
            self.monitoring_active = False

    async def stop_monitoring(self):
        """Stop security monitoring."""
        self.monitoring_active = False
        logger.info("Stopping governance security monitoring")

    async def _monitor_attack_type(self, attack_type: AttackType, interval: int):
        """Monitor for specific attack type."""
        while self.monitoring_active:
            try:
                if attack_type == AttackType.STAKE_CONCENTRATION:
                    await self._check_stake_concentration_attacks()
                elif attack_type == AttackType.SYBIL_ATTACK:
                    await self._check_sybil_attacks()
                elif attack_type == AttackType.COORDINATED_MANIPULATION:
                    await self._check_coordinated_manipulation()
                elif attack_type == AttackType.RAPID_TAKEOVER:
                    await self._check_rapid_takeover()
                elif attack_type == AttackType.CONSTITUTIONAL_VIOLATION:
                    await self._check_constitutional_violations()
                elif attack_type == AttackType.BYZANTINE_BEHAVIOR:
                    await self._check_byzantine_behavior()
                elif attack_type == AttackType.VOTING_MANIPULATION:
                    await self._check_voting_manipulation()
                elif attack_type == AttackType.PROPOSAL_SPAM:
                    await self._check_proposal_spam()

                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error monitoring {attack_type}: {e}")
                await asyncio.sleep(interval)

    async def _monitor_general_patterns(self):
        """Monitor general suspicious patterns."""
        while self.monitoring_active:
            try:
                # Clean old activity data
                self._clean_old_activity_data()

                # Check for anomalous activity patterns
                await self._check_activity_anomalies()

                # Check system health metrics
                await self._check_system_health()

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in general pattern monitoring: {e}")
                await asyncio.sleep(60)

    async def _check_stake_concentration_attacks(self):
        """Check for stake concentration attacks."""
        stakeholders = governance_engine.stakeholders
        if not stakeholders:
            return

        total_stake = sum(s.stake_amount for s in stakeholders.values())
        if total_stake == 0:
            return

        # Check individual concentrations
        for stakeholder_id, stakeholder in stakeholders.items():
            individual_percentage = stakeholder.stake_amount / total_stake

            if (
                individual_percentage
                >= self.threat_thresholds["stake_concentration_critical"]
            ):
                await self._create_alert(
                    ThreatLevel.CRITICAL,
                    AttackType.STAKE_CONCENTRATION,
                    f"Critical stake concentration: {stakeholder_id} controls {individual_percentage*100:.1f}% of total stake",
                    [stakeholder_id],
                    {
                        "stake_percentage": individual_percentage,
                        "absolute_stake": stakeholder.stake_amount,
                        "total_stake": total_stake,
                        "threshold_exceeded": "critical",
                    },
                )
            elif (
                individual_percentage
                >= self.threat_thresholds["stake_concentration_warning"]
            ):
                await self._create_alert(
                    ThreatLevel.HIGH,
                    AttackType.STAKE_CONCENTRATION,
                    f"High stake concentration: {stakeholder_id} controls {individual_percentage*100:.1f}% of total stake",
                    [stakeholder_id],
                    {
                        "stake_percentage": individual_percentage,
                        "absolute_stake": stakeholder.stake_amount,
                        "total_stake": total_stake,
                        "threshold_exceeded": "warning",
                    },
                )

        # Check coordinated group concentrations
        for group_id, group_members in governance_engine.stake_groups.items():
            group_stake = sum(
                stakeholders[member_id].stake_amount
                for member_id in group_members
                if member_id in stakeholders
            )
            group_percentage = group_stake / total_stake

            if group_percentage >= self.threat_thresholds["coordinated_group_critical"]:
                await self._create_alert(
                    ThreatLevel.EMERGENCY,
                    AttackType.COORDINATED_MANIPULATION,
                    f"Critical coordinated stake concentration: Group {group_id} controls {group_percentage*100:.1f}% of total stake",
                    list(group_members),
                    {
                        "group_id": group_id,
                        "group_stake_percentage": group_percentage,
                        "group_members": list(group_members),
                        "group_size": len(group_members),
                    },
                )

    async def _check_sybil_attacks(self):
        """Check for Sybil attacks and fake accounts."""
        recent_registrations = [
            activity
            for activity in self.activity_windows["registrations"]
            if (datetime.now(timezone.utc) - activity["timestamp"]).total_seconds()
            < 3600
        ]

        if (
            len(recent_registrations)
            > self.threat_thresholds["rapid_registration_threshold"]
        ):
            # Analyze registration patterns
            similar_patterns = self._analyze_registration_patterns(recent_registrations)

            if len(similar_patterns) > 3:
                await self._create_alert(
                    ThreatLevel.HIGH,
                    AttackType.SYBIL_ATTACK,
                    f"Potential Sybil attack: {len(recent_registrations)} registrations in 1 hour with {len(similar_patterns)} similar patterns",
                    [reg["stakeholder_id"] for reg in recent_registrations],
                    {
                        "registration_count": len(recent_registrations),
                        "similar_patterns": len(similar_patterns),
                        "pattern_details": similar_patterns,
                    },
                )

        # Check for identity verification anomalies
        identity_anomalies = self._check_identity_anomalies()
        if identity_anomalies:
            await self._create_alert(
                ThreatLevel.MEDIUM,
                AttackType.IDENTITY_FRAUD,
                f"Identity verification anomalies detected for {len(identity_anomalies)} accounts",
                identity_anomalies,
                {"anomalous_accounts": identity_anomalies},
            )

    async def _check_coordinated_manipulation(self):
        """Check for coordinated manipulation attempts."""
        # Analyze voting patterns for coordination
        coordinated_voters = self._detect_coordinated_voting()

        if len(coordinated_voters) > 5:
            await self._create_alert(
                ThreatLevel.HIGH,
                AttackType.COORDINATED_MANIPULATION,
                f"Coordinated voting detected among {len(coordinated_voters)} accounts",
                coordinated_voters,
                {
                    "coordinated_accounts": coordinated_voters,
                    "coordination_strength": self._calculate_coordination_strength(
                        coordinated_voters
                    ),
                },
            )

        # Check for coordinated proposal submission
        recent_proposals = [
            activity
            for activity in self.activity_windows["proposals"]
            if (datetime.now(timezone.utc) - activity["timestamp"]).total_seconds()
            < 7200
        ]

        if len(recent_proposals) > 5:
            # Check if proposals come from coordinated accounts
            proposer_ids = [p["proposer_id"] for p in recent_proposals]
            if self._are_accounts_coordinated(proposer_ids):
                await self._create_alert(
                    ThreatLevel.HIGH,
                    AttackType.COORDINATED_MANIPULATION,
                    f"Coordinated proposal submission detected from {len(set(proposer_ids))} accounts",
                    proposer_ids,
                    {
                        "proposal_count": len(recent_proposals),
                        "proposer_accounts": list(set(proposer_ids)),
                    },
                )

    async def _check_rapid_takeover(self):
        """Check for rapid governance takeover attempts."""
        # Check for rapid stake accumulation
        recent_stake_changes = [
            activity
            for activity in self.activity_windows["stake_changes"]
            if (datetime.now(timezone.utc) - activity["timestamp"]).total_seconds()
            < 1800  # 30 minutes
        ]

        if recent_stake_changes:
            # Group by stakeholder
            stake_changes_by_user = defaultdict(list)
            for change in recent_stake_changes:
                stake_changes_by_user[change["stakeholder_id"]].append(change)

            for stakeholder_id, changes in stake_changes_by_user.items():
                total_increase = sum(c.get("stake_increase", 0) for c in changes)

                if total_increase > 5000:  # Significant stake increase
                    await self._create_alert(
                        ThreatLevel.HIGH,
                        AttackType.RAPID_TAKEOVER,
                        f"Rapid stake accumulation: {stakeholder_id} increased stake by {total_increase} in 30 minutes",
                        [stakeholder_id],
                        {
                            "stakeholder_id": stakeholder_id,
                            "stake_increase": total_increase,
                            "change_count": len(changes),
                            "time_window_minutes": 30,
                        },
                    )

        # Check for emergency lockdown triggers
        if governance_engine.governance_parameters.get("emergency_lockdown", {}).get(
            "active"
        ):
            lockdown_reason = governance_engine.governance_parameters[
                "emergency_lockdown"
            ]["reason"]
            await self._create_alert(
                ThreatLevel.EMERGENCY,
                AttackType.RAPID_TAKEOVER,
                f"Emergency governance lockdown activated: {lockdown_reason}",
                [],
                governance_engine.governance_parameters["emergency_lockdown"],
            )

    async def _check_constitutional_violations(self):
        """Check for constitutional violations."""
        recent_violations = [
            v
            for v in constitutional_framework.constitutional_violations
            if (datetime.now(timezone.utc) - v["timestamp"]).total_seconds() < 3600
        ]

        for violation in recent_violations:
            threat_level = (
                ThreatLevel.CRITICAL
                if violation["severity"] == "critical"
                else ThreatLevel.HIGH
            )

            await self._create_alert(
                threat_level,
                AttackType.CONSTITUTIONAL_VIOLATION,
                f"Constitutional violation: {violation['violation_reason']}",
                [violation.get("proposer_id", "unknown")],
                violation,
            )

        # Check constitutional integrity
        if not constitutional_framework.verify_constitutional_integrity():
            await self._create_alert(
                ThreatLevel.EMERGENCY,
                AttackType.CONSTITUTIONAL_VIOLATION,
                "Constitutional framework integrity violation detected!",
                [],
                {"integrity_check": "failed"},
            )

    async def _check_byzantine_behavior(self):
        """Check for Byzantine behavior in consensus nodes."""
        if not hasattr(consensus_engine, "nodes"):
            return

        for node_id, node in consensus_engine.nodes.items():
            byzantine_score = consensus_engine.detect_byzantine_behavior(node_id)

            if byzantine_score >= self.threat_thresholds["byzantine_score_critical"]:
                await self._create_alert(
                    ThreatLevel.CRITICAL,
                    AttackType.BYZANTINE_BEHAVIOR,
                    f"Critical Byzantine behavior detected: Node {node_id} (score: {byzantine_score:.2f})",
                    [node_id],
                    {
                        "node_id": node_id,
                        "byzantine_score": byzantine_score,
                        "node_reputation": node.reputation,
                        "node_stake": node.stake,
                    },
                )
            elif byzantine_score >= self.threat_thresholds["byzantine_score_warning"]:
                await self._create_alert(
                    ThreatLevel.HIGH,
                    AttackType.BYZANTINE_BEHAVIOR,
                    f"Byzantine behavior warning: Node {node_id} (score: {byzantine_score:.2f})",
                    [node_id],
                    {
                        "node_id": node_id,
                        "byzantine_score": byzantine_score,
                        "node_reputation": node.reputation,
                        "node_stake": node.stake,
                    },
                )

    async def _check_voting_manipulation(self):
        """Check for voting manipulation."""
        recent_votes = [
            activity
            for activity in self.activity_windows["votes"]
            if (datetime.now(timezone.utc) - activity["timestamp"]).total_seconds()
            < 3600
        ]

        if not recent_votes:
            return

        # Check for unusual voting patterns
        voting_patterns = self._analyze_voting_patterns(recent_votes)

        if (
            voting_patterns["anomaly_score"]
            > self.threat_thresholds["voting_pattern_anomaly"]
        ):
            await self._create_alert(
                ThreatLevel.HIGH,
                AttackType.VOTING_MANIPULATION,
                f"Voting manipulation detected: Anomaly score {voting_patterns['anomaly_score']:.2f}",
                voting_patterns["suspicious_voters"],
                voting_patterns,
            )

    async def _check_proposal_spam(self):
        """Check for proposal spam attacks."""
        recent_proposals = [
            activity
            for activity in self.activity_windows["proposals"]
            if (datetime.now(timezone.utc) - activity["timestamp"]).total_seconds()
            < 3600
        ]

        if len(recent_proposals) > self.threat_thresholds["proposal_spam_threshold"]:
            proposer_counts = defaultdict(int)
            for proposal in recent_proposals:
                proposer_counts[proposal["proposer_id"]] += 1

            spam_proposers = [
                proposer_id
                for proposer_id, count in proposer_counts.items()
                if count > 3  # More than 3 proposals in 1 hour
            ]

            if spam_proposers:
                await self._create_alert(
                    ThreatLevel.MEDIUM,
                    AttackType.PROPOSAL_SPAM,
                    f"Proposal spam detected: {len(spam_proposers)} accounts submitting excessive proposals",
                    spam_proposers,
                    {
                        "total_proposals": len(recent_proposals),
                        "spam_proposers": dict(proposer_counts),
                        "time_window_hours": 1,
                    },
                )

    async def _create_alert(
        self,
        threat_level: ThreatLevel,
        attack_type: AttackType,
        description: str,
        affected_entities: List[str],
        evidence: Dict[str, Any],
    ):
        """Create and process security alert."""
        alert_id = f"alert_{attack_type.value}_{int(datetime.now().timestamp())}"

        alert = SecurityAlert(
            alert_id=alert_id,
            threat_level=threat_level,
            attack_type=attack_type,
            description=description,
            affected_entities=affected_entities,
            evidence=evidence,
        )

        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.alert_stats[attack_type] += 1

        # Log alert
        log_level = {
            ThreatLevel.LOW: logging.INFO,
            ThreatLevel.MEDIUM: logging.WARNING,
            ThreatLevel.HIGH: logging.ERROR,
            ThreatLevel.CRITICAL: logging.CRITICAL,
            ThreatLevel.EMERGENCY: logging.CRITICAL,
        }[threat_level]

        logger.log(
            log_level, f"SECURITY ALERT [{threat_level.value.upper()}]: {description}"
        )

        # Emit audit event
        audit_emitter.emit_security_event(
            f"governance_security_alert_{attack_type.value}",
            {
                "alert_id": alert_id,
                "threat_level": threat_level.value,
                "attack_type": attack_type.value,
                "description": description,
                "affected_entities": affected_entities,
                "evidence": evidence,
                "timestamp": alert.timestamp.isoformat(),
            },
        )

        # Trigger automated responses for critical/emergency threats
        if threat_level in [ThreatLevel.CRITICAL, ThreatLevel.EMERGENCY]:
            await self._trigger_automated_response(alert)

    async def _trigger_automated_response(self, alert: SecurityAlert):
        """Trigger automated response to critical threats."""
        response_actions = []

        if (
            alert.attack_type == AttackType.CONSTITUTIONAL_VIOLATION
            and alert.threat_level == ThreatLevel.EMERGENCY
        ):
            # Activate constitutional emergency
            constitutional_framework.activate_constitutional_emergency(
                f"Automated response to alert {alert.alert_id}", duration_hours=24
            )
            response_actions.append("constitutional_emergency_activated")

        elif alert.attack_type == AttackType.RAPID_TAKEOVER:
            # Activate governance lockdown
            governance_engine.implement_emergency_governance_lockdown(
                f"Automated response to rapid takeover: {alert.description}",
                duration_hours=12,
            )
            response_actions.append("governance_lockdown_activated")

        elif (
            alert.attack_type == AttackType.BYZANTINE_BEHAVIOR
            and alert.threat_level == ThreatLevel.CRITICAL
        ):
            # Apply economic penalties to Byzantine nodes
            for node_id in alert.affected_entities:
                consensus_engine.implement_economic_penalties(
                    node_id,
                    penalty_amount=1000.0,
                    reason=f"Automated penalty for alert {alert.alert_id}",
                )
                response_actions.append(f"penalty_applied_to_{node_id}")

        alert.response_actions = response_actions
        logger.info(
            f"Automated responses triggered for alert {alert.alert_id}: {response_actions}"
        )

    def _analyze_registration_patterns(
        self, registrations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Analyze registration patterns for similarity."""
        patterns = []

        # Group by similar timing
        time_groups = defaultdict(list)
        for reg in registrations:
            time_bucket = int(reg["timestamp"].timestamp() // 300)  # 5-minute buckets
            time_groups[time_bucket].append(reg)

        for time_bucket, group in time_groups.items():
            if len(group) > 3:  # More than 3 registrations in 5 minutes
                patterns.append(
                    {
                        "pattern_type": "temporal_clustering",
                        "time_bucket": time_bucket,
                        "registration_count": len(group),
                        "stakeholder_ids": [r["stakeholder_id"] for r in group],
                    }
                )

        return patterns

    def _check_identity_anomalies(self) -> List[str]:
        """Check for identity verification anomalies."""
        anomalous_accounts = []

        for (
            stakeholder_id,
            verification,
        ) in governance_engine.identity_verifications.items():
            # Check for weak verification scores
            if verification.get("verification_score", 0) < 0.8:
                anomalous_accounts.append(stakeholder_id)

            # Check for suspicious behavioral patterns
            identifiers = verification.get("unique_identifiers", [])
            if len(identifiers) < 2:  # Too few unique identifiers
                anomalous_accounts.append(stakeholder_id)

        return list(set(anomalous_accounts))

    def _detect_coordinated_voting(self) -> List[str]:
        """Detect coordinated voting patterns."""
        coordinated_voters = []

        # Analyze recent votes for correlation
        recent_votes = [
            v
            for v in self.activity_windows["votes"]
            if (datetime.now(timezone.utc) - v["timestamp"]).total_seconds() < 3600
        ]

        # Group votes by proposal
        votes_by_proposal = defaultdict(list)
        for vote in recent_votes:
            votes_by_proposal[vote["proposal_id"]].append(vote)

        # Look for highly correlated voting patterns
        voter_patterns = defaultdict(list)
        for proposal_id, votes in votes_by_proposal.items():
            for vote in votes:
                voter_patterns[vote["voter_id"]].append(
                    {
                        "proposal_id": proposal_id,
                        "vote_type": vote["vote_type"],
                        "timestamp": vote["timestamp"],
                    }
                )

        # Find voters with very similar patterns
        voters = list(voter_patterns.keys())
        for i, voter1 in enumerate(voters):
            for voter2 in voters[i + 1 :]:
                similarity = self._calculate_voting_similarity(
                    voter_patterns[voter1], voter_patterns[voter2]
                )
                if similarity > 0.9:  # Very high similarity
                    coordinated_voters.extend([voter1, voter2])

        return list(set(coordinated_voters))

    def _calculate_voting_similarity(
        self, pattern1: List[Dict], pattern2: List[Dict]
    ) -> float:
        """Calculate similarity between two voting patterns."""
        if not pattern1 or not pattern2:
            return 0.0

        # Find common proposals
        proposals1 = {p["proposal_id"] for p in pattern1}
        proposals2 = {p["proposal_id"] for p in pattern2}
        common_proposals = proposals1.intersection(proposals2)

        if not common_proposals:
            return 0.0

        # Calculate agreement rate on common proposals
        agreements = 0
        for proposal_id in common_proposals:
            vote1 = next(p for p in pattern1 if p["proposal_id"] == proposal_id)
            vote2 = next(p for p in pattern2 if p["proposal_id"] == proposal_id)

            if vote1["vote_type"] == vote2["vote_type"]:
                agreements += 1

        return agreements / len(common_proposals)

    def _are_accounts_coordinated(self, account_ids: List[str]) -> bool:
        """Check if accounts show signs of coordination."""
        if len(account_ids) < 2:
            return False

        # Check registration timing
        registration_times = []
        for account_id in account_ids:
            if account_id in governance_engine.stakeholders:
                registration_times.append(
                    governance_engine.stakeholders[account_id].joined_date
                )

        if len(registration_times) < 2:
            return False

        # Check if registrations are clustered in time
        registration_times.sort()
        max_gap = max(
            (registration_times[i + 1] - registration_times[i]).total_seconds()
            for i in range(len(registration_times) - 1)
        )

        # If all registrations within 2 hours, consider coordinated
        return max_gap < 7200

    def _calculate_coordination_strength(self, account_ids: List[str]) -> float:
        """Calculate coordination strength score."""
        if len(account_ids) < 2:
            return 0.0

        coordination_factors = []

        # Check temporal coordination
        if self._are_accounts_coordinated(account_ids):
            coordination_factors.append(0.4)

        # Check voting coordination
        voting_similarities = []
        for i, account1 in enumerate(account_ids):
            for account2 in account_ids[i + 1 :]:
                if (
                    account1 in governance_engine.voting_power_history
                    and account2 in governance_engine.voting_power_history
                ):
                    # Simplified similarity check
                    similarity = 0.8  # Placeholder
                    voting_similarities.append(similarity)

        if voting_similarities:
            avg_similarity = sum(voting_similarities) / len(voting_similarities)
            coordination_factors.append(avg_similarity * 0.6)

        return sum(coordination_factors)

    def _analyze_voting_patterns(self, votes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze voting patterns for anomalies."""
        if not votes:
            return {"anomaly_score": 0.0, "suspicious_voters": []}

        # Calculate various anomaly indicators
        anomaly_indicators = []

        # Check for identical timing patterns
        timestamps = [v["timestamp"] for v in votes]
        unique_timestamps = len(set(timestamps))
        if unique_timestamps < len(timestamps) * 0.5:  # Too many identical timestamps
            anomaly_indicators.append(0.3)

        # Check for voting power concentration
        vote_powers = [v.get("voting_power", 0) for v in votes]
        if vote_powers:
            max_power = max(vote_powers)
            total_power = sum(vote_powers)
            if max_power / total_power > 0.5:  # One vote dominates
                anomaly_indicators.append(0.4)

        # Check for unusual vote distribution
        vote_types = [v["vote_type"] for v in votes]
        vote_type_counts = defaultdict(int)
        for vote_type in vote_types:
            vote_type_counts[vote_type] += 1

        if len(vote_type_counts) == 1:  # All votes the same type
            anomaly_indicators.append(0.3)

        anomaly_score = sum(anomaly_indicators)

        # Identify suspicious voters
        suspicious_voters = []
        voter_counts = defaultdict(int)
        for vote in votes:
            voter_counts[vote["voter_id"]] += 1

        for voter_id, count in voter_counts.items():
            if count > 5:  # Excessive voting
                suspicious_voters.append(voter_id)

        return {
            "anomaly_score": anomaly_score,
            "suspicious_voters": suspicious_voters,
            "total_votes": len(votes),
            "unique_voters": len(set(v["voter_id"] for v in votes)),
            "anomaly_indicators": anomaly_indicators,
        }

    def _clean_old_activity_data(self):
        """Clean old activity data to prevent memory bloat."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

        for window_name, window_data in self.activity_windows.items():
            # Remove old entries
            while window_data and window_data[0]["timestamp"] < cutoff_time:
                window_data.popleft()

    async def _check_activity_anomalies(self):
        """Check for general activity anomalies."""
        # Check for unusual activity spikes
        current_hour = datetime.now(timezone.utc).replace(
            minute=0, second=0, microsecond=0
        )

        for window_name, window_data in self.activity_windows.items():
            recent_activity = [
                activity
                for activity in window_data
                if activity["timestamp"] >= current_hour
            ]

            if len(recent_activity) > 50:  # Unusual activity spike
                await self._create_alert(
                    ThreatLevel.MEDIUM,
                    AttackType.COORDINATED_MANIPULATION,
                    f"Unusual activity spike: {len(recent_activity)} {window_name} in current hour",
                    [],
                    {
                        "activity_type": window_name,
                        "activity_count": len(recent_activity),
                        "time_window": "1_hour",
                    },
                )

    async def _check_system_health(self):
        """Check overall system health metrics."""
        # Check governance engine health
        if not governance_engine.stakeholders:
            await self._create_alert(
                ThreatLevel.HIGH,
                AttackType.RAPID_TAKEOVER,
                "No stakeholders registered - potential system initialization issue",
                [],
                {"stakeholder_count": 0},
            )

        # Check constitutional framework integrity
        if not constitutional_framework.verify_constitutional_integrity():
            await self._create_alert(
                ThreatLevel.EMERGENCY,
                AttackType.CONSTITUTIONAL_VIOLATION,
                "Constitutional framework integrity check failed",
                [],
                {"integrity_status": "failed"},
            )

    def record_activity(self, activity_type: str, activity_data: Dict[str, Any]):
        """Record activity for monitoring."""
        if activity_type in self.activity_windows:
            activity_data["timestamp"] = datetime.now(timezone.utc)
            self.activity_windows[activity_type].append(activity_data)

    def get_security_status(self) -> Dict[str, Any]:
        """Get current security monitoring status."""
        return {
            "monitoring_active": self.monitoring_active,
            "active_alerts": len(self.active_alerts),
            "total_alerts": len(self.alert_history),
            "alert_stats": dict(self.alert_stats),
            "critical_alerts": len(
                [
                    a
                    for a in self.active_alerts.values()
                    if a.threat_level in [ThreatLevel.CRITICAL, ThreatLevel.EMERGENCY]
                ]
            ),
            "recent_alerts": len(
                [
                    a
                    for a in self.alert_history
                    if (datetime.now(timezone.utc) - a.timestamp).total_seconds() < 3600
                ]
            ),
            "threat_thresholds": self.threat_thresholds,
            "monitoring_intervals": self.monitoring_intervals,
        }

    def acknowledge_alert(self, alert_id: str, acknowledger: str) -> bool:
        """Acknowledge security alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logger.info(f"Alert {alert_id} acknowledged by {acknowledger}")
            return True
        return False

    def resolve_alert(
        self, alert_id: str, resolver: str, resolution_notes: str
    ) -> bool:
        """Resolve security alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_notes = resolution_notes
            del self.active_alerts[alert_id]
            logger.info(f"Alert {alert_id} resolved by {resolver}: {resolution_notes}")
            return True
        return False


# Global security monitor instance
security_monitor = GovernanceSecurityMonitor()
