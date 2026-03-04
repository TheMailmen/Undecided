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

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

st.set_page_config(page_title="Dashboard", layout="wide") if not hasattr(st, '_is_running_with_streamlit') else None

st.title("Dashboard")

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
col1, col2, col3, col4 = st.columns(4)
col1.metric("T12 NOI", f"${t12['NET OPERATING INCOME (NOI)']:,.0f}",
            delta=f"${d_noi:,.0f} MoM" if d_noi is not None else None)
col2.metric("T12 CFADS", f"${t12['CASH FLOW AFTER DEBT SERVICE']:,.0f}",
            delta=f"${d_cfads:,.0f} MoM" if d_cfads is not None else None)
col3.metric("DSCR", f"{t12['DSCR']:.2f}x",
            delta=f"{d_dscr:.2f}" if d_dscr is not None else None)
col4.metric("Cap Rate", f"{t12['Cap Rate'] * 100:.1f}%")

col5, col6, col7, col8 = st.columns(4)
col5.metric("T12 EGI", f"${t12['EFFECTIVE GROSS INCOME (EGI)']:,.0f}",
            delta=f"${d_egi:,.0f} MoM" if d_egi is not None else None)
col6.metric("T12 OpEx", f"${t12['Total Operating Expenses']:,.0f}",
            delta=f"${d_opex:,.0f} MoM" if d_opex is not None else None,
            delta_color="inverse")
col7.metric("Expense Ratio", f"{t12['Expense Ratio'] * 100:.1f}%")
col8.metric("Cash-on-Cash", f"{t12['Cash-on-Cash (CFADS)'] * 100:.1f}%")

st.divider()

# ── Chart 1: Monthly NOI Trend ────────────────────────────────────
st.subheader("Monthly NOI Trend")
noi_series = get_monthly_series(df, 'NET OPERATING INCOME (NOI)')
noi_series['Rolling3'] = noi_series['Amount'].rolling(3).mean()

fig_noi = go.Figure()
fig_noi.add_trace(go.Bar(
    x=noi_series['Month'], y=noi_series['Amount'],
    name='Monthly NOI', marker_color='#1E8449', opacity=0.7,
))
fig_noi.add_trace(go.Scatter(
    x=noi_series['Month'], y=noi_series['Rolling3'],
    name='3-Mo Rolling Avg', line=dict(color='#0D1B2A', width=2),
))
fig_noi.update_layout(
    height=350, margin=dict(l=0, r=0, t=30, b=0),
    yaxis_title="$", xaxis_title="",
)
st.plotly_chart(fig_noi, use_container_width=True)

# ── Chart 2: T12 Cash Flow Waterfall ──────────────────────────────
st.subheader("T12 Cash Flow Waterfall")
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
    connector=dict(line=dict(color='#7F8C8D')),
    increasing=dict(marker=dict(color='#1E8449')),
    decreasing=dict(marker=dict(color='#C00000')),
    totals=dict(marker=dict(color='#1B4F72')),
))
fig_wf.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig_wf, use_container_width=True)

# ── Charts 3 & 4: Side by Side ───────────────────────────────────
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("T12 Expense Breakdown")
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
        color_discrete_sequence=['#1B4F72'],
    )
    fig_exp.update_layout(
        height=400, margin=dict(l=0, r=0, t=10, b=0),
        yaxis=dict(autorange='reversed'),
    )
    st.plotly_chart(fig_exp, use_container_width=True)

with right_col:
    st.subheader("Revenue vs Expenses (Monthly)")
    egi_s = get_monthly_series(df, 'EFFECTIVE GROSS INCOME (EGI)')
    opex_s = get_monthly_series(df, 'Total Operating Expenses')

    fig_rev = go.Figure()
    fig_rev.add_trace(go.Scatter(
        x=egi_s['Month'], y=egi_s['Amount'],
        name='EGI', fill='tozeroy', fillcolor='rgba(30,132,73,0.2)',
        line=dict(color='#1E8449'),
    ))
    fig_rev.add_trace(go.Scatter(
        x=opex_s['Month'], y=opex_s['Amount'],
        name='OpEx', fill='tozeroy', fillcolor='rgba(192,0,0,0.2)',
        line=dict(color='#C00000'),
    ))
    fig_rev.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_rev, use_container_width=True)

# ── Rent Comparables Table ────────────────────────────────────────
comps_csv = os.path.join(BASE_DIR, 'data', 'rent_comps.csv')
if os.path.exists(comps_csv):
    st.subheader("Rent Comparables")
    comps_df = pd.read_csv(comps_csv)
    st.dataframe(comps_df, use_container_width=True, hide_index=True)
