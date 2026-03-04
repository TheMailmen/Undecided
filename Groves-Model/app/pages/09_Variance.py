"""Budget vs Actual Variance — Compare actuals to underwriting projections."""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_engine import get_t12_totals, get_monthly_series, load_pl_data
from ui.theme import inject_theme, COLORS, PLOTLY_LAYOUT, fmt_currency, fmt_pct
from ui.components import page_header, kpi_row, section_header, spacer, styled_table, no_data_page

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

page_header(
    "Budget vs Actual Variance",
    "Compare actual performance to underwriting assumptions",
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

# ── Underwriting Budget Inputs ────────────────────────────────────
section_header("Underwriting Budget (Annual)",
               "Enter the Year 1 underwriting assumptions. These are compared against T-12 actuals.")

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

spacer(8)

# ── Variance Summary KPIs ────────────────────────────────────────
section_header("T-12 Actuals vs Underwriting")

noi_var = a_noi - b_noi
ncf_var = a_ncf - b_ncf

kpi_row([
    {"label": "Actual NOI", "value": fmt_currency(a_noi),
     "delta": f"{fmt_currency(noi_var)} vs UW"},
    {"label": "Budget NOI", "value": fmt_currency(b_noi)},
    {"label": "Actual NCF", "value": fmt_currency(a_ncf),
     "delta": f"{fmt_currency(ncf_var)} vs UW"},
    {"label": "Budget NCF", "value": fmt_currency(b_ncf)},
])

spacer(8)

# ── Detailed Variance Table ──────────────────────────────────────
section_header("Line-Item Variance")


def _var_color(v, favorable_positive=True):
    """Return color based on variance direction."""
    if favorable_positive:
        return COLORS["success"] if v > 0 else (COLORS["error"] if v < 0 else COLORS["text"])
    else:
        return COLORS["error"] if v > 0 else (COLORS["success"] if v < 0 else COLORS["text"])


items = [
    ('Gross Potential Rent', a_gpr, b['gpr'], True),
    ('Less: Vacancy & Loss', a_egi - a_gpr - (t12.get('Total Other Income', 0) if 'Total Other Income' in t12 else 0), -b['gpr'] * b['vacancy_pct'], False),
    ('Effective Gross Income', a_egi, b_egi, True),
    None,  # spacer
    ('Total Operating Expenses', a_opex, b_opex, False),
    ('NET OPERATING INCOME', a_noi, b_noi, True),
    None,  # spacer
    ('Total Debt Service', a_ds, b['debt_service'], False),
    ('CASH FLOW AFTER DEBT SVC', a_cfads, b_cfads, True),
    None,  # spacer
    ('Capital Expenditures', a_capex, b['capex'], False),
    ('NET CASH FLOW', a_ncf, b_ncf, True),
]

headers = ["Line Item", "T-12 Actual", "UW Budget", "Variance ($)", "Variance (%)"]
tbl_rows = []
col_align = ["left", "right", "right", "right", "right"]
highlight = set()

key_labels = {'NET OPERATING INCOME', 'CASH FLOW AFTER DEBT SVC', 'NET CASH FLOW', 'Effective Gross Income'}
row_idx = 0

for item in items:
    if item is None:
        continue

    label, actual, budget_val, favorable_positive = item
    variance = actual - budget_val
    var_pct = variance / abs(budget_val) if budget_val != 0 else 0
    vc = _var_color(variance, favorable_positive)

    is_key = label in key_labels
    if is_key:
        highlight.add(row_idx)

    bold = "font-weight:600;" if is_key else ""
    key_style = f"color:{COLORS['success']};" if is_key else ""

    tbl_rows.append([
        f"<span style='{bold}{key_style}'>{label}</span>",
        f"<span style='{bold}{key_style}'>{fmt_currency(actual)}</span>",
        fmt_currency(budget_val),
        f"<span style='color:{vc};font-weight:600;'>{fmt_currency(variance)}</span>",
        f"<span style='color:{vc};font-weight:600;'>{var_pct*100:.1f}%</span>",
    ])
    row_idx += 1

styled_table(headers, tbl_rows, col_align=col_align, highlight_rows=highlight)

spacer(8)

# ── Variance Waterfall Chart ─────────────────────────────────────
section_header("NOI Variance Waterfall")

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
    connector=dict(line=dict(color=COLORS["border"])),
    increasing=dict(marker=dict(color=COLORS["success"])),
    decreasing=dict(marker=dict(color=COLORS["error"])),
    totals=dict(marker=dict(color=COLORS["primary"])),
    texttemplate="%{y:$,.0f}",
    textposition="outside",
))
fig_wf.update_layout(**PLOTLY_LAYOUT, height=400)
st.plotly_chart(fig_wf, use_container_width=True)

spacer(8)

# ── Monthly Actual vs Budget Trend ────────────────────────────────
section_header("Monthly NOI: Actual vs Budget")

noi_series = get_monthly_series(df, 'NET OPERATING INCOME (NOI)')
monthly_budget_noi = b_noi / 12

fig_trend = go.Figure()
fig_trend.add_trace(go.Bar(
    x=noi_series['Month'], y=noi_series['Amount'],
    name='Actual NOI', marker_color=COLORS["accent"], opacity=0.8,
))
fig_trend.add_hline(
    y=monthly_budget_noi, line_dash="dash", line_color=COLORS["error"],
    annotation_text=f"Budget: {fmt_currency(monthly_budget_noi)}/mo",
)
fig_trend.update_layout(
    **PLOTLY_LAYOUT,
    height=350,
    yaxis_title="$",
)
st.plotly_chart(fig_trend, use_container_width=True)
