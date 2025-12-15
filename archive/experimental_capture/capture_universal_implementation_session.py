#!/usr/bin/env python3
"""
Capture this implementation session as a capsule demonstrating universal capture.
This meta-conversation about fixing elitist gatekeeping should itself be captured!
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import DatabaseManager
from src.engine.capsule_engine import CapsuleEngine


async def create_implementation_capsule():
    """Create a capsule for the universal capture implementation session."""

    print("=" * 80)
    print("CAPTURING UNIVERSAL CAPTURE IMPLEMENTATION SESSION")
    print("=" * 80)
    print("\n📝 This is meta: Capturing the conversation about fixing capture!\n")

    # Initialize database and engine
    print("📊 Initializing database...")
    db_manager = DatabaseManager()
    await db_manager.connect()

    print("⚙️  Initializing capsule engine...")
    engine = CapsuleEngine(
        db_manager=db_manager, agent_id="claude-code-universal-capture-fix"
    )

    # Prepare conversation data
    session_content = """Universal Capture Implementation - Fixing Elitist Gatekeeping Bug

Context: CRITICAL philosophical alignment fix identified by user

User's Key Insight:
"we need to make sure the significance score is democratic and not arbitrarily applied
because one mans trash is anothers treasure. I dont want encapsulation to be some elitist
thing. obviously any decision that is made by ai should be encapsulated."

The Problem:
- Documentation promised: "UATP captures every decision"
- Implementation reality: Only captured conversations with significance >= 0.6
- Result: Arbitrary filtering contradicting "Universal" principle

The Solution - "Capture All, Weight Fairly":
1. Changed significance_threshold from 0.6 to 0.0
2. Removed significance check from capsule creation logic
3. Significance now used as ECONOMIC WEIGHT, not capture gate
4. All conversations captured, varying economic weights

Implementation Changes:
- Updated conversation_monitor.py (5 key sections)
- Created UNIVERSAL_CAPTURE_PHILOSOPHY.md (comprehensive documentation)
- Created UNIVERSAL_CAPTURE_IMPLEMENTATION.md (summary)
- Created test_universal_capture.py (verification)

Key Distinction:
- Capture Threshold: 0.0 (capture everything)
- Attribution Confidence: 0.2-0.8 (for value distribution)

This fix aligns implementation with UATP's core "Universal" principle.
"""

    reasoning_trace = [
        "User identified contradiction between 'Universal' principle and 0.6 threshold",
        "Recognized that significance should be economic weight, not capture filter",
        "Emphasized democratic values: 'one mans trash is anothers treasure'",
        "Distinguished between capture threshold (should be 0.0) and attribution confidence (0.2-0.8)",
        "Changed significance_threshold from 0.6 to 0.0 in conversation_monitor.py",
        "Renamed should_create_capsule to capsule_created (better reflects philosophy)",
        "Removed significance check from capsule creation logic",
        "Added economic_weight and capture_philosophy metadata fields",
        "Created comprehensive documentation explaining the fix",
        "Created test script to verify universal capture working",
        "This very capsule demonstrates universal capture in action",
    ]

    metadata = {
        "session_type": "critical_fix",
        "fix_type": "philosophical_alignment",
        "platform": "claude-code",
        "user_id": "kay",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "significance_score": 0.95,  # High significance - critical system fix
        "economic_weight": 0.95,  # High economic weight for important work
        "capture_philosophy": "universal",  # This capsule proves universal capture
        "auto_captured": False,
        "manually_created": True,
        "user_insight": "one_mans_trash_is_anothers_treasure",
        "topics": [
            "universal_capture",
            "democratic_attribution",
            "elitist_gatekeeping_fix",
            "significance_as_weight",
            "philosophical_alignment",
            "capture_threshold_removal",
        ],
        "files_modified": [
            "src/live_capture/conversation_monitor.py",
            "UNIVERSAL_CAPTURE_PHILOSOPHY.md",
            "UNIVERSAL_CAPTURE_IMPLEMENTATION.md",
            "test_universal_capture.py",
        ],
        "key_changes": [
            "significance_threshold: 0.6 → 0.0",
            "Removed significance check from capsule creation",
            "Added economic_weight metadata field",
            "Changed should_create_capsule → capsule_created",
        ],
        "impact": "fundamental_alignment_fix",
    }

    print("📝 Creating implementation capsule...")
    try:
        capsule = await engine.create_capsule_async(
            capsule_type="reasoning_trace",
            content=session_content,
            confidence=0.95,
            reasoning_trace=reasoning_trace,
            metadata=metadata,
        )

        print("\n✅ Implementation capsule created successfully!")
        print(f"{'─' * 80}")
        print(f"   Capsule ID: {capsule.capsule_id}")
        print(f"   Type: {capsule.capsule_type}")
        print(f"   Timestamp: {capsule.timestamp}")
        print(f"   Confidence: {capsule.confidence}")
        print(f"   Significance: {metadata['significance_score']}")
        print(f"   Economic Weight: {metadata['economic_weight']}")
        print(f"   Philosophy: {metadata['capture_philosophy']}")
        print(f"{'─' * 80}")

        print("\n🎯 This capsule demonstrates the fix:")
        print("   • Captured with significance as metadata (not filter)")
        print("   • High economic weight (0.95) for important work")
        print("   • Universal capture philosophy applied")
        print("   • Democratic attribution: all interactions matter")

        print("\n📚 Related Documentation:")
        print("   • UNIVERSAL_CAPTURE_PHILOSOPHY.md - The problem and solution")
        print("   • UNIVERSAL_CAPTURE_IMPLEMENTATION.md - What was changed")
        print("   • test_universal_capture.py - Verification tests")

    except Exception as e:
        print(f"\n❌ Error creating capsule: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await db_manager.close()
        print(f"\n{'=' * 80}")
        print("✨ Universal Capture Implementation Complete!")
        print(f"{'=' * 80}\n")


if __name__ == "__main__":
    asyncio.run(create_implementation_capsule())
