"""Constellations API routes.

Provides read-only access to the lineage graph managed by the
ConstellationsService. Routes are prefixed by ``/api/v1`` in ``app_factory``.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.constellations.service import service as constellations_service

router = APIRouter(tags=["Constellations"])


@router.get("/constellations/{capsule_id}/ancestors")
async def get_ancestors(capsule_id: str, depth: Optional[int] = Query(None, ge=1)):
    """Return ancestor capsule IDs up to the optional *depth*."""
    try:
        ancestors = constellations_service.ancestors(capsule_id, depth)
        return {"capsule_id": capsule_id, "ancestors": ancestors}
    except Exception as exc:  # pragma: no cover – generic safeguard
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/constellations/{capsule_id}/descendants")
async def get_descendants(capsule_id: str, depth: Optional[int] = Query(None, ge=1)):
    """Return descendant capsule IDs up to the optional *depth*."""
    try:
        descendants = constellations_service.descendants(capsule_id, depth)
        return {"capsule_id": capsule_id, "descendants": descendants}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/constellations/{capsule_id}/lineage")
async def get_lineage(capsule_id: str):
    """Return ordered lineage from genesis → *capsule_id*."""
    try:
        lineage = constellations_service.lineage(capsule_id)
        return {"capsule_id": capsule_id, "lineage": lineage}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/constellations/export")
async def export_graph():
    """Return serialisable representation of the entire lineage graph."""
    try:
        return constellations_service.export()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
