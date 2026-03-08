#!/usr/bin/env python3
"""
UATP Capsule REST API
=====================

This module provides REST API endpoints for capsule CRUD operations,
search, filtering, and real-time streaming.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

from quart import Quart, jsonify, request, websocket
from quart_cors import cors

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text

from src.core.database import db
from src.filters.sqlite_capsule_creator import (
    initialize_sqlite_capsule_creator,
)

logger = logging.getLogger(__name__)

# Initialize Quart app
app = Quart(__name__)
app.config["PROVIDE_AUTOMATIC_OPTIONS"] = True
app = cors(app)

# Global capsule creator instance
capsule_creator = None


async def init_capsule_api():
    """Initialize the capsule API with database connection."""
    global capsule_creator

    try:
        capsule_creator = await initialize_sqlite_capsule_creator()
        logger.info(" Capsule API initialized successfully")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize capsule API: {e}")
        return False


@app.route("/api/capsules", methods=["GET"])
async def get_capsules():
    """Get capsules with pagination and filtering."""

    try:
        # Parse query parameters
        page = int(request.args.get("page", 1))
        limit = min(int(request.args.get("limit", 20)), 100)  # Max 100 per page
        platform = request.args.get("platform")
        user_id = request.args.get("user_id")
        min_significance = request.args.get("min_significance", type=float)
        max_significance = request.args.get("max_significance", type=float)
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        search = request.args.get("search")

        offset = (page - 1) * limit

        # Build query
        query_parts = []
        params = {}

        base_query = """
            SELECT c.capsule_id, c.capsule_type, c.timestamp, c.payload, c.verification,
                   a.platform, a.significance_score, a.user_id, a.conversation_id, a.metadata
            FROM capsules_filter c
            JOIN attributions_filter a ON c.capsule_id = a.capsule_id
        """

        # Add filters
        if platform:
            query_parts.append("a.platform = :platform")
            params["platform"] = platform

        if user_id:
            query_parts.append("a.user_id = :user_id")
            params["user_id"] = user_id

        if min_significance is not None:
            query_parts.append("a.significance_score >= :min_significance")
            params["min_significance"] = min_significance

        if max_significance is not None:
            query_parts.append("a.significance_score <= :max_significance")
            params["max_significance"] = max_significance

        if start_date:
            query_parts.append("c.timestamp >= :start_date")
            params["start_date"] = start_date

        if end_date:
            query_parts.append("c.timestamp <= :end_date")
            params["end_date"] = end_date

        if search:
            query_parts.append("(c.payload LIKE :search OR a.metadata LIKE :search)")
            params["search"] = f"%{search}%"

        # Combine query parts
        where_clause = ""
        if query_parts:
            where_clause = "WHERE " + " AND ".join(query_parts)

        final_query = f"{base_query} {where_clause} ORDER BY c.timestamp DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        # Execute query
        async with db.get_session() as session:
            result = await session.execute(text(final_query), params)
            rows = result.fetchall()

            # Get total count
            count_query = f"SELECT COUNT(*) FROM capsules_filter c JOIN attributions_filter a ON c.capsule_id = a.capsule_id {where_clause}"
            count_result = await session.execute(
                text(count_query),
                {k: v for k, v in params.items() if k not in ["limit", "offset"]},
            )
            total_count = count_result.scalar()

        # Format response
        capsules = []
        for row in rows:
            payload = json.loads(row[3]) if row[3] else {}
            metadata = json.loads(row[9]) if row[9] else {}

            capsule = {
                "capsule_id": row[0],
                "type": row[1],
                "timestamp": row[2],
                "platform": row[5],
                "significance_score": row[6],
                "user_id": row[7],
                "conversation_id": row[8],
                "payload": payload,
                "metadata": metadata,
            }
            capsules.append(capsule)

        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit

        return jsonify(
            {
                "capsules": capsules,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1,
                },
                "filters": {
                    "platform": platform,
                    "user_id": user_id,
                    "min_significance": min_significance,
                    "max_significance": max_significance,
                    "start_date": start_date,
                    "end_date": end_date,
                    "search": search,
                },
            }
        )

    except Exception as e:
        logger.error(f"[ERROR] Error getting capsules: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/capsules/<capsule_id>", methods=["GET"])
async def get_capsule(capsule_id: str):
    """Get a specific capsule by ID."""

    try:
        async with db.get_session() as session:
            result = await session.execute(
                text(
                    """
                SELECT c.capsule_id, c.capsule_type, c.version, c.timestamp, c.status,
                       c.verification, c.payload, a.platform, a.significance_score,
                       a.user_id, a.conversation_id, a.metadata
                FROM capsules_filter c
                JOIN attributions_filter a ON c.capsule_id = a.capsule_id
                WHERE c.capsule_id = :capsule_id
            """
                ),
                {"capsule_id": capsule_id},
            )

            row = result.fetchone()

            if not row:
                return jsonify({"error": "Capsule not found"}), 404

            payload = json.loads(row[6]) if row[6] else {}
            verification = json.loads(row[5]) if row[5] else {}
            metadata = json.loads(row[11]) if row[11] else {}

            capsule = {
                "capsule_id": row[0],
                "type": row[1],
                "version": row[2],
                "timestamp": row[3],
                "status": row[4],
                "verification": verification,
                "payload": payload,
                "platform": row[7],
                "significance_score": row[8],
                "user_id": row[9],
                "conversation_id": row[10],
                "metadata": metadata,
            }

            return jsonify(capsule)

    except Exception as e:
        logger.error(f"[ERROR] Error getting capsule {capsule_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/capsules/search", methods=["POST"])
async def search_capsules():
    """Advanced capsule search with complex filters."""

    try:
        data = await request.get_json()

        # Parse search parameters
        query = data.get("query", "")
        filters = data.get("filters", {})
        sort_by = data.get("sort_by", "timestamp")
        sort_order = data.get("sort_order", "desc")
        page = data.get("page", 1)
        limit = min(data.get("limit", 20), 100)

        offset = (page - 1) * limit

        # Build advanced search query
        query_parts = []
        params = {}

        base_query = """
            SELECT c.capsule_id, c.capsule_type, c.timestamp, c.payload,
                   a.platform, a.significance_score, a.user_id, a.conversation_id, a.metadata
            FROM capsules_filter c
            JOIN attributions_filter a ON c.capsule_id = a.capsule_id
        """

        # Text search
        if query:
            query_parts.append(
                """
                (c.payload LIKE :query OR a.metadata LIKE :query OR c.capsule_id LIKE :query)
            """
            )
            params["query"] = f"%{query}%"

        # Advanced filters
        if filters.get("platforms"):
            placeholders = ", ".join(
                [f":platform_{i}" for i in range(len(filters["platforms"]))]
            )
            query_parts.append(f"a.platform IN ({placeholders})")
            for i, platform in enumerate(filters["platforms"]):
                params[f"platform_{i}"] = platform

        if filters.get("significance_range"):
            if filters["significance_range"].get("min") is not None:
                query_parts.append("a.significance_score >= :min_significance")
                params["min_significance"] = filters["significance_range"]["min"]
            if filters["significance_range"].get("max") is not None:
                query_parts.append("a.significance_score <= :max_significance")
                params["max_significance"] = filters["significance_range"]["max"]

        if filters.get("date_range"):
            if filters["date_range"].get("start"):
                query_parts.append("c.timestamp >= :start_date")
                params["start_date"] = filters["date_range"]["start"]
            if filters["date_range"].get("end"):
                query_parts.append("c.timestamp <= :end_date")
                params["end_date"] = filters["date_range"]["end"]

        if filters.get("user_ids"):
            placeholders = ", ".join(
                [f":user_{i}" for i in range(len(filters["user_ids"]))]
            )
            query_parts.append(f"a.user_id IN ({placeholders})")
            for i, user_id in enumerate(filters["user_ids"]):
                params[f"user_{i}"] = user_id

        if filters.get("capsule_types"):
            placeholders = ", ".join(
                [f":type_{i}" for i in range(len(filters["capsule_types"]))]
            )
            query_parts.append(f"c.capsule_type IN ({placeholders})")
            for i, capsule_type in enumerate(filters["capsule_types"]):
                params[f"type_{i}"] = capsule_type

        # Combine query parts
        where_clause = ""
        if query_parts:
            where_clause = "WHERE " + " AND ".join(query_parts)

        # Sort clause
        sort_column = {
            "timestamp": "c.timestamp",
            "significance": "a.significance_score",
            "platform": "a.platform",
            "user_id": "a.user_id",
        }.get(sort_by, "c.timestamp")

        sort_direction = "ASC" if sort_order.lower() == "asc" else "DESC"
        order_clause = f"ORDER BY {sort_column} {sort_direction}"

        final_query = (
            f"{base_query} {where_clause} {order_clause} LIMIT :limit OFFSET :offset"
        )
        params["limit"] = limit
        params["offset"] = offset

        # Execute search
        async with db.get_session() as session:
            result = await session.execute(text(final_query), params)
            rows = result.fetchall()

            # Get total count
            count_query = f"SELECT COUNT(*) FROM capsules_filter c JOIN attributions_filter a ON c.capsule_id = a.capsule_id {where_clause}"
            count_result = await session.execute(
                text(count_query),
                {k: v for k, v in params.items() if k not in ["limit", "offset"]},
            )
            total_count = count_result.scalar()

        # Format response
        capsules = []
        for row in rows:
            payload = json.loads(row[3]) if row[3] else {}
            metadata = json.loads(row[8]) if row[8] else {}

            capsule = {
                "capsule_id": row[0],
                "type": row[1],
                "timestamp": row[2],
                "platform": row[4],
                "significance_score": row[5],
                "user_id": row[6],
                "conversation_id": row[7],
                "payload": payload,
                "metadata": metadata,
            }
            capsules.append(capsule)

        total_pages = (total_count + limit - 1) // limit

        return jsonify(
            {
                "capsules": capsules,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1,
                },
                "search_params": {
                    "query": query,
                    "filters": filters,
                    "sort_by": sort_by,
                    "sort_order": sort_order,
                },
            }
        )

    except Exception as e:
        logger.error(f"[ERROR] Error searching capsules: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/capsules/stats", methods=["GET"])
async def get_capsule_stats():
    """Get capsule statistics and analytics."""

    try:
        stats = await capsule_creator.get_capsule_stats()

        # Additional analytics
        async with db.get_session() as session:
            # Platform distribution
            platform_result = await session.execute(
                text(
                    """
                SELECT platform, COUNT(*) as count, AVG(significance_score) as avg_significance
                FROM attributions_filter
                GROUP BY platform
                ORDER BY count DESC
            """
                )
            )

            platforms = {}
            for row in platform_result.fetchall():
                platforms[row[0]] = {
                    "count": row[1],
                    "avg_significance": round(row[2], 2),
                }

            # Daily activity
            daily_result = await session.execute(
                text(
                    """
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM capsules_filter
                WHERE timestamp >= DATE('now', '-30 days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """
                )
            )

            daily_activity = []
            for row in daily_result.fetchall():
                daily_activity.append({"date": row[0], "count": row[1]})

            # Top users
            user_result = await session.execute(
                text(
                    """
                SELECT user_id, COUNT(*) as count, AVG(significance_score) as avg_significance
                FROM attributions_filter
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT 10
            """
                )
            )

            top_users = []
            for row in user_result.fetchall():
                top_users.append(
                    {
                        "user_id": row[0],
                        "count": row[1],
                        "avg_significance": round(row[2], 2),
                    }
                )

        return jsonify(
            {
                "basic_stats": stats,
                "analytics": {
                    "platforms": platforms,
                    "daily_activity": daily_activity,
                    "top_users": top_users,
                },
            }
        )

    except Exception as e:
        logger.error(f"[ERROR] Error getting capsule stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/capsules/recent", methods=["GET"])
async def get_recent_capsules():
    """Get recent capsules with optional limit."""

    try:
        limit = min(int(request.args.get("limit", 10)), 50)

        recent_capsules = await capsule_creator.get_recent_capsules(limit)

        return jsonify({"capsules": recent_capsules, "count": len(recent_capsules)})

    except Exception as e:
        logger.error(f"[ERROR] Error getting recent capsules: {e}")
        return jsonify({"error": str(e)}), 500


@app.websocket("/api/capsules/stream")
async def capsule_stream():
    """WebSocket endpoint for real-time capsule updates."""

    logger.info(" New WebSocket connection for capsule stream")

    try:
        # Send initial connection message
        await websocket.send(
            json.dumps(
                {
                    "type": "connection",
                    "message": "Connected to UATP capsule stream",
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

        # Send recent capsules
        recent_capsules = await capsule_creator.get_recent_capsules(5)
        await websocket.send(
            json.dumps(
                {
                    "type": "recent_capsules",
                    "capsules": recent_capsules,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

        # Keep connection alive and send updates
        while True:
            # In a real implementation, you would listen for database changes
            # For now, we'll send a heartbeat every 30 seconds
            await asyncio.sleep(30)

            await websocket.send(
                json.dumps(
                    {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
                )
            )

    except Exception as e:
        logger.error(f"[ERROR] WebSocket error: {e}")
        await websocket.send(
            json.dumps(
                {
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )


@app.route("/api/health", methods=["GET"])
async def health_check():
    """Health check endpoint."""

    try:
        # Check database connection
        db_healthy = capsule_creator and capsule_creator._db_connected

        # Check recent activity
        recent_capsules = (
            await capsule_creator.get_recent_capsules(1) if db_healthy else []
        )

        health_status = {
            "status": "healthy" if db_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "connected": db_healthy,
                "recent_activity": len(recent_capsules) > 0,
            },
            "api": {"version": "1.0.0", "uptime": "unknown"},  # You could track this
        }

        status_code = 200 if db_healthy else 503
        return jsonify(health_status), status_code

    except Exception as e:
        logger.error(f"[ERROR] Health check error: {e}")
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            503,
        )


# Error handlers
@app.errorhandler(404)
async def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(405)
async def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
async def internal_error(error):
    logger.error(f"[ERROR] Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Initialize the API
    async def startup():
        await init_capsule_api()

    # Run the startup function
    asyncio.run(startup())

    # Run the app
    app.run(host="0.0.0.0", port=8000, debug=True)
