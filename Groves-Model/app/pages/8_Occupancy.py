"""Occupancy & Rent Growth — Track occupancy trends, rent growth, and renovation ROI."""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

st.title("Occupancy & Rent Growth")
st.caption("Physical occupancy, average rents, loss-to-lease, and renovation ROI.")

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

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Current Occupancy",
    f"{latest_occ * 100:.1f}%",
    delta=f"{(latest_occ - prev_occ) * 100:.1f}pp" if latest_occ != prev_occ else None,
)
col2.metric(
    "Avg In-Place Rent",
    f"${latest_avg:,.0f}",
    delta=f"${latest_avg - prev_avg:,.0f}" if latest_avg != prev_avg else None,
)
col3.metric(
    "Vacant Units",
    f"{UNITS - occupied_counts[-1]}",
)
col4.metric(
    "Rent Growth (Since Acq.)",
    f"{rent_growth_total * 100:.1f}%",
)

st.divider()

# ── Chart 1: Occupancy Trend ─────────────────────────────────────
st.subheader("Physical Occupancy Trend")

fig_occ = go.Figure()
fig_occ.add_trace(go.Scatter(
    x=month_labels, y=[o * 100 for o in occupancy_pcts],
    mode='lines+markers', name='Occupancy %',
    line=dict(color='#1B4F72', width=2.5),
    marker=dict(size=6),
    fill='tozeroy', fillcolor='rgba(27,79,114,0.1)',
))
fig_occ.add_hline(y=95, line_dash="dash", line_color="#1E8449",
                  annotation_text="95% target", opacity=0.6)
fig_occ.update_layout(
    height=300, margin=dict(l=0, r=0, t=30, b=0),
    yaxis_title="Occupancy %", yaxis_range=[80, 102],
)
st.plotly_chart(fig_occ, use_container_width=True)

# ── Chart 2: Average Rent Trend ──────────────────────────────────
st.subheader("Average In-Place Rent")

fig_rent = go.Figure()
fig_rent.add_trace(go.Bar(
    x=month_labels, y=avg_rents,
    name='Avg Rent', marker_color='#1E8449', opacity=0.7,
))

# Add market rent lines
unit_mix = st.session_state.unit_mix
weighted_market = sum(
    v['market_rent'] * v['count'] for v in unit_mix.values()
) / sum(v['count'] for v in unit_mix.values())

fig_rent.add_hline(
    y=weighted_market, line_dash="dash", line_color="#C00000",
    annotation_text=f"Wtd Market: ${weighted_market:,.0f}", opacity=0.7,
)
fig_rent.update_layout(
    height=300, margin=dict(l=0, r=0, t=30, b=0),
    yaxis_title="$/Month",
)
st.plotly_chart(fig_rent, use_container_width=True)

# ── Charts 3 & 4 side by side ────────────────────────────────────
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Total Rent Collected")
    fig_total = go.Figure()
    fig_total.add_trace(go.Bar(
        x=month_labels, y=total_rent_collected,
        marker_color='#1B4F72', opacity=0.8,
    ))

    # GPR line (all units at market)
    gpr = sum(v['market_rent'] * v['count'] for v in unit_mix.values())
    fig_total.add_hline(y=gpr, line_dash="dot", line_color="#7F8C8D",
                        annotation_text=f"GPR: ${gpr:,.0f}")
    fig_total.update_layout(
        height=350, margin=dict(l=0, r=0, t=30, b=0),
        yaxis_title="$",
    )
    st.plotly_chart(fig_total, use_container_width=True)

with right_col:
    st.subheader("Month-over-Month Rent Growth")
    mom_growth = []
    for i in range(len(avg_rents)):
        if i == 0:
            mom_growth.append(0)
        else:
            pct = (avg_rents[i] / avg_rents[i - 1] - 1) if avg_rents[i - 1] else 0
            mom_growth.append(pct * 100)

    colors = ['#1E8449' if v >= 0 else '#C00000' for v in mom_growth]
    fig_mom = go.Figure()
    fig_mom.add_trace(go.Bar(
        x=month_labels, y=mom_growth,
        marker_color=colors, opacity=0.8,
    ))
    fig_mom.add_hline(y=0, line_color="#7F8C8D", opacity=0.3)
    fig_mom.update_layout(
        height=350, margin=dict(l=0, r=0, t=30, b=0),
        yaxis_title="% Change",
    )
    st.plotly_chart(fig_mom, use_container_width=True)

st.divider()

# ── Loss-to-Lease Analysis ───────────────────────────────────────
st.subheader("Loss-to-Lease Analysis")
st.caption("Gap between in-place rents and market rents by unit.")

C_TITLE = "#0D1B2A"
C_ALT = "#F7F9FC"
C_GREEN = "#1E8449"
C_RED = "#C00000"

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

col1, col2, col3 = st.columns(3)
col1.metric("Total Monthly LTL", f"${total_ltl:,.0f}")
col2.metric("Annual LTL Opportunity", f"${total_ltl * 12:,.0f}")
col3.metric("Avg LTL per Unit", f"${avg_ltl:,.0f}")

# Top 10 units with biggest LTL gap
top_ltl = occupied.head(15)
if len(top_ltl) > 0:
    fig_ltl = go.Figure()
    fig_ltl.add_trace(go.Bar(
        x=top_ltl['Unit'], y=top_ltl['CurrentRent'],
        name='In-Place Rent', marker_color='#1B4F72',
    ))
    fig_ltl.add_trace(go.Bar(
        x=top_ltl['Unit'], y=top_ltl['LTL'],
        name='Loss-to-Lease Gap', marker_color='#C00000', opacity=0.7,
    ))
    fig_ltl.update_layout(
        barmode='stack', height=350,
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis_title="$/Month",
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )
    st.plotly_chart(fig_ltl, use_container_width=True)

st.divider()

# ── Renovation ROI ────────────────────────────────────────────────
if os.path.exists(UI_CSV):
    st.subheader("Renovation ROI")
    st.caption("Rent lift from unit renovations.")

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

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Units Renovated", f"{len(has_current)}")
            col2.metric("Avg Rent Lift", f"${avg_lift:,.0f}/mo")
            col3.metric("Avg Lift %", f"{avg_lift_pct * 100:.1f}%")
            col4.metric("Annual Lift Total", f"${total_annual_lift:,.0f}")

            fig_reno = go.Figure()
            fig_reno.add_trace(go.Bar(
                x=has_current['Unit'], y=has_current['OrigRent'],
                name='Original Rent', marker_color='#7F8C8D',
            ))
            fig_reno.add_trace(go.Bar(
                x=has_current['Unit'], y=has_current['RentLift'],
                name='Rent Lift', marker_color='#1E8449',
            ))
            fig_reno.update_layout(
                barmode='stack', height=350,
                margin=dict(l=0, r=0, t=30, b=0),
                yaxis_title="$/Month",
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
            )
            st.plotly_chart(fig_reno, use_container_width=True)
