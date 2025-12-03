"""Legend components for UATP 7.0 visualizations.

This module provides reusable legend components for capsule type colors
and relationship types that can be used across different visualizations.
"""

import matplotlib.pyplot as plt
import streamlit as st

from visualizer.components.capsule_network import RELATIONSHIP_STYLES
from visualizer.utils.colors import CAPSULE_TYPE_COLORS


def render_capsule_type_legend(container=None):
    """Render a color legend for capsule types.

    Args:
        container: Optional streamlit container to render in
    """
    # Use provided container or st directly
    ctx = container if container else st

    # Get all capsule types and their colors
    capsule_types = list(CAPSULE_TYPE_COLORS.keys())
    # Sort them alphabetically but keep DEFAULT at the end if present
    if "DEFAULT" in capsule_types:
        capsule_types.remove("DEFAULT")
        capsule_types.sort()
        capsule_types.append("DEFAULT")

    ctx.markdown("### Capsule Type Legend")

    # Create a grid of color boxes
    col_count = 3  # Number of columns in the grid
    cols = ctx.columns(col_count)

    for i, capsule_type in enumerate(capsule_types):
        color = CAPSULE_TYPE_COLORS[capsule_type]
        col_idx = i % col_count
        # Create a colored box with the capsule type name
        cols[col_idx].markdown(
            f"<div style='background-color:{color};padding:5px;border-radius:3px;margin:2px;'>"
            f"<span style='color:black;font-weight:bold;'>{capsule_type}</span></div>",
            unsafe_allow_html=True,
        )


def render_relationship_legend(container=None):
    """Render a legend for relationship types and their line styles.

    Args:
        container: Optional streamlit container to render in
    """
    # Use provided container or st directly
    ctx = container if container else st

    ctx.markdown("### Relationship Type Legend")

    # Create a Matplotlib figure for the legend
    fig, ax = plt.subplots(figsize=(10, len(RELATIONSHIP_STYLES) * 0.5))
    ax.axis("off")

    # Create legend entries
    legend_entries = []
    for rel_type, style in RELATIONSHIP_STYLES.items():
        color = style.get("color", "gray")
        line_style = style.get("style", "-")
        width = style.get("width", 1)

        # Format relationship type name
        rel_name = rel_type.replace("_", " ").title()

        # Create a line for the legend
        line = plt.Line2D(
            [0], [0], color=color, linewidth=width, linestyle=line_style, label=rel_name
        )
        legend_entries.append(line)

    # Add the legend to the figure
    ax.legend(handles=legend_entries, loc="center", frameon=False, fontsize=12)

    # Display the legend
    ctx.pyplot(fig)


def render_visualization_legends(
    container=None, show_capsule_types=True, show_relationships=True
):
    """Render both capsule type and relationship legends.

    Args:
        container: Optional streamlit container to render in
        show_capsule_types: Whether to show capsule type legend
        show_relationships: Whether to show relationship legend
    """
    # Use provided container or st directly
    ctx = container if container else st

    ctx.markdown("## Visualization Legend")

    # Create expander for legends to save space
    with ctx.expander("Show/Hide Legends", expanded=False):
        if show_capsule_types:
            render_capsule_type_legend(ctx)

        if show_relationships:
            ctx.markdown("---")  # Add separator
            render_relationship_legend(ctx)
