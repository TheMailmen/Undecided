# src/report_charts.py -- Generate charts for the quarterly investor PDF
import os
import tempfile
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Brand colors (match design.py)
NAVY = '#0D1B2A'
STEEL = '#1B4F72'
GREEN = '#1E8449'
RED = '#C00000'
GOLD = '#D4AC0D'
GRAY = '#7F8C8D'
LIGHT_GRAY = '#E8EAED'
WHITE = '#FFFFFF'


def _fmt_month(m):
    """'2025-01-01' -> 'Jan 25'"""
    try:
        dt = datetime.strptime(m, '%Y-%m-%d')
        return dt.strftime('%b %y')
    except (ValueError, TypeError):
        return str(m)


def _dollar_fmt(x, _pos=None):
    if abs(x) >= 1_000_000:
        return f'${x / 1_000_000:.1f}M'
    if abs(x) >= 1_000:
        return f'${x / 1_000:.0f}K'
    return f'${x:,.0f}'


def _setup_ax(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(LIGHT_GRAY)
    ax.spines['bottom'].set_color(LIGHT_GRAY)
    ax.tick_params(colors=GRAY, labelsize=8)
    ax.set_facecolor(WHITE)


def noi_trend_chart(data, path=None):
    """Monthly NOI + EGI trend with DSCR on secondary axis."""
    if path is None:
        path = os.path.join(tempfile.gettempdir(), 'noi_trend.png')

    months = [_fmt_month(m) for m in data['trends']['months']]
    noi = data['trends']['noi']
    egi = data['trends']['egi']
    dscr = data['trends']['dscr']

    if not months:
        return None

    fig, ax1 = plt.subplots(figsize=(7.5, 3.0), dpi=150)
    fig.patch.set_facecolor(WHITE)
    _setup_ax(ax1)

    ax1.bar(months, egi, color=LIGHT_GRAY, label='EGI', width=0.6, zorder=2)
    ax1.bar(months, noi, color=STEEL, label='NOI', width=0.6, zorder=3)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(_dollar_fmt))
    ax1.set_ylabel('Amount', fontsize=8, color=GRAY)
    ax1.legend(loc='upper left', fontsize=7, frameon=False)

    ax2 = ax1.twinx()
    ax2.plot(months, dscr, color=GREEN, marker='o', markersize=4, linewidth=2,
             label='DSCR', zorder=5)
    ax2.set_ylabel('DSCR', fontsize=8, color=GREEN)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_color(GREEN)
    ax2.tick_params(axis='y', colors=GREEN, labelsize=8)
    ax2.legend(loc='upper right', fontsize=7, frameon=False)

    plt.xticks(rotation=45, ha='right', fontsize=7)
    plt.title('Monthly NOI & EGI with DSCR', fontsize=10, color=NAVY,
              fontweight='bold', pad=10)
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight', facecolor=WHITE)
    plt.close()
    return path


def quarterly_performance_chart(data, path=None):
    """Quarterly NOI vs EGI bar chart showing quarter-over-quarter trend."""
    if path is None:
        path = os.path.join(tempfile.gettempdir(), 'quarterly_perf.png')

    qt = data.get('quarterly_trends')
    if not qt or not qt['labels']:
        return None

    labels = qt['labels']
    noi = qt['noi']
    egi = qt['egi']

    x = range(len(labels))
    bar_w = 0.35

    fig, ax = plt.subplots(figsize=(7.5, 3.0), dpi=150)
    fig.patch.set_facecolor(WHITE)
    _setup_ax(ax)

    bars_egi = ax.bar([i - bar_w / 2 for i in x], egi, bar_w,
                      color=LIGHT_GRAY, label='EGI', zorder=2)
    bars_noi = ax.bar([i + bar_w / 2 for i in x], noi, bar_w,
                      color=STEEL, label='NOI', zorder=3)

    # Value labels on NOI bars
    for bar, val in zip(bars_noi, noi):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                _dollar_fmt(val), ha='center', va='bottom',
                fontsize=7, color=NAVY, fontweight='bold')

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_dollar_fmt))
    ax.legend(fontsize=7, frameon=False)
    plt.title('Quarterly NOI vs EGI', fontsize=10, color=NAVY,
              fontweight='bold', pad=10)
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight', facecolor=WHITE)
    plt.close()
    return path


def occupancy_chart(data, path=None):
    """Occupancy rate trend line."""
    if path is None:
        path = os.path.join(tempfile.gettempdir(), 'occupancy.png')

    months_raw = data['rent_roll']['occ_trend_months']
    occ = data['rent_roll']['occ_trend']
    if not months_raw:
        return None

    # Only show last 12
    months_raw = months_raw[-12:]
    occ = occ[-12:]
    months = [_fmt_month(m) for m in months_raw]

    fig, ax = plt.subplots(figsize=(7.5, 2.5), dpi=150)
    fig.patch.set_facecolor(WHITE)
    _setup_ax(ax)

    ax.fill_between(range(len(months)), occ, alpha=0.15, color=STEEL)
    ax.plot(months, occ, color=STEEL, marker='o', markersize=5, linewidth=2.5)

    for i, v in enumerate(occ):
        ax.annotate(f'{v:.1%}', (i, v), textcoords='offset points',
                    xytext=(0, 8), ha='center', fontsize=7, color=NAVY)

    ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0, decimals=0))
    ax.set_ylim(min(occ) - 0.03, 1.02)
    plt.xticks(rotation=45, ha='right', fontsize=7)
    plt.title('Occupancy Rate Trend', fontsize=10, color=NAVY,
              fontweight='bold', pad=10)
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight', facecolor=WHITE)
    plt.close()
    return path


def cashflow_waterfall(data, path=None):
    """Waterfall chart: EGI -> OpEx -> NOI -> DS -> CFADS -> CapEx -> NCF.
    Uses quarterly totals."""
    if path is None:
        path = os.path.join(tempfile.gettempdir(), 'waterfall.png')

    s = data['snapshot']
    labels = ['EGI', 'OpEx', 'NOI', 'Debt Svc', 'CFADS', 'CapEx', 'NCF']
    values = [
        s['egi'],
        -s['opex'],
        s['noi'],
        -s['debt_service'],
        s['cfads'],
        -s['capex'],
        s['ncf'],
    ]

    bottoms = []
    running = 0
    totals = {0, 2, 4, 6}
    for i, v in enumerate(values):
        if i in totals:
            bottoms.append(0)
            running = v
        else:
            bottoms.append(running + v if v < 0 else running)
            running += v

    colors = []
    for i, v in enumerate(values):
        if i in totals:
            colors.append(STEEL if v >= 0 else RED)
        else:
            colors.append(RED if v < 0 else GREEN)

    fig, ax = plt.subplots(figsize=(7.5, 3.0), dpi=150)
    fig.patch.set_facecolor(WHITE)
    _setup_ax(ax)

    bars = ax.bar(labels, [abs(v) for v in values], bottom=bottoms,
                  color=colors, width=0.5, edgecolor=WHITE, linewidth=0.5)

    for bar, v in zip(bars, values):
        y = bar.get_y() + bar.get_height() + 200
        ax.text(bar.get_x() + bar.get_width() / 2, y,
                _dollar_fmt(abs(v)), ha='center', va='bottom',
                fontsize=7, color=NAVY, fontweight='bold')

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_dollar_fmt))
    q_label = data.get('quarter_label', 'Quarter')
    plt.title(f'Cash Flow Waterfall - {q_label}', fontsize=10, color=NAVY,
              fontweight='bold', pad=10)
    plt.tight_layout()
    plt.savefig(path, bbox_inches='tight', facecolor=WHITE)
    plt.close()
    return path


def generate_all_charts(data):
    """Generate all charts, return dict of {name: filepath}."""
    chart_dir = os.path.join(tempfile.gettempdir(), 'groves_charts')
    os.makedirs(chart_dir, exist_ok=True)

    charts = {}

    result = noi_trend_chart(data, os.path.join(chart_dir, 'noi_trend.png'))
    if result:
        charts['noi_trend'] = result

    result = quarterly_performance_chart(data, os.path.join(chart_dir, 'quarterly_perf.png'))
    if result:
        charts['quarterly_perf'] = result

    result = occupancy_chart(data, os.path.join(chart_dir, 'occupancy.png'))
    if result:
        charts['occupancy'] = result

    result = cashflow_waterfall(data, os.path.join(chart_dir, 'waterfall.png'))
    if result:
        charts['waterfall'] = result

    return charts
