#!/usr/bin/env python3
"""
UATP Capsule Visualizer - Database Edition
==========================================

This is the updated visualizer that uses the SQLite database instead of JSONL files.
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st

# Add project root and src directory to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from utils.database_loader import (
    get_capsule_stats_cached,
    get_storage_backend,
    load_capsules_cached,
    search_capsules_cached,
)


def main():
    """Main visualizer application."""

    st.set_page_config(
        page_title="UATP Capsule Visualizer (Database)", page_icon="", layout="wide"
    )

    st.title(" UATP Capsule Visualizer (Database Edition)")
    st.markdown(
        "Real-time visualization of Universal Attribution and Transparency Protocol capsules"
    )

    # Show storage backend status
    backend = get_storage_backend()
    backend_emoji = "" if backend == "sqlite" else ""
    st.info(f"{backend_emoji} Storage Backend: {backend.upper()}")

    # Sidebar controls
    st.sidebar.header(" Controls")

    # Data source selection
    use_database = st.sidebar.checkbox(
        "Use Database", value=True, help="Use SQLite database instead of JSONL fallback"
    )

    # Load capsules
    with st.spinner("Loading capsules..."):
        capsules = load_capsules_cached(use_database=use_database)

    if not capsules:
        st.warning("No capsules found. Make sure the system is generating capsules.")
        return

    # Statistics
    stats = get_capsule_stats_cached()

    # Display stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Capsules", stats.get("total_capsules", 0))

    with col2:
        st.metric("Storage Backend", stats.get("storage_backend", "unknown"))

    with col3:
        platforms = stats.get("platforms", {})
        st.metric("Platforms", len(platforms))

    with col4:
        if capsules:
            avg_significance = sum(
                c.get("significance_score", 0) for c in capsules
            ) / len(capsules)
            st.metric("Avg Significance", f"{avg_significance:.2f}")

    # Filters
    st.sidebar.subheader(" Filters")

    # Platform filter
    platforms = list(stats.get("platforms", {}).keys())
    selected_platform = st.sidebar.selectbox("Platform", ["All"] + platforms, index=0)

    # Significance filter
    min_significance = st.sidebar.slider("Min Significance", 0.0, 10.0, 0.0, 0.1)

    # Search filter
    search_query = st.sidebar.text_input("Search", placeholder="Search capsules...")

    # Apply filters
    filtered_capsules = capsules

    if selected_platform != "All":
        filtered_capsules = [
            c for c in filtered_capsules if c.get("platform") == selected_platform
        ]

    if min_significance > 0:
        filtered_capsules = [
            c
            for c in filtered_capsules
            if c.get("significance_score", 0) >= min_significance
        ]

    if search_query:
        filtered_capsules = search_capsules_cached(
            query=search_query,
            platform=selected_platform if selected_platform != "All" else None,
            min_significance=min_significance if min_significance > 0 else None,
        )

    st.sidebar.write(f"Showing {len(filtered_capsules)} of {len(capsules)} capsules")

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        [" Overview", " Capsule Explorer", " Analytics", " Database Info"]
    )

    with tab1:
        render_overview(filtered_capsules, stats)

    with tab2:
        render_capsule_explorer(filtered_capsules)

    with tab3:
        render_analytics(filtered_capsules, stats)

    with tab4:
        render_database_info(stats)


def render_overview(capsules: List[Dict[str, Any]], stats: Dict[str, Any]):
    """Render the overview tab."""

    if not capsules:
        st.info("No capsules match the current filters.")
        return

    # Platform distribution
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(" Platform Distribution")
        platforms = stats.get("platforms", {})

        if platforms:
            fig = px.pie(
                values=list(platforms.values()),
                names=list(platforms.keys()),
                title="Capsules by Platform",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No platform data available")

    with col2:
        st.subheader(" Significance Distribution")

        # Create significance histogram
        significance_scores = [c.get("significance_score", 0) for c in capsules]

        if significance_scores:
            fig = px.histogram(
                x=significance_scores, title="Significance Score Distribution", nbins=20
            )
            fig.update_layout(
                xaxis_title="Significance Score", yaxis_title="Number of Capsules"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No significance data available")

    # Recent activity
    st.subheader(" Recent Activity")

    recent_capsules = sorted(
        capsules, key=lambda x: x.get("timestamp", ""), reverse=True
    )[:10]

    if recent_capsules:
        for capsule in recent_capsules:
            with st.expander(f" {capsule.get('capsule_id', 'Unknown ID')[:20]}..."):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Platform:** {capsule.get('platform', 'Unknown')}")
                    st.write(f"**User:** {capsule.get('user_id', 'Unknown')}")

                with col2:
                    st.write(
                        f"**Significance:** {capsule.get('significance_score', 0):.2f}"
                    )
                    st.write(f"**Timestamp:** {capsule.get('timestamp', 'Unknown')}")

                with col3:
                    st.write(f"**Type:** {capsule.get('type', 'Unknown')}")
                    st.write(
                        f"**Storage:** {capsule.get('storage_backend', 'Unknown')}"
                    )


def render_capsule_explorer(capsules: List[Dict[str, Any]]):
    """Render the capsule explorer tab."""

    if not capsules:
        st.info("No capsules match the current filters.")
        return

    st.subheader(" Capsule Explorer")

    # Create a dataframe for easier manipulation
    df_data = []
    for capsule in capsules:
        df_data.append(
            {
                "Capsule ID": capsule.get("capsule_id", "Unknown")[:20] + "...",
                "Platform": capsule.get("platform", "Unknown"),
                "Significance": capsule.get("significance_score", 0),
                "User ID": capsule.get("user_id", "Unknown"),
                "Timestamp": capsule.get("timestamp", "Unknown"),
                "Type": capsule.get("type", "Unknown"),
                "Storage": capsule.get("storage_backend", "Unknown"),
            }
        )

    df = pd.DataFrame(df_data)

    # Display the table
    st.dataframe(df, use_container_width=True)

    # Detailed view
    st.subheader(" Detailed View")

    if capsules:
        selected_index = st.selectbox(
            "Select capsule to view details:",
            range(len(capsules)),
            format_func=lambda i: f"{capsules[i].get('capsule_id', 'Unknown')[:20]}... ({capsules[i].get('platform', 'Unknown')})",
        )

        selected_capsule = capsules[selected_index]

        # Display detailed information
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Basic Information:**")
            st.json(
                {
                    "capsule_id": selected_capsule.get("capsule_id"),
                    "type": selected_capsule.get("type"),
                    "platform": selected_capsule.get("platform"),
                    "user_id": selected_capsule.get("user_id"),
                    "timestamp": selected_capsule.get("timestamp"),
                    "significance_score": selected_capsule.get("significance_score"),
                    "storage_backend": selected_capsule.get("storage_backend"),
                }
            )

        with col2:
            st.write("**Metadata:**")
            metadata = selected_capsule.get("metadata", {})
            if metadata:
                st.json(metadata)
            else:
                st.info("No metadata available")


def render_analytics(capsules: List[Dict[str, Any]], stats: Dict[str, Any]):
    """Render the analytics tab."""

    if not capsules:
        st.info("No capsules match the current filters.")
        return

    st.subheader(" Analytics Dashboard")

    # Time-based analysis
    st.subheader(" Time-based Analysis")

    # Group by date
    date_counts = {}
    for capsule in capsules:
        timestamp = capsule.get("timestamp", "")
        if timestamp:
            try:
                date = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).date()
                date_counts[date] = date_counts.get(date, 0) + 1
            except:
                continue

    if date_counts:
        dates = list(date_counts.keys())
        counts = list(date_counts.values())

        fig = px.line(
            x=dates,
            y=counts,
            title="Capsule Creation Over Time",
            labels={"x": "Date", "y": "Number of Capsules"},
        )
        st.plotly_chart(fig, use_container_width=True)

    # Platform comparison
    st.subheader(" Platform Comparison")

    platform_data = {}
    for capsule in capsules:
        platform = capsule.get("platform", "Unknown")
        if platform not in platform_data:
            platform_data[platform] = {
                "count": 0,
                "total_significance": 0,
                "avg_significance": 0,
            }

        platform_data[platform]["count"] += 1
        platform_data[platform]["total_significance"] += capsule.get(
            "significance_score", 0
        )

    # Calculate averages
    for platform in platform_data:
        platform_data[platform]["avg_significance"] = (
            platform_data[platform]["total_significance"]
            / platform_data[platform]["count"]
        )

    # Display platform comparison
    if platform_data:
        comparison_df = pd.DataFrame.from_dict(platform_data, orient="index")
        comparison_df = comparison_df.round(2)

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Platform Statistics:**")
            st.dataframe(comparison_df)

        with col2:
            fig = px.bar(
                x=list(platform_data.keys()),
                y=[data["avg_significance"] for data in platform_data.values()],
                title="Average Significance by Platform",
            )
            st.plotly_chart(fig, use_container_width=True)


def render_database_info(stats: Dict[str, Any]):
    """Render the database info tab."""

    st.subheader(" Database Information")

    # Database stats
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Database Statistics:**")
        st.json(
            {
                "total_capsules": stats.get("total_capsules", 0),
                "auto_filtered_capsules": stats.get("auto_filtered_capsules", 0),
                "storage_backend": stats.get("storage_backend", "unknown"),
                "database_size": stats.get("database_size", 0),
            }
        )

    with col2:
        st.write("**Platform Distribution:**")
        platforms = stats.get("platforms", {})
        if platforms:
            st.json(platforms)
        else:
            st.info("No platform data available")

    # System status
    st.subheader(" System Status")

    backend = get_storage_backend()

    if backend == "sqlite":
        st.success("[OK] SQLite database is active")
    elif backend == "jsonl_fallback":
        st.warning("[WARN] Using JSONL fallback (database unavailable)")
    else:
        st.error("[ERROR] Unknown storage backend")

    # Refresh button
    if st.button(" Refresh Data"):
        st.cache_data.clear()
        st.experimental_rerun()


if __name__ == "__main__":
    main()
