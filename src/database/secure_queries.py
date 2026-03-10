"""
Secure query utilities for asyncpg operations.
Pre-defined, parameterized queries to ensure SQL injection protection.
"""

from typing import List


class SecureCapsuleQueries:
    """Pre-defined, secure queries for capsule operations."""

    # Read queries
    LOAD_CAPSULES = """
        SELECT capsule_id, version, timestamp, status, capsule_type, verification, payload
        FROM capsules
        WHERE capsule_type = ANY($1::text[])
        ORDER BY timestamp DESC
        OFFSET $2 LIMIT $3
    """

    GET_CAPSULE_BY_ID = """
        SELECT capsule_id, version, timestamp, status, capsule_type, verification, payload
        FROM capsules
        WHERE capsule_id = $1
    """

    COUNT_CAPSULES = """
        SELECT COUNT(*)
        FROM capsules
        WHERE capsule_type = ANY($1::text[])
    """

    # Write queries
    INSERT_CAPSULE = """
        INSERT INTO capsules (
            capsule_id, version, timestamp, status,
            capsule_type, verification, payload
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (capsule_id) DO NOTHING
        RETURNING capsule_id
    """

    # Bulk insert for performance (uses COPY protocol)
    @staticmethod
    def prepare_bulk_insert_data(capsules: List[dict]) -> List[tuple]:
        """Prepare capsule data for bulk insert using COPY."""
        return [
            (
                c["capsule_id"],
                c["version"],
                c["timestamp"],
                c["status"],
                c["capsule_type"],
                c["verification"],  # Must be JSON string
                c["payload"],  # Must be JSON string
            )
            for c in capsules
        ]


class QueryValidator:
    """Validate query parameters to prevent injection attacks."""

    VALID_CAPSULE_TYPES = {
        "reasoning_trace",
        "economic_transaction",
        "governance_vote",
        "ethics_trigger",
        "post_quantum_signature",
        "consent",
        "remix",
        "trust_renewal",
        "simulated_malice",
        "implicit_consent",
        "temporal_justice",
        "uncertainty",
        "conflict_resolution",
        "perspective",
        "feedback_assimilation",
        "knowledge_expiry",
        "emotional_load",
        "manipulation_attempt",
        "compute_footprint",
        "hand_off",
        "retirement",
        "audit",
        "refusal",
        "cloning_rights",
        "evolution",
        "dividend_bond",
        "citizenship",
        "akc",
        "akc_cluster",
    }

    VALID_STATUS_VALUES = {"active", "draft", "sealed", "verified", "archived"}

    @classmethod
    def validate_capsule_types(cls, types: List[str]) -> List[str]:
        """Validate and filter capsule types."""
        from src.observability.security_monitor import get_security_monitor

        validated = [t for t in types if t in cls.VALID_CAPSULE_TYPES]
        invalid = [t for t in types if t not in cls.VALID_CAPSULE_TYPES]

        # Log invalid types
        if invalid:
            get_security_monitor().record_validation_failure(
                field="capsule_types",
                value=invalid,
                reason=f"Invalid capsule types: {invalid}",
            )

        if not validated:
            raise ValueError("No valid capsule types provided")

        return validated

    @classmethod
    def validate_pagination(cls, skip: int, limit: int) -> tuple[int, int]:
        """Validate and sanitize pagination parameters."""
        skip = max(0, min(skip, 1_000_000))  # Cap at 1M offset
        limit = max(1, min(limit, 1000))  # Cap at 1000 per page
        return skip, limit

    @classmethod
    def validate_capsule_id(cls, capsule_id: str) -> str:
        """Validate capsule ID format."""
        from src.observability.security_monitor import (
            SecurityEventType,
            get_security_monitor,
        )

        # Format: caps_YYYY_MM_DD_hexstring (16 chars)
        try:
            if not capsule_id.startswith("caps_"):
                raise ValueError("Invalid capsule ID format")

            parts = capsule_id.split("_")
            if len(parts) != 4:
                raise ValueError("Invalid capsule ID structure")

            # Validate date part (YYYY_MM_DD)
            year = int(parts[1])
            month = int(parts[2])
            day = int(parts[3][:2])  # First 2 chars

            if not (2020 <= year <= 2100):
                raise ValueError("Invalid year in capsule ID")
            if not (1 <= month <= 12):
                raise ValueError("Invalid month in capsule ID")
            if not (1 <= day <= 31):
                raise ValueError("Invalid day in capsule ID")

        except (ValueError, IndexError) as e:
            # Check for SQL injection patterns
            suspicious_patterns = [
                "'",
                '"',
                "--",
                ";",
                "DROP",
                "DELETE",
                "UPDATE",
                "INSERT",
            ]
            if any(pattern in capsule_id.upper() for pattern in suspicious_patterns):
                get_security_monitor().record_event(
                    event_type=SecurityEventType.SQL_INJECTION_ATTEMPT,
                    severity="critical",
                    description=f"Potential SQL injection in capsule_id: {capsule_id[:50]}",
                    details={"capsule_id": capsule_id[:100]},
                )
            else:
                get_security_monitor().record_validation_failure(
                    field="capsule_id", value=capsule_id[:50], reason=str(e)
                )
            raise

        return capsule_id


# Performance optimization: Prepared statement cache
class PreparedStatementCache:
    """Cache prepared statements for reuse."""

    def __init__(self):
        self._cache = {}

    async def get_or_prepare(self, connection, query: str, name: str):
        """Get a cached prepared statement or create new one."""
        if name not in self._cache:
            self._cache[name] = await connection.prepare(query)
        return self._cache[name]


# Export for easy imports
__all__ = ["SecureCapsuleQueries", "QueryValidator", "PreparedStatementCache"]
