"""Refi Scenario — Visualize refinance scenarios and compare to current debt."""

import os
import sys

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_engine import get_t12_totals, load_pl_data
from ui.theme import inject_theme, COLORS, PLOTLY_LAYOUT, fmt_currency, fmt_pct
from ui.components import page_header, kpi_row, section_header, spacer, styled_table, no_data_page, page_footer

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

page_header(
    "Refinance Scenario Analysis",
    "Compare current debt terms vs refinance options",
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
t12 = get_t12_totals(df, cfg)

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
section_header("Refinance Assumptions")

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

spacer(8)

# ── Side-by-Side Comparison ──────────────────────────────────────
section_header("Current vs Refinanced")

col_curr, col_vs, col_refi = st.columns([2, 1, 2])

with col_curr:
    st.markdown(f"**Current Loan**")
    st.metric("Balance", fmt_currency(loan['est_current_balance']))
    st.metric("Rate", fmt_pct(loan['rate']))
    st.metric("Annual Debt Service", fmt_currency(current_annual_ds))
    st.metric("Monthly Payment", fmt_currency(current_monthly_ds))
    st.metric("DSCR", f"{current_dscr:.2f}x")
    st.metric("CFADS", fmt_currency(current_cfads))

with col_vs:
    st.markdown("")
    st.markdown("")
    st.markdown("")
    ds_delta = refi_annual_ds - current_annual_ds
    st.markdown(f"### {'>' if ds_delta > 0 else '<'}")
    if ds_delta > 0:
        st.caption(f"+{fmt_currency(ds_delta)}/yr")
    else:
        st.caption(f"-{fmt_currency(abs(ds_delta))}/yr")

with col_refi:
    st.markdown(f"**Refinanced Loan**")
    st.metric("New Balance", fmt_currency(refi_loan_amount))
    st.metric("Rate", fmt_pct(refi_rate))
    st.metric("Annual Debt Service", fmt_currency(refi_annual_ds),
              delta=fmt_currency(refi_annual_ds - current_annual_ds),
              delta_color="inverse")
    st.metric("Monthly Payment", fmt_currency(refi_monthly_ds))
    st.metric("DSCR", f"{refi_dscr:.2f}x",
              delta=f"{refi_dscr - current_dscr:.2f}")
    st.metric("CFADS (post-refi)", fmt_currency(post_refi_cfads),
              delta=fmt_currency(post_refi_cfads - current_cfads))

spacer(8)

# ── Cash-Out Analysis ────────────────────────────────────────────
section_header("Cash-Out at Refinance")

kpi_row([
    {"label": "New Loan Amount", "value": fmt_currency(refi_loan_amount)},
    {"label": "Payoff Current", "value": fmt_currency(loan['est_current_balance'])},
    {"label": "Closing Costs", "value": fmt_currency(refi_closing_costs)},
    {"label": "Net Cash Out",
     "value": fmt_currency(cash_out) if cash_out >= 0 else f"({fmt_currency(abs(cash_out))})",
     "delta": "Cash to distribute" if cash_out > 0 else "Cash needed"},
])

if cash_out > 0:
    spacer(8)
    section_header("Cash-Out Distribution by Owner")

    cols = st.columns(len(st.session_state.tic))
    for col, (owner, info) in zip(cols, st.session_state.tic.items()):
        owner_cashout = cash_out * info['pct']
        with col:
            st.metric(owner, fmt_currency(owner_cashout))
            st.caption(f"{info['pct']*100:.3f}%")

spacer(8)

# ── Rate Sensitivity ─────────────────────────────────────────────
section_header("DSCR by Rate")

rates = [r / 100 for r in range(400, 901, 25)]
dscrs = []
for r in rates:
    ds = monthly_payment(refi_loan_amount, r, refi_amort, refi_io) * 12
    dscrs.append(current_noi / ds if ds else 0)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=[r * 100 for r in rates], y=dscrs,
    mode='lines+markers', name='DSCR',
    line=dict(color=COLORS["accent"], width=2.5),
    marker=dict(size=4),
))

# 1.25x DSCR threshold
fig.add_hline(y=1.25, line_dash="dash", line_color=COLORS["error"],
              annotation_text="1.25x min DSCR")
fig.add_hline(y=1.0, line_dash="dot", line_color=COLORS["muted"],
              annotation_text="1.0x breakeven")

# Mark current refi rate
fig.add_vline(x=refi_rate * 100, line_dash="dot", line_color=COLORS["success"],
              annotation_text=f"Refi: {refi_rate*100:.2f}%")

fig.update_layout(
    **PLOTLY_LAYOUT,
    height=350,
    xaxis_title="Interest Rate (%)", yaxis_title="DSCR",
)
st.plotly_chart(fig, use_container_width=True)

spacer(8)

# ── LTV Comparison ───────────────────────────────────────────────
section_header("Proceeds by LTV")

ltvs = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]

headers = ["LTV", "Loan Amount", "Annual DS", "DSCR", "Net Cash Out", "Post-Refi CFADS"]
tbl_rows = []
col_align = ["center", "right", "right", "center", "right", "right"]
highlight = set()

for i, ltv in enumerate(ltvs):
    loan_amt = refi_value * ltv
    ds = monthly_payment(loan_amt, refi_rate, refi_amort, refi_io) * 12
    dscr = current_noi / ds if ds else 0
    co = loan_amt - loan['est_current_balance'] - loan_amt * refi_costs_pct
    cfads = current_noi - ds

    dscr_color = COLORS["success"] if dscr >= 1.25 else (COLORS["error"] if dscr < 1.0 else COLORS["text"])
    if abs(ltv - refi_ltv) < 0.001:
        highlight.add(i)

    tbl_rows.append([
        f"<b>{ltv*100:.0f}%</b>",
        fmt_currency(loan_amt),
        fmt_currency(ds),
        f"<span style='color:{dscr_color};font-weight:600;'>{dscr:.2f}x</span>",
        f"<b>{fmt_currency(co)}</b>",
        fmt_currency(cfads),
    ])

styled_table(headers, tbl_rows, col_align=col_align, highlight_rows=highlight)

page_footer()
