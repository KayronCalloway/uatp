"""
Sankey diagram visualization component for the UATP Capsule Visualizer.
"""

from typing import Dict, List

import plotly.graph_objects as go
import streamlit as st
from capsule_schema import Capsule

from visualizer.utils.colors import CAPSULE_TYPE_COLORS


def render_sankey(capsules: List[Capsule], capsule_map: Dict[str, Capsule]):
    """Render a Sankey diagram to visualize capsule flows and merges."""
    st.header("Capsule Chain Sankey Diagram")

    # Build nodes and links for Sankey
    node_labels = []
    node_colors = []
    node_index = {}
    links = {"source": [], "target": [], "value": [], "color": []}

    # Assign each capsule a node index
    for i, capsule in enumerate(capsules):
        label = f"{capsule.capsule_type[:3]}...{capsule.capsule_id[:4]}"
        node_labels.append(label)
        node_colors.append(
            CAPSULE_TYPE_COLORS.get(
                capsule.capsule_type, CAPSULE_TYPE_COLORS["DEFAULT"]
            )
        )
        node_index[capsule.capsule_id] = i

    # Add links for previous_capsule_id (chain) and merged_from_ids (fork/merge)
    for capsule in capsules:
        target_idx = node_index[capsule.capsule_id]
        # Chain links
        if (
            getattr(capsule, "previous_capsule_id", None)
            and capsule.previous_capsule_id in node_index
        ):
            source_idx = node_index[capsule.previous_capsule_id]
            links["source"].append(source_idx)
            links["target"].append(target_idx)
            links["value"].append(1)
            links["color"].append("rgba(160,160,160,0.25)")
        # Merge links
        if getattr(capsule, "merged_from_ids", None):
            for merged_id in capsule.merged_from_ids:
                if merged_id in node_index:
                    source_idx = node_index[merged_id]
                    links["source"].append(source_idx)
                    links["target"].append(target_idx)
                    links["value"].append(1)
                    links["color"].append("rgba(200,160,60,0.4)")

    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=18,
                    thickness=18,
                    line=dict(color="rgba(0,0,0,0.1)", width=1),
                    label=node_labels,
                    color=node_colors,
                ),
                link=dict(
                    source=links["source"],
                    target=links["target"],
                    value=links["value"],
                    color=links["color"],
                ),
            )
        ]
    )

    fig.update_layout(
        margin=dict(l=15, r=15, t=30, b=15),
        font=dict(size=12),
        height=540,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Flows represent capsule chains and merges. Hover for details. Colors indicate capsule type."
    )
