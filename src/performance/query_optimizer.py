"""
Database Query Optimization System
==================================

Production-grade query optimization with:
- Slow query logging and analysis
- Query execution plan monitoring
- Index optimization recommendations
- Query performance metrics collection
- Automated query analysis and suggestions
- Connection pool optimization
"""

import asyncio
import json
import logging
import statistics
import time
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, NamedTuple
from dataclasses import dataclass, asdict
from enum import Enum
import re

import asyncpg
from asyncpg import Connection

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Query type classification."""

    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    ALTER = "alter"
    DROP = "drop"
    OTHER = "other"


@dataclass
class QueryMetrics:
    """Metrics for a database query."""

    query_hash: str
    query_text: str
    query_type: QueryType
    execution_count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    median_time_ms: float = 0.0
    p95_time_ms: float = 0.0
    p99_time_ms: float = 0.0
    recent_times: deque = None
    last_executed: Optional[datetime] = None
    error_count: int = 0
    rows_examined_avg: float = 0.0
    rows_returned_avg: float = 0.0
    tables_accessed: Set[str] = None

    def __post_init__(self):
        if self.recent_times is None:
            self.recent_times = deque(maxlen=100)  # Keep last 100 execution times
        if self.tables_accessed is None:
            self.tables_accessed = set()

    def add_execution(
        self, execution_time_ms: float, rows_examined: int = 0, rows_returned: int = 0
    ):
        """Add a new execution time to metrics."""
        self.execution_count += 1
        self.total_time_ms += execution_time_ms
        self.min_time_ms = min(self.min_time_ms, execution_time_ms)
        self.max_time_ms = max(self.max_time_ms, execution_time_ms)
        self.avg_time_ms = self.total_time_ms / self.execution_count
        self.last_executed = datetime.now(timezone.utc)

        # Update recent times for percentile calculations
        self.recent_times.append(execution_time_ms)
        if len(self.recent_times) >= 10:  # Need at least 10 samples
            sorted_times = sorted(self.recent_times)
            self.median_time_ms = statistics.median(sorted_times)
            self.p95_time_ms = statistics.quantiles(sorted_times, n=20)[
                18
            ]  # 95th percentile
            self.p99_time_ms = statistics.quantiles(sorted_times, n=100)[
                98
            ]  # 99th percentile

        # Update row metrics
        if rows_examined > 0:
            self.rows_examined_avg = (
                self.rows_examined_avg * (self.execution_count - 1) + rows_examined
            ) / self.execution_count

        if rows_returned > 0:
            self.rows_returned_avg = (
                self.rows_returned_avg * (self.execution_count - 1) + rows_returned
            ) / self.execution_count


@dataclass
class QueryPlan:
    """Database query execution plan."""

    query_hash: str
    plan_json: Dict[str, Any]
    cost_estimate: float
    rows_estimate: int
    width_estimate: int
    execution_time_ms: float
    planning_time_ms: float
    created_at: datetime

    @property
    def scan_types(self) -> List[str]:
        """Extract scan types from execution plan."""

        def extract_scans(node):
            scans = []
            if isinstance(node, dict):
                node_type = node.get("Node Type", "")
                if "Scan" in node_type:
                    scans.append(node_type)

                # Recursively check child plans
                if "Plans" in node:
                    for child in node["Plans"]:
                        scans.extend(extract_scans(child))
            return scans

        return extract_scans(self.plan_json)

    @property
    def uses_index(self) -> bool:
        """Check if query uses indexes."""
        scan_types = self.scan_types
        return any("Index" in scan for scan in scan_types)

    @property
    def has_sequential_scan(self) -> bool:
        """Check if query has sequential scans."""
        scan_types = self.scan_types
        return "Seq Scan" in scan_types


class QueryOptimizer:
    """Database query optimization and monitoring system."""

    def __init__(self, slow_query_threshold_ms: float = 100.0):
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.query_metrics: Dict[str, QueryMetrics] = {}
        self.query_plans: Dict[str, QueryPlan] = {}
        self.table_stats: Dict[str, Dict[str, Any]] = {}
        self.index_recommendations: List[Dict[str, Any]] = []

        # Monitoring settings
        self.monitoring_enabled = True
        self.plan_collection_enabled = True
        self.auto_analyze_threshold = 100  # Auto-analyze after N slow queries

        # Performance tracking
        self.total_queries = 0
        self.slow_queries = 0
        self.optimization_suggestions = defaultdict(int)

    def normalize_query(self, query: str) -> Tuple[str, str]:
        """Normalize query for consistent tracking."""
        # Remove extra whitespace and normalize case
        normalized = re.sub(r"\s+", " ", query.strip().lower())

        # Replace literal values with placeholders for better grouping
        # Numbers
        normalized = re.sub(r"\b\d+\b", "?", normalized)
        # String literals
        normalized = re.sub(r"'[^']*'", "?", normalized)
        # IN clauses with multiple values
        normalized = re.sub(r"in\s*\([^)]+\)", "in (?)", normalized)

        # Create hash for grouping
        query_hash = str(hash(normalized))

        return query_hash, normalized

    def classify_query(self, query: str) -> QueryType:
        """Classify query by type."""
        query_lower = query.strip().lower()

        if query_lower.startswith("select"):
            return QueryType.SELECT
        elif query_lower.startswith("insert"):
            return QueryType.INSERT
        elif query_lower.startswith("update"):
            return QueryType.UPDATE
        elif query_lower.startswith("delete"):
            return QueryType.DELETE
        elif query_lower.startswith("create"):
            return QueryType.CREATE
        elif query_lower.startswith("alter"):
            return QueryType.ALTER
        elif query_lower.startswith("drop"):
            return QueryType.DROP
        else:
            return QueryType.OTHER

    def extract_tables(self, query: str) -> Set[str]:
        """Extract table names from query."""
        tables = set()

        # Simple regex-based extraction (could be improved with proper SQL parsing)
        # FROM clauses
        from_matches = re.finditer(r"from\s+([a-zA-Z_][a-zA-Z0-9_]*)", query.lower())
        for match in from_matches:
            tables.add(match.group(1))

        # JOIN clauses
        join_matches = re.finditer(r"join\s+([a-zA-Z_][a-zA-Z0-9_]*)", query.lower())
        for match in join_matches:
            tables.add(match.group(1))

        # INSERT/UPDATE/DELETE table names
        table_matches = re.finditer(
            r"(?:insert\s+into|update|delete\s+from)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            query.lower(),
        )
        for match in table_matches:
            tables.add(match.group(1))

        return tables

    async def track_query(
        self,
        query: str,
        execution_time_ms: float,
        rows_examined: int = 0,
        rows_returned: int = 0,
        connection: Optional[Connection] = None,
    ) -> None:
        """Track query performance metrics."""
        if not self.monitoring_enabled:
            return

        self.total_queries += 1

        # Normalize and hash query
        query_hash, normalized_query = self.normalize_query(query)

        # Get or create metrics
        if query_hash not in self.query_metrics:
            query_type = self.classify_query(normalized_query)
            tables = self.extract_tables(normalized_query)

            self.query_metrics[query_hash] = QueryMetrics(
                query_hash=query_hash,
                query_text=normalized_query,
                query_type=query_type,
                tables_accessed=tables,
            )

        # Update metrics
        metrics = self.query_metrics[query_hash]
        metrics.add_execution(execution_time_ms, rows_examined, rows_returned)

        # Track slow queries
        if execution_time_ms >= self.slow_query_threshold_ms:
            self.slow_queries += 1
            logger.warning(
                f"Slow query detected ({execution_time_ms:.2f}ms): {normalized_query[:100]}..."
            )

            # Collect execution plan for slow queries
            if connection and self.plan_collection_enabled:
                await self._collect_execution_plan(connection, query, query_hash)

        # Auto-analyze if we have enough slow queries
        if self.slow_queries % self.auto_analyze_threshold == 0:
            asyncio.create_task(self.analyze_performance())

    async def _collect_execution_plan(
        self, connection: Connection, query: str, query_hash: str
    ) -> None:
        """Collect execution plan for a query."""
        try:
            # Get execution plan
            explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {query}"
            plan_result = await connection.fetchval(explain_query)

            if plan_result and len(plan_result) > 0:
                plan_data = plan_result[0]

                self.query_plans[query_hash] = QueryPlan(
                    query_hash=query_hash,
                    plan_json=plan_data,
                    cost_estimate=plan_data.get("Total Cost", 0),
                    rows_estimate=plan_data.get("Plan Rows", 0),
                    width_estimate=plan_data.get("Plan Width", 0),
                    execution_time_ms=plan_data.get("Actual Total Time", 0),
                    planning_time_ms=plan_data.get("Planning Time", 0),
                    created_at=datetime.now(timezone.utc),
                )

        except Exception as e:
            logger.debug(f"Could not collect execution plan: {e}")

    async def analyze_performance(self) -> Dict[str, Any]:
        """Analyze query performance and generate recommendations."""
        logger.info("Starting query performance analysis...")

        analysis = {
            "summary": self._generate_summary(),
            "slow_queries": self._analyze_slow_queries(),
            "index_recommendations": self._generate_index_recommendations(),
            "query_patterns": self._analyze_query_patterns(),
            "table_analysis": self._analyze_table_usage(),
            "optimization_suggestions": list(self.optimization_suggestions.items()),
        }

        return analysis

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate performance summary."""
        if not self.query_metrics:
            return {"total_queries": 0, "slow_queries": 0}

        avg_execution_time = statistics.mean(
            [m.avg_time_ms for m in self.query_metrics.values()]
        )

        slow_query_rate = (
            (self.slow_queries / self.total_queries * 100)
            if self.total_queries > 0
            else 0
        )

        return {
            "total_queries": self.total_queries,
            "unique_queries": len(self.query_metrics),
            "slow_queries": self.slow_queries,
            "slow_query_rate_percent": round(slow_query_rate, 2),
            "avg_execution_time_ms": round(avg_execution_time, 2),
            "slow_query_threshold_ms": self.slow_query_threshold_ms,
        }

    def _analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """Analyze slow queries and return top offenders."""
        slow_queries = [
            m
            for m in self.query_metrics.values()
            if m.avg_time_ms >= self.slow_query_threshold_ms
        ]

        # Sort by total time impact (avg_time * execution_count)
        slow_queries.sort(key=lambda x: x.avg_time_ms * x.execution_count, reverse=True)

        result = []
        for metrics in slow_queries[:10]:  # Top 10 slow queries
            query_analysis = {
                "query_hash": metrics.query_hash,
                "query_text": metrics.query_text[:200] + "..."
                if len(metrics.query_text) > 200
                else metrics.query_text,
                "query_type": metrics.query_type.value,
                "execution_count": metrics.execution_count,
                "avg_time_ms": round(metrics.avg_time_ms, 2),
                "max_time_ms": round(metrics.max_time_ms, 2),
                "p95_time_ms": round(metrics.p95_time_ms, 2),
                "total_time_impact_ms": round(
                    metrics.avg_time_ms * metrics.execution_count, 2
                ),
                "tables_accessed": list(metrics.tables_accessed),
                "recommendations": [],
            }

            # Add specific recommendations
            if metrics.query_hash in self.query_plans:
                plan = self.query_plans[metrics.query_hash]
                if plan.has_sequential_scan:
                    query_analysis["recommendations"].append(
                        "Consider adding indexes to avoid sequential scans"
                    )
                    self.optimization_suggestions["missing_indexes"] += 1

                if not plan.uses_index:
                    query_analysis["recommendations"].append(
                        "Query does not use any indexes"
                    )
                    self.optimization_suggestions["no_index_usage"] += 1

                if plan.cost_estimate > 1000:
                    query_analysis["recommendations"].append(
                        "High-cost query - consider query rewriting"
                    )
                    self.optimization_suggestions["high_cost_queries"] += 1

            if metrics.rows_examined_avg > metrics.rows_returned_avg * 10:
                query_analysis["recommendations"].append(
                    "Query examines many more rows than returned - consider filtering"
                )
                self.optimization_suggestions["inefficient_filtering"] += 1

            result.append(query_analysis)

        return result

    def _generate_index_recommendations(self) -> List[Dict[str, Any]]:
        """Generate index recommendations based on query patterns."""
        recommendations = []

        # Analyze WHERE clauses and JOIN conditions
        table_columns = defaultdict(set)

        for metrics in self.query_metrics.values():
            if (
                metrics.query_type == QueryType.SELECT
                and metrics.avg_time_ms >= self.slow_query_threshold_ms
            ):
                # Simple extraction of potential index candidates
                query = metrics.query_text.lower()

                # Look for WHERE conditions
                where_match = re.search(
                    r"where\s+(.+?)(?:\s+(?:group|order|limit|$))", query
                )
                if where_match:
                    where_clause = where_match.group(1)
                    # Extract column references (simplified)
                    column_matches = re.findall(
                        r"([a-zA-Z_][a-zA-Z0-9_]*)\s*[=<>]", where_clause
                    )
                    for table in metrics.tables_accessed:
                        for column in column_matches:
                            table_columns[table].add(column)

                # Look for JOIN conditions
                join_matches = re.findall(
                    r"on\s+([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)", query
                )
                for join_col in join_matches:
                    if "." in join_col:
                        table, column = join_col.split(".", 1)
                        table_columns[table].add(column)

        # Generate recommendations
        for table, columns in table_columns.items():
            if len(columns) > 0:
                recommendations.append(
                    {
                        "table": table,
                        "columns": list(columns),
                        "recommendation": f'Consider creating indexes on {table}({", ".join(columns)})',
                        "reason": "Frequently used in WHERE clauses or JOIN conditions",
                        "priority": "high" if len(columns) <= 2 else "medium",
                    }
                )

        return recommendations[:10]  # Top 10 recommendations

    def _analyze_query_patterns(self) -> Dict[str, Any]:
        """Analyze query patterns and usage."""
        patterns = {
            "by_type": defaultdict(int),
            "by_table": defaultdict(int),
            "execution_distribution": {
                "single_execution": 0,
                "low_frequency": 0,  # 2-10 executions
                "medium_frequency": 0,  # 11-100 executions
                "high_frequency": 0,  # >100 executions
            },
        }

        for metrics in self.query_metrics.values():
            patterns["by_type"][metrics.query_type.value] += metrics.execution_count

            for table in metrics.tables_accessed:
                patterns["by_table"][table] += metrics.execution_count

            # Categorize by execution frequency
            if metrics.execution_count == 1:
                patterns["execution_distribution"]["single_execution"] += 1
            elif metrics.execution_count <= 10:
                patterns["execution_distribution"]["low_frequency"] += 1
            elif metrics.execution_count <= 100:
                patterns["execution_distribution"]["medium_frequency"] += 1
            else:
                patterns["execution_distribution"]["high_frequency"] += 1

        # Convert defaultdicts to regular dicts for JSON serialization
        patterns["by_type"] = dict(patterns["by_type"])
        patterns["by_table"] = dict(
            sorted(patterns["by_table"].items(), key=lambda x: x[1], reverse=True)[:10]
        )

        return patterns

    def _analyze_table_usage(self) -> Dict[str, Any]:
        """Analyze table usage patterns."""
        table_metrics = defaultdict(
            lambda: {
                "read_count": 0,
                "write_count": 0,
                "avg_query_time_ms": 0.0,
                "slow_queries": 0,
            }
        )

        for metrics in self.query_metrics.values():
            for table in metrics.tables_accessed:
                if metrics.query_type == QueryType.SELECT:
                    table_metrics[table]["read_count"] += metrics.execution_count
                else:
                    table_metrics[table]["write_count"] += metrics.execution_count

                # Update average query time
                current_avg = table_metrics[table]["avg_query_time_ms"]
                total_ops = (
                    table_metrics[table]["read_count"]
                    + table_metrics[table]["write_count"]
                )
                table_metrics[table]["avg_query_time_ms"] = (
                    current_avg * (total_ops - metrics.execution_count)
                    + metrics.avg_time_ms * metrics.execution_count
                ) / total_ops

                if metrics.avg_time_ms >= self.slow_query_threshold_ms:
                    table_metrics[table]["slow_queries"] += 1

        # Convert to regular dict and sort by activity
        result = {}
        for table, stats in table_metrics.items():
            total_activity = stats["read_count"] + stats["write_count"]
            result[table] = {
                **stats,
                "total_activity": total_activity,
                "read_write_ratio": stats["read_count"] / max(stats["write_count"], 1),
            }

        # Return top 10 most active tables
        sorted_tables = sorted(
            result.items(), key=lambda x: x[1]["total_activity"], reverse=True
        )
        return dict(sorted_tables[:10])

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        return {
            "total_queries_tracked": self.total_queries,
            "unique_queries": len(self.query_metrics),
            "slow_queries": self.slow_queries,
            "query_plans_collected": len(self.query_plans),
            "monitoring_enabled": self.monitoring_enabled,
            "slow_query_threshold_ms": self.slow_query_threshold_ms,
        }

    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        self.query_metrics.clear()
        self.query_plans.clear()
        self.table_stats.clear()
        self.index_recommendations.clear()
        self.optimization_suggestions.clear()
        self.total_queries = 0
        self.slow_queries = 0
        logger.info("Query optimizer metrics reset")

    async def export_metrics(self, filepath: str) -> None:
        """Export metrics to JSON file."""
        try:
            export_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "summary": self._generate_summary(),
                "metrics": {
                    hash_key: {
                        "query_hash": m.query_hash,
                        "query_text": m.query_text,
                        "query_type": m.query_type.value,
                        "execution_count": m.execution_count,
                        "avg_time_ms": m.avg_time_ms,
                        "max_time_ms": m.max_time_ms,
                        "p95_time_ms": m.p95_time_ms,
                        "tables_accessed": list(m.tables_accessed),
                        "last_executed": m.last_executed.isoformat()
                        if m.last_executed
                        else None,
                    }
                    for hash_key, m in self.query_metrics.items()
                },
                "analysis": await self.analyze_performance(),
            }

            with open(filepath, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Query metrics exported to {filepath}")

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")


# Global query optimizer instance
_global_optimizer: Optional[QueryOptimizer] = None


def get_query_optimizer() -> QueryOptimizer:
    """Get the global query optimizer instance."""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = QueryOptimizer()
    return _global_optimizer


def initialize_query_optimizer(
    slow_query_threshold_ms: float = 100.0,
) -> QueryOptimizer:
    """Initialize the global query optimizer."""
    global _global_optimizer
    _global_optimizer = QueryOptimizer(slow_query_threshold_ms)
    logger.info(
        f"Query optimizer initialized with {slow_query_threshold_ms}ms slow query threshold"
    )
    return _global_optimizer


# Context manager for query timing
class QueryTimer:
    """Context manager for timing database queries."""

    def __init__(self, query: str, connection: Optional[Connection] = None):
        self.query = query
        self.connection = connection
        self.start_time = None
        self.optimizer = get_query_optimizer()

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            execution_time_ms = (time.time() - self.start_time) * 1000
            await self.optimizer.track_query(
                self.query, execution_time_ms, connection=self.connection
            )


# Decorator for automatic query timing
def track_query_performance(func):
    """Decorator to automatically track query performance."""

    async def wrapper(*args, **kwargs):
        # Try to extract query from args
        query = None
        connection = None

        if args and isinstance(args[0], str):
            query = args[0]

        # Look for connection in args or kwargs
        for arg in args:
            if isinstance(arg, Connection):
                connection = arg
                break

        if "connection" in kwargs:
            connection = kwargs["connection"]

        if query:
            async with QueryTimer(query, connection):
                return await func(*args, **kwargs)
        else:
            return await func(*args, **kwargs)

    return wrapper
