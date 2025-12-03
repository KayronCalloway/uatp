"""
Force-directed graph visualization component for the UATP Capsule Visualizer.
"""

import tempfile
from pathlib import Path
from typing import Dict, List

import networkx as nx
import pandas as pd
import streamlit as st
from capsule_schema import Capsule
from pyvis.network import Network
from streamlit.components.v1 import html

from visualizer.utils.state import select_capsule

# Color palette with semantic meanings for each capsule type
COLOR_PALETTE = {
    "Refusal": "#e57373",  # Soft red
    "Introspective": "#64b5f6",  # Soft blue
    "Joint": "#81c784",  # Soft green
    "Merge": "#ffb74d",  # Soft orange
    "Perspective": "#ba68c8",  # Soft purple
    "DEFAULT": "#90a4ae",  # Soft gray
}


def render_force_graph(capsules: List[Capsule], capsule_map: Dict[str, Capsule]):
    """Render an interactive force-directed graph of the capsule chain."""
    st.header("Capsule Chain Network")

    # Graph settings
    col1, col2, col3 = st.columns(3)
    with col1:
        physics_enabled = st.toggle(
            "Enable Physics", value=True, help="Turn off for static layout"
        )
    with col2:
        show_labels = st.toggle("Show Labels", value=True)
    with col3:
        detail_level = st.select_slider(
            "Detail Level", options=["Low", "Medium", "High"], value="Medium"
        )

    # Build networkx graph
    G = nx.DiGraph()

    # Add nodes with attributes
    for capsule in capsules:
        # Get capsule type for styling
        capsule_type = capsule.capsule_type

        # Determine node color based on capsule type
        color = COLOR_PALETTE.get(capsule_type, COLOR_PALETTE["DEFAULT"])

        # Customize node size based on detail level
        if detail_level == "Low":
            size = 15
        elif detail_level == "Medium":
            size = 25
        else:
            size = 35

        # Create a label based on detail level
        if not show_labels:
            label = ""
        elif detail_level == "Low":
            label = capsule_type[0]  # Just first letter
        else:
            label = f"{capsule_type}\n{capsule.capsule_id[:6]}"

        # Create a title (tooltip) with more information
        title = f"""
        ID: {capsule.capsule_id}
        Type: {capsule_type}
        Agent: {capsule.agent_id}
        Timestamp: {capsule.timestamp}
        """

        # Add the node with all attributes
        G.add_node(
            capsule.capsule_id,
            title=title,
            label=label,
            color=color,
            shape="dot" if capsule_type != "Merge" else "diamond",
            size=size,
            borderWidth=2,
            borderWidthSelected=4,
        )

    # Add edges
    for capsule in capsules:
        # Add regular chain connections
        if capsule.previous_capsule_id:
            G.add_edge(
                capsule.previous_capsule_id,
                capsule.capsule_id,
                arrows="to",
                width=1.5,
                color={"color": "#9e9e9e", "opacity": 0.7},
            )

        # Add merge connections if applicable
        if capsule.capsule_type == "Merge" and hasattr(capsule, "merged_from_ids"):
            for merged_id in capsule.merged_from_ids:
                if merged_id in capsule_map:  # Ensure the merged capsule exists
                    G.add_edge(
                        merged_id,
                        capsule.capsule_id,
                        arrows="to",
                        width=1.5,
                        dashes=True,
                        color={"color": "#9e9e9e", "opacity": 0.5},
                    )

    # Create PyVis network from NetworkX graph
    net = Network(
        notebook=False,
        height="600px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#333333",
    )

    # Configure physics
    if physics_enabled:
        physics = {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": 100,
                    "springConstant": 0.08,
                },
                "maxVelocity": 50,
                "solver": "forceAtlas2Based",
                "timestep": 0.35,
                "stabilization": {"iterations": 150},
            }
        }
    else:
        physics = {"physics": {"enabled": False}}

    # Apply network configuration
    net.options = {
        "nodes": {
            "font": {"size": 12, "face": "Inter"},
            "borderWidth": 1,
            "shadow": {
                "enabled": True,
                "size": 5,
                "x": 0,
                "y": 0,
                "color": "rgba(0,0,0,0.2)",
            },
        },
        "edges": {
            "smooth": {"type": "continuous", "forceDirection": "none"},
            "color": {"inherit": False},
            "width": 1.5,
        },
        "interaction": {
            "hover": True,
            "navigationButtons": False,
            "keyboard": {"enabled": True},
            "multiselect": True,
        },
        **physics,
    }

    # Load the NetworkX graph into PyVis
    net.from_nx(G)

    # Generate HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
        net.save_graph(tmpfile.name)

        # Add custom JavaScript for interactivity
        with open(tmpfile.name) as f:
            html_string = f.read()

        # Insert custom click handler to integrate with Streamlit
        insert_pos = html_string.find("</head>")
        if insert_pos > 0:
            click_handler = """
            <script>
            function sendCapsuleSelection(capsuleId) {
                // Use Streamlit's setComponentValue to update session state
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: capsuleId
                }, '*');
            }

            // Add click event listener to nodes
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(function() {
                    network.on('click', function(params) {
                        if (params.nodes.length > 0) {
                            sendCapsuleSelection(params.nodes[0]);
                        }
                    });
                }, 1000); // Give time for the network to initialize
            });
            </script>
            """
            html_string = (
                html_string[:insert_pos] + click_handler + html_string[insert_pos:]
            )

        # Create a new file with the modified HTML
        with open(tmpfile.name, "w") as f:
            f.write(html_string)

        # Display the interactive graph in Streamlit
        with st.container():
            # Use components.html to render the PyVis graph
            components_value = html(open(tmpfile.name).read(), height=600)

            # If component value changed (node clicked), update selection
            if components_value:
                select_capsule(components_value)
                st.rerun()

    # Clean up the temporary file
    Path(tmpfile.name).unlink(missing_ok=True)

    # Display help text
    st.caption("Click on a node to select and view details. Drag to rearrange.")

    # Add a search box for finding specific capsules
    st.subheader("Search Capsules")
    search_term = st.text_input("Search by ID or content", key="graph_search")

    if search_term:
        # Filter capsules based on search term
        results = []
        for capsule in capsules:
            if (
                search_term.lower() in capsule.capsule_id.lower()
                or search_term.lower() in getattr(capsule, "content", "").lower()
                or search_term.lower() in capsule.capsule_type.lower()
            ):
                results.append(
                    {
                        "ID": capsule.capsule_id,
                        "Type": capsule.capsule_type,
                        "Agent": capsule.agent_id,
                        "Timestamp": capsule.timestamp,
                    }
                )

        # Display results in a table
        if results:
            st.write(f"Found {len(results)} matching capsules:")
            results_df = pd.DataFrame(results)
            st.dataframe(results_df, use_container_width=True)

            # Allow selecting a capsule from results
            selected_result = st.selectbox(
                "Select a capsule to focus",
                options=[r["ID"] for r in results],
                format_func=lambda x: f"{x[:8]}... ({next((r['Type'] for r in results if r['ID'] == x), '')})",
            )

            if selected_result and st.button("Focus Selected"):
                select_capsule(selected_result)
                st.rerun()
        else:
            st.info("No matching capsules found.")
