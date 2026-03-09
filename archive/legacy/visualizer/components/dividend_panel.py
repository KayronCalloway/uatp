"""
Dividend Panel Component

Displays UATP economic attribution results in the visualizer
"""

import streamlit as st

from src.economic.common_fund import CommonAttributionFund  # For fund balance display
from src.economic.dividend_engine import calculate_final_dividends


def render_dividend_panel(chain):
    """Render dividend allocation panel"""
    if not chain:
        st.warning("No capsules in chain")
        return

    # Calculate dividends
    dividends = calculate_final_dividends(chain)

    # Display individual allocations
    st.header("Economic Attribution")
    st.subheader("Individual Allocations")
    for entity, amount in dividends.items():
        st.metric(label=entity, value=f"{amount:.4f} units")

    # Display common fund
    fund = CommonAttributionFund()
    st.subheader("Common Attribution Fund")
    st.metric(label="Fund Balance", value=f"{fund.balance:.4f} units")
    st.caption("Funds are allocated for public goods and diffuse contributions")
