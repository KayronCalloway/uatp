"""
UATP Capsule Attribution Component

This module provides visualization of economic value attribution to specific capsules,
connecting capsule creation to economic outcomes.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import altair as alt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from capsule_schema import Capsule
from capsules.specialized_capsules import EconomicCapsule
from engine.economic_engine import UatpEconomicEngine


def render_capsule_attribution(
    capsules: List[Capsule], economic_engine: Optional[UatpEconomicEngine] = None
):
    """Render visualization showing attribution of economic value to specific capsules.

    Args:
        capsules: List of capsules to analyze
        economic_engine: Optional economic engine instance
    """
    st.markdown("## Capsule Economic Attribution")
    st.markdown(
        """This visualization shows how specific capsules in the chain contribute to
    economic value generation, enabling attribution-based rewards and dividends."""
    )

    # Filter for economic capsules
    economic_capsules = [c for c in capsules if isinstance(c, EconomicCapsule)]

    if not economic_capsules:
        st.info(
            "No economic capsules found for attribution analysis - using sample data"
        )
        # Generate sample data
        sample_attribution = generate_sample_attribution_data()
        capsule_attribution = sample_attribution
    else:
        # Extract real attribution data
        capsule_attribution = extract_capsule_attribution(
            economic_capsules, economic_engine
        )

    # Display attribution data
    if capsule_attribution:
        tabs = st.tabs(["Attribution Flow", "Value Contribution", "Residual Rights"])

        with tabs[0]:
            render_attribution_flow(capsule_attribution)

        with tabs[1]:
            render_value_contribution(capsule_attribution)

        with tabs[2]:
            render_residual_rights(capsule_attribution)
    else:
        st.warning("Insufficient data for attribution analysis")


def generate_sample_attribution_data() -> List[Dict[str, Any]]:
    """Generate sample attribution data for demonstration purposes."""
    # Create sample capsule IDs
    base_capsules = [f"capsule-{uuid.uuid4()}" for _ in range(5)]
    derivative_capsules = [f"capsule-{uuid.uuid4()}" for _ in range(10)]

    # Sample attribution records
    attribution_data = []

    # Base capsules (original content)
    for i, capsule_id in enumerate(base_capsules):
        attribution_data.append(
            {
                "capsule_id": capsule_id,
                "derived_from": None,
                "agent_id": f"agent-{i+1}",
                "attribution_type": "original",
                "value_generated": round(np.random.uniform(100, 500), 2),
                "timestamp": (
                    datetime.now() - timedelta(days=np.random.randint(1, 30))
                ).isoformat(),
                "residual_share": 1.0,
                "value_recipients": [{"agent": f"agent-{i+1}", "share": 1.0}],
            }
        )

    # Derivative capsules
    for i, capsule_id in enumerate(derivative_capsules):
        # Select a random base capsule this derives from
        base_capsule = np.random.choice(base_capsules)
        base_record = next(
            record
            for record in attribution_data
            if record["capsule_id"] == base_capsule
        )

        # Determine attribution type
        attribution_types = ["remix", "enhancement", "validation", "application"]
        attr_type = np.random.choice(attribution_types)

        # Determine residual distribution based on type
        if attr_type == "remix":
            original_share = 0.6  # Original gets 60%
            derivative_share = 0.4  # Derivative creator gets 40%
        elif attr_type == "enhancement":
            original_share = 0.7
            derivative_share = 0.3
        elif attr_type == "validation":
            original_share = 0.9
            derivative_share = 0.1
        else:  # application
            original_share = 0.5
            derivative_share = 0.5

        # New agent (different from original)
        new_agent = f"agent-{np.random.randint(1, 10)}"
        while new_agent == base_record["agent_id"]:
            new_agent = f"agent-{np.random.randint(1, 10)}"

        # Value generated (typically less than original for derivatives)
        value_generated = round(
            base_record["value_generated"] * np.random.uniform(0.1, 0.8), 2
        )

        attribution_data.append(
            {
                "capsule_id": capsule_id,
                "derived_from": base_capsule,
                "agent_id": new_agent,
                "attribution_type": attr_type,
                "value_generated": value_generated,
                "timestamp": (
                    datetime.now() - timedelta(days=np.random.randint(1, 20))
                ).isoformat(),
                "residual_share": derivative_share,
                "original_share": original_share,
                "value_recipients": [
                    {"agent": base_record["agent_id"], "share": original_share},
                    {"agent": new_agent, "share": derivative_share},
                ],
            }
        )

    return attribution_data


def extract_capsule_attribution(
    economic_capsules: List[EconomicCapsule],
    economic_engine: Optional[UatpEconomicEngine] = None,
) -> List[Dict[str, Any]]:
    """Extract attribution data from real economic capsules.

    Args:
        economic_capsules: List of economic capsules
        economic_engine: Optional economic engine instance

    Returns:
        List of attribution data records
    """
    attribution_data = []

    for capsule in economic_capsules:
        # Skip if missing necessary attributes
        if not hasattr(capsule, "capsule_id") or not hasattr(capsule, "value_amount"):
            continue

        # Get basic attribution data
        attribution_record = {
            "capsule_id": getattr(capsule, "capsule_id", str(uuid.uuid4())),
            "timestamp": getattr(capsule, "timestamp", datetime.now().isoformat()),
            "value_generated": getattr(capsule, "value_amount", 0),
        }

        # Get derivation information if available
        attribution_record["derived_from"] = getattr(capsule, "derived_from", None)

        # Get agent information
        resource_allocation = getattr(capsule, "resource_allocation", {})
        attribution_record["agent_id"] = resource_allocation.get("source", "system")

        # Get attribution type - this would come from capsule metadata
        # In a real system, we'd have specific capsule types or fields for this
        attribution_record["attribution_type"] = getattr(
            capsule, "attribution_type", "original"
        )

        # Get residual rights distribution
        value_recipients = getattr(capsule, "value_recipients", [])
        attribution_record["value_recipients"] = value_recipients

        # Calculate shares for original vs derivative
        if attribution_record["derived_from"] and value_recipients:
            # Find original creator's share
            original_share = sum(
                r.get("share", 0)
                for r in value_recipients
                if r.get("attribution_type") == "original"
            )
            attribution_record["original_share"] = original_share

            # This capsule creator's share
            derivative_share = sum(
                r.get("share", 0)
                for r in value_recipients
                if r.get("attribution_type") == attribution_record["attribution_type"]
            )
            attribution_record["residual_share"] = derivative_share
        else:
            # If it's an original capsule, creator gets full share
            attribution_record["residual_share"] = 1.0

        attribution_data.append(attribution_record)

    return attribution_data


def render_attribution_flow(attribution_data: List[Dict[str, Any]]):
    """Render a visualization of attribution flow between capsules."""
    st.markdown("### Attribution Flow")

    # Create nodes for all capsules
    capsule_ids = set()
    for record in attribution_data:
        capsule_ids.add(record["capsule_id"])
        if record["derived_from"]:
            capsule_ids.add(record["derived_from"])

    # Map capsule IDs to node indices
    capsule_to_node = {capsule_id: i for i, capsule_id in enumerate(capsule_ids)}

    # Create node labels
    node_labels = list(capsule_ids)

    # Create links between capsules
    links = []
    for record in attribution_data:
        if record["derived_from"]:
            source_idx = capsule_to_node[record["derived_from"]]
            target_idx = capsule_to_node[record["capsule_id"]]

            links.append(
                {
                    "source": source_idx,
                    "target": target_idx,
                    "value": record["value_generated"],
                    "type": record["attribution_type"],
                }
            )

    if links:
        # Create a Sankey diagram
        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=node_labels,
                        color="blue",
                    ),
                    link=dict(
                        source=[link["source"] for link in links],
                        target=[link["target"] for link in links],
                        value=[link["value"] for link in links],
                        label=[link["type"] for link in links],
                    ),
                )
            ]
        )

        fig.update_layout(height=500, title_text="Capsule Attribution Flow")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No attribution flows to display")


def render_value_contribution(attribution_data: List[Dict[str, Any]]):
    """Render a visualization of value contribution by capsule."""
    st.markdown("### Value Contribution by Capsule")

    # Convert to DataFrame for easier visualization
    df = pd.DataFrame(attribution_data)

    if not df.empty and "value_generated" in df.columns:
        # Create bar chart of value by capsule
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("capsule_id:N", title="Capsule ID", sort="-y"),
                y=alt.Y("value_generated:Q", title="Value Generated"),
                color=alt.Color("attribution_type:N", title="Attribution Type"),
                tooltip=[
                    "capsule_id",
                    "value_generated",
                    "attribution_type",
                    "agent_id",
                ],
            )
            .properties(height=400)
        )

        st.altair_chart(chart, use_container_width=True)

        # Summary stats
        st.markdown("### Value Generation Summary")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total Value Generated",
                f"{df['value_generated'].sum():.2f}",
                f"{len(df)} capsules",
            )

        with col2:
            if "attribution_type" in df.columns:
                original_value = df[df["attribution_type"] == "original"][
                    "value_generated"
                ].sum()
                st.metric(
                    "Original Content Value",
                    f"{original_value:.2f}",
                    f"{original_value / df['value_generated'].sum():.1%} of total",
                )

        with col3:
            if "agent_id" in df.columns:
                top_agent = df.groupby("agent_id")["value_generated"].sum().idxmax()
                top_agent_value = df.groupby("agent_id")["value_generated"].sum().max()
                st.metric(
                    "Top Value Creator", top_agent, f"{top_agent_value:.2f} value"
                )
    else:
        st.info("No value contribution data available")


def render_residual_rights(attribution_data: List[Dict[str, Any]]):
    """Render a visualization of residual rights distribution."""
    st.markdown("### Residual Rights Distribution")
    st.markdown(
        """This shows how economic value is distributed among creators based on
    attribution relationships between capsules."""
    )

    # Aggregate residuals by agent
    agent_residuals = {}

    for record in attribution_data:
        # Skip records without recipients
        if "value_recipients" not in record:
            continue

        value_generated = record.get("value_generated", 0)

        for recipient in record["value_recipients"]:
            agent = recipient.get("agent")
            share = recipient.get("share", 0)

            if agent:
                if agent not in agent_residuals:
                    agent_residuals[agent] = 0

                agent_residuals[agent] += value_generated * share

    if agent_residuals:
        # Create DataFrame for visualization
        residual_df = pd.DataFrame(
            {
                "Agent": list(agent_residuals.keys()),
                "Residual Value": list(agent_residuals.values()),
            }
        )

        # Sort by residual value
        residual_df = residual_df.sort_values("Residual Value", ascending=False)

        # Create chart
        chart = (
            alt.Chart(residual_df)
            .mark_bar()
            .encode(
                x=alt.X("Agent:N", title="Agent", sort="-y"),
                y=alt.Y("Residual Value:Q", title="Residual Value"),
                tooltip=["Agent", "Residual Value"],
            )
            .properties(height=400)
        )

        st.altair_chart(chart, use_container_width=True)

        # Create pie chart of distribution
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=residual_df["Agent"],
                    values=residual_df["Residual Value"],
                    hole=0.3,
                )
            ]
        )

        fig.update_layout(height=500, title_text="Residual Value Distribution")
        st.plotly_chart(fig, use_container_width=True)

        # Show top recipients
        st.markdown("### Top Value Recipients")
        st.dataframe(residual_df.head(10))
    else:
        st.info("No residual rights data available")
