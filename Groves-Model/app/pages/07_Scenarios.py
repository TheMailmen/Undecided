"""Scenarios — Sensitivity tables, what-if analysis, and scenario comparison."""

import json
import os
import sys

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_engine import get_t12_totals, load_pl_data
from ui.theme import inject_theme, COLORS, PLOTLY_LAYOUT, HEATMAP_COLORSCALE, fmt_currency, fmt_pct, fmt_multiple
from ui.components import (
    page_header, kpi_row, section_header, sensitivity_matrix, spacer, badge,
    styled_table, no_data_page, page_footer,
)

# ── Init ──────────────────────────────────────────────────────────
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

# ── Data guard ────────────────────────────────────────────────
if no_data_page("pl_actuals.csv"):
    st.stop()

# ── Data loading (cached) ────────────────────────────────────────
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
PL_CSV = os.path.join(BASE_DIR, 'data', 'pl_actuals.csv')


@st.cache_data(show_spinner="Loading financial data...")
def load_data(_version, csv_path, total_equity, purchase_price):
    return load_pl_data(csv_path, {
        'total_equity': total_equity,
        'purchase_price': purchase_price,
    })


df = load_data(
    st.session_state.data_version, PL_CSV,
    st.session_state.total_equity,
    st.session_state.property['purchase_price'],
)
t12 = get_t12_totals(df)

# ── Financial constants ──────────────────────────────────────────
current_noi = t12['NET OPERATING INCOME (NOI)']
current_ncf = t12['NET CASH FLOW']
current_cfads = t12['CASH FLOW AFTER DEBT SERVICE']
purchase_price = st.session_state.property['purchase_price']
total_equity = st.session_state.total_equity
loan_balance = st.session_state.loan['est_current_balance']


# ── Core projection engine ───────────────────────────────────────
def compute_irr(cashflows, guess=0.10, tol=1e-8, max_iter=200):
    rate = guess
    for _ in range(max_iter):
        if abs(1 + rate) < 1e-14:
            rate += 0.01
            continue
        npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))
        dnpv = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cashflows))
        if abs(dnpv) < 1e-14:
            break
        new_rate = rate - npv / dnpv
        if abs(new_rate - rate) < tol:
            return new_rate
        rate = new_rate
    return rate


def project_returns(exit_cap, noi_growth, hold, sell_cost=0.02):
    """Compute IRR, equity multiple, exit value, and net proceeds."""
    proj_noi = current_noi * (1 + noi_growth) ** hold
    exit_val = proj_noi / exit_cap
    net_sale = exit_val * (1 - sell_cost) - loan_balance

    cfs = [-total_equity]
    for yr in range(1, hold):
        cfs.append(current_ncf * (1 + noi_growth) ** yr)
    cfs.append(current_ncf * (1 + noi_growth) ** hold + net_sale)

    total_return = sum(cfs[1:])
    em = total_return / total_equity if total_equity else 0
    irr = compute_irr(cfs)
    avg_coc = (current_cfads / total_equity) if total_equity else 0
    return irr, em, exit_val, net_sale, avg_coc


# ── Default scenarios ────────────────────────────────────────────
DEFAULT_SCENARIOS = {
    'Conservative': {'exit_cap': 0.075, 'noi_growth': 0.01, 'hold': 5, 'sell_cost': 0.02},
    'Base Case':    {'exit_cap': 0.065, 'noi_growth': 0.03, 'hold': 5, 'sell_cost': 0.02},
    'Optimistic':   {'exit_cap': 0.055, 'noi_growth': 0.05, 'hold': 5, 'sell_cost': 0.02},
    'Quick Flip':   {'exit_cap': 0.060, 'noi_growth': 0.03, 'hold': 3, 'sell_cost': 0.02},
}

if 'scenarios' not in st.session_state:
    st.session_state.scenarios = dict(DEFAULT_SCENARIOS)

# ══════════════════════════════════════════════════════════════════
# PAGE LAYOUT
# ══════════════════════════════════════════════════════════════════

page_header(
    "Scenario & Sensitivity Analysis",
    "What-if modeling across exit cap rates, NOI growth, and hold periods",
    right_text=f"T-12 NOI: {fmt_currency(current_noi)}",
)

# ── Sidebar: Scenario Controls ───────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="margin-bottom:20px;">
        <p style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;
                   color:rgba(255,255,255,.5);margin:0 0 4px 0;font-weight:600;">
            Scenario Engine
        </p>
        <p style="font-size:0.85rem;color:rgba(255,255,255,.85);margin:0;">
            Adjust assumptions below to update all sensitivity tables and charts.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    base_hold = st.number_input(
        "Hold Period (years)", value=5, min_value=1, max_value=15,
        step=1, key="sc_hold",
        help="Number of years before exit/sale",
    )
    base_exit_cap = st.number_input(
        "Base Exit Cap Rate", value=0.065, min_value=0.03, max_value=0.12,
        step=0.005, format="%.3f", key="sc_exit_cap",
        help="Expected cap rate at disposition",
    )
    base_noi_growth = st.number_input(
        "Annual NOI Growth", value=0.03, min_value=-0.05, max_value=0.15,
        step=0.005, format="%.3f", key="sc_noi_growth",
        help="Projected annual NOI growth rate",
    )
    base_sell_cost = st.number_input(
        "Selling Costs", value=0.02, min_value=0.0, max_value=0.10,
        step=0.005, format="%.3f", key="sc_sell",
        help="Broker + closing costs as % of exit value",
    )

    # Validation
    if base_exit_cap < 0.04:
        st.warning("Exit cap below 4% is aggressive", icon="\u26a0\ufe0f")
    if base_noi_growth > 0.08:
        st.warning("NOI growth above 8% is unusual", icon="\u26a0\ufe0f")

    st.markdown("---")

    # Save / Load / Reset
    st.markdown(
        '<p style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.1em;'
        'color:rgba(255,255,255,.5);margin:0 0 8px 0;font-weight:600;">'
        'Scenario Management</p>',
        unsafe_allow_html=True,
    )

    # Save current scenario
    save_name = st.text_input("Scenario name", value="", key="sc_save_name",
                              placeholder="e.g., Aggressive Growth")
    if st.button("Save Scenario", use_container_width=True, type="primary"):
        if save_name.strip():
            st.session_state.scenarios[save_name.strip()] = {
                'exit_cap': base_exit_cap,
                'noi_growth': base_noi_growth,
                'hold': base_hold,
                'sell_cost': base_sell_cost,
            }
            st.success(f"Saved: {save_name.strip()}")
        else:
            st.error("Enter a name first")

    # Export JSON
    export_data = json.dumps(st.session_state.scenarios, indent=2)
    st.download_button(
        "Export All Scenarios",
        data=export_data,
        file_name="groves_scenarios.json",
        mime="application/json",
        use_container_width=True,
    )

    # Import JSON
    uploaded = st.file_uploader("Import scenarios", type=["json"], key="sc_import")
    if uploaded is not None:
        try:
            imported = json.loads(uploaded.read())
            st.session_state.scenarios.update(imported)
            st.success(f"Imported {len(imported)} scenario(s)")
        except Exception:
            st.error("Invalid JSON file")

    # Reset
    if st.button("Reset to Defaults", use_container_width=True):
        st.session_state.scenarios = dict(DEFAULT_SCENARIOS)
        st.rerun()


# ── KPI Summary (base case from sidebar inputs) ─────────────────
base_irr, base_em, base_exit_val, base_net_sale, base_coc = project_returns(
    base_exit_cap, base_noi_growth, base_hold, base_sell_cost,
)

kpi_row([
    {"label": "Projected IRR", "value": fmt_pct(base_irr)},
    {"label": "Equity Multiple", "value": fmt_multiple(base_em)},
    {"label": "Avg Cash-on-Cash", "value": fmt_pct(base_coc)},
    {"label": "Exit Value", "value": fmt_currency(base_exit_val)},
    {"label": "Net Proceeds", "value": fmt_currency(base_net_sale)},
])

spacer(16)

# ══════════════════════════════════════════════════════════════════
# SCENARIO COMPARISON TABLE
# ══════════════════════════════════════════════════════════════════
section_header("Scenario Comparison", "Side-by-side view of all saved scenarios")

scenarios = st.session_state.scenarios
sc_names = list(scenarios.keys())

# Build comparison table
headers = ["Metric"] + sc_names
comparison_rows = []

irr_vals, em_vals, exit_vals, net_vals, coc_vals = [], [], [], [], []
for name in sc_names:
    p = scenarios[name]
    irr_v, em_v, exit_v, net_v, coc_v = project_returns(
        p['exit_cap'], p['noi_growth'], p['hold'], p.get('sell_cost', 0.02),
    )
    irr_vals.append(irr_v)
    em_vals.append(em_v)
    exit_vals.append(exit_v)
    net_vals.append(net_v)
    coc_vals.append(coc_v)

# Assumptions rows
comparison_rows.append(
    ["Exit Cap Rate"] + [fmt_pct(scenarios[n]['exit_cap']) for n in sc_names]
)
comparison_rows.append(
    ["NOI Growth"] + [fmt_pct(scenarios[n]['noi_growth']) for n in sc_names]
)
comparison_rows.append(
    ["Hold Period"] + [f"{scenarios[n]['hold']} yr" for n in sc_names]
)

# Results rows
comparison_rows.append(
    [f"<b>IRR</b>"] + [
        f"<span style='color:{COLORS['success'] if v > 0.10 else COLORS['error'] if v < 0 else COLORS['text']};font-weight:600;'>"
        f"{fmt_pct(v)}</span>" for v in irr_vals
    ]
)
comparison_rows.append(
    [f"<b>Equity Multiple</b>"] + [
        f"<span style='color:{COLORS['success'] if v > 2.0 else COLORS['text']};font-weight:600;'>"
        f"{fmt_multiple(v)}</span>" for v in em_vals
    ]
)
comparison_rows.append(
    [f"<b>Exit Value</b>"] + [f"<b>{fmt_currency(v)}</b>" for v in exit_vals]
)
comparison_rows.append(
    [f"<b>Net Proceeds</b>"] + [
        f"<span style='color:{COLORS['success'] if v > 0 else COLORS['error']};font-weight:600;'>"
        f"{fmt_currency(v)}</span>" for v in net_vals
    ]
)

col_align = ["left"] + ["center"] * len(sc_names)
styled_table(headers, comparison_rows, col_align=col_align, highlight_rows={3, 4, 5, 6})

spacer(8)

# ══════════════════════════════════════════════════════════════════
# SENSITIVITY TABLES
# ══════════════════════════════════════════════════════════════════
section_header(
    "IRR Sensitivity Matrix",
    "Exit Cap Rate vs Annual NOI Growth"
)

cap_rates = [0.055, 0.060, 0.065, 0.070, 0.075, 0.080]
noi_growths = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05]
cap_labels = [f"{c*100:.1f}%" for c in cap_rates]
growth_labels = [f"{g*100:.0f}%" for g in noi_growths]

# Compute IRR matrix
irr_matrix_vals = []
irr_matrix_display = []
for cap in cap_rates:
    row_vals = []
    row_display = []
    for growth in noi_growths:
        irr_val, _, _, _, _ = project_returns(cap, growth, base_hold, base_sell_cost)
        row_vals.append(irr_val)
        row_display.append(f"{irr_val*100:.1f}%")
    irr_matrix_vals.append(row_vals)
    irr_matrix_display.append(row_display)


def irr_color(ri, ci, cell_str):
    v = irr_matrix_vals[ri][ci]
    if v > 0.10:
        return COLORS["success"]
    if v < 0:
        return COLORS["error"]
    return None


sensitivity_matrix(
    title="",
    row_label="Exit Cap",
    col_label="NOI Growth",
    row_keys=cap_labels,
    col_keys=growth_labels,
    values=irr_matrix_display,
    color_fn=irr_color,
)

# ── Equity Multiple Sensitivity ──────────────────────────────────
section_header(
    "Equity Multiple Sensitivity",
    "Exit Cap Rate vs Annual NOI Growth"
)

em_matrix_vals = []
em_matrix_display = []
for cap in cap_rates:
    row_vals = []
    row_display = []
    for growth in noi_growths:
        _, em_val, _, _, _ = project_returns(cap, growth, base_hold, base_sell_cost)
        row_vals.append(em_val)
        row_display.append(f"{em_val:.2f}x")
    em_matrix_vals.append(row_vals)
    em_matrix_display.append(row_display)


def em_color(ri, ci, cell_str):
    v = em_matrix_vals[ri][ci]
    if v > 2.0:
        return COLORS["success"]
    if v < 1.0:
        return COLORS["error"]
    return None


sensitivity_matrix(
    title="",
    row_label="Exit Cap",
    col_label="NOI Growth",
    row_keys=cap_labels,
    col_keys=growth_labels,
    values=em_matrix_display,
    color_fn=em_color,
)

# ── Hold Period Analysis ─────────────────────────────────────────
section_header(
    "IRR by Hold Period",
    f"NOI Growth: {fmt_pct(base_noi_growth)} (from sidebar)"
)

hold_periods = [3, 5, 7, 10]
hold_labels = [f"{h} yr" for h in hold_periods]

hold_matrix_vals = []
hold_matrix_display = []
for cap in cap_rates:
    row_vals = []
    row_display = []
    for h in hold_periods:
        irr_val, _, _, _, _ = project_returns(cap, base_noi_growth, h, base_sell_cost)
        row_vals.append(irr_val)
        row_display.append(f"{irr_val*100:.1f}%")
    hold_matrix_vals.append(row_vals)
    hold_matrix_display.append(row_display)


def hold_color(ri, ci, cell_str):
    v = hold_matrix_vals[ri][ci]
    if v > 0.10:
        return COLORS["success"]
    if v < 0:
        return COLORS["error"]
    return None


sensitivity_matrix(
    title="",
    row_label="Exit Cap",
    col_label="Hold Period",
    row_keys=cap_labels,
    col_keys=hold_labels,
    values=hold_matrix_display,
    color_fn=hold_color,
)

# ══════════════════════════════════════════════════════════════════
# EXIT VALUE HEATMAP
# ══════════════════════════════════════════════════════════════════
section_header("Exit Value Heatmap", "Projected disposition value by cap rate and NOI growth")

exit_val_matrix = []
for cap in cap_rates:
    row = []
    for growth in noi_growths:
        proj_noi = current_noi * (1 + growth) ** base_hold
        row.append(proj_noi / cap)
    exit_val_matrix.append(row)

# Custom teal-navy colorscale
colorscale = HEATMAP_COLORSCALE

fig = go.Figure(data=go.Heatmap(
    z=exit_val_matrix,
    x=[f"{g*100:.0f}%" for g in noi_growths],
    y=[f"{c*100:.1f}%" for c in cap_rates],
    colorscale=colorscale,
    texttemplate="$%{z:,.0f}",
    textfont=dict(size=11, family="Inter, system-ui, sans-serif"),
    hoverongaps=False,
    colorbar=dict(
        title=dict(text="Exit Value", font=dict(size=11)),
        tickprefix="$",
        tickformat=",",
    ),
))
heatmap_layout = {**PLOTLY_LAYOUT}
heatmap_layout['yaxis'] = dict(autorange='reversed', gridcolor=COLORS["grid"])
fig.update_layout(**heatmap_layout, height=420, xaxis_title="Annual NOI Growth", yaxis_title="Exit Cap Rate")
st.plotly_chart(fig, use_container_width=True)

spacer(8)

# ── Scenario IRR Bar Comparison ──────────────────────────────────
section_header("Scenario IRR Comparison", "Visual comparison of projected returns")

fig_bar = go.Figure()

# Compute for each scenario
bar_names = list(scenarios.keys())
bar_irrs = []
bar_ems = []
for name in bar_names:
    p = scenarios[name]
    irr_v, em_v, _, _, _ = project_returns(
        p['exit_cap'], p['noi_growth'], p['hold'], p.get('sell_cost', 0.02),
    )
    bar_irrs.append(irr_v * 100)
    bar_ems.append(em_v)

# IRR bars
bar_colors = [
    COLORS["success"] if v > 10 else (COLORS["error"] if v < 0 else COLORS["accent"])
    for v in bar_irrs
]
fig_bar.add_trace(go.Bar(
    x=bar_names, y=bar_irrs,
    marker_color=bar_colors, opacity=0.85,
    text=[f"{v:.1f}%" for v in bar_irrs],
    textposition='outside',
    textfont=dict(size=12, color=COLORS["text"]),
))

# 10% target line
fig_bar.add_hline(
    y=10, line_dash="dash", line_color=COLORS["muted"],
    annotation_text="10% target", annotation_font_size=10,
    opacity=0.6,
)

fig_bar.update_layout(
    **PLOTLY_LAYOUT,
    height=360,
    yaxis_title="IRR (%)",
    showlegend=False,
)
st.plotly_chart(fig_bar, use_container_width=True)

spacer(8)

# ── Assumptions Summary ──────────────────────────────────────────
with st.expander("Current Model Assumptions"):
    ac1, ac2, ac3 = st.columns(3)
    with ac1:
        st.markdown(f"**T-12 NOI:** {fmt_currency(current_noi)}")
        st.markdown(f"**T-12 NCF:** {fmt_currency(current_ncf)}")
        st.markdown(f"**Purchase Price:** {fmt_currency(purchase_price)}")
    with ac2:
        st.markdown(f"**Exit Cap Rate:** {fmt_pct(base_exit_cap)}")
        st.markdown(f"**Hold Period:** {base_hold} years")
        st.markdown(f"**NOI Growth:** {fmt_pct(base_noi_growth)}/yr")
    with ac3:
        st.markdown(f"**Selling Costs:** {fmt_pct(base_sell_cost)}")
        st.markdown(f"**Loan Balance:** {fmt_currency(loan_balance)}")
        st.markdown(f"**Total Equity:** {fmt_currency(total_equity)}")

page_footer()
