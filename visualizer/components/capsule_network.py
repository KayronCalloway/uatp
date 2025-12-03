"""Network visualization component for UATP 7.0 capsule relationships.

This module provides visualization tools for displaying relationships between
capsules in a chain, making it easier to understand cross-capsule dependencies,
influences, and connections as defined in the UATP 7.0 white paper.
"""

import os
import tempfile
from typing import Dict, List, Optional

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st

# Import capsule types
from capsule_schema import Capsule
from pyvis.network import Network

# Import color utilities
from visualizer.utils.colors import CAPSULE_TYPE_COLORS

# Define relationship types and their visual properties
RELATIONSHIP_STYLES = {
    "references": {"color": "#007bff", "width": 2, "style": "-"},
    "derives_from": {"color": "#28a745", "width": 3, "style": "-"},
    "supersedes": {"color": "#dc3545", "width": 2, "style": "--"},
    "modifies": {"color": "#fd7e14", "width": 2, "style": "-"},
    "impacts": {"color": "#6f42c1", "width": 1, "style": ":"},
    "verifies": {"color": "#20c997", "width": 2, "style": "-"},
    "extends": {"color": "#e83e8c", "width": 2, "style": "-."},
}


def extract_capsule_relationships(capsules: List[Capsule]) -> Dict[str, list]:
    """Extract relationships between capsules in a chain.

    This function analyzes a list of capsules and determines the relationships
    between them based on their types and contents, as specified in the UATP 7.0
    protocol.

    Args:
        capsules: List of capsules in the chain

    Returns:
        Dictionary of relationships where keys are relationship types and values
        are lists of tuples (source_id, target_id)
    """
    relationships = {
        "references": [],
        "derives_from": [],
        "supersedes": [],
        "modifies": [],
        "impacts": [],
        "verifies": [],
        "extends": [],
    }

    # Create lookup map for fast access
    capsule_map = {
        capsule.capsule_id: capsule
        for capsule in capsules
        if hasattr(capsule, "capsule_id")
    }

    for capsule in capsules:
        # Skip if capsule has no ID
        if not hasattr(capsule, "capsule_id"):
            continue

        capsule_id = capsule.capsule_id
        capsule_type = getattr(capsule, "capsule_type", "")

        # Extract relationships based on capsule type
        if capsule_type == "Remix":
            # Remix capsules derive from their source capsules
            if hasattr(capsule, "source_capsule_ids") and capsule.source_capsule_ids:
                for source_id in capsule.source_capsule_ids:
                    relationships["derives_from"].append((capsule_id, source_id))

        elif capsule_type == "TemporalSignature":
            # Look for references in the metadata
            if hasattr(capsule, "metadata") and capsule.metadata:
                for key, value in capsule.metadata.items():
                    if key == "related_capsules" and isinstance(value, list):
                        for related_id in value:
                            relationships["references"].append((capsule_id, related_id))

        elif capsule_type == "TrustRenewal":
            # Trust renewal verifies the target capsules
            if hasattr(capsule, "target_capsule_ids") and capsule.target_capsule_ids:
                for target_id in capsule.target_capsule_ids:
                    relationships["verifies"].append((capsule_id, target_id))

        elif capsule_type == "CapsuleExpiration":
            # Expiration supersedes and impacts its targets
            if hasattr(capsule, "target_capsule_ids") and capsule.target_capsule_ids:
                for target_id in capsule.target_capsule_ids:
                    relationships["supersedes"].append((capsule_id, target_id))

                # Replacement capsules extend the expired ones
                if (
                    hasattr(capsule, "replacement_capsule_ids")
                    and capsule.replacement_capsule_ids
                ):
                    for replacement_id in capsule.replacement_capsule_ids:
                        for target_id in capsule.target_capsule_ids:
                            relationships["extends"].append((replacement_id, target_id))

        elif capsule_type == "Governance":
            # Governance capsules modify or impact their governed entities
            if hasattr(capsule, "affected_entity_ids") and capsule.affected_entity_ids:
                for entity_id in capsule.affected_entity_ids:
                    # Check if entity ID is a capsule
                    if entity_id in capsule_map:
                        relationships["modifies"].append((capsule_id, entity_id))

        # Parent-child relationships for all capsules
        if hasattr(capsule, "parent_capsule_id") and capsule.parent_capsule_id:
            relationships["derives_from"].append(
                (capsule_id, capsule.parent_capsule_id)
            )

    return relationships


def create_capsule_network_graph(
    capsules: List[Capsule], highlighted_capsule_id: Optional[str] = None
) -> nx.DiGraph:
    """Create a NetworkX directed graph of capsule relationships.

    Args:
        capsules: List of capsules to include in the graph
        highlighted_capsule_id: Optional ID of capsule to highlight

    Returns:
        NetworkX DiGraph representing the capsule network
    """
    relationships = extract_capsule_relationships(capsules)
    capsule_map = {
        capsule.capsule_id: capsule
        for capsule in capsules
        if hasattr(capsule, "capsule_id")
    }

    # Build edge lists by relationship type
    G = nx.DiGraph()

    for rel_type, edge_list in relationships.items():
        rel_props = RELATIONSHIP_STYLES.get(
            rel_type, {"color": "gray", "width": 1, "style": "-"}
        )

        for source_id, target_id in edge_list:
            # Skip if nodes don't exist
            if source_id not in capsule_map or target_id not in capsule_map:
                continue

            # Add nodes if they don't exist yet
            if source_id not in G.nodes():
                source_capsule = capsule_map[source_id]
                source_type = getattr(source_capsule, "capsule_type", "DEFAULT")
                color = CAPSULE_TYPE_COLORS.get(
                    source_type, CAPSULE_TYPE_COLORS["DEFAULT"]
                )
                label = (
                    f"{source_type}\n{source_id[:8]}"
                    if hasattr(source_capsule, "capsule_type")
                    else source_id[:8]
                )

                G.add_node(
                    source_id,
                    color=color,
                    label=label,
                    title=source_id,
                    size=25 if source_id == highlighted_capsule_id else 15,
                )

            if target_id not in G.nodes():
                target_capsule = capsule_map[target_id]
                target_type = getattr(target_capsule, "capsule_type", "DEFAULT")
                color = CAPSULE_TYPE_COLORS.get(
                    target_type, CAPSULE_TYPE_COLORS["DEFAULT"]
                )
                label = (
                    f"{target_type}\n{target_id[:8]}"
                    if hasattr(target_capsule, "capsule_type")
                    else target_id[:8]
                )

                G.add_node(
                    target_id,
                    color=color,
                    label=label,
                    title=target_id,
                    size=25 if target_id == highlighted_capsule_id else 15,
                )

            # Add the edge with relationship properties
            # Convert matplotlib linestyle format to pyvis dashes format
            dashes = False
            if rel_props["style"] == "--":
                dashes = [5, 5]
            elif rel_props["style"] == ":":
                dashes = [2, 2]
            elif rel_props["style"] == "-.":
                dashes = [5, 2, 2, 2]

            G.add_edge(
                source_id,
                target_id,
                relationship=rel_type,
                title=rel_type,
                color=rel_props["color"],
                width=rel_props["width"],
                dashes=dashes,
            )

    return G


def render_capsule_network_mpl(
    capsules: List[Capsule], highlighted_capsule_id: Optional[str] = None
):
    """Render a capsule network visualization using Matplotlib.

    Args:
        capsules: List of capsules to include in the graph
        highlighted_capsule_id: Optional ID of capsule to highlight
    """
    if not capsules:
        st.warning("No capsules available to visualize relationships")
        return

    # Create the graph
    G = create_capsule_network_graph(capsules, highlighted_capsule_id)

    if len(G.nodes()) == 0:
        st.warning("No valid capsules found with proper IDs and types")
        return

    # Set up the figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Use a suitable layout algorithm
    if len(G.nodes()) < 10:
        pos = nx.spring_layout(G, seed=42)
    else:
        pos = nx.kamada_kawai_layout(G)

    # Extract node colors from attributes
    node_colors = [G.nodes[node]["color"] for node in G.nodes()]

    # Draw nodes
    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=[G.nodes[node].get("size", 20) * 20 for node in G.nodes()],
        node_color=node_colors,
        alpha=0.8,
    )

    # Draw edges with their specific styles
    for u, v, edge_attrs in G.edges(data=True):
        edge_color = edge_attrs.get("color", "gray")
        edge_width = edge_attrs.get("width", 1)
        edge_style = "dashed" if edge_attrs.get("dashes", False) else "solid"

        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=[(u, v)],
            width=edge_width,
            edge_color=edge_color,
            style=edge_style,
            alpha=0.7,
            arrows=True,
            arrowstyle="-|>",
            arrowsize=15,
        )

    # Draw labels
    nx.draw_networkx_labels(
        G,
        pos,
        labels={node: G.nodes[node]["label"] for node in G.nodes()},
        font_size=9,
        font_weight="bold",
    )

    # Create legend for relationship types
    legend_patches = []
    for rel_type, rel_props in RELATIONSHIP_TYPES.items():
        if any(rel_type == G.edges[u, v].get("title", "") for u, v in G.edges()):
            line_style = "dashed" if rel_props["dashes"] else "solid"
            patch = mpatches.Patch(
                color=rel_props["color"],
                label=rel_type.replace("_", " ").title(),
                linestyle=line_style,
            )
            legend_patches.append(patch)

    # Add legend if we have relationship types to show
    if legend_patches:
        plt.legend(handles=legend_patches, loc="upper right")

    # Remove axis
    plt.axis("off")
    plt.tight_layout()

    # Display the graph
    st.pyplot(fig)


def render_capsule_network_pyvis(
    capsules: List[Capsule],
    highlighted_capsule_id: Optional[str] = None,
    use_clustering: bool = False,
):
    """Render an interactive capsule network visualization using PyVis.

    Args:
        capsules: List of capsules to include in the graph
        highlighted_capsule_id: Optional ID of capsule to highlight
        use_clustering: Whether to enable clustering by capsule type for large networks
    """
    if not capsules:
        st.warning("No capsules available to visualize relationships")
        return

    # Create the graph
    G = create_capsule_network_graph(capsules, highlighted_capsule_id)

    if len(G.nodes()) == 0:
        st.warning("No valid capsules found with proper IDs and types")
        return

    # Create PyVis network
    net = Network(
        height="600px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="black",
    )

    # Prepare for clustering
    cluster_mapping = {}

    # Add nodes
    for node, node_attrs in G.nodes(data=True):
        # Extract capsule type from the label
        label = node_attrs.get("label", "")
        capsule_type = label.split("\n")[0] if "\n" in label else "Unknown"

        # Track nodes by capsule type for clustering
        if capsule_type not in cluster_mapping:
            cluster_mapping[capsule_type] = []
        cluster_mapping[capsule_type].append(node)

        # Add node
        net.add_node(
            node,
            label=node_attrs.get("label", node),
            title=node_attrs.get("title", node),
            color=node_attrs.get("color", "#bdbdbd"),
            shape=node_attrs.get("shape", "dot"),
            size=node_attrs.get("size", 20),
        )

    # Add edges
    for u, v, edge_attrs in G.edges(data=True):
        net.add_edge(
            u,
            v,
            title=edge_attrs.get("title", ""),
            color=edge_attrs.get("color", "gray"),
            width=edge_attrs.get("width", 1),
            dashes=edge_attrs.get("dashes", False),
        )

    # Configure physics
    net.barnes_hut(
        gravity=-80000, central_gravity=0.3, spring_length=250, spring_strength=0.05
    )

    # Add clustering if enabled and we have a large network
    if use_clustering and len(G.nodes()) > 20:
        for capsule_type, node_ids in cluster_mapping.items():
            if len(node_ids) > 1:  # Only create clusters with multiple nodes
                net.add_node(
                    f"cluster_{capsule_type}",
                    label=f"{capsule_type} Group",
                    shape="ellipse",
                )
                for node_id in node_ids:
                    net.add_edge(
                        f"cluster_{capsule_type}",
                        node_id,
                        color="rgba(0,0,0,0.2)",
                        width=1,
                    )

    # Use temp file for HTML
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
        net.save_graph(tmpfile.name)

        # Display the HTML file
        with open(tmpfile.name) as f:
            html_content = f.read()
            st.components.v1.html(html_content, height=600)

        # Clean up the temp file
        os.unlink(tmpfile.name)


def render_capsule_network(
    capsules: List[Capsule],
    interactive: bool = True,
    highlighted_capsule_id: Optional[str] = None,
):
    """Render a capsule network visualization.

    Args:
        capsules: List of capsules to include in the graph
        interactive: Whether to use interactive PyVis (True) or static Matplotlib (False)
        highlighted_capsule_id: Optional ID of capsule to highlight
    """
    st.subheader("Capsule Relationship Network")
    st.caption(
        "Visualizing relationships between capsules as defined in the UATP 7.0 white paper"
    )

    # Import the legends module
    from visualizer.components.visualization_legends import render_visualization_legends

    # Add the legends in an expander
    render_visualization_legends()

    # Advanced options in an expander
    with st.expander("Network Visualization Options", expanded=False):
        # Performance options
        st.markdown("### Performance Options")

        # Clustering option for large networks
        use_clustering = st.checkbox(
            "Enable clustering by capsule type",
            value=len(capsules) > 30,
            help="Group capsules by type to improve performance and readability for large networks",
        )

        # Node limit warning
        if len(capsules) > 50:
            st.warning(
                f"⚠️ Large network detected ({len(capsules)} nodes). Consider using clustering or static visualization for better performance."
            )

    # Render appropriate visualization
    try:
        if (
            interactive and len(capsules) <= 100
        ):  # Higher limit now that we have clustering
            render_capsule_network_pyvis(
                capsules, highlighted_capsule_id, use_clustering=use_clustering
            )
        else:
            if interactive and len(capsules) > 100:
                st.info(
                    "Interactive visualization disabled for very large networks (>100 nodes). Using static visualization."
                )
            render_capsule_network_mpl(capsules, highlighted_capsule_id)
    except Exception as e:
        st.error(f"Error rendering network visualization: {str(e)}")
