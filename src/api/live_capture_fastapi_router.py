"""
Live Capture FastAPI Router - Real-time Capsule Generation
Provides endpoints for capturing live AI conversations and generating capsules.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/live", tags=["Live Capture"])


# Pydantic models for request/response
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


class BatchMessagesRequest(BaseModel):
    """Request model for batch message capture."""

    messages: List[ConversationMessage]


class OpenAIConversationRequest(BaseModel):
    """Request model for OpenAI conversations."""

    session_id: Optional[str] = None
    user_id: str = "anonymous"
    messages: List[Dict]
    model: str = "gpt-3.5-turbo"


class ClaudeConversationRequest(BaseModel):
    """Request model for Claude conversations."""

    session_id: Optional[str] = None
    user_id: str = "anonymous"
    user_message: str = ""
    assistant_message: str = ""


# Dependency to get monitor instance
async def get_monitor_instance(request: Request):
    """Dependency to get the conversation monitor from app state."""
    return request.app.state.conversation_monitor


@router.post("/capture/message")
async def capture_message(
    message: ConversationMessage,
    monitor: "LiveConversationMonitor" = Depends(get_monitor_instance),
):
    """Capture a conversation message for real-time monitoring."""
    try:
        # Add message to monitor
        monitor.add_conversation_message(
            session_id=message.session_id,
            user_id=message.user_id,
            platform=message.platform,
            role=message.role,
            content=message.content,
            metadata=message.metadata,
        )

        return {
            "success": True,
            "message": "Message captured successfully",
            "session_id": message.session_id,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/capture/conversation/{session_id}")
async def get_conversation_status(
    session_id: str, monitor: "LiveConversationMonitor" = Depends(get_monitor_instance)
):
    """Get the status of a conversation being monitored."""
    try:
        status = monitor.get_conversation_status(session_id)

        if status is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"success": True, "conversation": status}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capture/conversations")
async def list_active_conversations(
    monitor: "LiveConversationMonitor" = Depends(get_monitor_instance),
):
    """List all active conversations being monitored."""
    try:
        conversations = []

        for session_id in monitor.active_conversations:
            status = monitor.get_conversation_status(session_id)
            if status:
                conversations.append(status)

        return {
            "success": True,
            "conversations": conversations,
            "count": len(conversations),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capture/batch")
async def capture_batch_messages(
    request: BatchMessagesRequest,
    monitor: "LiveConversationMonitor" = Depends(get_monitor_instance),
):
    """Capture multiple messages in a batch for better performance."""
    try:
        results = []

        for message in request.messages:
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

        return {"success": True, "results": results, "processed": len(results)}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/capture/openai")
async def capture_openai_conversation(
    request: OpenAIConversationRequest,
    monitor: "LiveConversationMonitor" = Depends(get_monitor_instance),
):
    """Specialized endpoint for OpenAI conversations."""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or f"openai-{datetime.now().timestamp()}"

        # Add all messages to the conversation
        for message in request.messages:
            monitor.add_conversation_message(
                session_id=session_id,
                user_id=request.user_id,
                platform="openai",
                role=message.get("role", "user"),
                content=message.get("content", ""),
                metadata={
                    "model": request.model,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        # Get conversation status
        status = monitor.get_conversation_status(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "conversation_status": status,
            "messages_processed": len(request.messages),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/capture/claude")
async def capture_claude_conversation(
    request: ClaudeConversationRequest,
    monitor: "LiveConversationMonitor" = Depends(get_monitor_instance),
):
    """Specialized endpoint for Claude conversations."""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or f"claude-{datetime.now().timestamp()}"

        # Add user message
        if request.user_message:
            monitor.add_conversation_message(
                session_id=session_id,
                user_id=request.user_id,
                platform="claude",
                role="user",
                content=request.user_message,
                metadata={
                    "model": "claude-3",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        # Add assistant message
        if request.assistant_message:
            monitor.add_conversation_message(
                session_id=session_id,
                user_id=request.user_id,
                platform="claude",
                role="assistant",
                content=request.assistant_message,
                metadata={
                    "model": "claude-3",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        # Get conversation status
        status = monitor.get_conversation_status(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "conversation_status": status,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/monitor/start")
async def start_monitoring(
    monitor: "LiveConversationMonitor" = Depends(get_monitor_instance),
):
    """Start the live monitoring system."""
    try:
        # Start monitoring in the background
        asyncio.create_task(monitor.start_monitoring())

        return {"success": True, "message": "Live monitoring started"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/status")
async def get_monitoring_status(
    monitor: "LiveConversationMonitor" = Depends(get_monitor_instance),
):
    """Get the current monitoring status."""
    try:
        return {
            "success": True,
            "status": {
                "active_conversations": len(monitor.active_conversations),
                "agent_id": monitor.agent_id,
                "significance_threshold": monitor.significance_threshold,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
