"""Investor Portal — Personalized per-owner view of equity, distributions, and returns."""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_engine import get_monthly_series, get_t12_totals, load_pl_data
from ui.theme import inject_theme, COLORS, PLOTLY_LAYOUT, fmt_currency, fmt_pct
from ui.components import page_header, kpi_row, section_header, spacer, styled_table, no_data_page, page_footer

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

page_header(
    "Investor Portal",
    "Personalized equity tracking and distribution statements",
)

# ── Data guard ────────────────────────────────────────────────
if no_data_page("pl_actuals.csv"):
    st.stop()

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

# ── Owner Selector ────────────────────────────────────────────────
owners = list(st.session_state.tic.keys())
selected_owner = st.selectbox("Select Investor", owners)

owner_info = st.session_state.tic[selected_owner]
pct = owner_info['pct']
equity = owner_info['equity']

st.markdown(
    f'<p style="font-size:0.85rem;color:{COLORS["muted"]};margin:-8px 0 16px 0;">'
    f'Ownership: <b>{pct*100:.3f}%</b> &bull; Equity Invested: <b>{fmt_currency(equity)}</b></p>',
    unsafe_allow_html=True,
)

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
remaining_to_breakeven = equity - total_distributed

kpi_row([
    {"label": "Equity Invested", "value": fmt_currency(equity)},
    {"label": "Total Distributions", "value": fmt_currency(total_distributed)},
    {"label": "Annualized Cash-on-Cash", "value": fmt_pct(coc)},
    {"label": "Months Held", "value": str(months_held)},
])

kpi_row([
    {"label": "T-12 NOI Share", "value": fmt_currency(t12_noi)},
    {"label": "T-12 CFADS Share", "value": fmt_currency(t12_cfads)},
    {"label": "T-12 NCF Share", "value": fmt_currency(t12_ncf)},
    {"label": "To Breakeven",
     "value": fmt_currency(max(0, remaining_to_breakeven)) if remaining_to_breakeven > 0 else "Recovered!"},
])

spacer(8)

# ── CapEx Plan Context ───────────────────────────────────────────
capex_budget = st.session_state.capex_budget
actual_capex = t12.get('Total Capital Expenditures', 0)
capex_remaining = capex_budget - actual_capex
capex_pct = actual_capex / capex_budget * 100 if capex_budget else 0

# CFADS before CapEx vs after
t12_cfads_total = t12['CASH FLOW AFTER DEBT SERVICE']
capex_impact = actual_capex * pct

section_header("Capital Expenditure Plan",
               "Renovation spend is below-the-line — it reduces NCF distributions but builds long-term value")

capex_c1, capex_c2 = st.columns(2)

with capex_c1:
    kpi_row([
        {"label": "CapEx Budget", "value": fmt_currency(capex_budget)},
        {"label": "Spent to Date", "value": fmt_currency(actual_capex),
         "delta": f"{capex_pct:.0f}% of budget"},
        {"label": "Remaining", "value": fmt_currency(capex_remaining)},
    ])

with capex_c2:
    kpi_row([
        {"label": "Your CFADS (pre-CapEx)", "value": fmt_currency(t12_cfads)},
        {"label": "CapEx Impact on Your Share", "value": fmt_currency(-capex_impact)},
        {"label": "Your NCF (post-CapEx)", "value": fmt_currency(t12_ncf)},
    ])

# Progress bar
bar_pct = min(capex_pct, 100)
st.markdown(
    f'<div style="background:{COLORS["surface"]};border:1px solid {COLORS["border"]};'
    f'border-radius:8px;padding:12px 16px;margin:0 0 8px 0;">'
    f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
    f'<span style="font-size:0.78rem;font-weight:600;color:{COLORS["text"]};">Renovation Progress</span>'
    f'<span style="font-size:0.78rem;color:{COLORS["muted"]};">{fmt_currency(actual_capex)} / {fmt_currency(capex_budget)}</span>'
    f'</div>'
    f'<div style="background:{COLORS["border"]};border-radius:4px;height:10px;overflow:hidden;">'
    f'<div style="background:{COLORS["accent"]};width:{bar_pct:.0f}%;height:100%;border-radius:4px;"></div>'
    f'</div>'
    f'<p style="margin:6px 0 0 0;font-size:0.76rem;color:{COLORS["muted"]};">'
    f'CapEx is invested in unit renovations that drive rent growth and property value — '
    f'distributions will increase as the renovation plan completes.</p>'
    f'</div>',
    unsafe_allow_html=True,
)

spacer(8)

# ── Chart 1: Monthly Distribution Timeline ───────────────────────
section_header(f"Monthly Distribution \u2014 {selected_owner}")

fig = go.Figure()

# Monthly bars
colors = [COLORS["success"] if v >= 0 else COLORS["error"] for v in ncf_series['Owner_Share']]
fig.add_trace(go.Bar(
    x=ncf_series['Month'], y=ncf_series['Owner_Share'],
    name='Monthly Distribution', marker_color=colors, opacity=0.7,
))

# Cumulative line
fig.add_trace(go.Scatter(
    x=ncf_series['Month'], y=ncf_series['Cumulative'],
    name='Cumulative', line=dict(color=COLORS["primary"], width=2.5),
    mode='lines+markers', yaxis='y2',
))

# Zero line
fig.add_hline(y=0, line_dash="dot", line_color=COLORS["muted"], opacity=0.3)

portal_layout = {**PLOTLY_LAYOUT}
portal_layout['yaxis'] = dict(title="Monthly ($)", gridcolor=COLORS["grid"])
fig.update_layout(**portal_layout, height=400, yaxis2=dict(title="Cumulative ($)", overlaying='y', side='right', gridcolor=COLORS["grid"]))
st.plotly_chart(fig, use_container_width=True)

spacer(8)

# ── Distribution Statement Table ─────────────────────────────────
section_header("Distribution Statement")

headers = ["Month", "Property NCF", f"Your Share ({pct*100:.3f}%)", "Cumulative", "% of Equity Returned"]
tbl_rows = []
col_align = ["left", "right", "right", "right", "right"]

cumul = 0
for _, row in ncf_series.iterrows():
    month_label = row['Month'].strftime('%b %Y')
    prop_ncf = row['Amount']
    owner_share = row['Owner_Share']
    cumul += owner_share
    pct_returned = cumul / equity if equity else 0

    share_color = COLORS["success"] if owner_share >= 0 else COLORS["error"]

    tbl_rows.append([
        month_label,
        fmt_currency(prop_ncf),
        f"<span style='color:{share_color};font-weight:600;'>{fmt_currency(owner_share)}</span>",
        fmt_currency(cumul),
        fmt_pct(pct_returned),
    ])

# Total row
tbl_rows.append([
    f"<b style='color:{COLORS['success']}'>TOTAL</b>",
    f"<b style='color:{COLORS['success']}'>{fmt_currency(ncf_series['Amount'].sum())}</b>",
    f"<b style='color:{COLORS['success']}'>{fmt_currency(total_distributed)}</b>",
    f"<b style='color:{COLORS['success']}'>{fmt_currency(cumul)}</b>",
    f"<b style='color:{COLORS['success']}'>{fmt_pct(cumul / equity if equity else 0)}</b>",
])

styled_table(headers, tbl_rows, col_align=col_align, highlight_rows={len(tbl_rows) - 1})

spacer(8)

# ── Equity Recovery Progress ─────────────────────────────────────
section_header("Equity Recovery Progress")

recovery_pct = min(total_distributed / equity, 1.0) if equity else 0

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=recovery_pct * 100,
    delta={'reference': 100, 'relative': False, 'suffix': 'pp to go'},
    title={'text': "Equity Returned (%)", 'font': {'size': 14, 'color': COLORS["text"]}},
    number={'font': {'size': 36, 'color': COLORS["primary"]}},
    gauge={
        'axis': {'range': [0, 100], 'tickfont': {'size': 11, 'color': COLORS["muted"]}},
        'bar': {'color': COLORS["accent"]},
        'steps': [
            {'range': [0, 50], 'color': '#F0FDFA'},
            {'range': [50, 100], 'color': '#CCFBF1'},
        ],
        'threshold': {
            'line': {'color': COLORS["error"], 'width': 3},
            'thickness': 0.8,
            'value': 100,
        },
    },
))
fig_gauge.update_layout(
    height=300, margin=dict(l=30, r=30, t=60, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, sans-serif"),
)
st.plotly_chart(fig_gauge, use_container_width=True)

page_footer()
