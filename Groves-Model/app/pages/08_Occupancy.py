"""Occupancy & Rent Growth — Track occupancy trends, rent growth, and renovation ROI."""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ui.theme import inject_theme, COLORS, PLOTLY_LAYOUT, PLOTLY_COLORS
from ui.components import page_header, kpi_row, section_header, spacer, no_data_page, page_footer

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

page_header(
    "Occupancy & Rent Growth",
    "Physical occupancy, average rents, loss-to-lease, and renovation ROI",
)

# ── Data guard ────────────────────────────────────────────────
if no_data_page("rent_roll.csv"):
    st.stop()

# ── Data loading ──────────────────────────────────────────────────
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
RR_CSV = os.path.join(BASE_DIR, 'data', 'rent_roll.csv')
UI_CSV = os.path.join(BASE_DIR, 'data', 'unit_improvements.csv')

UNITS = st.session_state.property['units']


@st.cache_data(show_spinner="Loading rent roll...")
def load_rent_roll(_version, csv_path):
    rr = pd.read_csv(csv_path)
    months = [c for c in rr.columns if c != 'Unit']
    return rr, months


rr_df, months = load_rent_roll(st.session_state.data_version, RR_CSV)

# ── Compute occupancy and rent metrics by month ──────────────────
month_labels = []
occupancy_pcts = []
avg_rents = []
total_rent_collected = []
occupied_counts = []

for m in months:
    dt = pd.Timestamp(m)
    month_labels.append(dt.strftime('%b %y'))

    rents = rr_df[m].astype(float)
    occupied = (rents > 0).sum()
    total_units = len(rents)

    occ_pct = occupied / total_units if total_units else 0
    occupancy_pcts.append(occ_pct)
    occupied_counts.append(occupied)

    avg_rent = rents[rents > 0].mean() if occupied > 0 else 0
    avg_rents.append(avg_rent)
    total_rent_collected.append(rents.sum())

# ── KPI Cards ─────────────────────────────────────────────────────
latest_occ = occupancy_pcts[-1] if occupancy_pcts else 0
latest_avg = avg_rents[-1] if avg_rents else 0
first_avg = avg_rents[0] if avg_rents else 0
rent_growth_total = (latest_avg / first_avg - 1) if first_avg else 0

# Month-over-month delta
prev_occ = occupancy_pcts[-2] if len(occupancy_pcts) > 1 else latest_occ
prev_avg = avg_rents[-2] if len(avg_rents) > 1 else latest_avg

kpi_row([
    {"label": "Current Occupancy", "value": f"{latest_occ * 100:.1f}%",
     "delta": f"{(latest_occ - prev_occ) * 100:.1f}pp" if latest_occ != prev_occ else None},
    {"label": "Avg In-Place Rent", "value": f"${latest_avg:,.0f}",
     "delta": f"${latest_avg - prev_avg:,.0f}" if latest_avg != prev_avg else None},
    {"label": "Vacant Units", "value": f"{UNITS - occupied_counts[-1]}"},
    {"label": "Rent Growth (Since Acq.)", "value": f"{rent_growth_total * 100:.1f}%"},
])

spacer(8)

# ── Chart 1: Occupancy Trend ─────────────────────────────────────
section_header("Physical Occupancy Trend")

fig_occ = go.Figure()
fig_occ.add_trace(go.Scatter(
    x=month_labels, y=[o * 100 for o in occupancy_pcts],
    mode='lines+markers', name='Occupancy %',
    line=dict(color=COLORS["accent"], width=2.5),
    marker=dict(size=6),
    fill='tozeroy', fillcolor='rgba(47,143,157,0.08)',
))
fig_occ.add_hline(y=95, line_dash="dash", line_color=COLORS["success"],
                  annotation_text="95% target", opacity=0.6)
fig_occ.update_layout(
    **PLOTLY_LAYOUT,
    height=300,
    yaxis_title="Occupancy %", yaxis_range=[80, 102],
)
st.plotly_chart(fig_occ, use_container_width=True)

# ── Occupancy by Building ────────────────────────────────────────
section_header("Occupancy by Building")

# Identify buildings from unit prefixes
rr_units = rr_df['Unit'].tolist()
building_ids = sorted(set(u.split('-')[0] for u in rr_units))
bldg_labels_map = {b: f"Bldg {b}" for b in building_ids}

bldg_occ_data = []
for m in months:
    dt = pd.Timestamp(m)
    label = dt.strftime('%b %y')
    rents = rr_df[['Unit', m]].copy()
    rents[m] = rents[m].astype(float)
    for b in building_ids:
        bldg_units = rents[rents['Unit'].str.startswith(b + '-')]
        total = len(bldg_units)
        occupied_b = (bldg_units[m] > 0).sum()
        bldg_occ_data.append({
            'Month': label, 'Building': bldg_labels_map[b],
            'Occupancy': occupied_b / total * 100 if total else 0,
            'Occupied': occupied_b, 'Total': total,
        })

bldg_occ_df = pd.DataFrame(bldg_occ_data)

fig_bldg = go.Figure()
for i, b in enumerate(building_ids):
    bdf = bldg_occ_df[bldg_occ_df['Building'] == bldg_labels_map[b]]
    fig_bldg.add_trace(go.Scatter(
        x=bdf['Month'], y=bdf['Occupancy'],
        mode='lines+markers', name=bldg_labels_map[b],
        line=dict(color=PLOTLY_COLORS[i % len(PLOTLY_COLORS)], width=2),
        marker=dict(size=5),
    ))
fig_bldg.add_hline(y=95, line_dash="dash", line_color=COLORS["success"],
                    annotation_text="95% target", opacity=0.5)
fig_bldg.update_layout(
    **PLOTLY_LAYOUT,
    height=350,
    yaxis_title="Occupancy %", yaxis_range=[75, 102],
)
st.plotly_chart(fig_bldg, use_container_width=True)

# ── Move-In / Move-Out Net Absorption ────────────────────────────
section_header("Move-Ins & Move-Outs (Net Absorption)",
               "Tracks unit turnover and net absorption each month")

move_ins = []
move_outs = []

for i in range(1, len(months)):
    prev_rents = rr_df[months[i - 1]].astype(float)
    curr_rents = rr_df[months[i]].astype(float)

    # Move-out: was occupied (>0) last month, vacant (0) this month
    outs = ((prev_rents > 0) & (curr_rents == 0)).sum()
    # Move-in: was vacant (0) last month, occupied (>0) this month
    ins = ((prev_rents == 0) & (curr_rents > 0)).sum()

    move_ins.append(ins)
    move_outs.append(outs)

absorption_labels = month_labels[1:]
net_absorption = [mi - mo for mi, mo in zip(move_ins, move_outs)]

left_abs, right_abs = st.columns(2)

with left_abs:
    fig_moves = go.Figure()
    fig_moves.add_trace(go.Bar(
        x=absorption_labels, y=move_ins,
        name='Move-Ins', marker_color=COLORS["success"], opacity=0.8,
    ))
    fig_moves.add_trace(go.Bar(
        x=absorption_labels, y=[-o for o in move_outs],
        name='Move-Outs', marker_color=COLORS["error"], opacity=0.8,
    ))
    fig_moves.add_hline(y=0, line_color=COLORS["muted"], opacity=0.3)
    fig_moves.update_layout(
        **PLOTLY_LAYOUT,
        height=350,
        yaxis_title="Units", barmode='relative',
    )
    st.plotly_chart(fig_moves, use_container_width=True)

with right_abs:
    net_colors = [COLORS["success"] if v >= 0 else COLORS["error"] for v in net_absorption]
    fig_net = go.Figure()
    fig_net.add_trace(go.Bar(
        x=absorption_labels, y=net_absorption,
        marker_color=net_colors, opacity=0.85,
        text=[f"+{v}" if v > 0 else str(v) for v in net_absorption],
        textposition='outside',
    ))
    fig_net.add_hline(y=0, line_color=COLORS["muted"], opacity=0.3)
    fig_net.update_layout(
        **PLOTLY_LAYOUT,
        title="Net Absorption",
        height=350,
        yaxis_title="Net Units",
    )
    st.plotly_chart(fig_net, use_container_width=True)

# Turnover summary KPIs
total_move_ins = sum(move_ins)
total_move_outs = sum(move_outs)
turnover_rate = total_move_outs / UNITS * 100

kpi_row([
    {"label": "Total Move-Ins", "value": str(total_move_ins)},
    {"label": "Total Move-Outs", "value": str(total_move_outs)},
    {"label": "Net Absorption", "value": f"{total_move_ins - total_move_outs:+d}"},
    {"label": "Turnover Rate", "value": f"{turnover_rate:.1f}%"},
])

spacer(8)

# ── Unit-Level Occupancy Heatmap ─────────────────────────────────
section_header("Unit-Level Occupancy Grid",
               "Green = occupied, Red = vacant. Select a building or view all.")

occ_matrix = rr_df.set_index('Unit')[months].astype(float)
occ_binary = (occ_matrix > 0).astype(int)
occ_binary = occ_binary.sort_index()

heatmap_month_labels = [pd.Timestamp(m).strftime('%b %y') for m in months]

selected_bldg = st.selectbox(
    "Building:", ["All Buildings"] + [bldg_labels_map[b] for b in building_ids]
)

if selected_bldg == "All Buildings":
    display_matrix = occ_binary
else:
    prefix = [b for b, lbl in bldg_labels_map.items() if lbl == selected_bldg][0]
    display_matrix = occ_binary[occ_binary.index.str.startswith(prefix + '-')]

# Custom hover text showing rent or "Vacant"
hover_text = []
display_rents = occ_matrix.loc[display_matrix.index]
for unit in display_matrix.index:
    row_text = []
    for m in months:
        rent = display_rents.loc[unit, m]
        if rent > 0:
            row_text.append(f"Unit {unit}<br>{pd.Timestamp(m).strftime('%b %y')}<br>${rent:,.0f}/mo")
        else:
            row_text.append(f"Unit {unit}<br>{pd.Timestamp(m).strftime('%b %y')}<br>VACANT")
    hover_text.append(row_text)

fig_heat = go.Figure(data=go.Heatmap(
    z=display_matrix.values,
    x=heatmap_month_labels,
    y=display_matrix.index.tolist(),
    colorscale=[[0, COLORS["error"]], [1, COLORS["success"]]],
    showscale=False,
    text=hover_text,
    hovertemplate='%{text}<extra></extra>',
    xgap=1, ygap=1,
))
fig_heat.update_layout(
    **PLOTLY_LAYOUT,
    height=max(400, len(display_matrix) * 14),
    yaxis=dict(dtick=1, autorange='reversed', gridcolor=COLORS["grid"]),
)
st.plotly_chart(fig_heat, use_container_width=True)

spacer(8)

# ── Chart 2: Average Rent Trend ──────────────────────────────────
section_header("Average In-Place Rent")

fig_rent = go.Figure()
fig_rent.add_trace(go.Bar(
    x=month_labels, y=avg_rents,
    name='Avg Rent', marker_color=COLORS["success"], opacity=0.7,
))

# Add market rent lines
unit_mix = st.session_state.unit_mix
weighted_market = sum(
    v['market_rent'] * v['count'] for v in unit_mix.values()
) / sum(v['count'] for v in unit_mix.values())

fig_rent.add_hline(
    y=weighted_market, line_dash="dash", line_color=COLORS["error"],
    annotation_text=f"Wtd Market: ${weighted_market:,.0f}", opacity=0.7,
)
fig_rent.update_layout(
    **PLOTLY_LAYOUT,
    height=300,
    yaxis_title="$/Month",
)
st.plotly_chart(fig_rent, use_container_width=True)

# ── Charts 3 & 4 side by side ────────────────────────────────────
left_col, right_col = st.columns(2)

with left_col:
    section_header("Total Rent Collected")
    fig_total = go.Figure()
    fig_total.add_trace(go.Bar(
        x=month_labels, y=total_rent_collected,
        marker_color=COLORS["accent"], opacity=0.8,
    ))

    # GPR line (all units at market)
    gpr = sum(v['market_rent'] * v['count'] for v in unit_mix.values())
    fig_total.add_hline(y=gpr, line_dash="dot", line_color=COLORS["muted"],
                        annotation_text=f"GPR: ${gpr:,.0f}")
    fig_total.update_layout(
        **PLOTLY_LAYOUT,
        height=350,
        yaxis_title="$",
    )
    st.plotly_chart(fig_total, use_container_width=True)

with right_col:
    section_header("Month-over-Month Rent Growth")
    mom_growth = []
    for i in range(len(avg_rents)):
        if i == 0:
            mom_growth.append(0)
        else:
            pct_g = (avg_rents[i] / avg_rents[i - 1] - 1) if avg_rents[i - 1] else 0
            mom_growth.append(pct_g * 100)

    colors = [COLORS["success"] if v >= 0 else COLORS["error"] for v in mom_growth]
    fig_mom = go.Figure()
    fig_mom.add_trace(go.Bar(
        x=month_labels, y=mom_growth,
        marker_color=colors, opacity=0.8,
    ))
    fig_mom.add_hline(y=0, line_color=COLORS["muted"], opacity=0.3)
    fig_mom.update_layout(
        **PLOTLY_LAYOUT,
        height=350,
        yaxis_title="% Change",
    )
    st.plotly_chart(fig_mom, use_container_width=True)

spacer(8)

# ── Loss-to-Lease Analysis ───────────────────────────────────────
section_header("Loss-to-Lease Analysis",
               "Gap between in-place rents and market rents by unit")

latest_month = months[-1]
current_rents = rr_df[['Unit', latest_month]].copy()
current_rents.columns = ['Unit', 'CurrentRent']
current_rents['CurrentRent'] = current_rents['CurrentRent'].astype(float)

# Load unit improvements for market rent data
if os.path.exists(UI_CSV):
    ui_df = pd.read_csv(UI_CSV)
    ui_merge = ui_df[['Unit', 'MktRent', 'Condition']].copy()
    ltl_df = current_rents.merge(ui_merge, on='Unit', how='left')
else:
    # Fallback: estimate market rent from unit mix
    ltl_df = current_rents.copy()
    ltl_df['MktRent'] = weighted_market
    ltl_df['Condition'] = 'Classic'

# Fill missing market rents with weighted average
ltl_df['MktRent'] = ltl_df['MktRent'].fillna(weighted_market)
ltl_df['Condition'] = ltl_df['Condition'].fillna('Classic')

# Only occupied units
occupied = ltl_df[ltl_df['CurrentRent'] > 0].copy()
occupied['LTL'] = occupied['MktRent'] - occupied['CurrentRent']
occupied['LTL_Pct'] = occupied['LTL'] / occupied['MktRent']
occupied = occupied.sort_values('LTL', ascending=False)

# Summary metrics
total_ltl = occupied['LTL'].sum()
avg_ltl = occupied['LTL'].mean()

kpi_row([
    {"label": "Total Monthly LTL", "value": f"${total_ltl:,.0f}"},
    {"label": "Annual LTL Opportunity", "value": f"${total_ltl * 12:,.0f}"},
    {"label": "Avg LTL per Unit", "value": f"${avg_ltl:,.0f}"},
])

# Top 15 units with biggest LTL gap
top_ltl = occupied.head(15)
if len(top_ltl) > 0:
    fig_ltl = go.Figure()
    fig_ltl.add_trace(go.Bar(
        x=top_ltl['Unit'], y=top_ltl['CurrentRent'],
        name='In-Place Rent', marker_color=COLORS["accent"],
    ))
    fig_ltl.add_trace(go.Bar(
        x=top_ltl['Unit'], y=top_ltl['LTL'],
        name='Loss-to-Lease Gap', marker_color=COLORS["error"], opacity=0.7,
    ))
    fig_ltl.update_layout(
        **PLOTLY_LAYOUT,
        barmode='stack', height=350,
        yaxis_title="$/Month",
    )
    st.plotly_chart(fig_ltl, use_container_width=True)

spacer(8)

# ── Renovation ROI ────────────────────────────────────────────────
if os.path.exists(UI_CSV):
    section_header("Renovation ROI", "Rent lift from unit renovations")

    ui_df = pd.read_csv(UI_CSV)
    renovated = ui_df[ui_df['Condition'] == 'Renovated'].copy()

    if len(renovated) > 0:
        renovated['OrigRent'] = renovated['OrigRent'].astype(float)
        renovated['CurrRent'] = pd.to_numeric(renovated['CurrRent'], errors='coerce')
        has_current = renovated.dropna(subset=['CurrRent'])

        if len(has_current) > 0:
            has_current = has_current.copy()
            has_current['RentLift'] = has_current['CurrRent'] - has_current['OrigRent']
            has_current['LiftPct'] = has_current['RentLift'] / has_current['OrigRent']

            avg_lift = has_current['RentLift'].mean()
            avg_lift_pct = has_current['LiftPct'].mean()
            total_annual_lift = has_current['RentLift'].sum() * 12

            kpi_row([
                {"label": "Units Renovated", "value": str(len(has_current))},
                {"label": "Avg Rent Lift", "value": f"${avg_lift:,.0f}/mo"},
                {"label": "Avg Lift %", "value": f"{avg_lift_pct * 100:.1f}%"},
                {"label": "Annual Lift Total", "value": f"${total_annual_lift:,.0f}"},
            ])

            fig_reno = go.Figure()
            fig_reno.add_trace(go.Bar(
                x=has_current['Unit'], y=has_current['OrigRent'],
                name='Original Rent', marker_color=COLORS["muted"],
            ))
            fig_reno.add_trace(go.Bar(
                x=has_current['Unit'], y=has_current['RentLift'],
                name='Rent Lift', marker_color=COLORS["success"],
            ))
            fig_reno.update_layout(
                **PLOTLY_LAYOUT,
                barmode='stack', height=350,
                yaxis_title="$/Month",
            )
            st.plotly_chart(fig_reno, use_container_width=True)

page_footer()
