"""
Onboarding FastAPI Router for UATP Capsule Engine.

Provides endpoints for onboarding new users and platforms to the system.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth_middleware import get_current_user

router = APIRouter(prefix="/onboarding/api", tags=["Onboarding"])


# Pydantic models
class Platform(BaseModel):
    """Platform model."""

    id: str
    name: str
    status: str
    connected: bool
    last_sync: Optional[str]
    capsules_count: int


class OnboardingStatus(BaseModel):
    """Onboarding status model."""

    user_id: str
    status: str  # 'not_started', 'in_progress', 'completed'
    steps_completed: List[str]
    current_step: Optional[str]
    platforms_connected: int
    created_at: str


@router.get("/health")
async def onboarding_health():
    """Get onboarding system health status."""
    return {
        "status": "healthy",
        "onboarding_enabled": True,
        "available_platforms": ["openai", "anthropic", "claude", "cursor", "windsurf"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/platforms")
async def get_platforms():
    """Get list of available AI platforms for integration."""
    # Mock data for now - will be replaced with real platform status
    platforms = [
        {
            "id": "openai",
            "name": "OpenAI",
            "status": "available",
            "connected": True,
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "capsules_count": 25,
        },
        {
            "id": "anthropic",
            "name": "Anthropic Claude",
            "status": "available",
            "connected": True,
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "capsules_count": 18,
        },
        {
            "id": "cursor",
            "name": "Cursor AI",
            "status": "available",
            "connected": False,
            "last_sync": None,
            "capsules_count": 0,
        },
        {
            "id": "windsurf",
            "name": "Windsurf",
            "status": "available",
            "connected": False,
            "last_sync": None,
            "capsules_count": 0,
        },
        {
            "id": "claude-code",
            "name": "Claude Code",
            "status": "available",
            "connected": True,
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "capsules_count": 0,
        },
    ]

    return {
        "platforms": platforms,
        "total": len(platforms),
        "connected": len([p for p in platforms if p["connected"]]),
    }


@router.get("/status/{user_id}")
async def get_onboarding_status(
    user_id: str, current_user: dict = Depends(get_current_user)
):
    """Get onboarding status for a specific user."""
    if str(current_user.get("sub", current_user.get("user_id"))) != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this user's onboarding status",
        )
    # Mock data for now - will be replaced with real user onboarding status
    # In production, this would query the database for user's onboarding progress

    return {
        "user_id": user_id,
        "status": "in_progress",
        "steps_completed": ["account_created", "email_verified", "profile_completed"],
        "current_step": "connect_platforms",
        "total_steps": 5,
        "completed_steps": 3,
        "platforms_connected": 2,
        "onboarding_progress": 60,
        "created_at": "2025-01-01T00:00:00Z",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "next_action": {
            "step": "connect_platforms",
            "title": "Connect AI Platforms",
            "description": "Connect your AI platforms to start capturing conversations",
            "action_url": "/platforms",
        },
    }


@router.post("/start/{user_id}")
async def start_onboarding(
    user_id: str, current_user: dict = Depends(get_current_user)
):
    """Start the onboarding process for a user."""
    if str(current_user.get("sub", current_user.get("user_id"))) != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to start onboarding for this user"
        )
    return {
        "success": True,
        "user_id": user_id,
        "status": "started",
        "message": "Onboarding process initiated",
        "next_step": "profile_setup",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/complete-step/{user_id}/{step}")
async def complete_onboarding_step(
    user_id: str, step: str, current_user: dict = Depends(get_current_user)
):
    """Mark an onboarding step as completed."""
    if str(current_user.get("sub", current_user.get("user_id"))) != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to modify this user's onboarding status",
        )
    valid_steps = [
        "account_created",
        "email_verified",
        "profile_completed",
        "connect_platforms",
        "first_capsule",
    ]

    if step not in valid_steps:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid step: {step}. Must be one of: {', '.join(valid_steps)}",
        )

    return {
        "success": True,
        "user_id": user_id,
        "step_completed": step,
        "message": f"Step '{step}' marked as completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/connect-platform/{user_id}/{platform_id}")
async def connect_platform(
    user_id: str, platform_id: str, current_user: dict = Depends(get_current_user)
):
    """Connect a platform for a user."""
    if str(current_user.get("sub", current_user.get("user_id"))) != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to connect platforms for this user"
        )
    valid_platforms = [
        "openai",
        "anthropic",
        "claude",
        "cursor",
        "windsurf",
        "claude-code",
    ]

    if platform_id not in valid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform: {platform_id}. Must be one of: {', '.join(valid_platforms)}",
        )

    return {
        "success": True,
        "user_id": user_id,
        "platform_id": platform_id,
        "status": "connected",
        "message": f"Platform '{platform_id}' connected successfully",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
