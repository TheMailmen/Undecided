"""Refi Scenario — Visualize refinance scenarios and compare to current debt."""

import os
import sys

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_engine import get_t12_totals, load_pl_data
from ui.theme import inject_theme, COLORS, PLOTLY_LAYOUT, fmt_currency, fmt_pct
from ui.components import page_header, section_header, spacer

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

page_header(
    "Refinance Scenario Analysis",
    "Compare current debt terms vs refinance options",
)

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

# ── Current Loan Summary ─────────────────────────────────────────
loan = st.session_state.loan
current_noi = t12['NET OPERATING INCOME (NOI)']


def monthly_payment(principal, annual_rate, amort_years, io=False):
    """Calculate monthly debt service."""
    if io:
        return principal * annual_rate / 12
    r = annual_rate / 12
    n = amort_years * 12
    if r == 0:
        return principal / n
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


current_monthly_ds = monthly_payment(
    loan['est_current_balance'], loan['rate'], loan['amort_years'], loan['io']
)
current_annual_ds = current_monthly_ds * 12
current_dscr = current_noi / current_annual_ds if current_annual_ds else 0

# ── Refi Assumptions ─────────────────────────────────────────────
st.subheader("Refinance Assumptions")

refi = st.session_state.refi
col1, col2, col3, col4 = st.columns(4)

with col1:
    refi_value = st.number_input(
        "Property Value ($)", value=refi['property_value'],
        step=100_000, format="%d", key="refi_val")
    refi_ltv = st.number_input(
        "Target LTV", value=refi['ltv'],
        min_value=0.0, max_value=0.85, step=0.05, format="%.2f", key="refi_ltv")
with col2:
    refi_rate = st.number_input(
        "New Rate", value=refi['rate'],
        min_value=0.01, max_value=0.15, step=0.0025, format="%.4f", key="refi_rate")
    refi_amort = st.number_input(
        "Amort (years)", value=refi['amort_years'],
        min_value=5, max_value=35, step=1, key="refi_amort")
with col3:
    refi_term = st.number_input(
        "Term (years)", value=refi['term_years'],
        min_value=1, max_value=15, step=1, key="refi_term")
    refi_io = st.checkbox(
        "Interest Only", value=refi['io'], key="refi_io_cb")
with col4:
    refi_costs_pct = st.number_input(
        "Closing Costs (%)", value=0.02,
        min_value=0.0, max_value=0.05, step=0.005, format="%.3f", key="refi_costs")

# ── Refi Calculations ────────────────────────────────────────────
refi_loan_amount = refi_value * refi_ltv
refi_closing_costs = refi_loan_amount * refi_costs_pct
refi_monthly_ds = monthly_payment(refi_loan_amount, refi_rate, refi_amort, refi_io)
refi_annual_ds = refi_monthly_ds * 12
refi_dscr = current_noi / refi_annual_ds if refi_annual_ds else 0

# Cash-out at refi
cash_out = refi_loan_amount - loan['est_current_balance'] - refi_closing_costs

# Post-refi CFADS
post_refi_cfads = current_noi - refi_annual_ds
current_cfads = t12['CASH FLOW AFTER DEBT SERVICE']

st.divider()

# ── Side-by-Side Comparison ──────────────────────────────────────
st.subheader("Current vs Refinanced")

col_curr, col_vs, col_refi = st.columns([2, 1, 2])

with col_curr:
    st.markdown(f"**Current Loan**")
    st.metric("Balance", f"${loan['est_current_balance']:,.0f}")
    st.metric("Rate", f"{loan['rate']*100:.2f}%")
    st.metric("Annual Debt Service", f"${current_annual_ds:,.0f}")
    st.metric("Monthly Payment", f"${current_monthly_ds:,.0f}")
    st.metric("DSCR", f"{current_dscr:.2f}x")
    st.metric("CFADS", f"${current_cfads:,.0f}")

with col_vs:
    st.markdown("")
    st.markdown("")
    st.markdown("")
    ds_delta = refi_annual_ds - current_annual_ds
    st.markdown(f"### {'>' if ds_delta > 0 else '<'}")
    if ds_delta > 0:
        st.caption(f"+${ds_delta:,.0f}/yr")
    else:
        st.caption(f"-${abs(ds_delta):,.0f}/yr")

with col_refi:
    st.markdown(f"**Refinanced Loan**")
    st.metric("New Balance", f"${refi_loan_amount:,.0f}")
    st.metric("Rate", f"{refi_rate*100:.2f}%")
    st.metric("Annual Debt Service", f"${refi_annual_ds:,.0f}",
              delta=f"${refi_annual_ds - current_annual_ds:,.0f}",
              delta_color="inverse")
    st.metric("Monthly Payment", f"${refi_monthly_ds:,.0f}")
    st.metric("DSCR", f"{refi_dscr:.2f}x",
              delta=f"{refi_dscr - current_dscr:.2f}")
    st.metric("CFADS (post-refi)", f"${post_refi_cfads:,.0f}",
              delta=f"${post_refi_cfads - current_cfads:,.0f}")

st.divider()

# ── Cash-Out Analysis ────────────────────────────────────────────
st.subheader("Cash-Out at Refinance")

col1, col2, col3, col4 = st.columns(4)
col1.metric("New Loan Amount", f"${refi_loan_amount:,.0f}")
col2.metric("Payoff Current", f"${loan['est_current_balance']:,.0f}")
col3.metric("Closing Costs", f"${refi_closing_costs:,.0f}")
col4.metric("Net Cash Out",
            f"${cash_out:,.0f}" if cash_out >= 0 else f"(${abs(cash_out):,.0f})",
            delta="Cash to distribute" if cash_out > 0 else "Cash needed")

if cash_out > 0:
    st.divider()
    st.subheader("Cash-Out Distribution by Owner")

    cols = st.columns(len(st.session_state.tic))
    for col, (owner, info) in zip(cols, st.session_state.tic.items()):
        owner_cashout = cash_out * info['pct']
        with col:
            st.metric(owner, f"${owner_cashout:,.0f}")
            st.caption(f"{info['pct']*100:.3f}%")

st.divider()

# ── Rate Sensitivity ─────────────────────────────────────────────
st.subheader("DSCR by Rate")

rates = [r / 100 for r in range(400, 901, 25)]
dscrs = []
for r in rates:
    ds = monthly_payment(refi_loan_amount, r, refi_amort, refi_io) * 12
    dscrs.append(current_noi / ds if ds else 0)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=[r * 100 for r in rates], y=dscrs,
    mode='lines+markers', name='DSCR',
    line=dict(color=C_ACCENT, width=2.5),
    marker=dict(size=4),
))

# 1.25x DSCR threshold
fig.add_hline(y=1.25, line_dash="dash", line_color=C_RED,
              annotation_text="1.25x min DSCR")
fig.add_hline(y=1.0, line_dash="dot", line_color="#7F8C8D",
              annotation_text="1.0x breakeven")

# Mark current refi rate
fig.add_vline(x=refi_rate * 100, line_dash="dot", line_color=C_GREEN,
              annotation_text=f"Refi: {refi_rate*100:.2f}%")

fig.update_layout(
    height=350, margin=dict(l=0, r=0, t=30, b=0),
    xaxis_title="Interest Rate (%)", yaxis_title="DSCR",
)
st.plotly_chart(fig, use_container_width=True)

# ── LTV Comparison ───────────────────────────────────────────────
st.subheader("Proceeds by LTV")

ltvs = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]

html = [f'''
<div style="overflow-x:auto;">
<table style="border-collapse:collapse;width:100%;font-family:Calibri,sans-serif;font-size:13px;text-align:center;">
<thead>
<tr style="background-color:{C_TITLE};color:white;font-weight:700;">
    <td style="padding:8px 12px;">LTV</td>
    <td style="padding:8px 12px;">Loan Amount</td>
    <td style="padding:8px 12px;">Annual DS</td>
    <td style="padding:8px 12px;">DSCR</td>
    <td style="padding:8px 12px;">Net Cash Out</td>
    <td style="padding:8px 12px;">Post-Refi CFADS</td>
</tr>
</thead>
<tbody>
''']

def _fmt(v):
    if v < 0:
        return f"(${abs(v):,.0f})"
    return f"${v:,.0f}"

for i, ltv in enumerate(ltvs):
    loan_amt = refi_value * ltv
    ds = monthly_payment(loan_amt, refi_rate, refi_amort, refi_io) * 12
    dscr = current_noi / ds if ds else 0
    co = loan_amt - loan['est_current_balance'] - loan_amt * refi_costs_pct
    cfads = current_noi - ds

    bg = f"background-color:{C_ALT};" if i % 2 == 0 else ""
    dscr_color = C_GREEN if dscr >= 1.25 else (C_RED if dscr < 1.0 else "#333")
    selected = "border:2px solid #1E8449;" if abs(ltv - refi_ltv) < 0.001 else ""

    html.append(f'''
<tr style="{bg}{selected}">
    <td style="padding:6px 12px;font-weight:700;">{ltv*100:.0f}%</td>
    <td style="padding:6px 12px;">{_fmt(loan_amt)}</td>
    <td style="padding:6px 12px;">{_fmt(ds)}</td>
    <td style="padding:6px 12px;color:{dscr_color};font-weight:700;">{dscr:.2f}x</td>
    <td style="padding:6px 12px;font-weight:600;">{_fmt(co)}</td>
    <td style="padding:6px 12px;">{_fmt(cfads)}</td>
</tr>''')

html.append('</tbody></table></div>')
st.markdown('\n'.join(html), unsafe_allow_html=True)
