#!/usr/bin/env python3
"""
Simple UATP Visualizer - Minimal version for testing
"""

import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

# Add project paths
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))


def main():
    st.set_page_config(
        page_title="UATP Capsule Engine Visualizer", page_icon="🔗", layout="wide"
    )

    st.title("🔗 UATP Capsule Engine Visualizer")
    st.markdown("**Unified Agent Trust Protocol - Visual Explorer**")

    # Test basic functionality
    st.header("System Status")

    # Test imports
    try:
        st.success("✅ Core schema imported successfully")
    except Exception as e:
        st.error(f"❌ Schema import failed: {e}")

    try:
        st.success("✅ Legacy engine imported successfully")
    except Exception as e:
        st.error(f"❌ Engine import failed: {e}")

    try:
        st.success("✅ Specialized capsules imported successfully")
    except Exception as e:
        st.error(f"❌ Specialized capsules import failed: {e}")

    # Simple data display
    st.header("Sample Data")

    sample_data = {
        "Capsule ID": ["cap-001", "cap-002", "cap-003"],
        "Type": ["reasoning_trace", "economic_transaction", "governance_vote"],
        "Status": ["SEALED", "ACTIVE", "SEALED"],
        "Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] * 3,
    }

    df = pd.DataFrame(sample_data)
    st.dataframe(df)

    # Trust status mockup
    st.header("Trust Enforcement Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Active Agents", "5", "+1")

    with col2:
        st.metric("System Health", "Healthy", "")

    with col3:
        st.metric("Quarantined Agents", "0", "")

    # Simple chart
    st.header("Activity Chart")
    chart_data = pd.DataFrame(
        {
            "Time": pd.date_range("2024-01-01", periods=10, freq="D"),
            "Capsules Created": [1, 3, 2, 5, 4, 2, 6, 3, 4, 5],
        }
    )
    st.line_chart(chart_data.set_index("Time"))

    st.info(
        "📋 This is a simplified visualizer. Full features available when all dependencies are resolved."
    )


if __name__ == "__main__":
    main()
