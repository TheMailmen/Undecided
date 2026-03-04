"""Investor Portal — Personalized per-owner view of equity, distributions, and returns."""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_engine import get_monthly_series, get_t12_totals, load_pl_data

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

st.title("Investor Portal")

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

C_TITLE = "#0D1B2A"
C_GREEN = "#1E8449"
C_RED = "#C00000"
C_ALT = "#F7F9FC"
C_ACCENT = "#1B4F72"
C_NOTE_BG = "#E8F5E9"

# ── Owner Selector ────────────────────────────────────────────────
owners = list(st.session_state.tic.keys())
selected_owner = st.selectbox("Select Investor", owners)

owner_info = st.session_state.tic[selected_owner]
pct = owner_info['pct']
equity = owner_info['equity']

st.caption(f"Ownership: {pct*100:.3f}% | Equity Invested: ${equity:,.0f}")
st.divider()

# ── Monthly NCF series for this owner ─────────────────────────────
ncf_series = get_monthly_series(df, 'NET CASH FLOW')
ncf_series['Owner_Share'] = ncf_series['Amount'] * pct

# Cumulative distributions
ncf_series['Cumulative'] = ncf_series['Owner_Share'].cumsum()

total_distributed = ncf_series['Owner_Share'].sum()
months_held = len(ncf_series)

# Annualized metrics
annual_cf = total_distributed * (12 / months_held) if months_held else 0
coc = annual_cf / equity if equity else 0

# T-12 owner share
t12_ncf = t12['NET CASH FLOW'] * pct
t12_noi = t12['NET OPERATING INCOME (NOI)'] * pct
t12_cfads = t12['CASH FLOW AFTER DEBT SERVICE'] * pct

# ── KPI Cards ─────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Equity Invested", f"${equity:,.0f}")
col2.metric("Total Distributions", f"${total_distributed:,.0f}")
col3.metric("Annualized Cash-on-Cash", f"{coc * 100:.1f}%")
col4.metric("Months Held", f"{months_held}")

col5, col6, col7, col8 = st.columns(4)
col5.metric("T-12 NOI Share", f"${t12_noi:,.0f}")
col6.metric("T-12 CFADS Share", f"${t12_cfads:,.0f}")
col7.metric("T-12 NCF Share", f"${t12_ncf:,.0f}")
remaining_to_breakeven = equity - total_distributed
col8.metric(
    "To Breakeven",
    f"${max(0, remaining_to_breakeven):,.0f}" if remaining_to_breakeven > 0 else "Recovered!",
)

st.divider()

# ── Chart 1: Monthly Distribution Timeline ───────────────────────
st.subheader(f"Monthly Distribution — {selected_owner}")

fig = go.Figure()

# Monthly bars
colors = [C_GREEN if v >= 0 else C_RED for v in ncf_series['Owner_Share']]
fig.add_trace(go.Bar(
    x=ncf_series['Month'], y=ncf_series['Owner_Share'],
    name='Monthly Distribution', marker_color=colors, opacity=0.7,
))

# Cumulative line
fig.add_trace(go.Scatter(
    x=ncf_series['Month'], y=ncf_series['Cumulative'],
    name='Cumulative', line=dict(color=C_TITLE, width=2.5),
    mode='lines+markers', yaxis='y2',
))

# Equity invested line
fig.add_hline(y=0, line_dash="dot", line_color="#7F8C8D", opacity=0.3)

fig.update_layout(
    height=400, margin=dict(l=0, r=0, t=30, b=0),
    yaxis=dict(title="Monthly ($)"),
    yaxis2=dict(title="Cumulative ($)", overlaying='y', side='right'),
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Distribution Statement Table ─────────────────────────────────
st.subheader("Distribution Statement")

html = [f'''
<div style="overflow-x:auto;">
<table style="border-collapse:collapse;width:100%;font-family:Calibri,sans-serif;font-size:13px;">
<thead>
<tr style="background-color:{C_TITLE};color:white;font-weight:700;text-align:center;">
    <td style="text-align:left;padding:8px 12px;">Month</td>
    <td style="padding:8px 12px;">Property NCF</td>
    <td style="padding:8px 12px;">Your Share ({pct*100:.3f}%)</td>
    <td style="padding:8px 12px;">Cumulative</td>
    <td style="padding:8px 12px;">% of Equity Returned</td>
</tr>
</thead>
<tbody>
''']

cumul = 0
for i, row in ncf_series.iterrows():
    month_label = row['Month'].strftime('%b %Y')
    prop_ncf = row['Amount']
    owner_share = row['Owner_Share']
    cumul += owner_share
    pct_returned = cumul / equity if equity else 0

    bg = f"background-color:{C_ALT};" if i % 2 == 0 else ""
    share_color = C_GREEN if owner_share >= 0 else C_RED

    def _fmt(v):
        if v < 0:
            return f"(${abs(v):,.0f})"
        return f"${v:,.0f}"

    html.append(f'''
<tr style="{bg}">
    <td style="padding:5px 12px;font-weight:600;">{month_label}</td>
    <td style="text-align:right;padding:5px 12px;">{_fmt(prop_ncf)}</td>
    <td style="text-align:right;padding:5px 12px;color:{share_color};font-weight:600;">{_fmt(owner_share)}</td>
    <td style="text-align:right;padding:5px 12px;">{_fmt(cumul)}</td>
    <td style="text-align:right;padding:5px 12px;">{pct_returned*100:.1f}%</td>
</tr>''')

# Total row
html.append(f'''
<tr style="background-color:{C_NOTE_BG};font-weight:700;">
    <td style="padding:6px 12px;color:{C_GREEN};">TOTAL</td>
    <td style="text-align:right;padding:6px 12px;color:{C_GREEN};">{_fmt(ncf_series["Amount"].sum())}</td>
    <td style="text-align:right;padding:6px 12px;color:{C_GREEN};">{_fmt(total_distributed)}</td>
    <td style="text-align:right;padding:6px 12px;color:{C_GREEN};">{_fmt(cumul)}</td>
    <td style="text-align:right;padding:6px 12px;color:{C_GREEN};">{cumul/equity*100:.1f}%</td>
</tr>''')

html.append('</tbody></table></div>')
st.markdown('\n'.join(html), unsafe_allow_html=True)

st.divider()

# ── Equity Recovery Progress ─────────────────────────────────────
st.subheader("Equity Recovery Progress")

recovery_pct = min(total_distributed / equity, 1.0) if equity else 0

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=recovery_pct * 100,
    delta={'reference': 100, 'relative': False, 'suffix': 'pp to go'},
    title={'text': "Equity Returned (%)"},
    gauge={
        'axis': {'range': [0, 100]},
        'bar': {'color': C_GREEN},
        'steps': [
            {'range': [0, 50], 'color': '#F7F9FC'},
            {'range': [50, 100], 'color': '#E8F5E9'},
        ],
        'threshold': {
            'line': {'color': C_RED, 'width': 3},
            'thickness': 0.8,
            'value': 100,
        },
    },
))
fig_gauge.update_layout(height=300, margin=dict(l=30, r=30, t=60, b=0))
st.plotly_chart(fig_gauge, use_container_width=True)
