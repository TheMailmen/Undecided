"""Budget vs Actual Variance — Compare actuals to underwriting projections."""

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

st.title("Budget vs Actual Variance")
st.caption("Compare actual performance to underwriting assumptions.")

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

# ── Underwriting Budget Inputs ────────────────────────────────────
st.subheader("Underwriting Budget (Annual)")
st.caption("Enter the Year 1 underwriting assumptions. These are compared against T-12 actuals.")

# Initialize budget in session state
if 'budget' not in st.session_state:
    unit_mix = st.session_state.unit_mix
    # Reasonable defaults based on property config
    gpr = sum(v['market_rent'] * v['count'] for v in unit_mix.values()) * 12
    st.session_state.budget = {
        'gpr': gpr,
        'vacancy_pct': 0.07,
        'other_income': 60_000,
        'real_estate_taxes': 220_000,
        'insurance': 130_000,
        'payroll': 140_000,
        'utilities': 180_000,
        'maintenance': 120_000,
        'management_fee_pct': 0.04,
        'other_opex': 80_000,
        'debt_service': 600_000,
        'capex': 100_000,
    }

with st.expander("Edit Budget Assumptions", expanded=False):
    budget = st.session_state.budget
    col1, col2, col3 = st.columns(3)
    with col1:
        budget['gpr'] = st.number_input("Gross Potential Rent (Annual)", value=budget['gpr'], step=10_000, format="%d")
        budget['vacancy_pct'] = st.number_input("Vacancy & Loss %", value=budget['vacancy_pct'], step=0.01, format="%.2f")
        budget['other_income'] = st.number_input("Other Income (Annual)", value=budget['other_income'], step=5_000, format="%d")
        budget['debt_service'] = st.number_input("Total Debt Service (Annual)", value=budget['debt_service'], step=10_000, format="%d")
    with col2:
        budget['real_estate_taxes'] = st.number_input("Real Estate Taxes", value=budget['real_estate_taxes'], step=5_000, format="%d")
        budget['insurance'] = st.number_input("Insurance", value=budget['insurance'], step=5_000, format="%d")
        budget['payroll'] = st.number_input("Payroll", value=budget['payroll'], step=5_000, format="%d")
        budget['capex'] = st.number_input("CapEx (Annual)", value=budget['capex'], step=10_000, format="%d")
    with col3:
        budget['utilities'] = st.number_input("Utilities", value=budget['utilities'], step=5_000, format="%d")
        budget['maintenance'] = st.number_input("R&M / Maintenance", value=budget['maintenance'], step=5_000, format="%d")
        budget['management_fee_pct'] = st.number_input("Management Fee %", value=budget['management_fee_pct'], step=0.005, format="%.3f")
        budget['other_opex'] = st.number_input("Other OpEx", value=budget['other_opex'], step=5_000, format="%d")

# ── Compute budget line items ─────────────────────────────────────
b = st.session_state.budget
b_egi = b['gpr'] * (1 - b['vacancy_pct']) + b['other_income']
b_opex = (b['real_estate_taxes'] + b['insurance'] + b['payroll'] +
          b['utilities'] + b['maintenance'] + b['other_opex'] +
          b_egi * b['management_fee_pct'])
b_noi = b_egi - b_opex
b_cfads = b_noi - b['debt_service']
b_ncf = b_cfads - b['capex']

# ── Actual T-12 values ───────────────────────────────────────────
a_egi = t12.get('EFFECTIVE GROSS INCOME (EGI)', 0)
a_opex = t12.get('Total Operating Expenses', 0)
a_noi = t12.get('NET OPERATING INCOME (NOI)', 0)
a_ds = t12.get('Total Debt Service', 0)
a_cfads = t12.get('CASH FLOW AFTER DEBT SERVICE', 0)
a_capex = t12.get('Total Capital Expenditures', 0)
a_ncf = t12.get('NET CASH FLOW', 0)
a_gpr = t12.get('Gross Potential Rent', 0)

st.divider()

# ── Variance Summary KPIs ────────────────────────────────────────
st.subheader("T-12 Actuals vs Underwriting")

noi_var = a_noi - b_noi
ncf_var = a_ncf - b_ncf

col1, col2, col3, col4 = st.columns(4)
col1.metric("Actual NOI", f"${a_noi:,.0f}", delta=f"${noi_var:,.0f} vs UW")
col2.metric("Budget NOI", f"${b_noi:,.0f}")
col3.metric("Actual NCF", f"${a_ncf:,.0f}", delta=f"${ncf_var:,.0f} vs UW")
col4.metric("Budget NCF", f"${b_ncf:,.0f}")

st.divider()

# ── Detailed Variance Table ──────────────────────────────────────
st.subheader("Line-Item Variance")

def _fmt(v):
    if v < 0:
        return f"(${abs(v):,.0f})"
    return f"${v:,.0f}"

def _var_color(v, favorable_positive=True):
    """Return color based on variance direction."""
    if favorable_positive:
        return C_GREEN if v > 0 else (C_RED if v < 0 else "#333")
    else:
        return C_RED if v > 0 else (C_GREEN if v < 0 else "#333")

items = [
    ('Gross Potential Rent', a_gpr, b['gpr'], True),
    ('Less: Vacancy & Loss', a_egi - a_gpr - (t12.get('Total Other Income', 0) if 'Total Other Income' in t12 else 0), -b['gpr'] * b['vacancy_pct'], False),
    ('Effective Gross Income', a_egi, b_egi, True),
    ('', None, None, None),  # spacer
    ('Total Operating Expenses', a_opex, b_opex, False),
    ('NET OPERATING INCOME', a_noi, b_noi, True),
    ('', None, None, None),  # spacer
    ('Total Debt Service', a_ds, b['debt_service'], False),
    ('CASH FLOW AFTER DEBT SVC', a_cfads, b_cfads, True),
    ('', None, None, None),  # spacer
    ('Capital Expenditures', a_capex, b['capex'], False),
    ('NET CASH FLOW', a_ncf, b_ncf, True),
]

html = [f'''
<div style="overflow-x:auto;">
<table style="border-collapse:collapse;width:100%;font-family:Calibri,sans-serif;font-size:13px;">
<thead>
<tr style="background-color:{C_TITLE};color:white;font-weight:700;text-align:center;">
    <td style="text-align:left;padding:8px 12px;min-width:220px;">Line Item</td>
    <td style="padding:8px 12px;min-width:120px;">T-12 Actual</td>
    <td style="padding:8px 12px;min-width:120px;">UW Budget</td>
    <td style="padding:8px 12px;min-width:120px;">Variance ($)</td>
    <td style="padding:8px 12px;min-width:100px;">Variance (%)</td>
</tr>
</thead>
<tbody>
''']

alt = False
for label, actual, budget_val, favorable_positive in items:
    if actual is None:
        html.append('<tr style="height:8px;"><td colspan="5"></td></tr>')
        alt = False
        continue

    variance = actual - budget_val
    var_pct = variance / abs(budget_val) if budget_val != 0 else 0

    # For expense items, negative variance is favorable
    is_key = label in ('NET OPERATING INCOME', 'CASH FLOW AFTER DEBT SVC', 'NET CASH FLOW', 'Effective Gross Income')
    bg = f"background-color:#E8F5E9;" if is_key else (f"background-color:{C_ALT};" if alt else "")
    bold = "font-weight:700;" if is_key else ""
    green = f"color:{C_GREEN};" if is_key else ""
    var_color = _var_color(variance, favorable_positive)

    html.append(f'''
<tr style="{bg}">
    <td style="padding:6px 12px;{bold}{green}">{label}</td>
    <td style="text-align:right;padding:6px 12px;{bold}{green}">{_fmt(actual)}</td>
    <td style="text-align:right;padding:6px 12px;">{_fmt(budget_val)}</td>
    <td style="text-align:right;padding:6px 12px;color:{var_color};font-weight:600;">{_fmt(variance)}</td>
    <td style="text-align:right;padding:6px 12px;color:{var_color};font-weight:600;">{var_pct*100:.1f}%</td>
</tr>''')
    alt = not alt

html.append('</tbody></table></div>')
st.markdown('\n'.join(html), unsafe_allow_html=True)

st.divider()

# ── Variance Waterfall Chart ─────────────────────────────────────
st.subheader("NOI Variance Waterfall")

# Break down the NOI variance into components
egi_var = a_egi - b_egi
opex_var = -(a_opex - b_opex)  # Negative opex variance is favorable

waterfall_items = [
    ('UW NOI', b_noi, 'total'),
    ('Revenue Variance', egi_var, 'relative'),
    ('OpEx Variance', opex_var, 'relative'),
    ('Actual NOI', a_noi, 'total'),
]

fig_wf = go.Figure(go.Waterfall(
    x=[item[0] for item in waterfall_items],
    y=[item[1] for item in waterfall_items],
    measure=[item[2] for item in waterfall_items],
    connector=dict(line=dict(color='#7F8C8D')),
    increasing=dict(marker=dict(color='#1E8449')),
    decreasing=dict(marker=dict(color='#C00000')),
    totals=dict(marker=dict(color='#1B4F72')),
    texttemplate="%{y:$,.0f}",
    textposition="outside",
))
fig_wf.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig_wf, use_container_width=True)

# ── Monthly Actual vs Budget Trend ────────────────────────────────
st.subheader("Monthly NOI: Actual vs Budget")

from data_engine import get_monthly_series

noi_series = get_monthly_series(df, 'NET OPERATING INCOME (NOI)')
monthly_budget_noi = b_noi / 12

fig_trend = go.Figure()
fig_trend.add_trace(go.Bar(
    x=noi_series['Month'], y=noi_series['Amount'],
    name='Actual NOI', marker_color='#1B4F72', opacity=0.8,
))
fig_trend.add_hline(
    y=monthly_budget_noi, line_dash="dash", line_color="#C00000",
    annotation_text=f"Budget: ${monthly_budget_noi:,.0f}/mo",
)
fig_trend.update_layout(
    height=350, margin=dict(l=0, r=0, t=30, b=0),
    yaxis_title="$",
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
)
st.plotly_chart(fig_trend, use_container_width=True)
