"""Constellations Service

Provides a thin abstraction over the configured graph-store implementation to
add lineage edges and query ancestry/descendants for capsules.

This file contains no storage concerns – everything is delegated to the
``GraphStoreProtocol`` instance returned by ``get_graph_store`` to keep the
service stateless and easy to unit-test.
"""
from __future__ import annotations

from typing import Any, List, Optional

from . import get_graph_store, GraphStoreProtocol

__all__ = ["ConstellationsService", "service"]


class ConstellationsService:
    """Business-logic wrapper for Constellations graph operations."""

    def __init__(self, store: Optional[GraphStoreProtocol] = None) -> None:
        self._store = store or get_graph_store()

    # ---------------------------------------------------------------------
    # Lineage mutations
    # ---------------------------------------------------------------------
    def add_edge(self, parent_id: str, child_id: str, **metadata: Any) -> None:
        """Create a directed edge *parent* → *child* in the lineage DAG."""
        self._store.add_edge(parent_id, child_id, **metadata)

    # ---------------------------------------------------------------------
    # Lineage queries
    # ---------------------------------------------------------------------
    def ancestors(self, capsule_id: str, depth: int | None = None) -> List[str]:
        return self._store.ancestors(capsule_id, depth)

    def descendants(self, capsule_id: str, depth: int | None = None) -> List[str]:
        return self._store.descendants(capsule_id, depth)

    def lineage(self, capsule_id: str) -> List[str]:
        return self._store.lineage(capsule_id)

    def export(self) -> dict[str, Any]:
        return self._store.export()


# Singleton instance
service = ConstellationsService()
