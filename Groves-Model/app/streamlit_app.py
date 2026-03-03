"""Groves Investor Model — Streamlit Web Application.

Run with: streamlit run app/streamlit_app.py
"""

import os
import sys

import streamlit as st

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="Groves Investor Model",
    page_icon=":office:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    """Initialize session state with defaults from config.py."""
    if 'initialized' not in st.session_state:
        from config import (
            PROPERTY, UNIT_MIX, LOAN, TIC, TOTAL_EQUITY,
            VALUATION, ESCROW_NAMES, REFI,
        )

        st.session_state.property = dict(PROPERTY)
        st.session_state.unit_mix = {k: dict(v) for k, v in UNIT_MIX.items()}
        st.session_state.loan = dict(LOAN)
        st.session_state.tic = {k: dict(v) for k, v in TIC.items()}
        st.session_state.total_equity = TOTAL_EQUITY
        st.session_state.valuation = dict(VALUATION)
        st.session_state.escrow_names = list(ESCROW_NAMES)
        st.session_state.refi = dict(REFI)
        st.session_state.data_version = 0
        st.session_state.initialized = True


init_session_state()

# Landing page
st.title("The Groves Apartments | Investor Model")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Property", st.session_state.property['name'])
with col2:
    st.metric("Units", st.session_state.property['units'])
with col3:
    st.metric("Purchase Price", f"${st.session_state.property['purchase_price']:,.0f}")

st.divider()

st.markdown(
    "Use the **sidebar navigation** to access the different sections:\n\n"
    "- **Dashboard** — KPI cards and interactive charts\n"
    "- **Assumptions** — Edit model assumptions with live recalculation\n"
    "- **Upload Data** — Upload new CSV data files\n"
    "- **Download Excel** — Generate and download the formatted Excel model\n"
    "- **P&L Viewer** — Clean tabbed P&L with Executive Summary, T-12, Full P&L, and Distribution Model"
)

st.caption(
    f"Address: {st.session_state.property['address']}  |  "
    f"Year Built: {st.session_state.property['year_built']}  |  "
    f"Rentable SF: {st.session_state.property['rentable_sf']:,}"
)
