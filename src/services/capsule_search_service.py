"""
Capsule Search Service - Full-text search for capsules.

MAIF-inspired feature providing unified search across SQLite (FTS5) and PostgreSQL (ts_vector).
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import DATABASE_URL

logger = logging.getLogger(__name__)

# Determine database type
IS_SQLITE = "sqlite" in DATABASE_URL.lower()


@dataclass
class SearchHit:
    """A single search result."""

    capsule_id: str
    capsule_type: str
    timestamp: str
    snippet: str
    relevance_score: float
    payload_preview: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "capsule_id": self.capsule_id,
            "capsule_type": self.capsule_type,
            "timestamp": self.timestamp,
            "snippet": self.snippet,
            "relevance_score": self.relevance_score,
            "payload_preview": self.payload_preview,
        }


@dataclass
class SearchResults:
    """Search results with pagination."""

    query: str
    total_count: int
    results: List[SearchHit] = field(default_factory=list)
    page: int = 1
    per_page: int = 10
    has_more: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "total_count": self.total_count,
            "results": [r.to_dict() for r in self.results],
            "page": self.page,
            "per_page": self.per_page,
            "has_more": self.has_more,
            "total_pages": (self.total_count + self.per_page - 1) // self.per_page
            if self.per_page > 0
            else 0,
        }


class CapsuleSearchService:
    """
    Unified search service for capsules.

    Uses FTS5 for SQLite and ts_vector for PostgreSQL.
    """

    async def search(
        self,
        session: AsyncSession,
        query: str,
        page: int = 1,
        per_page: int = 10,
        capsule_type: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> SearchResults:
        """
        Search capsules by text query.

        Args:
            session: Database session
            query: Search query string
            page: Page number (1-indexed)
            per_page: Results per page
            capsule_type: Optional filter by capsule type
            owner_id: Optional filter by owner

        Returns:
            SearchResults with matching capsules
        """
        if IS_SQLITE:
            return await self._search_fts5(
                session, query, page, per_page, capsule_type, owner_id
            )
        else:
            return await self._search_postgresql(
                session, query, page, per_page, capsule_type, owner_id
            )

    async def _search_fts5(
        self,
        session: AsyncSession,
        query: str,
        page: int,
        per_page: int,
        capsule_type: Optional[str],
        owner_id: Optional[str],
    ) -> SearchResults:
        """Search using SQLite FTS5."""
        offset = (page - 1) * per_page

        # Escape special FTS5 characters
        safe_query = self._escape_fts5_query(query)

        # Build WHERE clause for filters
        where_clauses = []
        params = {"query": safe_query, "limit": per_page, "offset": offset}

        if capsule_type:
            where_clauses.append("c.capsule_type = :capsule_type")
            params["capsule_type"] = capsule_type

        if owner_id:
            where_clauses.append("c.owner_id = :owner_id")
            params["owner_id"] = owner_id

        where_sql = ""
        if where_clauses:
            where_sql = "AND " + " AND ".join(where_clauses)

        # Count query
        count_sql = f"""
            SELECT COUNT(*)
            FROM capsules_fts fts
            JOIN capsules c ON c.id = fts.rowid
            WHERE capsules_fts MATCH :query
            {where_sql}
        """

        try:
            count_result = await session.execute(text(count_sql), params)
            total_count = count_result.scalar() or 0
        except Exception as e:
            logger.warning(f"FTS5 count query failed: {e}")
            total_count = 0

        # Search query with snippets
        search_sql = f"""
            SELECT
                c.capsule_id,
                c.capsule_type,
                c.timestamp,
                c.payload,
                snippet(capsules_fts, 1, '<mark>', '</mark>', '...', 32) as snippet,
                bm25(capsules_fts) as score
            FROM capsules_fts fts
            JOIN capsules c ON c.id = fts.rowid
            WHERE capsules_fts MATCH :query
            {where_sql}
            ORDER BY score
            LIMIT :limit OFFSET :offset
        """

        results = []
        try:
            result = await session.execute(text(search_sql), params)
            rows = result.fetchall()

            for row in rows:
                capsule_id, capsule_type, timestamp, payload, snippet, score = row

                # Parse payload for preview
                payload_preview = None
                if payload:
                    try:
                        payload_dict = (
                            json.loads(payload) if isinstance(payload, str) else payload
                        )
                        # Extract key fields for preview
                        payload_preview = {
                            "topics": payload_dict.get("session_metadata", {}).get(
                                "topics", []
                            ),
                            "platform": payload_dict.get("session_metadata", {}).get(
                                "platform"
                            ),
                        }
                    except (json.JSONDecodeError, TypeError):
                        pass

                # Format timestamp
                ts_str = (
                    timestamp.isoformat()
                    if hasattr(timestamp, "isoformat")
                    else str(timestamp)
                )

                results.append(
                    SearchHit(
                        capsule_id=capsule_id,
                        capsule_type=capsule_type,
                        timestamp=ts_str,
                        snippet=snippet or "",
                        relevance_score=abs(score) if score else 0.0,
                        payload_preview=payload_preview,
                    )
                )

        except Exception as e:
            logger.error(f"FTS5 search failed: {e}")
            # Return empty results on error
            return SearchResults(
                query=query,
                total_count=0,
                results=[],
                page=page,
                per_page=per_page,
                has_more=False,
            )

        return SearchResults(
            query=query,
            total_count=total_count,
            results=results,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total_count,
        )

    async def _search_postgresql(
        self,
        session: AsyncSession,
        query: str,
        page: int,
        per_page: int,
        capsule_type: Optional[str],
        owner_id: Optional[str],
    ) -> SearchResults:
        """Search using PostgreSQL ts_vector."""
        offset = (page - 1) * per_page

        # Build WHERE clause
        where_clauses = [
            "to_tsvector('english', payload::text) @@ plainto_tsquery(:query)"
        ]
        params = {"query": query, "limit": per_page, "offset": offset}

        if capsule_type:
            where_clauses.append("capsule_type = :capsule_type")
            params["capsule_type"] = capsule_type

        if owner_id:
            where_clauses.append("owner_id = :owner_id")
            params["owner_id"] = owner_id

        where_sql = " AND ".join(where_clauses)

        # Count query
        count_sql = f"SELECT COUNT(*) FROM capsules WHERE {where_sql}"

        try:
            count_result = await session.execute(text(count_sql), params)
            total_count = count_result.scalar() or 0
        except Exception as e:
            logger.warning(f"PostgreSQL count query failed: {e}")
            total_count = 0

        # Search query with ranking
        search_sql = f"""
            SELECT
                capsule_id,
                capsule_type,
                timestamp,
                payload,
                ts_headline('english', payload::text, plainto_tsquery(:query),
                    'MaxWords=35, MinWords=15, StartSel=<mark>, StopSel=</mark>') as snippet,
                ts_rank(to_tsvector('english', payload::text), plainto_tsquery(:query)) as score
            FROM capsules
            WHERE {where_sql}
            ORDER BY score DESC
            LIMIT :limit OFFSET :offset
        """

        results = []
        try:
            result = await session.execute(text(search_sql), params)
            rows = result.fetchall()

            for row in rows:
                capsule_id, capsule_type, timestamp, payload, snippet, score = row

                # Parse payload for preview
                payload_preview = None
                if payload:
                    try:
                        payload_dict = (
                            json.loads(payload) if isinstance(payload, str) else payload
                        )
                        payload_preview = {
                            "topics": payload_dict.get("session_metadata", {}).get(
                                "topics", []
                            ),
                            "platform": payload_dict.get("session_metadata", {}).get(
                                "platform"
                            ),
                        }
                    except (json.JSONDecodeError, TypeError):
                        pass

                ts_str = (
                    timestamp.isoformat()
                    if hasattr(timestamp, "isoformat")
                    else str(timestamp)
                )

                results.append(
                    SearchHit(
                        capsule_id=capsule_id,
                        capsule_type=capsule_type,
                        timestamp=ts_str,
                        snippet=snippet or "",
                        relevance_score=float(score) if score else 0.0,
                        payload_preview=payload_preview,
                    )
                )

        except Exception as e:
            logger.error(f"PostgreSQL search failed: {e}")
            return SearchResults(
                query=query,
                total_count=0,
                results=[],
                page=page,
                per_page=per_page,
                has_more=False,
            )

        return SearchResults(
            query=query,
            total_count=total_count,
            results=results,
            page=page,
            per_page=per_page,
            has_more=(page * per_page) < total_count,
        )

    def _escape_fts5_query(self, query: str) -> str:
        """
        Escape special characters for FTS5 query.

        FTS5 uses these as operators: AND OR NOT () " *
        """
        import re

        # For simple queries, just wrap in quotes to treat as phrase
        # Remove any existing quotes first
        clean_query = query.replace('"', "")

        # Check for FTS5 operators as whole words (not substrings like "WORLD" containing "OR")
        has_operators = bool(re.search(r"\b(AND|OR|NOT)\b", clean_query, re.IGNORECASE))

        # If query has multiple words and no operators, wrap in quotes
        if " " in clean_query and not has_operators:
            return f'"{clean_query}"'

        return clean_query


# Global singleton
_search_service: Optional[CapsuleSearchService] = None


def get_search_service() -> CapsuleSearchService:
    """Get the capsule search service singleton."""
    global _search_service
    if _search_service is None:
        _search_service = CapsuleSearchService()
    return _search_service
