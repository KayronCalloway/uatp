"""Mirror Mode – Self-auditing agent skeleton.

This module provides a lightweight **MirrorAgent** that can asynchronously
re-evaluate capsules after creation using the same policy engine (EthicsCircuitBreaker)
that guards real-time generation.  The initial implementation is intentionally
minimal – it only performs a probabilistic audit and logs any discrepancies.

Future iterations will:
* Replay full reasoning traces with different sampling windows.
* Persist refusal capsules when violations are detected.
* Record compute/latency metrics for optimisation.
"""

from __future__ import annotations

import asyncio
import os
import random
from typing import Optional

import structlog

from src.audit.events import audit_emitter

logger = structlog.get_logger(__name__)


class MirrorAgent:
    """Probabilistic self-auditing mirror agent."""

    def __init__(
        self,
        *,
        sample_rate: float = 0.1,
        strict_mode: bool = False,
        policy_engine=None,
        capsule_engine=None,
    ) -> None:
        if not 0 <= sample_rate <= 1:
            raise ValueError("sample_rate must be between 0 and 1")
        self.sample_rate = sample_rate
        self.strict_mode = strict_mode
        self._policy_engine = (
            policy_engine  # Injected dependency (e.g., EthicsCircuitBreaker)
        )
        self._capsule_engine = capsule_engine

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def maybe_audit_capsule(self, capsule) -> None:  # noqa: ANN001 – generic capsule
        """Audit *capsule* with probability *sample_rate* in the background."""
        # Skip audits entirely during test runs or when sample_rate dictates
        if os.getenv("PYTEST_CURRENT_TEST") or random.random() > self.sample_rate:
            return  # Skip audit

        # Run actual audit in a fire-and-forget task so it doesn't block.
        asyncio.create_task(self._run_audit(capsule))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _run_audit(self, capsule):  # noqa: ANN001 – generic capsule
        try:
            # Simple re-run of ethics check for now.
            if self._policy_engine is None or self._capsule_engine is None:
                logger.warning(
                    "MirrorAgent missing dependencies; skipping audit persistence"
                )
                return

            allowed, refusal = await self._policy_engine.pre_creation_check(capsule)

            import uuid
            from datetime import datetime, timezone

            from src.capsule_schema import (
                AuditCapsule,
                CapsuleStatus,
                RefusalCapsule,
                UTCDateTime,
                Verification,
            )

            timestamp = datetime.now(timezone.utc)
            if allowed:
                # Construct and persist AuditCapsule
                audit_capsule = AuditCapsule(
                    capsule_id=f"caps_{timestamp:%Y_%m_%d}_{uuid.uuid4().hex[:16]}",
                    timestamp=timestamp,
                    status=CapsuleStatus.ACTIVE,
                    verification=Verification(),
                    audit={
                        "audited_capsule_id": capsule.capsule_id,
                        "audit_score": 1.0,
                        "violations": [],
                    },
                )
                await self._capsule_engine.create_capsule_async(audit_capsule)
            else:
                # Construct and persist RefusalCapsule
                refusal_capsule = RefusalCapsule(
                    capsule_id=f"caps_{timestamp:%Y_%m_%d}_{uuid.uuid4().hex[:16]}",
                    timestamp=timestamp,
                    status=CapsuleStatus.ACTIVE,
                    verification=Verification(),
                    refusal={
                        "refused_capsule_id": capsule.capsule_id,
                        "explanation": refusal.explanation,
                        "violations": [v.violation_code for v in refusal.violations]
                        if hasattr(refusal, "violations")
                        else [],
                    },
                )
                await self._capsule_engine.create_capsule_async(refusal_capsule)

                if self.strict_mode:
                    # Trigger quarantine / revocation flow.
                    await self._capsule_engine.quarantine_capsule_async(
                        capsule.capsule_id,
                        reason=f"Mirror Mode Audit Failed: {refusal.explanation}",
                    )
        except Exception as exc:  # pragma: no cover – audit failures non-fatal
            logger.error(
                "MirrorMode audit failed", capsule_id=capsule.capsule_id, error=str(exc)
            )


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_agent: Optional[MirrorAgent] = None


def get_mirror_agent(*, policy_engine=None, capsule_engine=None) -> MirrorAgent:  # noqa: D401
    """Return global **MirrorAgent** instance configured via environment vars."""
    global _agent  # noqa: PLW0603 – global singleton by design
    if _agent is None:
        sample_rate = float(os.getenv("UATP_MIRROR_SAMPLE_RATE", "0.1"))
        # Disable audits during test runs for isolation
        if os.getenv("PYTEST_CURRENT_TEST"):
            sample_rate = 0.0
        strict = os.getenv("UATP_MIRROR_STRICT_MODE", "false").lower() == "true"
        _agent = MirrorAgent(
            sample_rate=sample_rate,
            strict_mode=strict,
            policy_engine=policy_engine,
            capsule_engine=capsule_engine,
        )
    return _agent
