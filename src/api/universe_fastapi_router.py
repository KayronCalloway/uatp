"""
Universe Visualization FastAPI Router for UATP Capsule Engine.

Provides endpoints for capsule universe visualization data.
"""

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(prefix="/universe", tags=["Universe Visualization"])


@router.get("/visualization-data")
async def get_visualization_data() -> Dict[str, Any]:
    """Get data for universe visualization."""
    return {
        "nodes": [
            {
                "id": "node-1",
                "type": "capsule",
                "label": "Reasoning Capsule",
                "size": 10,
                "color": "#4f46e5",
                "x": 0,
                "y": 0,
                "z": 0,
            },
            {
                "id": "node-2",
                "type": "capsule",
                "label": "Decision Capsule",
                "size": 8,
                "color": "#059669",
                "x": 50,
                "y": 30,
                "z": 20,
            },
            {
                "id": "node-3",
                "type": "agent",
                "label": "AI Agent",
                "size": 12,
                "color": "#dc2626",
                "x": -30,
                "y": 50,
                "z": -10,
            },
        ],
        "links": [
            {"source": "node-1", "target": "node-2", "strength": 0.8},
            {"source": "node-2", "target": "node-3", "strength": 0.6},
            {"source": "node-1", "target": "node-3", "strength": 0.4},
        ],
        "metadata": {
            "total_nodes": 3,
            "total_links": 3,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }
