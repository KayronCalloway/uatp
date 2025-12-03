"""
Live capture API routes for real-time capsule generation.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional

from quart import Blueprint, jsonify, request, current_app
from pydantic import BaseModel

from .dependencies import require_api_key
from ..live_capture.conversation_monitor import get_monitor


# Create blueprint
live_capture_bp = Blueprint("live_capture", __name__, url_prefix="/api/v1/live")


class ConversationMessage(BaseModel):
    """Model for conversation messages."""

    session_id: str
    user_id: str
    platform: str
    role: str  # 'user' or 'assistant'
    content: str
    metadata: Optional[Dict] = None


class ConversationStatus(BaseModel):
    """Model for conversation status."""

    session_id: str
    user_id: str
    platform: str
    message_count: int
    significance_score: float
    should_create_capsule: bool
    last_activity: str


@live_capture_bp.route("/capture/message", methods=["POST", "OPTIONS"])
async def capture_message():
    """Capture a conversation message for real-time monitoring."""
    try:
        data = await request.get_json()
        message = ConversationMessage(**data)

        # Add message to monitor
        db_manager = (
            current_app.engine.db_manager if hasattr(current_app, "engine") else None
        )
        monitor = get_monitor(db_manager)
        monitor.add_conversation_message(
            session_id=message.session_id,
            user_id=message.user_id,
            platform=message.platform,
            role=message.role,
            content=message.content,
            metadata=message.metadata,
        )

        return jsonify(
            {
                "success": True,
                "message": "Message captured successfully",
                "session_id": message.session_id,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@live_capture_bp.route("/capture/conversation/<session_id>", methods=["GET", "OPTIONS"])
async def get_conversation_status(session_id: str):
    """Get the status of a conversation being monitored."""
    try:
        db_manager = (
            current_app.engine.db_manager if hasattr(current_app, "engine") else None
        )
        monitor = get_monitor(db_manager)
        status = monitor.get_conversation_status(session_id)

        if status is None:
            return jsonify({"success": False, "error": "Conversation not found"}), 404

        return jsonify({"success": True, "conversation": status})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@live_capture_bp.route("/capture/conversations", methods=["GET", "OPTIONS"])
async def list_active_conversations():
    """List all active conversations being monitored."""
    try:
        db_manager = (
            current_app.engine.db_manager if hasattr(current_app, "engine") else None
        )
        monitor = get_monitor(db_manager)
        conversations = []

        for session_id in monitor.active_conversations:
            status = monitor.get_conversation_status(session_id)
            if status:
                conversations.append(status)

        return jsonify(
            {
                "success": True,
                "conversations": conversations,
                "count": len(conversations),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@live_capture_bp.route("/capture/batch", methods=["POST"])
async def capture_batch_messages():
    """Capture multiple messages in a batch for better performance."""
    try:
        data = await request.get_json()
        messages = [ConversationMessage(**msg) for msg in data.get("messages", [])]

        db_manager = (
            current_app.engine.db_manager if hasattr(current_app, "engine") else None
        )
        monitor = get_monitor(db_manager)
        results = []

        for message in messages:
            try:
                monitor.add_conversation_message(
                    session_id=message.session_id,
                    user_id=message.user_id,
                    platform=message.platform,
                    role=message.role,
                    content=message.content,
                    metadata=message.metadata,
                )
                results.append({"session_id": message.session_id, "success": True})
            except Exception as e:
                results.append(
                    {
                        "session_id": message.session_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        return jsonify({"success": True, "results": results, "processed": len(results)})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@live_capture_bp.route("/capture/openai", methods=["POST"])
async def capture_openai_conversation():
    """Specialized endpoint for OpenAI conversations."""
    try:
        data = await request.get_json()

        # Extract OpenAI-specific data
        session_id = data.get("session_id", f"openai-{datetime.now().timestamp()}")
        user_id = data.get("user_id", "anonymous")
        messages = data.get("messages", [])
        model = data.get("model", "gpt-3.5-turbo")

        db_manager = (
            current_app.engine.db_manager if hasattr(current_app, "engine") else None
        )
        monitor = get_monitor(db_manager)

        # Add all messages to the conversation
        for message in messages:
            monitor.add_conversation_message(
                session_id=session_id,
                user_id=user_id,
                platform="openai",
                role=message.get("role", "user"),
                content=message.get("content", ""),
                metadata={
                    "model": model,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        # Get conversation status
        status = monitor.get_conversation_status(session_id)

        return jsonify(
            {
                "success": True,
                "session_id": session_id,
                "conversation_status": status,
                "messages_processed": len(messages),
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@live_capture_bp.route("/capture/claude", methods=["POST"])
async def capture_claude_conversation():
    """Specialized endpoint for Claude conversations."""
    try:
        data = await request.get_json()

        # Extract Claude-specific data
        session_id = data.get("session_id", f"claude-{datetime.now().timestamp()}")
        user_id = data.get("user_id", "anonymous")
        user_message = data.get("user_message", "")
        assistant_message = data.get("assistant_message", "")

        db_manager = (
            current_app.engine.db_manager if hasattr(current_app, "engine") else None
        )
        monitor = get_monitor(db_manager)

        # Add user message
        if user_message:
            monitor.add_conversation_message(
                session_id=session_id,
                user_id=user_id,
                platform="claude",
                role="user",
                content=user_message,
                metadata={
                    "model": "claude-3",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        # Add assistant message
        if assistant_message:
            monitor.add_conversation_message(
                session_id=session_id,
                user_id=user_id,
                platform="claude",
                role="assistant",
                content=assistant_message,
                metadata={
                    "model": "claude-3",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        # Get conversation status
        status = monitor.get_conversation_status(session_id)

        return jsonify(
            {"success": True, "session_id": session_id, "conversation_status": status}
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@live_capture_bp.route("/monitor/start", methods=["POST", "OPTIONS"])
@require_api_key(["write"])
async def start_monitoring():
    """Start the live monitoring system."""
    try:
        db_manager = (
            current_app.engine.db_manager if hasattr(current_app, "engine") else None
        )
        monitor = get_monitor(db_manager)

        # Start monitoring in the background
        asyncio.create_task(monitor.start_monitoring())

        return jsonify({"success": True, "message": "Live monitoring started"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@live_capture_bp.route("/monitor/status", methods=["GET", "OPTIONS"])
@require_api_key(["read"])
async def get_monitoring_status():
    """Get the current monitoring status."""
    try:
        db_manager = (
            current_app.engine.db_manager if hasattr(current_app, "engine") else None
        )
        monitor = get_monitor(db_manager)

        return jsonify(
            {
                "success": True,
                "status": {
                    "active_conversations": len(monitor.active_conversations),
                    "agent_id": monitor.agent_id,
                    "significance_threshold": monitor.significance_threshold,
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
