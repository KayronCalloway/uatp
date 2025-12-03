"""
Complete UATP System Network Graph Visualization
Shows all providers, capsule types, system components, and their relationships
"""

import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components
from typing import Dict, List, Any
import tempfile
import os


class UATPSystemGraph:
    """Visualize the complete UATP ecosystem as an interactive node graph"""

    def __init__(self):
        self.net = Network(
            height="800px",
            width="100%",
            bgcolor="#1e1e1e",
            font_color="white",
            directed=True,
        )
        self.net.barnes_hut(
            gravity=-8000,
            central_gravity=0.3,
            spring_length=200,
            spring_strength=0.001,
            damping=0.09,
        )

    def build_complete_system_graph(self):
        """Build the complete UATP system graph with all components"""

        # ===== CORE ENGINE =====
        self.net.add_node(
            "capsule_engine",
            label="UATP Capsule Engine",
            shape="star",
            color="#ff6b6b",
            size=50,
            title="Core attribution engine",
        )

        # ===== LLM PROVIDERS =====
        llm_providers = [
            ("openai", "OpenAI", "#10a37f"),
            ("anthropic", "Anthropic", "#d97706"),
            ("claude", "Claude", "#8b5cf6"),
        ]

        for node_id, label, color in llm_providers:
            self.net.add_node(
                node_id,
                label=label,
                shape="dot",
                color=color,
                size=30,
                title=f"LLM Provider: {label}",
            )
            self.net.add_edge(
                "capsule_engine", node_id, title="integrates", color="#666"
            )

        # ===== SPATIAL AI PROVIDERS =====
        spatial_providers = [
            ("zed_camera", "ZED Camera", "#3b82f6"),
            ("velodyne_lidar", "Velodyne LiDAR", "#6366f1"),
            ("moveit_planner", "MoveIt Planner", "#8b5cf6"),
            ("ur5_controller", "UR5 Controller", "#a855f7"),
            ("gps_imu", "GPS+IMU Nav", "#c084fc"),
            ("robotiq_gripper", "Robotiq Gripper", "#d8b4fe"),
        ]

        for node_id, label, color in spatial_providers:
            self.net.add_node(
                node_id,
                label=label,
                shape="dot",
                color=color,
                size=30,
                title=f"Spatial AI Provider: {label}",
            )
            self.net.add_edge(
                "capsule_engine", node_id, title="integrates", color="#666"
            )

        # ===== CAPSULE TYPES =====
        capsule_types = [
            ("chat", "Chat", "#22c55e"),
            ("reasoning", "Reasoning", "#16a34a"),
            ("joint", "Joint", "#15803d"),
            ("refusal", "Refusal", "#dc2626"),
            ("consent", "Consent", "#ea580c"),
            ("perspective", "Perspective", "#d97706"),
            ("spatial_perception", "Spatial Perception", "#0ea5e9"),
            ("spatial_planning", "Spatial Planning", "#0284c7"),
            ("spatial_control", "Spatial Control", "#0369a1"),
            ("spatial_navigation", "Spatial Navigation", "#075985"),
            ("spatial_manipulation", "Spatial Manipulation", "#0c4a6e"),
        ]

        for node_id, label, color in capsule_types:
            self.net.add_node(
                node_id,
                label=label,
                shape="box",
                color=color,
                size=25,
                title=f"Capsule Type: {label}",
            )

        # ===== CONNECTIONS: PROVIDERS → CAPSULE TYPES =====
        # LLM providers create chat/reasoning capsules
        for provider in ["openai", "anthropic", "claude"]:
            self.net.add_edge(provider, "chat", title="creates", color="#4ade80")
            self.net.add_edge(provider, "reasoning", title="creates", color="#4ade80")
            self.net.add_edge(provider, "joint", title="creates", color="#4ade80")
            self.net.add_edge(provider, "refusal", title="creates", color="#f87171")
            self.net.add_edge(provider, "consent", title="creates", color="#fb923c")
            self.net.add_edge(provider, "perspective", title="creates", color="#fbbf24")

        # Spatial perception providers
        self.net.add_edge(
            "zed_camera", "spatial_perception", title="creates", color="#60a5fa"
        )
        self.net.add_edge(
            "velodyne_lidar", "spatial_perception", title="creates", color="#60a5fa"
        )

        # Spatial planning providers
        self.net.add_edge(
            "moveit_planner", "spatial_planning", title="creates", color="#60a5fa"
        )

        # Spatial control providers
        self.net.add_edge(
            "ur5_controller", "spatial_control", title="creates", color="#60a5fa"
        )
        self.net.add_edge(
            "robotiq_gripper", "spatial_manipulation", title="creates", color="#60a5fa"
        )

        # Spatial navigation providers
        self.net.add_edge(
            "gps_imu", "spatial_navigation", title="creates", color="#60a5fa"
        )

        # ===== SYSTEM COMPONENTS =====
        system_components = [
            (
                "trust_scorer",
                "Trust Scorer",
                "#f59e0b",
                "Evaluates provider reliability",
            ),
            ("fcde", "FCDE Economics", "#eab308", "Distributes economic value"),
            (
                "physical_ai_insurance",
                "Physical AI Insurance",
                "#84cc16",
                "Assesses physical risk",
            ),
            (
                "verification_system",
                "Verification System",
                "#10b981",
                "Cryptographic verification",
            ),
            ("governance", "Governance", "#14b8a6", "Consent & refusal management"),
        ]

        for node_id, label, color, description in system_components:
            self.net.add_node(
                node_id,
                label=label,
                shape="diamond",
                color=color,
                size=35,
                title=description,
            )
            # All system components connect to capsule engine
            self.net.add_edge("capsule_engine", node_id, title="uses", color="#94a3b8")

        # ===== SYSTEM COMPONENT INTERACTIONS =====
        # Trust scorer evaluates all providers
        for provider_id, _, _ in llm_providers + spatial_providers:
            self.net.add_edge(
                "trust_scorer",
                provider_id,
                title="evaluates",
                color="#fbbf24",
                dashes=True,
            )

        # FCDE distributes to all providers
        for provider_id, _, _ in llm_providers + spatial_providers:
            self.net.add_edge(
                "fcde", provider_id, title="pays", color="#a3e635", dashes=True
            )

        # Insurance assesses spatial capsule types
        for capsule_type in [
            "spatial_perception",
            "spatial_planning",
            "spatial_control",
            "spatial_navigation",
            "spatial_manipulation",
        ]:
            self.net.add_edge(
                "physical_ai_insurance",
                capsule_type,
                title="assesses",
                color="#86efac",
                dashes=True,
            )

        # Verification system verifies all capsule types
        for node_id, _, _ in capsule_types:
            self.net.add_edge(
                "verification_system",
                node_id,
                title="verifies",
                color="#6ee7b7",
                dashes=True,
            )

        # Governance manages consent/refusal
        self.net.add_edge(
            "governance", "consent", title="manages", color="#5eead4", dashes=True
        )
        self.net.add_edge(
            "governance", "refusal", title="manages", color="#5eead4", dashes=True
        )

        # ===== CAPSULE CHAINS (examples) =====
        # Show example chain: perception → planning → control
        self.net.add_edge(
            "spatial_perception",
            "spatial_planning",
            title="chains_to",
            color="#38bdf8",
            width=3,
        )
        self.net.add_edge(
            "spatial_planning",
            "spatial_control",
            title="chains_to",
            color="#38bdf8",
            width=3,
        )

        # Show example chain: chat → reasoning → joint
        self.net.add_edge(
            "chat", "reasoning", title="chains_to", color="#4ade80", width=3
        )
        self.net.add_edge(
            "reasoning", "joint", title="chains_to", color="#4ade80", width=3
        )

    def render(self, height="800px"):
        """Render the graph in Streamlit"""
        # Build the complete graph
        self.build_complete_system_graph()

        # Save to temporary HTML file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w")
        self.net.save_graph(temp_file.name)
        temp_file.close()

        # Read and display
        with open(temp_file.name, "r", encoding="utf-8") as f:
            html_content = f.read()

        components.html(html_content, height=int(height.replace("px", "")))

        # Cleanup
        os.unlink(temp_file.name)


def render_system_graph():
    """Main function to render the UATP system graph"""
    st.title("🌐 Complete UATP System Network")

    st.markdown(
        """
    This interactive graph shows the entire UATP ecosystem:

    **Node Types:**
    - 🔴 **Core Engine** (red star) - The UATP Capsule Engine
    - 🟢 **LLM Providers** (green dots) - OpenAI, Anthropic, Claude
    - 🔵 **Spatial AI Providers** (blue dots) - Cameras, LiDAR, planners, controllers
    - 🟦 **Capsule Types** (colored boxes) - All capsule types (chat, spatial_perception, etc.)
    - 🔶 **System Components** (orange diamonds) - Trust scorer, FCDE, insurance, verification, governance

    **Edge Types:**
    - **Solid lines** - Direct relationships (integrates, creates, uses)
    - **Dashed lines** - System interactions (evaluates, pays, assesses, verifies, manages)
    - **Thick lines** - Capsule chains (chains_to)

    **Interact with the graph:**
    - Drag nodes to rearrange
    - Hover over nodes/edges for details
    - Zoom and pan to explore
    """
    )

    # Render the graph
    graph = UATPSystemGraph()
    graph.render(height="800px")

    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("LLM Providers", "3")
    with col2:
        st.metric("Spatial Providers", "6")
    with col3:
        st.metric("Capsule Types", "11")
    with col4:
        st.metric("System Components", "5")


if __name__ == "__main__":
    render_system_graph()
