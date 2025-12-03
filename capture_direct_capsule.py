#!/usr/bin/env python3
"""
Directly create a capsule from the current session using the capsule engine.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.engine.capsule_engine import CapsuleEngine
from src.database.connection import DatabaseManager


async def create_session_capsule():
    """Create a capsule directly for this troubleshooting session."""

    print("🎯 Creating capsule for Claude Code troubleshooting session...")

    # Initialize database and engine
    print("📊 Initializing database connection...")
    db_manager = DatabaseManager()
    await db_manager.connect()  # Use connect() instead of initialize()

    print("⚙️  Initializing capsule engine...")
    engine = CapsuleEngine(
        db_manager=db_manager, agent_id="claude-code-session-capture"
    )

    # Prepare conversation data
    session_content = """Claude Code Troubleshooting Session - Demo Mode and Live Capture

    Context: Working on UATP frontend and backend integration

    Key accomplishments:
    1. Fixed Trust Dashboard to only show data in demo mode
    2. Essentialized Creator Mode tab with functional metrics
    3. Investigated live capture system and significance scoring
    4. Started monitoring system for conversation capsule creation

    Technical details:
    - Fixed demo mode data isolation in Trust Dashboard
    - Removed non-functional UI elements from Creator Dashboard
    - Analyzed significance scoring system (threshold: 0.6)
    - Debugged CSRF protection and live capture endpoints
    - Created capture scripts with explicit significance metadata

    Platforms: Claude Code, Frontend (Next.js), Backend (FastAPI/Python)
    """

    reasoning_trace = [
        "Identified issue with Trust Dashboard showing mock data in live mode",
        "Added demo mode checks to all Trust Dashboard queries",
        "Created mock data functions for trust policies, violations, and quarantined agents",
        "Simplified Creator Mode dashboard by removing non-functional elements",
        "Added demo mode toggle integration to Creator Dashboard",
        "Investigated live capture significance scoring system",
        "Found that significance calculation requires background monitoring loop",
        "Created improved capture script with explicit significance metadata",
        "Started monitoring system to enable automatic capsule creation",
    ]

    metadata = {
        "session_type": "troubleshooting",
        "platform": "claude-code",
        "user_id": "kay",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "conversation_length": 12,
        "significance_score": 0.95,
        "auto_selected": False,
        "manually_created": True,
        "topics": [
            "demo_mode_integration",
            "trust_dashboard_fixes",
            "creator_dashboard_simplification",
            "live_capture_system",
            "significance_scoring",
            "capsule_creation",
        ],
        "files_modified": [
            "frontend/src/components/trust/trust-dashboard.tsx",
            "frontend/src/components/creator/creator-dashboard.tsx",
            "frontend/src/lib/mock-data.ts",
            "capture_with_significance.py",
        ],
    }

    print("📝 Creating capsule...")
    try:
        capsule = await engine.create_capsule_async(
            capsule_type="reasoning_trace",
            content=session_content,
            confidence=0.95,
            reasoning_trace=reasoning_trace,
            metadata=metadata,
        )

        print(f"✅ Capsule created successfully!")
        print(f"   Capsule ID: {capsule.capsule_id}")
        print(f"   Type: {capsule.capsule_type}")
        print(f"   Timestamp: {capsule.timestamp}")
        print(f"   Confidence: {capsule.confidence}")

    except Exception as e:
        print(f"❌ Error creating capsule: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await db_manager.close()
        print("\n✨ Done!")


if __name__ == "__main__":
    asyncio.run(create_session_capsule())
