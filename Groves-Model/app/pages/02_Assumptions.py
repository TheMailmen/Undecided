"""Assumptions — Edit model configuration values with live recalculation."""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ui.theme import inject_theme
from ui.components import page_header

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

page_header(
    "Model Assumptions",
    "Edit values below \u2014 changes are reflected immediately across all pages",
)

# ── Property Details ──────────────────────────────────────────────
with st.expander("Property Details", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.property['name'] = st.text_input(
            "Property Name", value=st.session_state.property['name'])
        st.session_state.property['units'] = st.number_input(
            "Total Units", value=st.session_state.property['units'], step=1)
    with c2:
        st.session_state.property['purchase_price'] = st.number_input(
            "Purchase Price ($)", value=st.session_state.property['purchase_price'],
            step=100_000, format="%d")
        st.session_state.property['rentable_sf'] = st.number_input(
            "Rentable SF", value=st.session_state.property['rentable_sf'], step=100)
    with c3:
        st.session_state.property['year_built'] = st.number_input(
            "Year Built", value=st.session_state.property['year_built'], step=1)
        st.session_state.property['garages'] = st.number_input(
            "Garages", value=st.session_state.property['garages'], step=1)

# ── Loan Terms ────────────────────────────────────────────────────
with st.expander("Loan Terms", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.loan['original_amount'] = st.number_input(
            "Original Amount ($)", value=st.session_state.loan['original_amount'],
            step=10_000, format="%d")
        st.session_state.loan['rate'] = st.number_input(
            "Interest Rate", value=st.session_state.loan['rate'],
            min_value=0.0, max_value=0.20, step=0.0025, format="%.4f")
    with c2:
        st.session_state.loan['amort_years'] = st.number_input(
            "Amortization (years)", value=st.session_state.loan['amort_years'], step=1)
        st.session_state.loan['term_years'] = st.number_input(
            "Term (years)", value=st.session_state.loan['term_years'], step=1)
    with c3:
        st.session_state.loan['est_current_balance'] = st.number_input(
            "Est. Current Balance ($)",
            value=st.session_state.loan['est_current_balance'],
            step=10_000, format="%d")
        st.session_state.loan['io'] = st.checkbox(
            "Interest Only", value=st.session_state.loan['io'])

# ── TIC Ownership ─────────────────────────────────────────────────
with st.expander("TIC Ownership", expanded=False):
    for name in list(st.session_state.tic.keys()):
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.tic[name]['pct'] = st.number_input(
                f"{name} — Ownership %",
                value=st.session_state.tic[name]['pct'],
                min_value=0.0, max_value=1.0, step=0.001, format="%.5f",
                key=f"tic_pct_{name}")
        with c2:
            st.session_state.tic[name]['equity'] = st.number_input(
                f"{name} — Equity ($)",
                value=st.session_state.tic[name]['equity'],
                step=1000.0, format="%.2f", key=f"tic_eq_{name}")

    total_pct = sum(v['pct'] for v in st.session_state.tic.values())
    if abs(total_pct - 1.0) > 0.001:
        st.warning(f"Ownership totals {total_pct * 100:.3f}% (should be 100%)")
    else:
        st.success(f"Ownership: {total_pct * 100:.3f}%")

    st.session_state.total_equity = st.number_input(
        "Total Equity ($)", value=st.session_state.total_equity,
        step=10_000.0, format="%.2f")

# ── Unit Mix ──────────────────────────────────────────────────────
with st.expander("Unit Mix", expanded=False):
    for unit_type in list(st.session_state.unit_mix.keys()):
        st.subheader(unit_type)
        um = st.session_state.unit_mix[unit_type]
        c1, c2, c3 = st.columns(3)
        with c1:
            um['count'] = st.number_input(
                "Count", value=um['count'], step=1,
                key=f"um_count_{unit_type}")
        with c2:
            um['sf'] = st.number_input(
                "Avg SF", value=um['sf'], step=10,
                key=f"um_sf_{unit_type}")
        with c3:
            um['market_rent'] = st.number_input(
                "Market Rent ($)", value=um['market_rent'], step=25,
                key=f"um_rent_{unit_type}")

# ── Valuation ─────────────────────────────────────────────────────
with st.expander("Valuation (BOV)", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.valuation['bov_low'] = st.number_input(
            "BOV Low ($)", value=st.session_state.valuation['bov_low'],
            step=100_000, format="%d")
    with c2:
        st.session_state.valuation['bov_mid'] = st.number_input(
            "BOV Mid ($)", value=st.session_state.valuation['bov_mid'],
            step=100_000, format="%d")
    with c3:
        st.session_state.valuation['bov_high'] = st.number_input(
            "BOV High ($)", value=st.session_state.valuation['bov_high'],
            step=100_000, format="%d")

# ── Refinance Assumptions ─────────────────────────────────────────
with st.expander("Refinance Assumptions", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.refi['property_value'] = st.number_input(
            "Projected Value ($)", value=st.session_state.refi['property_value'],
            step=100_000, format="%d")
        st.session_state.refi['ltv'] = st.number_input(
            "Target LTV", value=st.session_state.refi['ltv'],
            min_value=0.0, max_value=1.0, step=0.05, format="%.2f")
    with c2:
        st.session_state.refi['rate'] = st.number_input(
            "New Rate", value=st.session_state.refi['rate'],
            min_value=0.0, max_value=0.20, step=0.0025, format="%.4f")
        st.session_state.refi['amort_years'] = st.number_input(
            "Amortization (years)", value=st.session_state.refi['amort_years'], step=1)
    with c3:
        st.session_state.refi['term_years'] = st.number_input(
            "Term (years)", value=st.session_state.refi['term_years'], step=1)
        st.session_state.refi['io'] = st.checkbox(
            "Interest Only (Refi)", value=st.session_state.refi['io'])

    st.session_state.refi['noah_equity_pct'] = st.number_input(
        "NOAH Equity %", value=st.session_state.refi['noah_equity_pct'],
        min_value=0.0, max_value=1.0, step=0.01, format="%.2f")
    st.session_state.refi['noah_pref_return'] = st.number_input(
        "NOAH Pref Return", value=st.session_state.refi['noah_pref_return'],
        min_value=0.0, max_value=0.20, step=0.0025, format="%.4f")

st.divider()

# ── Reset ─────────────────────────────────────────────────────────
if st.button("Reset All to Defaults"):
    for key in ['property', 'unit_mix', 'loan', 'tic', 'total_equity',
                'valuation', 'refi', 'escrow_names', 'initialized']:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.data_version = st.session_state.get('data_version', 0) + 1
    st.rerun()
