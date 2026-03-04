"""Dashboard — KPI cards and interactive Plotly charts."""

import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_engine import (
    get_expense_breakdown,
    get_monthly_series,
    get_t12_totals,
    load_pl_data,
)
from ui.theme import inject_theme, COLORS, PLOTLY_LAYOUT, fmt_currency, fmt_pct
from ui.components import page_header, kpi_row, section_header, spacer, no_data_page, styled_table, page_footer

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

# ── Data guard ────────────────────────────────────────────────
if no_data_page("pl_actuals.csv"):
    st.stop()

# Resolve CSV path
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
PL_CSV = os.path.join(BASE_DIR, 'data', 'pl_actuals.csv')

cfg = {
    'total_equity': st.session_state.total_equity,
    'purchase_price': st.session_state.property['purchase_price'],
}


@st.cache_data(show_spinner="Loading financial data...")
def load_data(_version, csv_path, total_equity, purchase_price):
    """Cache data, invalidated by version bump."""
    return load_pl_data(csv_path, {
        'total_equity': total_equity,
        'purchase_price': purchase_price,
    })


df = load_data(
    st.session_state.data_version,
    PL_CSV,
    cfg['total_equity'],
    cfg['purchase_price'],
)
t12 = get_t12_totals(df)

# ── Data freshness ────────────────────────────────────────────
latest_month = sorted(df['Month'].unique())[-1]
latest_label = latest_month.strftime('%B %Y') if hasattr(latest_month, 'strftime') else str(latest_month)
month_count = len(df['Month'].unique())

# ── Page Header ──────────────────────────────────────────────────
page_header(
    "Dashboard",
    "Trailing 12-month performance overview",
    right_text=f"{st.session_state.property['name']} \u2022 {st.session_state.property['units']} units \u2022 Data through {latest_label}",
)

# ── Compute MoM deltas for KPI cards ─────────────────────────────
all_months = sorted(df['Month'].unique())
if len(all_months) >= 2:
    last_m = all_months[-1]
    prev_m = all_months[-2]

    def _val(account, month):
        row = df[(df['Account'] == account) & (df['Month'] == month)]
        return row['Amount'].sum() if len(row) > 0 else 0

    d_noi = _val('NET OPERATING INCOME (NOI)', last_m) - _val('NET OPERATING INCOME (NOI)', prev_m)
    d_cfads = _val('CASH FLOW AFTER DEBT SERVICE', last_m) - _val('CASH FLOW AFTER DEBT SERVICE', prev_m)
    d_egi = _val('EFFECTIVE GROSS INCOME (EGI)', last_m) - _val('EFFECTIVE GROSS INCOME (EGI)', prev_m)
    d_opex = _val('Total Operating Expenses', last_m) - _val('Total Operating Expenses', prev_m)
    d_dscr = _val('DSCR', last_m) - _val('DSCR', prev_m)
else:
    d_noi = d_cfads = d_egi = d_opex = d_dscr = None

# ── KPI Cards ─────────────────────────────────────────────────────
kpi_row([
    {"label": "T-12 NOI", "value": fmt_currency(t12['NET OPERATING INCOME (NOI)']),
     "delta": f"${d_noi:,.0f} MoM" if d_noi is not None else None},
    {"label": "T-12 CFADS", "value": fmt_currency(t12['CASH FLOW AFTER DEBT SERVICE']),
     "delta": f"${d_cfads:,.0f} MoM" if d_cfads is not None else None},
    {"label": "DSCR", "value": f"{t12['DSCR']:.2f}x",
     "delta": f"{d_dscr:.2f}" if d_dscr is not None else None},
    {"label": "Cap Rate", "value": fmt_pct(t12['Cap Rate'])},
])

kpi_row([
    {"label": "T-12 EGI", "value": fmt_currency(t12['EFFECTIVE GROSS INCOME (EGI)']),
     "delta": f"${d_egi:,.0f} MoM" if d_egi is not None else None},
    {"label": "T-12 OpEx", "value": fmt_currency(t12['Total Operating Expenses']),
     "delta": f"${d_opex:,.0f} MoM" if d_opex is not None else None,
     "delta_inverse": True},
    {"label": "Expense Ratio", "value": fmt_pct(t12['Expense Ratio'])},
    {"label": "Cash-on-Cash", "value": fmt_pct(t12['Cash-on-Cash (CFADS)'])},
])

spacer(8)

# ── Chart 1: Monthly NOI Trend ────────────────────────────────────
section_header("Monthly NOI Trend")

noi_series = get_monthly_series(df, 'NET OPERATING INCOME (NOI)')
noi_series['Rolling3'] = noi_series['Amount'].rolling(3).mean()

fig_noi = go.Figure()
fig_noi.add_trace(go.Bar(
    x=noi_series['Month'], y=noi_series['Amount'],
    name='Monthly NOI', marker_color=COLORS["accent"], opacity=0.7,
))
fig_noi.add_trace(go.Scatter(
    x=noi_series['Month'], y=noi_series['Rolling3'],
    name='3-Mo Rolling Avg', line=dict(color=COLORS["primary"], width=2.5),
))
fig_noi.update_layout(
    **PLOTLY_LAYOUT,
    height=350,
    yaxis_title="$",
)
st.plotly_chart(fig_noi, use_container_width=True)

# ── Chart 2: T12 Cash Flow Waterfall ──────────────────────────────
section_header("T-12 Cash Flow Waterfall")

waterfall_items = [
    ('EGI', t12['EFFECTIVE GROSS INCOME (EGI)'], 'relative'),
    ('OpEx', -t12['Total Operating Expenses'], 'relative'),
    ('NOI', t12['NET OPERATING INCOME (NOI)'], 'total'),
    ('Debt Service', -(t12['NET OPERATING INCOME (NOI)'] - t12['CASH FLOW AFTER DEBT SERVICE']), 'relative'),
    ('CFADS', t12['CASH FLOW AFTER DEBT SERVICE'], 'total'),
    ('CapEx', -t12.get('Total Capital Expenditures', 0), 'relative'),
    ('Net Cash Flow', t12['NET CASH FLOW'], 'total'),
]
fig_wf = go.Figure(go.Waterfall(
    x=[item[0] for item in waterfall_items],
    y=[item[1] for item in waterfall_items],
    measure=[item[2] for item in waterfall_items],
    connector=dict(line=dict(color=COLORS["border"])),
    increasing=dict(marker=dict(color=COLORS["success"])),
    decreasing=dict(marker=dict(color=COLORS["error"])),
    totals=dict(marker=dict(color=COLORS["primary"])),
))
fig_wf.update_layout(**PLOTLY_LAYOUT, height=400)
st.plotly_chart(fig_wf, use_container_width=True)

# ── Charts 3 & 4: Side by Side ───────────────────────────────────
left_col, right_col = st.columns(2)

with left_col:
    section_header("T-12 Expense Breakdown")
    exp_df = get_expense_breakdown(df)
    if len(exp_df) > 10:
        top10 = exp_df.head(10)
        other = pd.DataFrame([{
            'Account': 'Other',
            'Amount': exp_df.iloc[10:]['Amount'].sum(),
        }])
        exp_df = pd.concat([top10, other], ignore_index=True)

    fig_exp = px.bar(
        exp_df, x='Amount', y='Account', orientation='h',
        color_discrete_sequence=[COLORS["accent"]],
    )
    fig_exp.update_layout(
        **PLOTLY_LAYOUT,
        height=400,
        yaxis=dict(autorange='reversed', gridcolor=COLORS["grid"]),
    )
    st.plotly_chart(fig_exp, use_container_width=True)

with right_col:
    section_header("Revenue vs Expenses")
    egi_s = get_monthly_series(df, 'EFFECTIVE GROSS INCOME (EGI)')
    opex_s = get_monthly_series(df, 'Total Operating Expenses')

    fig_rev = go.Figure()
    fig_rev.add_trace(go.Scatter(
        x=egi_s['Month'], y=egi_s['Amount'],
        name='EGI', fill='tozeroy', fillcolor='rgba(47,143,157,0.15)',
        line=dict(color=COLORS["accent"], width=2),
    ))
    fig_rev.add_trace(go.Scatter(
        x=opex_s['Month'], y=opex_s['Amount'],
        name='OpEx', fill='tozeroy', fillcolor='rgba(220,38,38,0.1)',
        line=dict(color=COLORS["error"], width=2),
    ))
    fig_rev.update_layout(**PLOTLY_LAYOUT, height=400)
    st.plotly_chart(fig_rev, use_container_width=True)

# ── Rent Comparables Table ────────────────────────────────────────
comps_csv = os.path.join(BASE_DIR, 'data', 'rent_comps.csv')
if os.path.exists(comps_csv):
    section_header("Rent Comparables")
    comps_df = pd.read_csv(comps_csv)
    comps_headers = list(comps_df.columns)
    comps_rows = [[str(v) for v in row] for row in comps_df.values]
    styled_table(comps_headers, comps_rows, compact=True)

# ── T-12 Data Export ─────────────────────────────────────────────
spacer(8)
with st.expander("Export T-12 Data"):
    t12_export = {
        "Metric": list(t12.keys()),
        "Value": list(t12.values()),
    }
    t12_df = pd.DataFrame(t12_export)
    st.download_button(
        label="Download T-12 Summary (CSV)",
        data=t12_df.to_csv(index=False),
        file_name="t12_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )

page_footer()
