"""Assumptions — Edit model configuration values with live recalculation."""

import json
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ui.theme import inject_theme, COLORS, fmt_currency, fmt_pct
from ui.components import page_header, kpi_row, section_header, spacer, badge

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

page_header(
    "Model Assumptions",
    "Edit values below \u2014 changes are reflected immediately across all pages",
)

# ── Summary KPIs ─────────────────────────────────────────────────
prop = st.session_state.property
loan = st.session_state.loan
total_pct = sum(v['pct'] for v in st.session_state.tic.values())
total_tic_equity = sum(v['equity'] for v in st.session_state.tic.values())
ltv = loan['est_current_balance'] / prop['purchase_price'] * 100 if prop['purchase_price'] else 0

kpi_row([
    {"label": "Purchase Price", "value": fmt_currency(prop['purchase_price'])},
    {"label": "Loan Balance", "value": fmt_currency(loan['est_current_balance'])},
    {"label": "LTV", "value": f"{ltv:.1f}%"},
    {"label": "Total Equity", "value": fmt_currency(st.session_state.total_equity)},
])

spacer(8)

# ── Property Details ──────────────────────────────────────────────
section_header("Property Details")

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

spacer(8)

# ── Loan Terms ────────────────────────────────────────────────────
section_header("Loan Terms")

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

spacer(8)

# ── TIC Ownership ─────────────────────────────────────────────────
section_header("TIC Ownership")

# Validation status
total_pct = sum(v['pct'] for v in st.session_state.tic.values())
pct_ok = abs(total_pct - 1.0) <= 0.001
pct_badge = badge(f"{total_pct * 100:.3f}%", "success" if pct_ok else "error")
st.markdown(
    f'<div style="margin-bottom:12px;">Ownership Total: {pct_badge}</div>',
    unsafe_allow_html=True,
)

for name in list(st.session_state.tic.keys()):
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.tic[name]['pct'] = st.number_input(
            f"{name} \u2014 Ownership %",
            value=st.session_state.tic[name]['pct'],
            min_value=0.0, max_value=1.0, step=0.001, format="%.5f",
            key=f"tic_pct_{name}")
    with c2:
        st.session_state.tic[name]['equity'] = st.number_input(
            f"{name} \u2014 Equity ($)",
            value=st.session_state.tic[name]['equity'],
            step=1000.0, format="%.2f", key=f"tic_eq_{name}")

if not pct_ok:
    st.warning(f"Ownership totals {total_pct * 100:.3f}% \u2014 should equal 100%")

st.session_state.total_equity = st.number_input(
    "Total Equity ($)", value=st.session_state.total_equity,
    step=10_000.0, format="%.2f")

# Cross-check equity
total_tic_equity = sum(v['equity'] for v in st.session_state.tic.values())
equity_diff = abs(total_tic_equity - st.session_state.total_equity)
if equity_diff > 1:
    st.warning(
        f"Sum of TIC equity ({fmt_currency(total_tic_equity)}) differs from "
        f"Total Equity ({fmt_currency(st.session_state.total_equity)}) "
        f"by {fmt_currency(equity_diff)}"
    )

spacer(8)

# ── Unit Mix ──────────────────────────────────────────────────────
section_header("Unit Mix")

total_units_check = 0
for unit_type in list(st.session_state.unit_mix.keys()):
    um = st.session_state.unit_mix[unit_type]
    st.markdown(
        f'<p style="margin:12px 0 4px 0;font-weight:600;font-size:0.88rem;'
        f'color:{COLORS["text"]};font-family:\'Inter\',system-ui,sans-serif;">'
        f'{unit_type}</p>',
        unsafe_allow_html=True,
    )
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
    total_units_check += um['count']

if total_units_check != st.session_state.property['units']:
    st.warning(
        f"Unit mix total ({total_units_check}) differs from "
        f"property units ({st.session_state.property['units']})"
    )

spacer(8)

# ── Valuation ─────────────────────────────────────────────────────
section_header("Valuation (BOV)")

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

spacer(8)

# ── Refinance Assumptions ─────────────────────────────────────────
section_header("Refinance Assumptions")

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

spacer(16)

# ── Export / Import Configuration ─────────────────────────────────
section_header("Configuration Management")

col_export, col_import, col_reset = st.columns(3)

with col_export:
    config_data = {
        'property': st.session_state.property,
        'unit_mix': st.session_state.unit_mix,
        'loan': st.session_state.loan,
        'tic': st.session_state.tic,
        'total_equity': st.session_state.total_equity,
        'valuation': st.session_state.valuation,
        'refi': st.session_state.refi,
        'escrow_names': st.session_state.escrow_names,
    }
    st.download_button(
        label="Export Config (JSON)",
        data=json.dumps(config_data, indent=2, default=str),
        file_name="groves_config.json",
        mime="application/json",
        use_container_width=True,
    )

with col_import:
    uploaded_config = st.file_uploader(
        "Import Config", type=['json'], key="config_upload",
        label_visibility="collapsed",
    )
    if uploaded_config is not None:
        try:
            imported = json.loads(uploaded_config.read())
            config_keys = ['property', 'unit_mix', 'loan', 'tic',
                           'total_equity', 'valuation', 'refi', 'escrow_names']
            missing = [k for k in config_keys if k not in imported]
            if missing:
                st.error(f"Missing keys: {missing}")
            else:
                for k in config_keys:
                    st.session_state[k] = imported[k]
                st.session_state.data_version = st.session_state.get('data_version', 0) + 1
                st.success("Configuration imported!")
                st.rerun()
        except Exception as e:
            st.error(f"Import failed: {e}")

with col_reset:
    if st.button("Reset to Defaults", use_container_width=True):
        for key in ['property', 'unit_mix', 'loan', 'tic', 'total_equity',
                    'valuation', 'refi', 'escrow_names', 'initialized']:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.data_version = st.session_state.get('data_version', 0) + 1
        st.rerun()
