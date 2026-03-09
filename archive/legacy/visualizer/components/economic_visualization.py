"""UATP 7.0 Economic Visualization Components

This module provides visualization components for the economic aspects
of UATP 7.0, including token flows, value distribution, stake and reputation.
"""

from datetime import datetime, timedelta
from typing import List, Optional

import altair as alt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from capsule_schema import Capsule
from capsules.specialized_capsules import EconomicCapsule
from engine.economic_engine import EconomicTransactionType, UatpEconomicEngine

from visualizer.components.capsule_attribution import render_capsule_attribution

# Import visualization components
from visualizer.components.insurance_risk_metrics import render_insurance_risk_metrics


def render_economic_dashboard(economic_engine: UatpEconomicEngine):
    """Render a dashboard showing economic activity and state.

    Args:
        economic_engine: The economic engine instance
    """
    st.markdown("## UATP 7.0 Economic Dashboard")

    # Get economic summary
    summary = economic_engine.get_economic_summary()

    # Display high-level metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Value in System", f"{summary['total_balance']:.2f}")

    with col2:
        st.metric("Total Staked Value", f"{summary['total_staked']:.2f}")

    with col3:
        st.metric("Active Agents", summary["agent_count"])

    # Display top agents by different metrics
    st.markdown("### Top Agents")
    tab1, tab2, tab3 = st.tabs(["By Balance", "By Stake", "By Reputation"])

    with tab1:
        if summary["top_by_balance"]:
            df = pd.DataFrame(
                {
                    "Agent": list(summary["top_by_balance"].keys()),
                    "Balance": list(summary["top_by_balance"].values()),
                }
            )

            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X("Balance:Q", title="Balance"),
                    y=alt.Y("Agent:N", sort="-x", title="Agent ID"),
                )
                .properties(height=min(300, len(df) * 30))
            )

            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No balance data available")

    with tab2:
        if summary["top_by_stake"]:
            df = pd.DataFrame(
                {
                    "Agent": list(summary["top_by_stake"].keys()),
                    "Stake": list(summary["top_by_stake"].values()),
                }
            )

            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X("Stake:Q", title="Stake Amount"),
                    y=alt.Y("Agent:N", sort="-x", title="Agent ID"),
                )
                .properties(height=min(300, len(df) * 30))
            )

            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No stake data available")

    with tab3:
        if summary["top_by_reputation"]:
            df = pd.DataFrame(
                {
                    "Agent": list(summary["top_by_reputation"].keys()),
                    "Reputation": list(summary["top_by_reputation"].values()),
                }
            )

            # Use a color scale for reputation
            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X("Reputation:Q", title="Reputation Score"),
                    y=alt.Y("Agent:N", sort="-x", title="Agent ID"),
                    color=alt.Color("Reputation:Q", scale=alt.Scale(scheme="viridis")),
                )
                .properties(height=min(300, len(df) * 30))
            )

            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No reputation data available")


def generate_sample_economic_data():
    """Generate sample economic data for testing visualizations.

    Returns:
        Tuple of (transactions, agent_balances, agent_stakes, agent_reputations)
    """
    # Get transaction types from the EconomicTransactionType class
    transaction_types = [
        EconomicTransactionType.VALUE_CREATION,
        EconomicTransactionType.VALUE_TRANSFER,
        EconomicTransactionType.VERIFICATION_REWARD,
        EconomicTransactionType.STAKE_DEPOSIT,
        EconomicTransactionType.STAKE_WITHDRAWAL,
        EconomicTransactionType.DIVIDEND_DISTRIBUTION,
        EconomicTransactionType.PENALTY,
        EconomicTransactionType.BOUNTY_REWARD,
    ]

    # Sample transactions
    transactions = [
        {
            "transaction_id": f"tx-{i}",
            "timestamp": (datetime.now() - timedelta(days=30 - i)).isoformat(),
            "transaction_type": np.random.choice(transaction_types),
            "amount": round(np.random.uniform(1.0, 100.0), 2),
            "from_agent": f"agent-{np.random.randint(1, 6)}",
            "to_agent": f"agent-{np.random.randint(1, 6)}",
            "related_capsule_id": f"capsule-{i}",
        }
        for i in range(30)
    ]

    # Sample agent data
    agent_ids = [f"agent-{i}" for i in range(1, 6)]

    agent_balances = {}
    agent_stakes = {}
    agent_reputations = {}

    for agent_id in agent_ids:
        agent_balances[agent_id] = round(np.random.uniform(100.0, 1000.0), 2)
        agent_stakes[agent_id] = round(np.random.uniform(10.0, 500.0), 2)
        agent_reputations[agent_id] = round(np.random.uniform(0.1, 1.0), 2)

    return transactions, agent_balances, agent_stakes, agent_reputations


def analyze_economic_transactions(capsules: List[Capsule]):
    """Analyze and visualize economic transactions in the capsule chain.

    Args:
        capsules: List of capsules to analyze
    """
    st.markdown("## Economic Transaction Analysis")

    # Filter for economic capsules
    economic_capsules = [c for c in capsules if isinstance(c, EconomicCapsule)]

    # Flag to indicate if we're using sample data
    using_sample_data = False

    if not economic_capsules:
        st.info(
            "No economic capsules found in the chain - using sample data for demonstration"
        )
        # Generate sample data for demonstration
        (
            sample_transactions,
            agent_balances,
            agent_stakes,
            agent_reputations,
        ) = generate_sample_economic_data()
        using_sample_data = True

        # Create transaction data directly from samples
        transaction_data = []
        for tx in sample_transactions:
            transaction_data.append(
                {
                    "capsule_id": tx["related_capsule_id"],
                    "timestamp": tx["timestamp"],
                    "transaction_type": tx["transaction_type"],
                    "value_amount": tx["amount"],
                    "recipient_count": 1,  # Sample data has 1:1 transactions
                    "sender": tx["from_agent"],
                    "recipients": [tx["to_agent"]],
                }
            )
    else:
        st.info(f"Found {len(economic_capsules)} economic capsules in the chain")
        # Extract transaction data from actual capsules
        transaction_data = []
        for capsule in economic_capsules:
            # Get timestamp
            timestamp = getattr(capsule, "timestamp", datetime.utcnow())

            # Check capsule.metadata for transaction_type and value_amount
            transaction_type = "Unknown"
            value_amount = 0.0
            recipients = []
            sender = ""

            # Get transaction type
            transaction_type = getattr(capsule, "economic_event_type", "unknown")

            # Get value amount
            value_amount = getattr(capsule, "value_amount", 0.0)

            # Get recipients
            recipients = getattr(capsule, "value_recipients", {})

            transaction_data.append(
                {
                    "capsule_id": capsule.capsule_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "transaction_type": transaction_type,
                    "value_amount": value_amount,
                    "recipient_count": len(recipients),
                    "recipients": recipients,
                }
            )

    # Create DataFrame
    df = pd.DataFrame(transaction_data)

    # Transaction type distribution
    st.markdown("### Transaction Type Distribution")

    type_counts = df["transaction_type"].value_counts().reset_index()
    type_counts.columns = ["Transaction Type", "Count"]

    chart = (
        alt.Chart(type_counts)
        .mark_arc()
        .encode(
            theta="Count:Q",
            color="Transaction Type:N",
            tooltip=["Transaction Type", "Count"],
        )
        .properties(height=300)
    )

    st.altair_chart(chart, use_container_width=True)

    # Value flow over time
    st.markdown("### Value Flow Over Time")

    # Ensure timestamp is datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Group by day and transaction type
    df["date"] = df["timestamp"].dt.date
    daily_value = (
        df.groupby(["date", "transaction_type"])["value_amount"].sum().reset_index()
    )

    # Plot
    chart = (
        alt.Chart(daily_value)
        .mark_line(point=True)
        .encode(
            x="date:T",
            y="value_amount:Q",
            color="transaction_type:N",
            tooltip=["date", "transaction_type", "value_amount"],
        )
        .properties(height=300)
    )

    st.altair_chart(chart, use_container_width=True)

    # Value distribution network
    st.markdown("### Value Distribution Network")

    # Extract all unique agents
    all_agents = set()
    links = []

    for capsule in economic_capsules:
        # Skip if missing needed attributes
        if not hasattr(capsule, "economic_event_type") or not hasattr(
            capsule, "value_recipients"
        ):
            continue

        # Get source
        resource_allocation = getattr(capsule, "resource_allocation", {})
        source = resource_allocation.get("source", "system")

        all_agents.add(source)

        # Get recipients and value amounts
        recipients = capsule.value_recipients
        value_amount = getattr(capsule, "value_amount", 1.0)

        for recipient, share in recipients.items():
            all_agents.add(recipient)
            links.append(
                {
                    "source": source,
                    "target": recipient,
                    "value": value_amount * share,
                    "transaction_type": capsule.economic_event_type,
                }
            )

    # Create Sankey diagram
    if links:
        # Create node mapping
        nodes = list(all_agents)
        node_indices = {node: i for i, node in enumerate(nodes)}

        # Create links with indices
        sankey_links = [
            {
                "source": node_indices[link["source"]],
                "target": node_indices[link["target"]],
                "value": link["value"],
                "type": link["transaction_type"],
            }
            for link in links
        ]

        # Create color mapping for transaction types
        transaction_types = {link["transaction_type"] for link in links}
        colors = px.colors.qualitative.Plotly[: len(transaction_types)]
        color_map = {t: c for t, c in zip(transaction_types, colors)}

        # Create figure
        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=nodes,
                    ),
                    link=dict(
                        source=[link["source"] for link in sankey_links],
                        target=[link["target"] for link in sankey_links],
                        value=[link["value"] for link in sankey_links],
                        color=[color_map[link["type"]] for link in sankey_links],
                    ),
                )
            ]
        )

        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient data for value distribution network")

    # Add insurance risk metrics visualization
    st.markdown("---")
    render_insurance_risk_metrics(transaction_data)

    # Add capsule attribution visualization
    st.markdown("---")
    render_capsule_attribution(capsules)


def render_agent_economic_profile(
    economic_engine: UatpEconomicEngine, agent_id: Optional[str] = None
):
    """Render economic profile for a specific agent.

    Args:
        economic_engine: The economic engine instance
        agent_id: Optional agent ID to display profile for, if None user can select
    """
    st.markdown("## Agent Economic Profile")

    # Get all agents with economic activity
    all_agents = set(economic_engine.agent_balances.keys()) | set(
        economic_engine.agent_stakes.keys()
    )

    if not all_agents:
        st.info("No agents with economic activity found")
        return

    # Allow user to select agent if not specified
    if agent_id is None or agent_id not in all_agents:
        agent_id = st.selectbox("Select Agent", list(all_agents))

    if not agent_id:
        return

    # Display agent metrics
    balance = economic_engine.get_agent_balance(agent_id)
    stake = economic_engine.get_agent_stake(agent_id)
    reputation = economic_engine.get_agent_reputation(agent_id)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Balance", f"{balance:.2f}")

    with col2:
        st.metric("Stake", f"{stake:.2f}")

    with col3:
        st.metric("Reputation", f"{reputation:.2f}")

    # Reputation gauge
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=reputation,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Reputation Score"},
            gauge={
                "axis": {"range": [0, 1]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 0.3], "color": "red"},
                    {"range": [0.3, 0.7], "color": "yellow"},
                    {"range": [0.7, 1.0], "color": "green"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": reputation,
                },
            },
        )
    )

    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

    # Economic activity (mock data for now - would be replaced with actual history)
    st.markdown("### Recent Economic Activity")

    # In a real implementation, we would get actual transaction history for this agent
    # For now, create mock data
    now = datetime.utcnow()

    data = []
    for i in range(10):
        data.append(
            {
                "timestamp": (now - timedelta(days=i)).strftime("%Y-%m-%d"),
                "transaction_type": np.random.choice(
                    [
                        EconomicTransactionType.VALUE_TRANSFER,
                        EconomicTransactionType.STAKE_DEPOSIT,
                        EconomicTransactionType.VERIFICATION_REWARD,
                    ]
                ),
                "amount": np.random.uniform(0.1, 10.0),
            }
        )

    df = pd.DataFrame(data)

    st.dataframe(df)

    # Provide action buttons
    st.markdown("### Agent Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Stake Tokens"):
            st.info("Staking functionality would be implemented here")

    with col2:
        if st.button("Withdraw Stake"):
            st.info("Withdrawal functionality would be implemented here")


def render_dividend_calculator():
    """Render a dividend calculation simulator."""
    st.markdown("## Dividend Calculator")
    st.markdown(
        """This tool helps simulate how dividends would be distributed
    based on contribution, stake, and reputation."""
    )

    # Input for value amount
    value_amount = st.number_input(
        "Total Value Amount", min_value=0.0, value=100.0, step=10.0
    )

    # Input for weights
    col1, col2, col3 = st.columns(3)

    with col1:
        contribution_weight = st.slider(
            "Contribution Weight", min_value=0.0, max_value=1.0, value=0.5, step=0.05
        )

    with col2:
        stake_weight = st.slider(
            "Stake Weight", min_value=0.0, max_value=1.0, value=0.3, step=0.05
        )

    with col3:
        reputation_weight = st.slider(
            "Reputation Weight", min_value=0.0, max_value=1.0, value=0.2, step=0.05
        )

    # Ensure weights sum to 1.0
    total_weight = contribution_weight + stake_weight + reputation_weight
    if abs(total_weight - 1.0) > 0.01:
        st.warning(f"Weights sum to {total_weight:.2f}, normalizing to 1.0")

        # Normalize weights
        contribution_weight /= total_weight
        stake_weight /= total_weight
        reputation_weight /= total_weight

    # Agent configuration
    st.markdown("### Configure Agents")

    # Start with a default set of agents
    if "dividend_agents" not in st.session_state:
        st.session_state.dividend_agents = [
            {"id": "agent1", "contribution": 0.4, "stake": 50.0, "reputation": 0.8},
            {"id": "agent2", "contribution": 0.3, "stake": 30.0, "reputation": 0.7},
            {"id": "agent3", "contribution": 0.2, "stake": 15.0, "reputation": 0.5},
            {"id": "agent4", "contribution": 0.1, "stake": 5.0, "reputation": 0.3},
        ]

    # Allow adding/removing agents
    if st.button("Add Agent"):
        new_id = f"agent{len(st.session_state.dividend_agents) + 1}"
        st.session_state.dividend_agents.append(
            {"id": new_id, "contribution": 0.0, "stake": 0.0, "reputation": 0.5}
        )

    # Display and edit agents
    for i, agent in enumerate(st.session_state.dividend_agents):
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

        with col1:
            st.session_state.dividend_agents[i]["id"] = st.text_input(
                f"ID #{i+1}", value=agent["id"], key=f"id_{i}"
            )

        with col2:
            st.session_state.dividend_agents[i]["contribution"] = st.number_input(
                f"Contribution #{i+1}",
                min_value=0.0,
                max_value=1.0,
                value=float(agent["contribution"]),
                step=0.05,
                format="%.2f",
                key=f"contrib_{i}",
            )

        with col3:
            st.session_state.dividend_agents[i]["stake"] = st.number_input(
                f"Stake #{i+1}",
                min_value=0.0,
                value=float(agent["stake"]),
                step=5.0,
                key=f"stake_{i}",
            )

        with col4:
            st.session_state.dividend_agents[i]["reputation"] = st.number_input(
                f"Reputation #{i+1}",
                min_value=0.0,
                max_value=1.0,
                value=float(agent["reputation"]),
                step=0.1,
                format="%.1f",
                key=f"rep_{i}",
            )

        with col5:
            if (
                st.button("Remove", key=f"remove_{i}")
                and len(st.session_state.dividend_agents) > 1
            ):
                st.session_state.dividend_agents.pop(i)
                st.experimental_rerun()

    # Check if contributions sum to 1.0
    total_contribution = sum(
        agent["contribution"] for agent in st.session_state.dividend_agents
    )
    if abs(total_contribution - 1.0) > 0.01:
        st.warning(f"Contributions sum to {total_contribution:.2f}, which is not 1.0")

    # Calculate dividends
    total_stake = sum(agent["stake"] for agent in st.session_state.dividend_agents)

    distributions = []
    for agent in st.session_state.dividend_agents:
        # Calculate components
        contribution_component = agent["contribution"] * contribution_weight

        stake_component = 0
        if total_stake > 0:
            stake_component = (agent["stake"] / total_stake) * stake_weight

        reputation_component = agent["reputation"] * reputation_weight

        # Calculate total score
        total_score = contribution_component + stake_component + reputation_component

        distributions.append(
            {
                "id": agent["id"],
                "contribution_component": contribution_component,
                "stake_component": stake_component,
                "reputation_component": reputation_component,
                "total_score": total_score,
            }
        )

    # Normalize scores
    total_score = sum(d["total_score"] for d in distributions)
    for d in distributions:
        d["normalized_score"] = d["total_score"] / total_score if total_score > 0 else 0
        d["dividend_amount"] = d["normalized_score"] * value_amount

    # Display results
    st.markdown("### Dividend Distribution Results")

    # Create DataFrame
    df = pd.DataFrame(distributions)
    df = df.rename(
        columns={
            "id": "Agent ID",
            "contribution_component": "Contribution Factor",
            "stake_component": "Stake Factor",
            "reputation_component": "Reputation Factor",
            "total_score": "Total Score",
            "normalized_score": "Share",
            "dividend_amount": "Dividend Amount",
        }
    )

    # Format columns
    for col in [
        "Contribution Factor",
        "Stake Factor",
        "Reputation Factor",
        "Total Score",
        "Share",
    ]:
        df[col] = df[col].map("{:.2f}".format)

    df["Dividend Amount"] = df["Dividend Amount"].map("{:.2f}".format)

    st.dataframe(df)

    # Create visualization of distribution
    dist_df = pd.DataFrame(
        {
            "Agent": [d["id"] for d in distributions],
            "Dividend": [d["dividend_amount"] for d in distributions],
        }
    )

    chart = (
        alt.Chart(dist_df)
        .mark_bar()
        .encode(
            x=alt.X("Agent:N", title="Agent ID"),
            y=alt.Y("Dividend:Q", title="Dividend Amount"),
        )
        .properties(height=300)
    )

    st.altair_chart(chart, use_container_width=True)

    # Component breakdown
    st.markdown("### Component Breakdown")

    # Create DataFrame with components
    # Create values list for the component breakdown
    agents = []
    components = []
    values = []

    for d in distributions:
        # Add each component type for this agent
        agents.extend([d["id"]] * 3)
        components.extend(["Contribution", "Stake", "Reputation"])
        values.extend(
            [
                d["contribution_component"] * value_amount,
                d["stake_component"] * value_amount,
                d["reputation_component"] * value_amount,
            ]
        )

    # Create DataFrame from the lists
    components_df = pd.DataFrame(
        {"Agent": agents, "Component": components, "Value": values}
    )

    # Create stacked bar chart
    chart = (
        alt.Chart(components_df)
        .mark_bar()
        .encode(
            x=alt.X("Agent:N", title="Agent ID"),
            y=alt.Y("Value:Q", title="Value Amount"),
            color="Component:N",
        )
        .properties(height=300)
    )

    st.altair_chart(chart, use_container_width=True)
