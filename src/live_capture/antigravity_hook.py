#!/usr/bin/env python3
"""
Antigravity (Google Gemini) Live Capture Integration
=====================================================

This module provides integration with Google's Antigravity (Gemini) for live
conversation capture and automatic capsule generation.

Matches the detail level of Claude Code capture including:
- Individual message capture (user/assistant)
- Session tracking with timestamps
- Significance analysis
- Rich metadata (confidence, uncertainty, topics)
- Automatic capsule creation

Refactored to use BaseHook for reduced duplication.

Usage:
    python antigravity_hook.py

    # Or programmatically:
    from src.live_capture.antigravity_hook import capture_antigravity_interaction
    await capture_antigravity_interaction(user_input, assistant_response)
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.live_capture.base_hook import BaseHook

logger = logging.getLogger(__name__)


class AntigravityLiveCapture(BaseHook):
    """Live capture integration for Google's Antigravity (Gemini)."""

    def __init__(
        self,
        user_id: str = "kay",
        session_id: Optional[str] = None,
        model: str = "gemini-2.5-pro",
    ):
        self.model = model

        # Conversation buffer for significance analysis
        self.conversation_buffer: List[Dict[str, Any]] = []
        self.auto_capture_enabled = True
        self.significance_threshold = 0.6

        # Artifact tracking
        self.artifacts_created: List[str] = []
        self.tool_calls_made: List[Dict[str, Any]] = []

        # Antigravity-specific paths
        self.antigravity_home = Path.home() / ".gemini" / "antigravity"
        self.brain_dir = self.antigravity_home / "brain"
        self.conversations_dir = self.antigravity_home / "conversations"

        super().__init__(platform="google_antigravity", user_id=user_id, session_id=session_id)

    def get_platform_emoji(self) -> str:
        return "✨"

    def get_platform_specific_metadata(self, **kwargs) -> Dict[str, Any]:
        """Get Antigravity-specific metadata."""
        return {
            "antigravity_version": "1.0",
            "api_provider": "google",
            "gemini_model": self.model,
            "workspace_context": kwargs.get("workspace_context"),
            "open_files": kwargs.get("open_files"),
            "artifacts_created": kwargs.get("artifacts_created", []),
            "tool_calls": kwargs.get("tool_calls", []),
            "total_artifacts_in_session": len(self.artifacts_created),
            "total_tool_calls_in_session": len(self.tool_calls_made),
            "task_status": kwargs.get("task_status"),
            "task_mode": kwargs.get("task_mode"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "conversation_turn": len(self.conversation_buffer) + 1,
        }

    def _log_platform_specific_init(self) -> None:
        """Log Antigravity-specific initialization."""
        logger.info(f"   Model: {self.model}")

    def _log_platform_specific_success(self, capsule_id: str, **kwargs) -> None:
        """Log Antigravity-specific success info."""
        task_mode = kwargs.get("task_mode")
        artifacts = kwargs.get("artifacts_created", [])
        tool_calls = kwargs.get("tool_calls", [])

        if task_mode:
            logger.info(f"   Mode: {task_mode}")
        if artifacts:
            logger.info(f"   Artifacts: {len(artifacts)}")
        if tool_calls:
            logger.info(f"   Tool calls: {len(tool_calls)}")

    # Convenience methods for Antigravity-specific interactions

    async def capture_antigravity_interaction(
        self,
        user_input: str,
        assistant_response: str,
        interaction_type: str = "agentic_coding",
        workspace_context: Optional[str] = None,
        open_files: Optional[List[str]] = None,
        artifacts_created: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        task_status: Optional[str] = None,
        task_mode: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Capture an Antigravity interaction and create capsule if significant.

        Thin wrapper around BaseHook.capture_interaction with Antigravity-specific tracking.
        """
        # Track artifacts and tool calls
        if artifacts_created:
            self.artifacts_created.extend(artifacts_created)
        if tool_calls:
            self.tool_calls_made.extend(tool_calls)

        # Add to conversation buffer
        self.conversation_buffer.append(
            {
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {"source": "antigravity"},
            }
        )
        self.conversation_buffer.append(
            {
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "interaction_type": interaction_type,
                    "task_status": task_status,
                    "task_mode": task_mode,
                },
            }
        )

        return await self.capture_interaction(
            user_input=user_input,
            assistant_response=assistant_response,
            model=self.model,
            interaction_type=interaction_type,
            workspace_context=workspace_context,
            open_files=open_files,
            artifacts_created=artifacts_created,
            tool_calls=tool_calls,
            task_status=task_status,
            task_mode=task_mode,
            **kwargs,
        )

    async def capture_planning_session(
        self,
        user_input: str,
        planning_response: str,
        implementation_plan: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture a planning session interaction."""
        return await self.capture_antigravity_interaction(
            user_input=user_input,
            assistant_response=planning_response,
            interaction_type="planning",
            task_mode="PLANNING",
            artifacts_created=["implementation_plan.md"]
            if implementation_plan
            else None,
            **kwargs,
        )

    async def capture_execution_session(
        self,
        user_input: str,
        execution_response: str,
        files_modified: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict]] = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture an execution session interaction."""
        return await self.capture_antigravity_interaction(
            user_input=user_input,
            assistant_response=execution_response,
            interaction_type="execution",
            task_mode="EXECUTION",
            tool_calls=tool_calls,
            files_modified=files_modified,
            **kwargs,
        )

    async def capture_verification_session(
        self,
        user_input: str,
        verification_response: str,
        test_results: Optional[Dict] = None,
        walkthrough_created: bool = False,
        **kwargs,
    ) -> Optional[str]:
        """Capture a verification session interaction."""
        artifacts = ["walkthrough.md"] if walkthrough_created else None
        return await self.capture_antigravity_interaction(
            user_input=user_input,
            assistant_response=verification_response,
            interaction_type="verification",
            task_mode="VERIFICATION",
            artifacts_created=artifacts,
            test_results=test_results,
            **kwargs,
        )

    async def capture_artifact_creation(
        self,
        artifact_type: str,
        artifact_path: str,
        artifact_content: str,
        related_conversation: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture artifact creation event."""
        user_msg = f"Creating {artifact_type} artifact"
        assistant_msg = (
            f"Created {artifact_type} at {artifact_path}: {artifact_content[:500]}..."
        )

        return await self.capture_antigravity_interaction(
            user_input=user_msg,
            assistant_response=assistant_msg,
            interaction_type="artifact_creation",
            artifacts_created=[artifact_path],
            artifact_type=artifact_type,
            **kwargs,
        )

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for the current session."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "platform": self.platform,
            "model": self.model,
            "conversation_turns": len(self.conversation_buffer) // 2,
            "total_messages": len(self.conversation_buffer),
            "artifacts_created": len(self.artifacts_created),
            "tool_calls_made": len(self.tool_calls_made),
            "auto_capture_enabled": self.auto_capture_enabled,
        }

    def get_conversation_buffer(self) -> List[Dict[str, Any]]:
        """Get the current conversation buffer."""
        return self.conversation_buffer.copy()

    def clear_conversation_buffer(self):
        """Clear the conversation buffer after capsule creation."""
        self.conversation_buffer = []
        logger.info("🧹 Conversation buffer cleared")


# Global instance for easy access
_antigravity_capture: Optional[AntigravityLiveCapture] = None


def get_antigravity_capture(
    user_id: str = "kay",
    session_id: Optional[str] = None,
    model: str = "gemini-2.5-pro",
) -> AntigravityLiveCapture:
    """Get the global Antigravity capture instance."""
    global _antigravity_capture
    if _antigravity_capture is None:
        _antigravity_capture = AntigravityLiveCapture(user_id, session_id, model)
    return _antigravity_capture


async def capture_antigravity_interaction(
    user_input: str,
    assistant_response: str,
    interaction_type: str = "agentic_coding",
    workspace_context: Optional[str] = None,
    open_files: Optional[List[str]] = None,
    artifacts_created: Optional[List[str]] = None,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    task_status: Optional[str] = None,
    task_mode: Optional[str] = None,
    user_id: str = "kay",
    session_id: Optional[str] = None,
    model: str = "gemini-2.5-pro",
    **kwargs,
) -> Optional[str]:
    """
    Convenience function to capture Antigravity interactions.

    Args:
        user_input: User's message to Gemini
        assistant_response: Gemini's response
        interaction_type: Type of interaction
        workspace_context: Current workspace context
        open_files: Currently open files
        artifacts_created: Artifacts created
        tool_calls: Tool calls made
        task_status: Current task status
        task_mode: Current mode
        user_id: User identifier
        session_id: Session identifier
        model: Gemini model used
        **kwargs: Additional metadata

    Returns:
        Capsule ID if created, None if not significant
    """
    capture = get_antigravity_capture(user_id, session_id, model)
    return await capture.capture_antigravity_interaction(
        user_input=user_input,
        assistant_response=assistant_response,
        interaction_type=interaction_type,
        workspace_context=workspace_context,
        open_files=open_files,
        artifacts_created=artifacts_created,
        tool_calls=tool_calls,
        task_status=task_status,
        task_mode=task_mode,
        **kwargs,
    )


async def main():
    """Test the Antigravity integration."""

    print("✨ Testing Antigravity Live Capture Integration (with BaseHook)")
    print("=" * 60)

    # Test agentic coding interaction
    print("\n🔧 Testing agentic coding capture...")
    agentic_capsule = await capture_antigravity_interaction(
        user_input="Help me capture Antigravity conversations for UATP at the same detail level as Claude Code",
        assistant_response="""I'll create a comprehensive capture system for Antigravity/Gemini conversations
        that matches your Claude Code capture detail level. This includes:
        - Individual message capture with timestamps
        - Session tracking
        - Significance analysis
        - Rich metadata (confidence, uncertainty, topics)
        - Automatic capsule creation
        - Artifact correlation (task.md, walkthrough.md)""",
        interaction_type="agentic_coding",
        workspace_context="/Users/kay/uatp-capsule-engine",
        open_files=["src/live_capture/antigravity_hook.py"],
        task_mode="EXECUTION",
        task_status="Creating antigravity_hook.py",
        user_id="kay",
        model="gemini-2.5-pro",
    )

    if agentic_capsule:
        print(f"✅ Agentic coding interaction captured: {agentic_capsule}")
    else:
        print("❌ No capsule created - interaction not significant enough")

    # Test planning session
    print("\n📝 Testing planning session capture...")
    planning_capsule = await capture_antigravity_interaction(
        user_input="What's the implementation plan for this feature?",
        assistant_response="""Here's the implementation plan:
        1. Create antigravity_hook.py with AntigravityLiveCapture class
        2. Integrate with RealTimeCapsuleGenerator
        3. Add artifact correlation
        4. Apply RichCaptureEnhancer for metadata
        5. Test with current conversation""",
        interaction_type="planning",
        task_mode="PLANNING",
        artifacts_created=["implementation_plan.md"],
        user_id="kay",
    )

    if planning_capsule:
        print(f"✅ Planning session captured: {planning_capsule}")
    else:
        print("❌ No capsule created")

    # Show session stats
    capture = get_antigravity_capture()
    stats = capture.get_session_stats()
    print("\n📊 Session Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n✅ Antigravity integration test completed (with BaseHook refactoring)!")


if __name__ == "__main__":
    asyncio.run(main())
