"""Constellations – Causal Graph Memory module.

This package provides a pluggable graph-store abstraction that materialises the
capsule lineage DAG required by the Constellations specification.

The default backend is an in-process NetworkX graph which is adequate for unit
and integration tests.  In production, swap it for a Neo4j/Dgraph backend via
`CONSTELLATIONS_BACKEND` env-var.
"""
from __future__ import annotations

import os
from typing import Protocol, List, Dict, Any

import networkx as nx

__all__ = [
    "GraphStoreProtocol",
    "InMemoryGraphStore",
    "get_graph_store",
]


class GraphStoreProtocol(Protocol):
    """Behaviour expected from a Constellations graph store implementation."""

    # --------------------------- Mutations ---------------------------------
    def add_edge(self, parent_id: str, child_id: str, **metadata: Any) -> None:  # noqa: D401,E501
        """Insert a directed edge parent→child with optional metadata."""

    # ---------------------------- Queries ----------------------------------
    def ancestors(self, capsule_id: str, depth: int | None = None) -> List[str]:
        """Return ancestor ids up to *depth* generations (unlimited if None)."""

    def descendants(self, capsule_id: str, depth: int | None = None) -> List[str]:
        """Return descendants ids up to *depth* generations (unlimited if None)."""

    def lineage(self, capsule_id: str) -> List[str]:
        """Return ordered path from *capsule_id* to genesis (root ancestor)."""

    # --------------------------- Utilities ---------------------------------
    def export(self) -> Dict[str, Any]:
        """Return serialisable representation (nodes + edges)."""


class InMemoryGraphStore(GraphStoreProtocol):
    """Simple NetworkX-based implementation used for development & tests."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    # --------------------------- Mutations ---------------------------------
    def add_edge(self, parent_id: str, child_id: str, **metadata: Any) -> None:  # noqa: D401,E501
        # Ensure both nodes exist
        self._graph.add_node(parent_id)
        self._graph.add_node(child_id)
        self._graph.add_edge(parent_id, child_id, **metadata)

    # ---------------------------- Queries ----------------------------------
    def ancestors(self, capsule_id: str, depth: int | None = None) -> List[str]:
        ancestors = nx.ancestors(self._graph, capsule_id)
        if depth is None:
            return list(ancestors)
        # Limit by depth using BFS
        result: set[str] = set()
        current = {capsule_id}
        for _ in range(depth):
            nxt = set()
            for node in current:
                nxt.update(self._graph.predecessors(node))
            result.update(nxt)
            current = nxt
            if not current:
                break
        return list(result)

    def descendants(self, capsule_id: str, depth: int | None = None) -> List[str]:
        descendants = nx.descendants(self._graph, capsule_id)
        if depth is None:
            return list(descendants)
        result: set[str] = set()
        current = {capsule_id}
        for _ in range(depth):
            nxt = set()
            for node in current:
                nxt.update(self._graph.successors(node))
            result.update(nxt)
            current = nxt
            if not current:
                break
        return list(result)

    def lineage(self, capsule_id: str) -> List[str]:
        # Trace back along any parent until root (node with no predecessors)
        path = [capsule_id]
        current = capsule_id
        while list(self._graph.predecessors(current)):
            current = next(iter(self._graph.predecessors(current)))
            path.append(current)
        return path[::-1]  # genesis → capsule_id

    # --------------------------- Utilities ---------------------------------
    def export(self) -> Dict[str, Any]:
        return {
            "nodes": list(self._graph.nodes),
            "edges": [
                {
                    "parent": u,
                    "child": v,
                    **self._graph.edges[u, v],
                }
                for u, v in self._graph.edges
            ],
        }


# ---------------------------------------------------------------------------
# Singleton access helper
# ---------------------------------------------------------------------------

_graph_store: GraphStoreProtocol | None = None


def get_graph_store() -> GraphStoreProtocol:  # noqa: D401
    """Return singleton graph store based on configuration."""
    global _graph_store  # noqa: PLW0603 – intentional singleton
    if _graph_store is None:
        backend = os.getenv("CONSTELLATIONS_BACKEND", "inmemory").lower()
        match backend:
            case "inmemory":
                _graph_store = InMemoryGraphStore()
            # Future: case "neo4j":
            # Future backends plugged here via dynamic import
            case _:
                raise RuntimeError(f"Unknown Constellations backend: {backend}")
    return _graph_store
