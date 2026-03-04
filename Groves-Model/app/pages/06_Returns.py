"""Investment Returns — IRR, Equity Multiple, and per-owner return projections."""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_engine import get_t12_totals, load_pl_data
from ui.theme import inject_theme, COLORS, PLOTLY_LAYOUT, fmt_currency, fmt_pct, fmt_multiple
from ui.components import page_header, kpi_row, section_header, spacer, styled_table, no_data_page, page_footer

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

page_header(
    "Investment Returns",
    "Projected IRR, equity multiple, and per-owner returns based on exit assumptions",
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

# ── IRR Calculator ────────────────────────────────────────────────

def compute_irr(cashflows, guess=0.10, tol=1e-8, max_iter=200):
    """Compute IRR using Newton's method."""
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


# ── Exit Assumptions ──────────────────────────────────────────────
section_header("Exit Assumptions")

col1, col2, col3, col4 = st.columns(4)
with col1:
    exit_cap_rate = st.number_input(
        "Exit Cap Rate", value=0.065, min_value=0.03, max_value=0.12,
        step=0.005, format="%.3f", key="ret_exit_cap")
with col2:
    hold_years = st.number_input(
        "Hold Period (years)", value=5, min_value=1, max_value=15,
        step=1, key="ret_hold")
with col3:
    selling_costs_pct = st.number_input(
        "Selling Costs (%)", value=0.02, min_value=0.0, max_value=0.10,
        step=0.005, format="%.3f", key="ret_sell_cost")
with col4:
    annual_noi_growth = st.number_input(
        "Annual NOI Growth", value=0.03, min_value=-0.05, max_value=0.15,
        step=0.005, format="%.3f", key="ret_noi_growth")

spacer(8)

# ── Projections ───────────────────────────────────────────────────
current_noi = t12['NET OPERATING INCOME (NOI)']
current_cfads = t12['CASH FLOW AFTER DEBT SERVICE']
current_ncf = t12['NET CASH FLOW']
purchase_price = st.session_state.property['purchase_price']
total_equity = st.session_state.total_equity
loan_balance = st.session_state.loan['est_current_balance']

# Project forward NOI
projected_noi = current_noi * (1 + annual_noi_growth) ** hold_years

# Exit valuation
exit_value = projected_noi / exit_cap_rate
selling_costs = exit_value * selling_costs_pct
net_sale_proceeds = exit_value - selling_costs - loan_balance

# Annual cash flows for IRR (simplified: assume NCF grows at NOI growth rate)
annual_cashflows = [-total_equity]  # Year 0: equity invested
for yr in range(1, hold_years):
    yr_ncf = current_ncf * (1 + annual_noi_growth) ** yr
    annual_cashflows.append(yr_ncf)
# Final year: NCF + sale proceeds
final_yr_ncf = current_ncf * (1 + annual_noi_growth) ** hold_years
annual_cashflows.append(final_yr_ncf + net_sale_proceeds)

# Compute returns
total_distributions = sum(annual_cashflows[1:])  # Excludes initial equity
equity_multiple = (total_distributions) / total_equity if total_equity else 0
irr = compute_irr(annual_cashflows)

# Cumulative distributions (without sale)
cumulative_cf = sum(
    current_ncf * (1 + annual_noi_growth) ** yr
    for yr in range(1, hold_years + 1)
)

# ── Returns Summary ───────────────────────────────────────────────
section_header("Returns Summary")

kpi_row([
    {"label": "Projected IRR", "value": fmt_pct(irr)},
    {"label": "Equity Multiple", "value": fmt_multiple(equity_multiple)},
    {"label": "Exit Value", "value": fmt_currency(exit_value)},
    {"label": "Net Sale Proceeds", "value": fmt_currency(net_sale_proceeds)},
])

kpi_row([
    {"label": "Total Equity Invested", "value": fmt_currency(total_equity)},
    {"label": "Cumulative Cash Flow", "value": fmt_currency(cumulative_cf)},
    {"label": "Projected Exit NOI", "value": fmt_currency(projected_noi)},
    {"label": "Total Return", "value": fmt_currency(total_distributions)},
])

spacer(8)

# ── Hold Period Cash Flow Timeline ────────────────────────────────
section_header("Projected Cash Flow Timeline")

timeline_data = []
cumulative = 0
for yr in range(hold_years + 1):
    if yr == 0:
        timeline_data.append({
            'Year': f'Year 0\n(Investment)',
            'Cash Flow': -total_equity,
            'Cumulative': -total_equity,
            'Type': 'Investment',
        })
        cumulative = -total_equity
    elif yr < hold_years:
        yr_cf = current_ncf * (1 + annual_noi_growth) ** yr
        cumulative += yr_cf
        timeline_data.append({
            'Year': f'Year {yr}',
            'Cash Flow': yr_cf,
            'Cumulative': cumulative,
            'Type': 'Operating CF',
        })
    else:
        yr_cf = current_ncf * (1 + annual_noi_growth) ** yr
        total_yr = yr_cf + net_sale_proceeds
        cumulative += total_yr
        timeline_data.append({
            'Year': f'Year {yr}\n(Exit)',
            'Cash Flow': total_yr,
            'Cumulative': cumulative,
            'Type': 'Exit + CF',
        })

tl_df = pd.DataFrame(timeline_data)

fig = go.Figure()

# Cash flow bars
colors = [COLORS["error"] if v < 0 else COLORS["accent"] if t == 'Operating CF' else COLORS["success"]
          for v, t in zip(tl_df['Cash Flow'], tl_df['Type'])]
fig.add_trace(go.Bar(
    x=tl_df['Year'], y=tl_df['Cash Flow'],
    name='Annual Cash Flow', marker_color=colors, opacity=0.85,
))

# Cumulative line
fig.add_trace(go.Scatter(
    x=tl_df['Year'], y=tl_df['Cumulative'],
    name='Cumulative', line=dict(color=COLORS["primary"], width=2.5),
    mode='lines+markers',
))

# Break-even line
fig.add_hline(y=0, line_dash="dash", line_color=COLORS["muted"], opacity=0.5)

fig.update_layout(
    **PLOTLY_LAYOUT,
    height=400,
    yaxis_title="$", barmode='relative',
)
st.plotly_chart(fig, use_container_width=True)

spacer(8)

# ── Per-Owner Returns ─────────────────────────────────────────────
section_header("Per-Owner Returns")

headers = ["Owner", "Ownership %", "Equity Invested", "Cumulative CF",
           "Sale Proceeds", "Total Return", "Equity Multiple", "IRR"]
rows = []
col_align = ["left", "center", "right", "right", "right", "right", "center", "center"]

for owner, info in st.session_state.tic.items():
    pct = info['pct']
    equity = info['equity']
    owner_cum_cf = cumulative_cf * pct
    owner_sale = net_sale_proceeds * pct
    owner_total = owner_cum_cf + owner_sale
    owner_em = owner_total / equity if equity else 0

    # Per-owner IRR
    owner_cashflows = [-equity]
    for yr in range(1, hold_years):
        owner_cashflows.append(current_ncf * (1 + annual_noi_growth) ** yr * pct)
    final_cf = current_ncf * (1 + annual_noi_growth) ** hold_years * pct
    owner_cashflows.append(final_cf + owner_sale)
    owner_irr = compute_irr(owner_cashflows)

    irr_color = COLORS["success"] if owner_irr > 0.10 else COLORS["text"]
    rows.append([
        f"<b>{owner}</b>",
        f"{pct*100:.3f}%",
        fmt_currency(equity),
        fmt_currency(owner_cum_cf),
        fmt_currency(owner_sale),
        f"<span style='color:{COLORS['success']};font-weight:600;'>{fmt_currency(owner_total)}</span>",
        f"<b>{fmt_multiple(owner_em)}</b>",
        f"<span style='color:{irr_color};font-weight:600;'>{fmt_pct(owner_irr)}</span>",
    ])

styled_table(headers, rows, col_align=col_align)

spacer(8)

# ── Key Assumptions Recap ─────────────────────────────────────────
with st.expander("Assumptions Used"):
    assumptions_headers = ["Assumption", "Value", "Assumption", "Value", "Assumption", "Value"]
    assumptions_rows = [
        [
            "<b>T-12 NOI</b>", fmt_currency(current_noi),
            "<b>Exit Cap Rate</b>", fmt_pct(exit_cap_rate),
            "<b>Selling Costs</b>", fmt_pct(selling_costs_pct),
        ],
        [
            "<b>T-12 NCF</b>", fmt_currency(current_ncf),
            "<b>Hold Period</b>", f"{hold_years} years",
            "<b>Loan Balance</b>", fmt_currency(loan_balance),
        ],
        [
            "<b>Purchase Price</b>", fmt_currency(purchase_price),
            "<b>NOI Growth</b>", f"{fmt_pct(annual_noi_growth)}/yr",
            "<b>Total Equity</b>", fmt_currency(total_equity),
        ],
    ]
    styled_table(
        assumptions_headers, assumptions_rows,
        col_align=["left", "right", "left", "right", "left", "right"],
        compact=True,
    )

page_footer()
