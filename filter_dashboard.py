#!/usr/bin/env python3
"""
UATP Universal Filter Dashboard
===============================

Real-time dashboard for monitoring and configuring the universal filter system.

Features:
- Live filter statistics
- Configuration management
- Real-time filtering decisions
- Platform-specific metrics
- Threshold adjustment
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add project root to path
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from filters.universal_filter import get_universal_filter, FilterDecision, FilterConfig
from filters.integration_layer import get_integration_layer

# Configure Streamlit
st.set_page_config(
    page_title="UATP Universal Filter Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize filter system
universal_filter = get_universal_filter()
integration_layer = get_integration_layer()


def main():
    """Main dashboard function."""

    st.title("🔍 UATP Universal Filter Dashboard")
    st.markdown("*Real-time monitoring and configuration of AI interaction filtering*")

    # Sidebar configuration
    with st.sidebar:
        st.header("🔧 Filter Configuration")

        # Current configuration
        current_config = universal_filter.config

        # Significance threshold
        new_threshold = st.slider(
            "Significance Threshold",
            min_value=0.0,
            max_value=2.0,
            value=current_config.significance_threshold,
            step=0.1,
            help="Minimum significance score for encapsulation",
        )

        # Conversation length limits
        min_length = st.number_input(
            "Min Conversation Length",
            min_value=1,
            max_value=10,
            value=current_config.min_conversation_length,
            help="Minimum number of messages required",
        )

        max_length = st.number_input(
            "Max Conversation Length",
            min_value=10,
            max_value=1000,
            value=current_config.max_conversation_length,
            help="Maximum number of messages to process",
        )

        # Platform weights
        st.subheader("Platform Weights")
        platform_weights = {}
        for platform, current_weight in current_config.platform_weights.items():
            platform_weights[platform] = st.slider(
                f"{platform.title()}",
                min_value=0.0,
                max_value=2.0,
                value=current_weight,
                step=0.1,
                key=f"weight_{platform}",
            )

        # Update configuration
        if st.button("💾 Update Configuration"):
            universal_filter.update_config(
                {
                    "significance_threshold": new_threshold,
                    "min_conversation_length": min_length,
                    "max_conversation_length": max_length,
                    "platform_weights": platform_weights,
                }
            )
            st.success("Configuration updated!")
            st.rerun()

    # Main dashboard content
    col1, col2, col3, col4 = st.columns(4)

    # Get current stats
    stats = universal_filter.get_stats()

    with col1:
        st.metric(
            "Total Processed",
            stats["total_processed"],
            help="Total interactions processed",
        )

    with col2:
        st.metric(
            "Encapsulated",
            stats["total_encapsulated"],
            delta=f"{stats['encapsulation_rate']:.1%}",
            help="Interactions that were encapsulated",
        )

    with col3:
        st.metric(
            "Discarded",
            stats["total_discarded"],
            delta=f"{stats['discard_rate']:.1%}",
            help="Interactions that were discarded",
        )

    with col4:
        st.metric(
            "Threshold",
            f"{stats['config']['significance_threshold']:.1f}",
            help="Current significance threshold",
        )

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Live Stats", "⚙️ Filter Test", "📈 Analytics", "🔧 Advanced"]
    )

    with tab1:
        render_live_stats()

    with tab2:
        render_filter_test()

    with tab3:
        render_analytics()

    with tab4:
        render_advanced_config()


def render_live_stats():
    """Render live statistics section."""

    st.subheader("📊 Real-time Filter Statistics")

    # Create placeholder for live updates
    stats_placeholder = st.empty()

    # Create a simple visualization
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Filter Decisions")

        # Mock data for demonstration
        decisions_data = {
            "Decision": ["Encapsulate", "Discard", "Defer", "Review"],
            "Count": [
                universal_filter.total_encapsulated,
                universal_filter.total_discarded,
                5,  # Mock defer count
                2,  # Mock review count
            ],
        }

        fig = px.pie(
            values=decisions_data["Count"],
            names=decisions_data["Decision"],
            title="Filter Decision Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Platform Activity")

        # Mock platform data
        platform_data = {
            "Platform": ["OpenAI", "Claude", "Claude Code", "Windsurf"],
            "Interactions": [45, 32, 28, 15],
        }

        fig = px.bar(
            x=platform_data["Platform"],
            y=platform_data["Interactions"],
            title="Interactions by Platform",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Recent activity
    st.subheader("Recent Filter Activity")

    # Mock recent activity data
    recent_activity = pd.DataFrame(
        {
            "Timestamp": [datetime.now().strftime("%H:%M:%S")] * 5,
            "Platform": ["OpenAI", "Claude", "Claude Code", "OpenAI", "Claude"],
            "Decision": ["Encapsulate", "Discard", "Encapsulate", "Defer", "Review"],
            "Score": [0.85, 0.45, 0.92, 0.58, 0.62],
            "Reason": [
                "Code generation detected",
                "Casual conversation",
                "Technical depth, debugging",
                "Close to threshold",
                "Manual review needed",
            ],
        }
    )

    st.dataframe(recent_activity, use_container_width=True)


def render_filter_test():
    """Render filter testing section."""

    st.subheader("⚙️ Test the Filter")
    st.markdown("Test how the filter would handle different types of interactions.")

    # Test input
    col1, col2 = st.columns(2)

    with col1:
        platform = st.selectbox(
            "Platform", ["openai", "claude", "claude_code", "windsurf", "cursor"]
        )

        user_id = st.text_input("User ID", value="test-user")

    with col2:
        model = st.text_input("Model", value="gpt-4")

        session_id = st.text_input("Session ID", value="test-session")

    # Message input
    st.subheader("Conversation Messages")

    # Simple message input
    user_message = st.text_area(
        "User Message", placeholder="Enter what the user said...", height=100
    )

    assistant_message = st.text_area(
        "Assistant Message", placeholder="Enter what the AI responded...", height=100
    )

    if st.button("🧪 Test Filter"):
        if user_message and assistant_message:
            # Create test messages
            test_messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message},
            ]

            # Test the filter
            with st.spinner("Testing filter..."):
                try:
                    # Import the async function
                    from filters.integration_layer import process_ai_interaction

                    # Run the test
                    result = asyncio.run(
                        process_ai_interaction(
                            messages=test_messages,
                            user_id=user_id,
                            platform=platform,
                            context={"model": model, "test": True},
                            session_id=session_id,
                            model=model,
                        )
                    )

                    # Display results
                    st.success("Filter test completed!")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Decision", result.decision.value.title())

                    with col2:
                        st.metric(
                            "Significance Score", f"{result.significance_score:.2f}"
                        )

                    with col3:
                        st.metric("Confidence", f"{result.confidence:.2f}")

                    # Show reasoning
                    if result.reasoning:
                        st.subheader("Reasoning Factors")
                        for factor in result.reasoning:
                            st.write(f"• {factor}")

                    # Show metadata
                    with st.expander("Full Result Details"):
                        st.json(result.to_dict())

                except Exception as e:
                    st.error(f"Error testing filter: {e}")
        else:
            st.warning("Please enter both user and assistant messages.")


def render_analytics():
    """Render analytics section."""

    st.subheader("📈 Filter Analytics")

    # Time series chart
    st.subheader("Activity Over Time")

    # Mock time series data
    import numpy as np

    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")

    time_series_data = pd.DataFrame(
        {
            "Date": dates,
            "Encapsulated": np.random.poisson(15, 30),
            "Discarded": np.random.poisson(25, 30),
            "Total": np.random.poisson(40, 30),
        }
    )

    fig = px.line(
        time_series_data,
        x="Date",
        y=["Encapsulated", "Discarded", "Total"],
        title="Filter Activity Over Time",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Significance score distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Significance Score Distribution")

        # Mock score distribution
        scores = np.random.beta(2, 5, 1000) * 2  # Beta distribution scaled to 0-2

        fig = px.histogram(
            x=scores, nbins=20, title="Distribution of Significance Scores"
        )
        fig.add_vline(
            x=universal_filter.config.significance_threshold,
            line_dash="dash",
            line_color="red",
            annotation_text="Threshold",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Platform Performance")

        # Mock platform performance
        platform_perf = pd.DataFrame(
            {
                "Platform": ["OpenAI", "Claude", "Claude Code", "Windsurf"],
                "Avg Score": [0.72, 0.68, 0.85, 0.76],
                "Encapsulation Rate": [0.65, 0.58, 0.78, 0.69],
            }
        )

        fig = px.scatter(
            platform_perf,
            x="Avg Score",
            y="Encapsulation Rate",
            size=[100, 80, 120, 60],
            text="Platform",
            title="Platform Performance",
        )
        st.plotly_chart(fig, use_container_width=True)


def render_advanced_config():
    """Render advanced configuration section."""

    st.subheader("🔧 Advanced Configuration")

    # Content type weights
    st.subheader("Content Type Weights")

    current_weights = universal_filter.config.content_weights

    col1, col2 = st.columns(2)

    with col1:
        code_weight = st.slider(
            "Code Generation",
            0.0,
            2.0,
            current_weights.get("code_generation", 1.3),
            0.1,
        )

        problem_weight = st.slider(
            "Problem Solving",
            0.0,
            2.0,
            current_weights.get("problem_solving", 1.2),
            0.1,
        )

        learning_weight = st.slider(
            "Learning Content", 0.0, 2.0, current_weights.get("learning", 1.1), 0.1
        )

    with col2:
        debug_weight = st.slider(
            "Debugging", 0.0, 2.0, current_weights.get("debugging", 1.4), 0.1
        )

        architecture_weight = st.slider(
            "Architecture", 0.0, 2.0, current_weights.get("architecture", 1.5), 0.1
        )

        casual_weight = st.slider(
            "Casual Chat", 0.0, 2.0, current_weights.get("casual_chat", 0.8), 0.1
        )

    # Export/Import configuration
    st.subheader("Configuration Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Export Configuration"):
            config_json = json.dumps(
                {
                    "significance_threshold": universal_filter.config.significance_threshold,
                    "min_conversation_length": universal_filter.config.min_conversation_length,
                    "max_conversation_length": universal_filter.config.max_conversation_length,
                    "platform_weights": universal_filter.config.platform_weights,
                    "content_weights": {
                        "code_generation": code_weight,
                        "problem_solving": problem_weight,
                        "learning": learning_weight,
                        "debugging": debug_weight,
                        "architecture": architecture_weight,
                        "casual_chat": casual_weight,
                    },
                },
                indent=2,
            )

            st.download_button(
                label="💾 Download Config",
                data=config_json,
                file_name="uatp_filter_config.json",
                mime="application/json",
            )

    with col2:
        uploaded_file = st.file_uploader("📤 Import Configuration", type=["json"])

        if uploaded_file:
            try:
                config_data = json.load(uploaded_file)
                universal_filter.update_config(config_data)
                st.success("Configuration imported successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error importing configuration: {e}")


if __name__ == "__main__":
    main()
