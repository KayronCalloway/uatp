"""
Test Live Capture Integration

Quick test to verify that the live capture system creates capsules
with all the rich metadata (uncertainty, critical path, trust score, etc.)
"""

import asyncio
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

sys.path.append(str(Path(__file__).parent))

from src.live_capture.rich_capture_integration import RichCaptureEnhancer


@dataclass
class Message:
    """Mock message for testing"""

    role: str
    content: str
    timestamp: datetime
    token_count: int = 100
    model_info: Optional[str] = None


@dataclass
class MockSession:
    """Mock Claude Code session for testing"""

    session_id: str
    platform: str = "claude-code"
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    messages: List[Message] = field(default_factory=list)
    total_tokens: int = 0
    topics: List[str] = field(default_factory=lambda: ["testing"])
    significance_score: float = 0.8


async def test_live_capture_integration():
    """Test that live capture creates capsules with full rich metadata"""

    print("=" * 70)
    print("  TESTING LIVE CAPTURE INTEGRATION")
    print("=" * 70)

    # Create a mock conversation session
    session = MockSession(
        session_id="test_session_123",
        topics=["performance optimization", "database queries"],
    )

    # Add some messages
    session.messages = [
        Message(
            role="user",
            content="How can I optimize my database queries?",
            timestamp=datetime.now(timezone.utc),
            token_count=50,
        ),
        Message(
            role="assistant",
            content="To optimize database queries, consider: 1) Add indexes, 2) Use caching, 3) Avoid N+1 queries",
            timestamp=datetime.now(timezone.utc),
            token_count=150,
        ),
    ]

    session.total_tokens = sum(m.token_count for m in session.messages)
    session.end_time = datetime.now(timezone.utc)

    print(
        f"\nMock Session: {len(session.messages)} messages, {session.total_tokens} tokens"
    )

    # Create capsule
    capsule = RichCaptureEnhancer.create_capsule_from_session_with_rich_metadata(
        session=session, user_id="test_user"
    )

    print(f"\n✅ Capsule Created: {capsule['capsule_id']}")

    # Check metadata
    payload = capsule["payload"]
    verification = capsule["verification"]

    print("\n🎯 Rich Metadata Check:")
    print(
        f"   {'✓' if 'trust_score' in verification else '✗'} Trust Score: {verification.get('trust_score', 'MISSING')}"
    )
    print(
        f"   {'✓' if 'uncertainty_analysis' in payload else '✗'} Uncertainty Analysis"
    )
    print(
        f"   {'✓' if 'critical_path_analysis' in payload else '✗'} Critical Path Analysis"
    )
    print(
        f"   {'✓' if 'improvement_recommendations' in payload else '✗'} Improvement Recommendations"
    )

    all_present = all(
        [
            "trust_score" in verification,
            "uncertainty_analysis" in payload,
            "critical_path_analysis" in payload,
            "improvement_recommendations" in payload,
        ]
    )

    print(f"\n{'✅ TEST PASSED' if all_present else '⚠️ TEST PARTIAL'}")
    return all_present


if __name__ == "__main__":
    success = asyncio.run(test_live_capture_integration())
    sys.exit(0 if success else 1)
