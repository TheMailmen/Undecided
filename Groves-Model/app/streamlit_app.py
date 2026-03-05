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
            VALUATION, ESCROW_NAMES, REFI, CAPEX_BUDGET,
        )

        st.session_state.property = dict(PROPERTY)
        st.session_state.unit_mix = {k: dict(v) for k, v in UNIT_MIX.items()}
        st.session_state.loan = dict(LOAN)
        st.session_state.tic = {k: dict(v) for k, v in TIC.items()}
        st.session_state.total_equity = TOTAL_EQUITY
        st.session_state.valuation = dict(VALUATION)
        st.session_state.escrow_names = list(ESCROW_NAMES)
        st.session_state.refi = dict(REFI)
        st.session_state.capex_budget = CAPEX_BUDGET
        st.session_state.data_version = 0
        st.session_state.initialized = True


init_session_state()

from ui.theme import inject_theme, COLORS

inject_theme()

# ── Sidebar Branding ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid rgba(255,255,255,.12);">
        <p style="margin:0 0 2px 0;font-size:0.65rem;font-weight:600;text-transform:uppercase;
                   letter-spacing:0.12em;color:rgba(255,255,255,.4);">
            Lakeshore Management
        </p>
        <p style="margin:0;font-size:1.05rem;font-weight:700;color:white;
                   letter-spacing:-0.01em;">
            {st.session_state.property['name']}
        </p>
        <p style="margin:4px 0 0 0;font-size:0.72rem;color:rgba(255,255,255,.5);">
            {st.session_state.property['units']} units &bull;
            {st.session_state.property['address'].split(',')[0]}
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── Landing Page ──────────────────────────────────────────────────

prop = st.session_state.property

st.markdown(f"""
<div style="margin-bottom:8px;">
    <p style="margin:0 0 4px 0;font-size:0.72rem;font-weight:600;text-transform:uppercase;
              letter-spacing:0.1em;color:{COLORS['accent']};">
        Lakeshore Management
    </p>
    <h1 style="margin:0;font-size:2rem;font-weight:700;color:{COLORS['primary']};
               letter-spacing:-0.02em;font-family:'Inter',system-ui,sans-serif;">
        {prop['name']}
    </h1>
    <p style="margin:4px 0 0 0;color:{COLORS['muted']};font-size:0.9rem;">
        {prop['address']}
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="display:flex;gap:24px;margin:24px 0;flex-wrap:wrap;">
    <div style="background:{COLORS['surface']};border:1px solid {COLORS['border']};
                border-radius:12px;padding:20px 28px;flex:1;min-width:180px;
                box-shadow:0 1px 3px rgba(0,0,0,.04);">
        <p style="margin:0;font-size:0.72rem;font-weight:600;text-transform:uppercase;
                  letter-spacing:0.04em;color:{COLORS['muted']};">Units</p>
        <p style="margin:4px 0 0 0;font-size:1.5rem;font-weight:700;color:{COLORS['text']};">
            {prop['units']}</p>
    </div>
    <div style="background:{COLORS['surface']};border:1px solid {COLORS['border']};
                border-radius:12px;padding:20px 28px;flex:1;min-width:180px;
                box-shadow:0 1px 3px rgba(0,0,0,.04);">
        <p style="margin:0;font-size:0.72rem;font-weight:600;text-transform:uppercase;
                  letter-spacing:0.04em;color:{COLORS['muted']};">Purchase Price</p>
        <p style="margin:4px 0 0 0;font-size:1.5rem;font-weight:700;color:{COLORS['text']};">
            ${prop['purchase_price']:,.0f}</p>
    </div>
    <div style="background:{COLORS['surface']};border:1px solid {COLORS['border']};
                border-radius:12px;padding:20px 28px;flex:1;min-width:180px;
                box-shadow:0 1px 3px rgba(0,0,0,.04);">
        <p style="margin:0;font-size:0.72rem;font-weight:600;text-transform:uppercase;
                  letter-spacing:0.04em;color:{COLORS['muted']};">Rentable SF</p>
        <p style="margin:4px 0 0 0;font-size:1.5rem;font-weight:700;color:{COLORS['text']};">
            {prop['rentable_sf']:,}</p>
    </div>
    <div style="background:{COLORS['surface']};border:1px solid {COLORS['border']};
                border-radius:12px;padding:20px 28px;flex:1;min-width:180px;
                box-shadow:0 1px 3px rgba(0,0,0,.04);">
        <p style="margin:0;font-size:0.72rem;font-weight:600;text-transform:uppercase;
                  letter-spacing:0.04em;color:{COLORS['muted']};">Year Built</p>
        <p style="margin:4px 0 0 0;font-size:1.5rem;font-weight:700;color:{COLORS['text']};">
            {prop['year_built']}</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# Navigation guide — clickable cards
nav_items = [
    ("Dashboard", "KPI cards and interactive trend charts", "\U0001f4ca", "pages/01_Dashboard.py"),
    ("Assumptions", "Edit model assumptions with live recalculation", "\u2699\ufe0f", "pages/02_Assumptions.py"),
    ("Upload Data", "Upload new CSV data files", "\U0001f4e4", "pages/03_Upload_Data.py"),
    ("Download Excel", "Generate and download the formatted workbook", "\U0001f4e5", "pages/04_Download_Excel.py"),
    ("P&L Viewer", "Executive Summary, T-12, Full P&L, and Distribution Model", "\U0001f4cb", "pages/05_PL_Viewer.py"),
    ("Returns", "Projected IRR, equity multiple, and per-owner analysis", "\U0001f4b0", "pages/06_Returns.py"),
    ("Scenarios", "Sensitivity tables and what-if analysis", "\U0001f500", "pages/07_Scenarios.py"),
    ("Occupancy", "Occupancy trends, rent growth, loss-to-lease, renovation ROI", "\U0001f3e0", "pages/08_Occupancy.py"),
    ("Variance", "Budget vs actual comparison with waterfall", "\U0001f4c9", "pages/09_Variance.py"),
    ("Investor Portal", "Per-investor distribution statements and equity recovery", "\U0001f464", "pages/10_Investor_Portal.py"),
    ("Refi", "Refinance scenario comparison and rate sensitivity", "\U0001f3e6", "pages/11_Refi.py"),
    ("PDF Report", "One-click investor report generation", "\U0001f4c4", "pages/12_PDF_Report.py"),
]

cols_per_row = 3
for i in range(0, len(nav_items), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, col in enumerate(cols):
        idx = i + j
        if idx < len(nav_items):
            title, desc, icon, page_path = nav_items[idx]
            with col:
                st.page_link(
                    page_path,
                    label=f"{icon} **{title}**",
                    use_container_width=True,
                )
                st.markdown(f"""
                <p style="margin:-8px 0 12px 0;font-size:0.8rem;color:{COLORS['muted']};
                          padding:0 4px;">{desc}</p>
                """, unsafe_allow_html=True)

st.markdown(f"""
<div style="margin-top:24px;padding-top:16px;border-top:1px solid {COLORS['border']};">
    <p style="font-size:0.75rem;color:{COLORS['muted']};margin:0;">
        {prop['structures']} &bull; {prop['garages']} garages &bull;
        Total Equity: ${st.session_state.total_equity:,.0f}
    </p>
</div>
""", unsafe_allow_html=True)
