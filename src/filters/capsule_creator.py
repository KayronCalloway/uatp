"""
Lightweight Capsule Creator for Universal Filter
================================================

This module provides a simplified capsule creation system that works with
the JSONL file format, integrating with the universal filter system.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FilterCapsuleCreator:
    """
    Lightweight capsule creator that writes directly to the JSONL chain file.
    Designed specifically for the universal filter system.
    """

    def __init__(self, chain_file: str = "capsule_chain.jsonl"):
        # Set up the chain file path
        if not os.path.isabs(chain_file):
            # If relative path, use project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.chain_file = os.path.join(project_root, chain_file)
        else:
            self.chain_file = chain_file

        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.chain_file), exist_ok=True)

        logger.info(
            f"🔗 FilterCapsuleCreator initialized with chain file: {self.chain_file}"
        )

    async def create_capsule_from_filter_result(
        self,
        filter_result: Dict[str, Any],
        messages: List[Dict[str, Any]],
        user_id: str,
        platform: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a capsule from a filter result.

        Args:
            filter_result: Result from the universal filter
            messages: Conversation messages
            user_id: User identifier
            platform: Platform name
            session_id: Session identifier

        Returns:
            Created capsule data
        """

        # Generate capsule ID
        capsule_id = f"filter_auto_{platform}_{int(datetime.now().timestamp())}"

        # Create capsule content
        content = self._format_conversation_content(messages, platform)

        # Extract reasoning steps from filter result
        reasoning_steps = []
        for factor in filter_result.get("reasoning", []):
            reasoning_steps.append(
                {
                    "step_type": "significance_detection",
                    "content": factor,
                    "weight": 0.1,  # Default weight
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

        # Create capsule data
        capsule_data = {
            "capsule_id": capsule_id,
            "type": "reasoning_trace",
            "content": content,
            "input_data": self._extract_user_input(messages),
            "output": self._extract_ai_response(messages),
            "reasoning": reasoning_steps,
            "model_version": f"{platform}-universal-filter",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": f"{platform}-auto-filter-system",
            "status": "SEALED",
            "metadata": {
                "interaction_type": f"{platform}_auto_filtered",
                "session_id": session_id,
                "user_id": user_id,
                "filter_decision": filter_result.get("decision", "encapsulate"),
                "significance_score": filter_result.get("significance_score", 0.0),
                "confidence": filter_result.get("confidence", 0.8),
                "auto_encapsulated": True,
                "filter_version": "1.0",
                "reasoning_factors": filter_result.get("reasoning", []),
                "platform_weight_applied": True,
                "conversation_length": len(messages),
                "created_by": "universal_filter_system",
            },
        }

        # Add to chain file
        await self._append_to_chain(capsule_data)

        logger.info(f"📦 Created filter capsule: {capsule_id}")
        logger.info(f"   Platform: {platform}")
        logger.info(
            f"   Significance: {filter_result.get('significance_score', 0.0):.2f}"
        )
        logger.info(f"   Factors: {', '.join(filter_result.get('reasoning', [])[:3])}")

        return capsule_data

    def _format_conversation_content(
        self, messages: List[Dict[str, Any]], platform: str
    ) -> str:
        """Format conversation content for the capsule."""

        if not messages:
            return f"Auto-filtered {platform} conversation"

        # Get the first user message as the topic
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            first_msg = user_messages[0].get("content", "")

            # Create a concise summary
            if len(first_msg) > 100:
                summary = first_msg[:100] + "..."
            else:
                summary = first_msg

            return f"Auto-filtered {platform.title()} interaction: {summary}"

        return f"Auto-filtered {platform} conversation"

    def _extract_user_input(self, messages: List[Dict[str, Any]]) -> str:
        """Extract user input from conversation."""
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            return user_messages[-1].get("content", "")
        return ""

    def _extract_ai_response(self, messages: List[Dict[str, Any]]) -> str:
        """Extract AI response from conversation."""
        ai_messages = [msg for msg in messages if msg.get("role") == "assistant"]
        if ai_messages:
            return ai_messages[-1].get("content", "")
        return ""

    async def _append_to_chain(self, capsule_data: Dict[str, Any]):
        """Append capsule data to the chain file AND database."""

        try:
            # Convert to JSON line
            json_line = json.dumps(capsule_data)

            # Append to file
            with open(self.chain_file, "a", encoding="utf-8") as f:
                f.write(json_line + "\n")

            logger.debug(f"✅ Appended capsule to chain: {self.chain_file}")

            # Write to SQLite database (backup)
            try:
                import sqlite3
                from datetime import datetime as dt

                db_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "uatp_dev.db",
                )

                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO capsules
                    (capsule_id, capsule_type, timestamp, status, payload, verification)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        capsule_data.get("capsule_id"),
                        capsule_data.get("type", "reasoning_trace"),
                        capsule_data.get("timestamp", dt.now().isoformat()),
                        capsule_data.get("status", "SEALED"),
                        json.dumps(capsule_data),
                        json.dumps(capsule_data.get("metadata", {})),
                    ),
                )

                conn.commit()
                conn.close()
                logger.debug("✅ Saved to SQLite")

            except Exception as sqlite_error:
                logger.warning(f"⚠️ SQLite save failed: {sqlite_error}")

            # ALSO write to PostgreSQL for frontend visibility (primary database)
            try:
                from datetime import datetime as dt

                import asyncpg

                # Get PostgreSQL URL from environment
                pg_url = os.getenv("DATABASE_URL", "")
                if "postgresql" in pg_url:
                    # Run async in sync context
                    import asyncio

                    async def save_to_postgres():
                        # Clean up URL for asyncpg
                        clean_url = pg_url.replace(
                            "postgresql+asyncpg://", "postgresql://"
                        )
                        conn = await asyncpg.connect(clean_url)

                        try:
                            # Check if exists
                            existing = await conn.fetchval(
                                "SELECT capsule_id FROM capsules WHERE capsule_id = $1",
                                capsule_data.get("capsule_id"),
                            )

                            if not existing:
                                # Parse timestamp
                                ts_str = capsule_data.get(
                                    "timestamp", dt.now().isoformat()
                                )
                                try:
                                    ts = dt.fromisoformat(ts_str.replace("Z", "+00:00"))
                                except:
                                    ts = dt.now()

                                await conn.execute(
                                    """
                                    INSERT INTO capsules (capsule_id, capsule_type, version, timestamp, status, verification, payload)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                                """,
                                    capsule_data.get("capsule_id"),
                                    capsule_data.get("type", "reasoning_trace"),
                                    "1.0",
                                    ts,
                                    capsule_data.get("status", "SEALED"),
                                    json.dumps(capsule_data.get("metadata", {})),
                                    json.dumps(capsule_data),
                                )
                                logger.info(
                                    "✅ Saved to PostgreSQL for frontend visibility"
                                )
                        finally:
                            await conn.close()

                    # Try to run in existing event loop or create new one
                    try:
                        loop = asyncio.get_running_loop()
                        asyncio.create_task(save_to_postgres())
                    except RuntimeError:
                        asyncio.run(save_to_postgres())

            except Exception as pg_error:
                logger.warning(
                    f"⚠️ PostgreSQL save failed (JSONL/SQLite still saved): {pg_error}"
                )

        except Exception as e:
            logger.error(f"❌ Error appending to chain file: {e}")
            raise

    def create_capsule_sync(
        self,
        filter_result: Dict[str, Any],
        messages: List[Dict[str, Any]],
        user_id: str,
        platform: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronous version of capsule creation."""

        import asyncio

        # Run the async version
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If there's already an event loop running, use it
                task = asyncio.create_task(
                    self.create_capsule_from_filter_result(
                        filter_result, messages, user_id, platform, session_id
                    )
                )
                return task  # Return the task for later awaiting
            else:
                # Create new event loop
                return asyncio.run(
                    self.create_capsule_from_filter_result(
                        filter_result, messages, user_id, platform, session_id
                    )
                )
        except Exception as e:
            logger.error(f"Error in sync capsule creation: {e}")
            raise

    def get_chain_stats(self) -> Dict[str, Any]:
        """Get statistics about the chain file."""

        try:
            if not os.path.exists(self.chain_file):
                return {
                    "total_capsules": 0,
                    "auto_filtered_capsules": 0,
                    "file_size": 0,
                    "last_modified": None,
                }

            # Count lines in file
            with open(self.chain_file, encoding="utf-8") as f:
                lines = f.readlines()

            total_capsules = len(lines)
            auto_filtered_capsules = 0

            # Count auto-filtered capsules
            for line in lines:
                if line.strip():
                    try:
                        capsule = json.loads(line)
                        if capsule.get("metadata", {}).get("auto_encapsulated"):
                            auto_filtered_capsules += 1
                    except json.JSONDecodeError:
                        continue

            # Get file stats
            file_stats = os.stat(self.chain_file)

            return {
                "total_capsules": total_capsules,
                "auto_filtered_capsules": auto_filtered_capsules,
                "file_size": file_stats.st_size,
                "last_modified": datetime.fromtimestamp(
                    file_stats.st_mtime
                ).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting chain stats: {e}")
            return {
                "total_capsules": 0,
                "auto_filtered_capsules": 0,
                "file_size": 0,
                "last_modified": None,
                "error": str(e),
            }


# Global instance
_capsule_creator = None


def get_capsule_creator() -> FilterCapsuleCreator:
    """Get the global capsule creator instance."""
    global _capsule_creator
    if _capsule_creator is None:
        _capsule_creator = FilterCapsuleCreator()
    return _capsule_creator


async def create_capsule_from_filter(
    filter_result: Dict[str, Any],
    messages: List[Dict[str, Any]],
    user_id: str,
    platform: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience function to create a capsule from filter result."""

    creator = get_capsule_creator()
    return await creator.create_capsule_from_filter_result(
        filter_result=filter_result,
        messages=messages,
        user_id=user_id,
        platform=platform,
        session_id=session_id,
    )
