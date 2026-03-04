"""Investment Returns — IRR, Equity Multiple, and per-owner return projections."""

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

st.title("Investment Returns")
st.caption("Projected IRR, equity multiple, and per-owner returns based on exit assumptions.")

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
st.subheader("Exit Assumptions")

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

st.divider()

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
st.subheader("Returns Summary")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Projected IRR", f"{irr * 100:.1f}%")
col2.metric("Equity Multiple", f"{equity_multiple:.2f}x")
col3.metric("Exit Value", f"${exit_value:,.0f}")
col4.metric("Net Sale Proceeds", f"${net_sale_proceeds:,.0f}")

col5, col6, col7, col8 = st.columns(4)
col5.metric("Total Equity Invested", f"${total_equity:,.0f}")
col6.metric("Cumulative Cash Flow", f"${cumulative_cf:,.0f}")
col7.metric("Projected Exit NOI", f"${projected_noi:,.0f}")
col8.metric("Total Return", f"${total_distributions:,.0f}")

st.divider()

# ── Hold Period Cash Flow Timeline ────────────────────────────────
st.subheader("Projected Cash Flow Timeline")

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
colors = ['#C00000' if v < 0 else '#1B4F72' if t == 'Operating CF' else '#1E8449'
          for v, t in zip(tl_df['Cash Flow'], tl_df['Type'])]
fig.add_trace(go.Bar(
    x=tl_df['Year'], y=tl_df['Cash Flow'],
    name='Annual Cash Flow', marker_color=colors, opacity=0.85,
))

# Cumulative line
fig.add_trace(go.Scatter(
    x=tl_df['Year'], y=tl_df['Cumulative'],
    name='Cumulative', line=dict(color='#0D1B2A', width=2.5),
    mode='lines+markers',
))

# Break-even line
fig.add_hline(y=0, line_dash="dash", line_color="#7F8C8D", opacity=0.5)

fig.update_layout(
    height=400, margin=dict(l=0, r=0, t=30, b=0),
    yaxis_title="$", barmode='relative',
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Per-Owner Returns ─────────────────────────────────────────────
st.subheader("Per-Owner Returns")

C_TITLE = "#0D1B2A"
C_ACCENT = "#1B4F72"
C_GREEN = "#1E8449"
C_ALT = "#F7F9FC"
C_NOTE_BG = "#E8F5E9"

def _fmt(v):
    if v < 0:
        return f"(${abs(v):,.0f})"
    return f"${v:,.0f}"

html = [f'''
<div style="overflow-x:auto;">
<table style="border-collapse:collapse;width:100%;font-family:Calibri,sans-serif;font-size:13px;">
<thead>
<tr style="background-color:{C_TITLE};color:white;font-weight:700;text-align:center;">
    <td style="text-align:left;padding:8px 12px;">Owner</td>
    <td style="padding:8px;">Ownership %</td>
    <td style="padding:8px;">Equity Invested</td>
    <td style="padding:8px;">Cumulative CF</td>
    <td style="padding:8px;">Sale Proceeds</td>
    <td style="padding:8px;">Total Return</td>
    <td style="padding:8px;">Equity Multiple</td>
    <td style="padding:8px;">IRR</td>
</tr>
</thead>
<tbody>
''']

for i, (owner, info) in enumerate(st.session_state.tic.items()):
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

    bg = f"background-color:{C_ALT};" if i % 2 == 0 else ""
    html.append(f'''
<tr style="{bg}">
    <td style="padding:6px 12px;font-weight:600;">{owner}</td>
    <td style="text-align:center;padding:6px 8px;">{pct*100:.3f}%</td>
    <td style="text-align:right;padding:6px 8px;">{_fmt(equity)}</td>
    <td style="text-align:right;padding:6px 8px;">{_fmt(owner_cum_cf)}</td>
    <td style="text-align:right;padding:6px 8px;">{_fmt(owner_sale)}</td>
    <td style="text-align:right;padding:6px 8px;color:{C_GREEN};font-weight:700;">{_fmt(owner_total)}</td>
    <td style="text-align:center;padding:6px 8px;font-weight:700;">{owner_em:.2f}x</td>
    <td style="text-align:center;padding:6px 8px;font-weight:700;color:{C_GREEN};">{owner_irr*100:.1f}%</td>
</tr>''')

html.append('</tbody></table></div>')
st.markdown('\n'.join(html), unsafe_allow_html=True)

st.divider()

# ── Key Assumptions Recap ─────────────────────────────────────────
with st.expander("Assumptions Used"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Current T-12 NOI:**", f"${current_noi:,.0f}")
        st.write("**Current T-12 NCF:**", f"${current_ncf:,.0f}")
        st.write("**Purchase Price:**", f"${purchase_price:,.0f}")
    with col2:
        st.write("**Exit Cap Rate:**", f"{exit_cap_rate*100:.1f}%")
        st.write("**Hold Period:**", f"{hold_years} years")
        st.write("**NOI Growth:**", f"{annual_noi_growth*100:.1f}%/yr")
    with col3:
        st.write("**Selling Costs:**", f"{selling_costs_pct*100:.1f}%")
        st.write("**Loan Balance:**", f"${loan_balance:,.0f}")
        st.write("**Total Equity:**", f"${total_equity:,.0f}")
