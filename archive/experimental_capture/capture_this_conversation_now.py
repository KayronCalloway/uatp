#!/usr/bin/env python3
"""
Capture this Claude Code conversation as a real capsule in the database.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from src.capsule_schema import (
    CapsuleStatus,
    ReasoningStep,
    ReasoningTraceCapsule,
    ReasoningTracePayload,
    Verification,
)
from src.core.database import db
from src.engine.capsule_engine import CapsuleEngine


async def capture_current_conversation():
    """Capture the current conversation as a real capsule."""

    # Initialize database
    class MockApp:
        pass

    app = MockApp()
    db.init_app(app)
    await db.create_all()

    # Create engine
    engine = CapsuleEngine(db_manager=db, agent_id="claude-sonnet-4")

    # Create a reasoning trace for this conversation
    capsule = ReasoningTraceCapsule(
        capsule_id=f"caps_{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.SEALED,
        verification=Verification(),
        reasoning_trace=ReasoningTracePayload(
            steps=[
                ReasoningStep(
                    content="User reported issue: database showing empty results despite valid capsules",
                    step_type="observation",
                    confidence=1.0,
                    metadata={"source": "user_report"},
                ),
                ReasoningStep(
                    content="Investigated CapsuleEngine to understand data source - found it uses database-backed storage",
                    step_type="analysis",
                    confidence=0.95,
                    metadata={"file": "src/engine/capsule_engine.py"},
                ),
                ReasoningStep(
                    content="Discovered database only contains 5 demo capsules (all IDs start with 'demo-')",
                    step_type="analysis",
                    confidence=1.0,
                    metadata={"database": "uatp_dev.db", "demo_count": 5},
                ),
                ReasoningStep(
                    content="Found frontend already has demo mode toggle functionality built-in",
                    step_type="discovery",
                    confidence=1.0,
                    metadata={
                        "components": ["demo-mode-context.tsx", "demo-mode-toggle.tsx"],
                        "feature": "Demo/Live mode switching",
                    },
                ),
                ReasoningStep(
                    content="User wants to see real auto-captured data, not demo data. Demo data should be toggleable.",
                    step_type="conclusion",
                    confidence=1.0,
                    metadata={"user_preference": "live_data_by_default"},
                ),
            ],
            context={
                "session_type": "claude_code_troubleshooting",
                "issue": "database_integration",
                "resolution": "demo_mode_filtering_and_live_capture",
            },
            conclusion="Successfully identified that system needs: (1) API filtering for demo capsules, (2) Real auto-captured conversation data",
        ),
    )

    # Create capsule through engine
    created_capsule = await engine.create_capsule_async(capsule)

    print(f"✅ Captured conversation as capsule: {created_capsule.capsule_id}")
    print(f"   Type: {created_capsule.capsule_type}")
    print(f"   Status: {created_capsule.status}")
    print(f"   Steps: {len(created_capsule.reasoning_trace.steps)}")

    return created_capsule


if __name__ == "__main__":
    asyncio.run(capture_current_conversation())
