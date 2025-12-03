"""
Cursor IDE Integration API Routes
Provides endpoints for capturing development workflows from Cursor IDE
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from quart import Blueprint, request, jsonify, g
from quart_schema import validate_json, validate_querystring

from src.integrations.cursor_ide_capture import (
    cursor_capture_system,
    start_cursor_capture_session,
    capture_cursor_ai_interaction,
    capture_cursor_code_change,
    end_cursor_capture_session,
)

logger = logging.getLogger(__name__)

cursor_bp = Blueprint("cursor", __name__)


@cursor_bp.route("/cursor/sessions/start", methods=["POST"])
@validate_json(
    {
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "project_path": {"type": "string"},
            "metadata": {"type": "object"},
        },
        "required": ["user_id", "project_path"],
    }
)
async def start_cursor_session():
    """Start a new Cursor IDE development session."""
    try:
        data = await request.get_json()
        user_id = data["user_id"]
        project_path = data["project_path"]
        metadata = data.get("metadata", {})

        session_id = await start_cursor_capture_session(user_id, project_path)

        logger.info(
            f"Started Cursor IDE session: {session_id} for project: {project_path}"
        )

        return (
            jsonify(
                {
                    "success": True,
                    "session_id": session_id,
                    "user_id": user_id,
                    "project_path": project_path,
                    "start_time": datetime.now().isoformat(),
                    "message": "Cursor IDE development session started successfully",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to start Cursor session: {e}")
        return (
            jsonify({"success": False, "error": f"Failed to start session: {str(e)}"}),
            500,
        )


@cursor_bp.route("/cursor/ai-interaction", methods=["POST"])
@validate_json(
    {
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "user_query": {"type": "string"},
            "ai_response": {"type": "string"},
            "context": {"type": "object"},
        },
        "required": ["session_id", "user_query", "ai_response"],
    }
)
async def capture_ai_interaction():
    """Capture AI interaction in Cursor IDE."""
    try:
        data = await request.get_json()
        session_id = data["session_id"]
        user_query = data["user_query"]
        ai_response = data["ai_response"]
        context = data.get("context", {})

        event_id = await capture_cursor_ai_interaction(
            session_id, user_query, ai_response, context
        )

        if event_id:
            logger.info(f"Captured AI interaction in Cursor session: {session_id}")
            return (
                jsonify(
                    {
                        "success": True,
                        "event_id": event_id,
                        "session_id": session_id,
                        "message": "AI interaction captured successfully",
                    }
                ),
                200,
            )
        else:
            return jsonify({"success": False, "error": "Session not found"}), 404

    except Exception as e:
        logger.error(f"Failed to capture AI interaction: {e}")
        return (
            jsonify(
                {"success": False, "error": f"Failed to capture interaction: {str(e)}"}
            ),
            500,
        )


@cursor_bp.route("/cursor/code-change", methods=["POST"])
@validate_json(
    {
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "file_path": {"type": "string"},
            "change_type": {"type": "string"},
            "content": {"type": "string"},
            "metadata": {"type": "object"},
        },
        "required": ["session_id", "file_path", "change_type", "content"],
    }
)
async def capture_code_change():
    """Capture code changes in Cursor IDE."""
    try:
        data = await request.get_json()
        session_id = data["session_id"]
        file_path = data["file_path"]
        change_type = data["change_type"]
        content = data["content"]
        metadata = data.get("metadata", {})

        event_id = await capture_cursor_code_change(
            session_id, file_path, change_type, content, metadata
        )

        if event_id:
            logger.info(f"Captured code change in Cursor session: {session_id}")
            return (
                jsonify(
                    {
                        "success": True,
                        "event_id": event_id,
                        "session_id": session_id,
                        "file_path": file_path,
                        "change_type": change_type,
                        "message": "Code change captured successfully",
                    }
                ),
                200,
            )
        else:
            return jsonify({"success": False, "error": "Session not found"}), 404

    except Exception as e:
        logger.error(f"Failed to capture code change: {e}")
        return (
            jsonify({"success": False, "error": f"Failed to capture change: {str(e)}"}),
            500,
        )


@cursor_bp.route("/cursor/sessions/<session_id>/end", methods=["POST"])
async def end_cursor_session(session_id: str):
    """End a Cursor IDE development session and potentially create a capsule."""
    try:
        capsule_id = await end_cursor_capture_session(session_id)

        response_data = {
            "success": True,
            "session_id": session_id,
            "end_time": datetime.now().isoformat(),
            "message": "Cursor IDE session ended successfully",
        }

        if capsule_id:
            response_data["capsule_created"] = True
            response_data["capsule_id"] = capsule_id
            logger.info(f"Cursor session {session_id} ended with capsule: {capsule_id}")
        else:
            response_data["capsule_created"] = False
            response_data[
                "reason"
            ] = "Session didn't meet significance threshold for capsule creation"
            logger.info(f"Cursor session {session_id} ended without capsule creation")

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Failed to end Cursor session: {e}")
        return (
            jsonify({"success": False, "error": f"Failed to end session: {str(e)}"}),
            500,
        )


@cursor_bp.route("/cursor/sessions/active", methods=["GET"])
async def get_active_cursor_sessions():
    """Get all currently active Cursor IDE sessions."""
    try:
        sessions = await cursor_capture_system.get_active_cursor_sessions()

        return (
            jsonify(
                {
                    "success": True,
                    "active_sessions": len(sessions),
                    "sessions": sessions,
                    "message": f"Retrieved {len(sessions)} active Cursor IDE sessions",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get active Cursor sessions: {e}")
        return (
            jsonify({"success": False, "error": f"Failed to get sessions: {str(e)}"}),
            500,
        )


@cursor_bp.route("/cursor/sessions/<session_id>", methods=["GET"])
async def get_cursor_session_details(session_id: str):
    """Get details about a specific Cursor IDE session."""
    try:
        if session_id in cursor_capture_system.active_sessions:
            session = cursor_capture_system.active_sessions[session_id]

            return (
                jsonify(
                    {
                        "success": True,
                        "session_id": session_id,
                        "session_details": {
                            "user_id": session.user_id,
                            "project_path": session.project_path,
                            "start_time": session.start_time.isoformat(),
                            "end_time": session.end_time.isoformat()
                            if session.end_time
                            else None,
                            "event_count": len(session.events),
                            "ai_interaction_count": len(session.ai_interactions),
                            "files_modified_count": len(session.files_modified),
                            "files_modified": session.files_modified,
                            "significance_score": await cursor_capture_system.calculate_session_significance(
                                session
                            ),
                            "should_create_capsule": await cursor_capture_system.should_create_capsule(
                                session
                            ),
                            "capsule_created": session.capsule_created,
                        },
                        "message": "Session details retrieved successfully",
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {"success": False, "error": "Session not found or no longer active"}
                ),
                404,
            )

    except Exception as e:
        logger.error(f"Failed to get Cursor session details: {e}")
        return (
            jsonify(
                {"success": False, "error": f"Failed to get session details: {str(e)}"}
            ),
            500,
        )


@cursor_bp.route("/cursor/stats", methods=["GET"])
async def get_cursor_capture_stats():
    """Get overall statistics for Cursor IDE capture system."""
    try:
        active_sessions = await cursor_capture_system.get_active_cursor_sessions()

        stats = {
            "active_sessions": len(active_sessions),
            "total_active_events": sum(
                s.get("event_count", 0) for s in active_sessions
            ),
            "total_ai_interactions": sum(
                s.get("ai_interaction_count", 0) for s in active_sessions
            ),
            "total_files_modified": sum(
                s.get("files_modified_count", 0) for s in active_sessions
            ),
            "avg_significance_score": (
                sum(s.get("significance_score", 0) for s in active_sessions)
                / len(active_sessions)
                if active_sessions
                else 0
            ),
            "eligible_for_capsules": sum(
                1 for s in active_sessions if s.get("should_create_capsule", False)
            ),
            "platform": "cursor-ide",
            "status": "active" if active_sessions else "idle",
        }

        return (
            jsonify(
                {
                    "success": True,
                    "stats": stats,
                    "message": "Cursor IDE capture statistics retrieved successfully",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get Cursor capture stats: {e}")
        return (
            jsonify({"success": False, "error": f"Failed to get stats: {str(e)}"}),
            500,
        )
