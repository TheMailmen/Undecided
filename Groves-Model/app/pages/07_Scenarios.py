"""Scenarios — Sensitivity tables and what-if analysis."""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_engine import get_t12_totals, load_pl_data

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

st.title("Scenario & Sensitivity Analysis")
st.caption("What-if analysis across exit cap rates, NOI growth, and hold periods.")

# ── Data loading ──────────────────────────────────────────────────
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
PL_CSV = os.path.join(BASE_DIR, 'data', 'pl_actuals.csv')

cfg = {
    'total_equity': st.session_state.total_equity,
    'purchase_price': st.session_state.property['purchase_price'],
}


@st.cache_data(show_spinner="Loading financial data...")
def load_data(_version, csv_path, total_equity, purchase_price):
    return load_pl_data(csv_path, {
        'total_equity': total_equity,
        'purchase_price': purchase_price,
    })


df = load_data(
    st.session_state.data_version, PL_CSV,
    cfg['total_equity'], cfg['purchase_price'],
)
t12 = get_t12_totals(df)

# ── Helpers ───────────────────────────────────────────────────────
current_noi = t12['NET OPERATING INCOME (NOI)']
current_ncf = t12['NET CASH FLOW']
purchase_price = st.session_state.property['purchase_price']
total_equity = st.session_state.total_equity
loan_balance = st.session_state.loan['est_current_balance']

C_TITLE = "#0D1B2A"
C_GREEN = "#1E8449"
C_RED = "#C00000"
C_ALT = "#F7F9FC"
C_ACCENT = "#1B4F72"


def compute_irr(cashflows, guess=0.10, tol=1e-8, max_iter=200):
    rate = guess
    for _ in range(max_iter):
        npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))
        dnpv = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cashflows))
        if abs(dnpv) < 1e-14:
            break
        new_rate = rate - npv / dnpv
        if abs(new_rate - rate) < tol:
            return new_rate
        rate = new_rate
    return rate


def project_returns(exit_cap, noi_growth, hold, sell_cost=0.02):
    """Compute IRR and equity multiple for a given scenario."""
    proj_noi = current_noi * (1 + noi_growth) ** hold
    exit_val = proj_noi / exit_cap
    net_sale = exit_val * (1 - sell_cost) - loan_balance

    cfs = [-total_equity]
    for yr in range(1, hold):
        cfs.append(current_ncf * (1 + noi_growth) ** yr)
    final_cf = current_ncf * (1 + noi_growth) ** hold + net_sale
    cfs.append(final_cf)

    total_return = sum(cfs[1:])
    em = total_return / total_equity if total_equity else 0
    irr = compute_irr(cfs)
    return irr, em, exit_val, net_sale


# ── Scenario Controls ─────────────────────────────────────────────
st.subheader("Base Assumptions")

col1, col2, col3 = st.columns(3)
with col1:
    base_hold = st.number_input(
        "Hold Period (years)", value=5, min_value=1, max_value=15,
        step=1, key="sc_hold")
with col2:
    base_sell_cost = st.number_input(
        "Selling Costs (%)", value=0.02, min_value=0.0, max_value=0.10,
        step=0.005, format="%.3f", key="sc_sell")
with col3:
    st.metric("Current T-12 NOI", f"${current_noi:,.0f}")

st.divider()

# ══════════════════════════════════════════════════════════════════
# SENSITIVITY TABLE 1: Exit Cap Rate × NOI Growth → IRR
# ══════════════════════════════════════════════════════════════════
st.subheader("IRR Sensitivity: Exit Cap Rate vs NOI Growth")

cap_rates = [0.055, 0.060, 0.065, 0.070, 0.075, 0.080]
noi_growths = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05]

irr_matrix = []
for cap in cap_rates:
    row = []
    for growth in noi_growths:
        irr_val, _, _, _ = project_returns(cap, growth, base_hold, base_sell_cost)
        row.append(irr_val)
    irr_matrix.append(row)

# Build HTML table
cap_labels = [f"{c*100:.1f}%" for c in cap_rates]
growth_labels = [f"{g*100:.0f}%" for g in noi_growths]

html = [f'''
<div style="overflow-x:auto;margin-bottom:20px;">
<table style="border-collapse:collapse;width:100%;font-family:Calibri,sans-serif;font-size:13px;text-align:center;">
<thead>
<tr style="background-color:{C_TITLE};color:white;font-weight:700;">
    <td style="padding:8px 12px;text-align:left;">Exit Cap ↓ / NOI Growth →</td>
''']
for gl in growth_labels:
    html.append(f'    <td style="padding:8px 12px;">{gl}</td>')
html.append('</tr></thead><tbody>')

for i, (cap_label, row) in enumerate(zip(cap_labels, irr_matrix)):
    bg = f"background-color:{C_ALT};" if i % 2 == 0 else ""
    html.append(f'<tr style="{bg}">')
    html.append(f'<td style="padding:6px 12px;font-weight:700;text-align:left;">{cap_label}</td>')
    for val in row:
        color = C_GREEN if val > 0.10 else (C_RED if val < 0 else "#333")
        weight = "700" if val > 0.10 else "400"
        html.append(f'<td style="padding:6px 12px;color:{color};font-weight:{weight};">{val*100:.1f}%</td>')
    html.append('</tr>')

html.append('</tbody></table></div>')
st.markdown('\n'.join(html), unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# SENSITIVITY TABLE 2: Exit Cap Rate × NOI Growth → Equity Multiple
# ══════════════════════════════════════════════════════════════════
st.subheader("Equity Multiple Sensitivity: Exit Cap Rate vs NOI Growth")

em_matrix = []
for cap in cap_rates:
    row = []
    for growth in noi_growths:
        _, em_val, _, _ = project_returns(cap, growth, base_hold, base_sell_cost)
        row.append(em_val)
    em_matrix.append(row)

html2 = [f'''
<div style="overflow-x:auto;margin-bottom:20px;">
<table style="border-collapse:collapse;width:100%;font-family:Calibri,sans-serif;font-size:13px;text-align:center;">
<thead>
<tr style="background-color:{C_TITLE};color:white;font-weight:700;">
    <td style="padding:8px 12px;text-align:left;">Exit Cap ↓ / NOI Growth →</td>
''']
for gl in growth_labels:
    html2.append(f'    <td style="padding:8px 12px;">{gl}</td>')
html2.append('</tr></thead><tbody>')

for i, (cap_label, row) in enumerate(zip(cap_labels, em_matrix)):
    bg = f"background-color:{C_ALT};" if i % 2 == 0 else ""
    html2.append(f'<tr style="{bg}">')
    html2.append(f'<td style="padding:6px 12px;font-weight:700;text-align:left;">{cap_label}</td>')
    for val in row:
        color = C_GREEN if val > 2.0 else (C_RED if val < 1.0 else "#333")
        weight = "700" if val > 2.0 else "400"
        html2.append(f'<td style="padding:6px 12px;color:{color};font-weight:{weight};">{val:.2f}x</td>')
    html2.append('</tr>')

html2.append('</tbody></table></div>')
st.markdown('\n'.join(html2), unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# SENSITIVITY TABLE 3: Hold Period × Exit Cap Rate → IRR
# ══════════════════════════════════════════════════════════════════
st.subheader("IRR by Hold Period")

hold_periods = [3, 5, 7, 10]

col1, col2 = st.columns([1, 1])
with col1:
    scenario_growth = st.number_input(
        "NOI Growth for Hold Period Analysis",
        value=0.03, min_value=-0.05, max_value=0.15,
        step=0.005, format="%.3f", key="sc_growth_hold")

html3 = [f'''
<div style="overflow-x:auto;margin-bottom:20px;">
<table style="border-collapse:collapse;width:100%;font-family:Calibri,sans-serif;font-size:13px;text-align:center;">
<thead>
<tr style="background-color:{C_TITLE};color:white;font-weight:700;">
    <td style="padding:8px 12px;text-align:left;">Exit Cap ↓ / Hold →</td>
''']
for h in hold_periods:
    html3.append(f'    <td style="padding:8px 12px;">{h} Years</td>')
html3.append('</tr></thead><tbody>')

for i, cap in enumerate(cap_rates):
    bg = f"background-color:{C_ALT};" if i % 2 == 0 else ""
    html3.append(f'<tr style="{bg}">')
    html3.append(f'<td style="padding:6px 12px;font-weight:700;text-align:left;">{cap*100:.1f}%</td>')
    for h in hold_periods:
        irr_val, _, _, _ = project_returns(cap, scenario_growth, h, base_sell_cost)
        color = C_GREEN if irr_val > 0.10 else (C_RED if irr_val < 0 else "#333")
        weight = "700" if irr_val > 0.10 else "400"
        html3.append(f'<td style="padding:6px 12px;color:{color};font-weight:{weight};">{irr_val*100:.1f}%</td>')
    html3.append('</tr>')

html3.append('</tbody></table></div>')
st.markdown('\n'.join(html3), unsafe_allow_html=True)

st.divider()

# ══════════════════════════════════════════════════════════════════
# SCENARIO COMPARISON: Side-by-side named scenarios
# ══════════════════════════════════════════════════════════════════
st.subheader("Named Scenario Comparison")

scenarios = {
    'Conservative': {'exit_cap': 0.075, 'noi_growth': 0.01, 'hold': 5},
    'Base Case':    {'exit_cap': 0.065, 'noi_growth': 0.03, 'hold': 5},
    'Optimistic':   {'exit_cap': 0.055, 'noi_growth': 0.05, 'hold': 5},
    'Quick Flip':   {'exit_cap': 0.060, 'noi_growth': 0.03, 'hold': 3},
}

cols = st.columns(len(scenarios))
for col, (name, params) in zip(cols, scenarios.items()):
    irr_val, em_val, exit_val, net_sale = project_returns(
        params['exit_cap'], params['noi_growth'],
        params['hold'], base_sell_cost,
    )
    proj_noi = current_noi * (1 + params['noi_growth']) ** params['hold']

    with col:
        st.markdown(f"**{name}**")
        st.caption(
            f"Cap: {params['exit_cap']*100:.1f}% | "
            f"Growth: {params['noi_growth']*100:.0f}% | "
            f"Hold: {params['hold']}yr"
        )
        st.metric("IRR", f"{irr_val*100:.1f}%")
        st.metric("Equity Multiple", f"{em_val:.2f}x")
        st.metric("Exit Value", f"${exit_val:,.0f}")
        st.metric("Net Proceeds", f"${net_sale:,.0f}")

st.divider()

# ── Exit Value Heatmap ────────────────────────────────────────────
st.subheader("Exit Value Heatmap")

exit_val_matrix = []
for cap in cap_rates:
    row = []
    for growth in noi_growths:
        proj_noi = current_noi * (1 + growth) ** base_hold
        row.append(proj_noi / cap)
    exit_val_matrix.append(row)

fig = go.Figure(data=go.Heatmap(
    z=exit_val_matrix,
    x=[f"{g*100:.0f}% growth" for g in noi_growths],
    y=[f"{c*100:.1f}% cap" for c in cap_rates],
    colorscale='Greens',
    texttemplate="$%{z:,.0f}",
    textfont=dict(size=11),
    hoverongaps=False,
    colorbar=dict(title="Exit Value ($)"),
))
fig.update_layout(
    height=400, margin=dict(l=0, r=0, t=30, b=0),
    xaxis_title="Annual NOI Growth",
    yaxis_title="Exit Cap Rate",
    yaxis=dict(autorange='reversed'),
)
st.plotly_chart(fig, use_container_width=True)
