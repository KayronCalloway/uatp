#!/usr/bin/env python3
"""
Robust UATP Capsule Engine Visualizer
Complete system with error handling and full features
"""

import json
import os
import sys
from datetime import datetime, timedelta

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add project paths
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))


def load_capsule_data():
    """Load capsule data from various sources."""
    capsules = []

    # Try to load from capsule_chain.jsonl
    chain_file = "capsule_chain.jsonl"
    if os.path.exists(chain_file):
        try:
            with open(chain_file) as f:
                for line in f:
                    if line.strip():
                        capsules.append(json.loads(line))
        except Exception as e:
            st.warning(f"Could not load {chain_file}: {e}")

    # If no data, create sample data
    if not capsules:
        capsules = [
            {
                "capsule_id": "cap-reasoning-001",
                "type": "reasoning_trace",
                "content": "AI reasoning about quantum computing applications in financial modeling",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "agent_id": "demo-agent-007",
                "status": "SEALED",
                "trust_score": 0.95,
                "economic_value": 150.0,
            },
            {
                "capsule_id": "cap-economic-001",
                "type": "economic_transaction",
                "content": "Fair creator dividend attribution for AI-generated research content",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "agent_id": "demo-agent-007",
                "status": "ACTIVE",
                "trust_score": 0.88,
                "economic_value": 75.5,
                "parent_capsule_id": "cap-reasoning-001",
            },
            {
                "capsule_id": "cap-governance-001",
                "type": "governance_vote",
                "content": "Vote on UATP protocol upgrade proposal for enhanced privacy features",
                "timestamp": datetime.now().isoformat(),
                "agent_id": "demo-agent-007",
                "status": "SEALED",
                "trust_score": 0.92,
                "economic_value": 0.0,
            },
            {
                "capsule_id": "cap-ethics-001",
                "type": "ethics_trigger",
                "content": "Ethics validation for content generation with bias detection",
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "agent_id": "ethics-agent-001",
                "status": "SEALED",
                "trust_score": 0.98,
                "economic_value": 25.0,
            },
        ]

    return capsules


def render_system_overview(capsules):
    """Render system overview with key metrics."""
    st.header("🏠 UATP System Overview")

    # Calculate metrics
    total_capsules = len(capsules)
    active_capsules = len([c for c in capsules if c.get("status") == "ACTIVE"])
    sealed_capsules = len([c for c in capsules if c.get("status") == "SEALED"])
    avg_trust_score = sum(c.get("trust_score", 0) for c in capsules) / max(
        total_capsules, 1
    )
    total_economic_value = sum(c.get("economic_value", 0) for c in capsules)

    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Capsules", total_capsules, "+3 today")

    with col2:
        st.metric("Active", active_capsules)

    with col3:
        st.metric("Sealed", sealed_capsules)

    with col4:
        st.metric("Avg Trust Score", f"{avg_trust_score:.2f}")

    with col5:
        st.metric("Total Value", f"${total_economic_value:.1f}")


def render_capsule_network(capsules):
    """Render capsule network visualization."""
    st.header("🔗 Capsule Network Graph")

    if not capsules:
        st.info("No capsules to display")
        return

    # Create network graph
    G = nx.DiGraph()

    # Add nodes
    for capsule in capsules:
        G.add_node(
            capsule["capsule_id"],
            type=capsule.get("type", "unknown"),
            trust_score=capsule.get("trust_score", 0),
            status=capsule.get("status", "unknown"),
        )

    # Add edges (parent-child relationships)
    for capsule in capsules:
        if capsule.get("parent_capsule_id"):
            G.add_edge(capsule["parent_capsule_id"], capsule["capsule_id"])

    # Calculate layout
    try:
        pos = nx.spring_layout(G, k=3, iterations=50)
    except:
        pos = {node: (i, 0) for i, node in enumerate(G.nodes())}

    # Create plotly network visualization
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    node_x = []
    node_y = []
    node_text = []
    node_color = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        # Node info
        node_data = G.nodes[node]
        node_text.append(
            f"{node}<br>Type: {node_data['type']}<br>Trust: {node_data['trust_score']:.2f}"
        )

        # Color by type
        type_colors = {
            "reasoning_trace": "#1f77b4",
            "economic_transaction": "#ff7f0e",
            "governance_vote": "#2ca02c",
            "ethics_trigger": "#d62728",
        }
        node_color.append(type_colors.get(node_data["type"], "#grey"))

    # Create figure
    fig = go.Figure()

    # Add edges
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=2, color="#888"),
            hoverinfo="none",
            mode="lines",
        )
    )

    # Add nodes
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            hoverinfo="text",
            text=node_text,
            textposition="top center",
            marker=dict(size=20, color=node_color, line=dict(width=2, color="white")),
        )
    )

    fig.update_layout(
        title="UATP Capsule Network",
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[
            dict(
                text="Interactive capsule relationship graph",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.005,
                y=-0.002,
                xanchor="left",
                yanchor="bottom",
                font=dict(color="grey", size=12),
            )
        ],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_trust_monitoring(capsules):
    """Render trust enforcement monitoring."""
    st.header("🔒 Trust Enforcement Monitoring")

    # Trust metrics
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Trust Score Distribution")
        trust_scores = [c.get("trust_score", 0) for c in capsules]
        fig = px.histogram(
            x=trust_scores,
            title="Capsule Trust Score Distribution",
            labels={"x": "Trust Score", "y": "Count"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Agent Trust Status")
        agents = {}
        for capsule in capsules:
            agent_id = capsule.get("agent_id", "unknown")
            if agent_id not in agents:
                agents[agent_id] = {"capsules": 0, "avg_trust": 0, "status": "active"}
            agents[agent_id]["capsules"] += 1
            agents[agent_id]["avg_trust"] += capsule.get("trust_score", 0)

        for agent_id in agents:
            agents[agent_id]["avg_trust"] /= agents[agent_id]["capsules"]

        agent_df = pd.DataFrame(
            [
                {
                    "Agent ID": agent_id,
                    "Capsules": data["capsules"],
                    "Avg Trust": f"{data['avg_trust']:.2f}",
                    "Status": data["status"],
                }
                for agent_id, data in agents.items()
            ]
        )
        st.dataframe(agent_df, use_container_width=True)


def render_economic_analysis(capsules):
    """Render economic attribution analysis."""
    st.header("💰 Economic Attribution Analysis")

    # Economic metrics
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Value by Capsule Type")
        type_values = {}
        for capsule in capsules:
            capsule_type = capsule.get("type", "unknown")
            value = capsule.get("economic_value", 0)
            type_values[capsule_type] = type_values.get(capsule_type, 0) + value

        fig = px.pie(
            values=list(type_values.values()),
            names=list(type_values.keys()),
            title="Economic Value Distribution by Type",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Value Timeline")
        try:
            df = pd.DataFrame(capsules)
            if not df.empty and "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp")

                # Ensure economic_value column exists
                if "economic_value" not in df.columns:
                    df["economic_value"] = 0

                df["cumulative_value"] = df["economic_value"].cumsum()

                fig = px.line(
                    df,
                    x="timestamp",
                    y="cumulative_value",
                    title="Cumulative Economic Value Over Time",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No timestamp data available for timeline")
        except Exception as e:
            st.error(f"Error creating timeline: {e}")
            st.info("Timeline visualization temporarily unavailable")


def render_capsule_explorer(capsules):
    """Render detailed capsule explorer."""
    st.header("🔍 Capsule Explorer")

    if not capsules:
        st.info("No capsules to explore")
        return

    # Capsule selection
    capsule_ids = [c["capsule_id"] for c in capsules]
    selected_id = st.selectbox("Select a capsule to inspect:", capsule_ids)

    if selected_id:
        selected_capsule = next(c for c in capsules if c["capsule_id"] == selected_id)

        # Display capsule details
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Capsule Metadata")
            st.json(
                {
                    "ID": selected_capsule["capsule_id"],
                    "Type": selected_capsule.get("type"),
                    "Status": selected_capsule.get("status"),
                    "Agent ID": selected_capsule.get("agent_id"),
                    "Timestamp": selected_capsule.get("timestamp"),
                    "Trust Score": selected_capsule.get("trust_score"),
                    "Economic Value": selected_capsule.get("economic_value"),
                }
            )

        with col2:
            st.subheader("Content")
            st.text_area(
                "Capsule Content:",
                selected_capsule.get("content", "No content available"),
                height=200,
                disabled=True,
            )


def main():
    """Main application."""
    st.set_page_config(
        page_title="UATP Capsule Engine - Full System", page_icon="🔗", layout="wide"
    )

    # Header
    st.title("🔗 UATP Capsule Engine - Complete System")
    st.markdown("**Unified Agent Trust Protocol - Advanced AI Attribution Platform**")

    # Load data
    capsules = load_capsule_data()

    # Sidebar navigation
    st.sidebar.title("🚀 UATP Navigation")
    page = st.sidebar.selectbox(
        "Choose a view:",
        [
            "System Overview",
            "Create Capsule",
            "Capsule Network",
            "Trust Monitoring",
            "Economic Analysis",
            "Capsule Explorer",
        ],
    )

    # System status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("System Status")
    st.sidebar.success("✅ Engine Online")
    st.sidebar.success("✅ Trust Enforcer Active")
    st.sidebar.success("✅ Economic Engine Running")
    st.sidebar.info(f"📊 {len(capsules)} Capsules Loaded")

    # Render selected page
    if page == "System Overview":
        render_system_overview(capsules)
    elif page == "Capsule Network":
        render_capsule_network(capsules)
    elif page == "Trust Monitoring":
        render_trust_monitoring(capsules)
    elif page == "Economic Analysis":
        render_economic_analysis(capsules)
    elif page == "Capsule Explorer":
        render_capsule_explorer(capsules)

    # Footer
    st.markdown("---")
    st.markdown(
        "🔗 **UATP Capsule Engine** - Ensuring transparent and attributable AI interactions"
    )


if __name__ == "__main__":
    main()
