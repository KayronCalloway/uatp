"""
UATP Insurance Risk Metrics Component

This module provides risk assessment metrics for insurance companies evaluating AI systems
through the UATP protocol, analyzing economic transaction patterns to quantify risk.
"""

import altair as alt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_insurance_risk_metrics(transaction_data):
    """Render insurance risk metrics based on economic transaction data.

    This function analyzes economic transaction patterns to produce risk metrics
    that would be valuable for insurance companies evaluating AI systems through UATP.

    Args:
        transaction_data (list): List of transaction dictionaries
    """
    st.markdown("## Insurance Risk Metrics")
    st.markdown(
        """These metrics provide insights into system risk factors
    based on economic transaction patterns, which can be used by insurance companies
    to assess and price coverage for AI systems."""
    )

    if not transaction_data:
        st.info("No transaction data available for risk assessment")
        return

    # Convert to DataFrame if not already
    if not isinstance(transaction_data, pd.DataFrame):
        df = pd.DataFrame(transaction_data)
    else:
        df = transaction_data.copy()

    # Ensure required columns exist
    required_cols = ["transaction_type", "value_amount", "timestamp"]
    if not all(col in df.columns for col in required_cols):
        st.warning("Transaction data missing required columns for risk assessment")
        return

    # Ensure timestamp is datetime
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Calculate metrics in tabs
    risk_tabs = st.tabs(
        ["Volatility Metrics", "Concentration Risk", "System Health", "Risk Score"]
    )

    # Tab 1: Volatility Metrics
    with risk_tabs[0]:
        st.markdown("### Volatility Metrics")

        # Daily transaction volume
        if "timestamp" in df.columns:
            df["date"] = df["timestamp"].dt.date
            daily_volume = (
                df.groupby("date")["value_amount"].agg(["sum", "count"]).reset_index()
            )
            daily_volume.columns = ["Date", "Value", "Count"]

            # Calculate coefficient of variation (volatility measure)
            cv = (
                daily_volume["Value"].std() / daily_volume["Value"].mean()
                if daily_volume["Value"].mean() > 0
                else 0
            )

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Transaction Volatility",
                    f"{cv:.2f}",
                    delta="High" if cv > 0.5 else "Moderate" if cv > 0.2 else "Low",
                )

            with col2:
                st.metric(
                    "Daily Transaction Avg",
                    f"{daily_volume['Value'].mean():.2f}",
                    f"{daily_volume['Count'].mean():.1f} tx/day",
                )

            # Plot daily volume
            chart = (
                alt.Chart(daily_volume)
                .mark_bar()
                .encode(
                    x=alt.X("Date:T", title="Date"),
                    y=alt.Y("Value:Q", title="Transaction Volume"),
                    tooltip=["Date", "Value", "Count"],
                )
                .properties(height=250)
            )

            st.altair_chart(chart, use_container_width=True)

    # Tab 2: Concentration Risk
    with risk_tabs[1]:
        st.markdown("### Concentration Risk")

        # Agent concentration (similar to market concentration)
        agents = set()
        agent_volumes = {}

        # Extract agents and their transaction volumes
        for tx in transaction_data:
            if "sender" in tx and tx["sender"]:
                agent = tx["sender"]
                agents.add(agent)
                agent_volumes[agent] = agent_volumes.get(agent, 0) + tx.get(
                    "value_amount", 0
                )

            if "recipients" in tx and tx["recipients"]:
                for recipient in tx["recipients"]:
                    agents.add(recipient)

        # Calculate Herfindahl-Hirschman Index (measure of concentration)
        total_volume = sum(agent_volumes.values())
        if total_volume > 0:
            market_shares = [volume / total_volume for volume in agent_volumes.values()]
            hhi = sum(share**2 for share in market_shares)

            # HHI interpretation
            if hhi < 0.15:
                hhi_text = "Low Concentration"
                hhi_delta = "Unconcentrated"
            elif hhi < 0.25:
                hhi_text = "Moderate Concentration"
                hhi_delta = "Moderately Concentrated"
            else:
                hhi_text = "High Concentration"
                hhi_delta = "Highly Concentrated"

            st.metric("Agent Concentration (HHI)", f"{hhi:.2f}", hhi_delta)

            # Display agent distribution
            agent_df = pd.DataFrame(
                {
                    "Agent": list(agent_volumes.keys()),
                    "Volume": list(agent_volumes.values()),
                    "Share": [v / total_volume for v in agent_volumes.values()],
                }
            )

            agent_df = agent_df.sort_values("Volume", ascending=False)
            agent_df["Share"] = agent_df["Share"].map("{:.1%}".format)

            st.dataframe(agent_df)
        else:
            st.info("Insufficient data to calculate concentration metrics")

    # Tab 3: System Health
    with risk_tabs[2]:
        st.markdown("### System Health Indicators")

        # Transaction type distribution as health indicator
        if "transaction_type" in df.columns:
            type_dist = df["transaction_type"].value_counts().to_dict()

            # Calculate risk ratios
            total_tx = sum(type_dist.values())
            penalty_ratio = (
                type_dist.get("penalty", 0) / total_tx if total_tx > 0 else 0
            )
            reward_ratio = (
                (
                    type_dist.get("verification_reward", 0)
                    + type_dist.get("bounty_reward", 0)
                )
                / total_tx
                if total_tx > 0
                else 0
            )
            stake_ratio = (
                (
                    type_dist.get("stake_deposit", 0)
                    - type_dist.get("stake_withdrawal", 0)
                )
                / total_tx
                if total_tx > 0
                else 0
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Penalty Rate",
                    f"{penalty_ratio:.1%}",
                    delta="High Risk"
                    if penalty_ratio > 0.05
                    else "Medium Risk"
                    if penalty_ratio > 0.01
                    else "Low Risk",
                    delta_color="inverse",
                )

            with col2:
                st.metric(
                    "Verification Reward Rate",
                    f"{reward_ratio:.1%}",
                    delta="Healthy"
                    if reward_ratio > 0.2
                    else "Moderate"
                    if reward_ratio > 0.1
                    else "Concerning",
                    delta_color="normal",
                )

            with col3:
                st.metric(
                    "Net Staking Rate",
                    f"{stake_ratio:.1%}",
                    delta="Growing Trust"
                    if stake_ratio > 0.1
                    else "Stable"
                    if stake_ratio > -0.1
                    else "Declining Trust",
                    delta_color="normal",
                )

            # Health score calculation
            health_score = (
                (1 - min(penalty_ratio * 10, 1)) * 0.4
                + min(reward_ratio * 5, 1) * 0.3  # Lower penalties = better
                + (min(stake_ratio * 5 + 0.5, 1))  # Higher rewards = better
                * 0.3  # Higher staking = better
            ) * 100

            st.markdown(f"### Overall System Health Score: {health_score:.1f}/100")

            # Health gauge
            gauge_chart = {
                "type": "indicator",
                "mode": "gauge+number",
                "value": health_score,
                "gauge": {
                    "axis": {"range": [0, 100]},
                    "bar": {
                        "color": "green"
                        if health_score >= 70
                        else "orange"
                        if health_score >= 40
                        else "red"
                    },
                    "steps": [
                        {"range": [0, 40], "color": "lightgray"},
                        {"range": [40, 70], "color": "gray"},
                    ],
                    "threshold": {
                        "line": {"color": "black", "width": 4},
                        "thickness": 0.75,
                        "value": health_score,
                    },
                },
            }

            fig = go.Figure(gauge_chart)
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)

    # Tab 4: Risk Score & Premium Calculation
    with risk_tabs[3]:
        st.markdown("### Insurance Risk Score")
        st.markdown(
            """This score represents a simplified model of how an insurance
        company might assess risk and calculate premiums for AI systems based on their
        UATP economic activity."""
        )

        # Let user adjust risk parameters
        st.markdown("#### Risk Parameter Weights")
        col1, col2, col3 = st.columns(3)

        with col1:
            volatility_weight = st.slider("Volatility Impact", 0.1, 1.0, 0.3, 0.1)
        with col2:
            concentration_weight = st.slider("Concentration Impact", 0.1, 1.0, 0.3, 0.1)
        with col3:
            health_weight = st.slider("System Health Impact", 0.1, 1.0, 0.4, 0.1)

        # Calculate a composite risk score (simplified model)
        # We'll use the metrics we calculated earlier
        if "cv" in locals() and "hhi" in locals() and "health_score" in locals():
            # Convert metrics to risk factors (higher = more risky)
            volatility_risk = min(cv * 2, 1)  # Scale coefficient of variation
            concentration_risk = min(hhi * 4, 1)  # Scale HHI
            health_risk = (100 - health_score) / 100  # Invert health score to get risk

            # Weighted average for risk score
            composite_risk = (
                volatility_risk * volatility_weight
                + concentration_risk * concentration_weight
                + health_risk * health_weight
            ) / (volatility_weight + concentration_weight + health_weight)

            # Scale to 0-100 for display
            risk_score = composite_risk * 100

            # Risk tier classification
            if risk_score < 30:
                risk_tier = "Low Risk"
                color = "green"
                base_premium = 0.5  # % of system value
            elif risk_score < 60:
                risk_tier = "Moderate Risk"
                color = "orange"
                base_premium = 1.0  # % of system value
            else:
                risk_tier = "High Risk"
                color = "red"
                base_premium = 2.0  # % of system value

            # Display risk score
            st.markdown(f"#### Risk Score: **{risk_score:.1f}/100** ({risk_tier})")

            # Risk visualization with bullet chart
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=risk_score,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Risk Score", "font": {"size": 24}},
                    delta={"reference": 50, "increasing": {"color": "red"}},
                    gauge={
                        "axis": {"range": [None, 100], "tickwidth": 1},
                        "bar": {"color": color},
                        "bgcolor": "white",
                        "borderwidth": 2,
                        "bordercolor": "gray",
                        "steps": [
                            {"range": [0, 30], "color": "lightgreen"},
                            {"range": [30, 60], "color": "lightyellow"},
                            {"range": [60, 100], "color": "lightsalmon"},
                        ],
                        "threshold": {
                            "line": {"color": "black", "width": 4},
                            "thickness": 0.75,
                            "value": risk_score,
                        },
                    },
                )
            )

            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)

            # Premium calculator
            st.markdown("#### Premium Calculation Model")
            system_value = st.number_input(
                "System Value ($)",
                min_value=10000.0,
                max_value=100000000.0,
                value=1000000.0,
                step=100000.0,
                format="%.2f",
            )

            # Calculate insurance premium
            annual_premium = system_value * base_premium / 100 * (1 + composite_risk)
            monthly_premium = annual_premium / 12

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Annual Premium",
                    f"${annual_premium:,.2f}",
                    f"Base: ${system_value * base_premium / 100:,.2f}",
                )

            with col2:
                st.metric(
                    "Monthly Premium",
                    f"${monthly_premium:,.2f}",
                    f"Risk Multiplier: {1 + composite_risk:.2f}x",
                )

            st.info(
                """This premium model is a simplified example of how insurance
            companies might price AI system coverage based on UATP data. Actual
            pricing models would incorporate additional risk factors and historical
            claims data."""
            )
        else:
            st.warning("Insufficient data to calculate risk score")
