"""P&L Viewer — Clean tabbed view of the financial model."""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_engine import load_pl_data, get_monthly_series, get_t12_totals
from config import CHART_OF_ACCOUNTS, TOTAL_EQUITY, PROPERTY, TIC, LOAN, VALUATION
from ui.theme import inject_theme, COLORS
from ui.components import page_header, no_data_page

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

# ── Data guard ────────────────────────────────────────────────
if no_data_page("pl_actuals.csv"):
    st.stop()

# ── Design tokens (P&L-specific — kept for table rendering) ──────
C_TITLE = COLORS["primary"]
C_ACCENT = COLORS["accent"]
C_GREEN = COLORS["success"]
C_RED = COLORS["error"]
C_SUBTOTAL = "#E8EAED"
C_ALT = COLORS["row_alt"]
C_NOTE_BG = "#E0F2FE"
C_SECTION = COLORS["primary"]

# ── Data loading ───────────────────────────────────────────────────
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

# ── Helpers ────────────────────────────────────────────────────────
UNITS = st.session_state.property['units']
RSF = st.session_state.property['rentable_sf']


def _fmt_dollar(v):
    if pd.isna(v) or v == 0:
        return "-"
    if v < 0:
        return f"(${abs(v):,.0f})"
    return f"${v:,.0f}"


def _fmt_pct(v):
    if pd.isna(v) or v == 0:
        return "-"
    return f"{v * 100:.1f}%"


def _fmt_pct2(v):
    if pd.isna(v) or v == 0:
        return "-"
    return f"{v * 100:.2f}%"


def _fmt_ratio(v):
    if pd.isna(v) or v == 0:
        return "-"
    return f"{v:.2f}x"


def _row_style(rtype, account):
    """Return CSS style string for a row based on its type."""
    if rtype == 'section':
        return f"background-color:{C_SECTION};color:white;font-weight:700;font-size:0.85em;letter-spacing:0.5px;"
    if rtype == 'subtotal':
        if account in ('NET OPERATING INCOME (NOI)', 'CASH FLOW AFTER DEBT SERVICE',
                        'NET CASH FLOW', 'EFFECTIVE GROSS INCOME (EGI)'):
            return f"background-color:{C_NOTE_BG};color:{C_GREEN};font-weight:700;"
        return f"background-color:{C_SUBTOTAL};font-weight:700;"
    if rtype == 'metric':
        return f"background-color:{C_ALT};font-style:italic;"
    return ""


@st.cache_data(show_spinner=False)
def _build_pl_pivot_cached(_version, months_tuple, csv_path, total_equity, purchase_price):
    """Cached P&L pivot — keyed by data version and month list."""
    _df = load_pl_data(csv_path, {
        'total_equity': total_equity,
        'purchase_price': purchase_price,
    })
    rows = []
    for gl, account, rtype in CHART_OF_ACCOUNTS:
        if rtype == 'spacer':
            rows.append({'_type': 'spacer', 'Account': '', '_gl': ''})
            continue

        row_data = {
            '_type': rtype,
            '_gl': gl or '',
            'Account': account or '',
        }

        if rtype == 'section':
            for m in months_tuple:
                row_data[m] = ''
            rows.append(row_data)
            continue

        for m in months_tuple:
            match = _df[(_df['Account'] == account) & (_df['Month'] == pd.Timestamp(m))]
            row_data[m] = match['Amount'].sum() if len(match) > 0 else 0

        rows.append(row_data)

    return rows


def build_pl_pivot(months_list):
    """Build a P&L table following the chart of accounts order (cached)."""
    return _build_pl_pivot_cached(
        st.session_state.data_version,
        tuple(months_list),
        PL_CSV,
        cfg['total_equity'],
        cfg['purchase_price'],
    )


def render_pl_table(rows, months_list, show_t12=True, show_per_unit=True):
    """Render the P&L as a styled HTML table."""
    # Compute EGI T-12 for % of EGI
    egi_t12 = 0
    for r in rows:
        if r.get('Account') == 'EFFECTIVE GROSS INCOME (EGI)':
            egi_t12 = sum(r.get(m, 0) for m in months_list if isinstance(r.get(m, 0), (int, float)))
            break

    # Month header labels
    month_labels = []
    for m in months_list:
        dt = pd.Timestamp(m)
        month_labels.append(dt.strftime('%b %y'))

    # Build HTML
    html = ['<div style="overflow-x:auto;border:1px solid ' + COLORS["border"] + ';border-radius:12px;"><table style="border-collapse:collapse;width:100%;font-family:Inter,system-ui,sans-serif;font-size:0.82rem;">']

    # Header row
    html.append(f'<thead><tr style="background-color:{C_TITLE};color:white;font-weight:700;text-align:center;">')
    html.append('<td style="text-align:left;padding:6px 10px;min-width:220px;">Account</td>')
    for label in month_labels:
        html.append(f'<td style="padding:6px 8px;min-width:85px;">{label}</td>')
    if show_t12:
        html.append(f'<td style="padding:6px 8px;min-width:100px;border-left:2px solid {C_ACCENT};">T-12 Total</td>')
    if show_per_unit:
        html.append(f'<td style="padding:6px 8px;min-width:85px;">$/Unit</td>')
        html.append(f'<td style="padding:6px 8px;min-width:85px;">$/SF</td>')
        html.append(f'<td style="padding:6px 8px;min-width:75px;">% EGI</td>')
    html.append('</tr></thead><tbody>')

    alt = False
    for r in rows:
        rtype = r['_type']
        account = r['Account']

        if rtype == 'spacer':
            html.append('<tr style="height:8px;"><td colspan="100"></td></tr>')
            alt = False
            continue

        style = _row_style(rtype, account)
        if not style:
            bg = C_ALT if alt else "#FFFFFF"
            style = f"background-color:{bg};"
            alt = not alt

        html.append(f'<tr style="{style}">')

        # Account name
        indent = "padding-left:24px;" if rtype == 'line' else "padding-left:10px;"
        html.append(f'<td style="{indent}padding:5px 10px;white-space:nowrap;">{account}</td>')

        is_metric = rtype == 'metric'
        fmt = _fmt_pct2 if account in ('DSCR', 'Cap Rate', 'Expense Ratio',
                                        'Cash-on-Cash (CFADS)', 'Cash-on-Cash (Ann.)') else _fmt_dollar

        # Monthly values
        for m in months_list:
            val = r.get(m, '')
            if rtype == 'section' or val == '':
                html.append('<td style="text-align:right;padding:5px 8px;"></td>')
            else:
                color = ""
                if isinstance(val, (int, float)) and val < 0:
                    color = f"color:{C_RED};"
                cell_val = fmt(val) if isinstance(val, (int, float)) else str(val)
                html.append(f'<td style="text-align:right;padding:5px 8px;{color}">{cell_val}</td>')

        # T-12 total
        if show_t12:
            if rtype in ('line', 'subtotal') and not is_metric:
                t12_val = sum(r.get(m, 0) for m in months_list if isinstance(r.get(m, 0), (int, float)))
                color = f"color:{C_RED};" if t12_val < 0 else ""
                html.append(f'<td style="text-align:right;padding:5px 8px;font-weight:600;border-left:2px solid {C_ACCENT};{color}">{_fmt_dollar(t12_val)}</td>')
            elif is_metric:
                # For metrics, show the latest month value
                last_vals = [r.get(m, 0) for m in months_list if isinstance(r.get(m, 0), (int, float))]
                latest = last_vals[-1] if last_vals else 0
                html.append(f'<td style="text-align:right;padding:5px 8px;border-left:2px solid {C_ACCENT};">{fmt(latest)}</td>')
            else:
                html.append(f'<td style="border-left:2px solid {C_ACCENT};"></td>')

        # Per-unit columns
        if show_per_unit:
            if rtype in ('line', 'subtotal') and not is_metric:
                t12_val = sum(r.get(m, 0) for m in months_list if isinstance(r.get(m, 0), (int, float)))
                per_unit = t12_val / UNITS if UNITS else 0
                per_sf = t12_val / RSF if RSF else 0
                pct_egi = t12_val / egi_t12 if egi_t12 else 0
                html.append(f'<td style="text-align:right;padding:5px 8px;">{_fmt_dollar(per_unit)}</td>')
                html.append(f'<td style="text-align:right;padding:5px 8px;">{_fmt_dollar(per_sf)}</td>')
                html.append(f'<td style="text-align:right;padding:5px 8px;">{_fmt_pct(pct_egi)}</td>')
            else:
                html.append('<td></td><td></td><td></td>')

    html.append('</tbody></table></div>')
    return '\n'.join(html)


def render_exec_summary(t12):
    """Render executive summary as styled HTML."""
    prop = st.session_state.property
    pp = prop['purchase_price']
    noi = t12['NET OPERATING INCOME (NOI)']
    cfads = t12['CASH FLOW AFTER DEBT SERVICE']

    html = [f'''
    <div style="font-family:Inter,system-ui,sans-serif;border:1px solid {COLORS["border"]};border-radius:12px;overflow:hidden;">
    <table style="border-collapse:collapse;width:100%;font-size:0.82rem;">

    <tr style="background-color:{C_SECTION};color:white;font-weight:700;">
        <td colspan="4" style="padding:8px 12px;letter-spacing:0.5px;">PROPERTY OVERVIEW</td>
    </tr>
    <tr style="background-color:{C_ALT};">
        <td style="padding:5px 12px;font-weight:600;width:25%;">Property</td>
        <td style="padding:5px 12px;width:25%;">{prop['name']}</td>
        <td style="padding:5px 12px;font-weight:600;width:25%;">Address</td>
        <td style="padding:5px 12px;width:25%;">{prop['address']}</td>
    </tr>
    <tr>
        <td style="padding:5px 12px;font-weight:600;">Units</td>
        <td style="padding:5px 12px;">{prop['units']}</td>
        <td style="padding:5px 12px;font-weight:600;">Rentable SF</td>
        <td style="padding:5px 12px;">{prop['rentable_sf']:,}</td>
    </tr>
    <tr style="background-color:{C_ALT};">
        <td style="padding:5px 12px;font-weight:600;">Year Built</td>
        <td style="padding:5px 12px;">{prop['year_built']}</td>
        <td style="padding:5px 12px;font-weight:600;">Structures</td>
        <td style="padding:5px 12px;">{prop['structures']}</td>
    </tr>
    <tr>
        <td style="padding:5px 12px;font-weight:600;">Purchase Price</td>
        <td style="padding:5px 12px;">{_fmt_dollar(pp)}</td>
        <td style="padding:5px 12px;font-weight:600;">Purchase Date</td>
        <td style="padding:5px 12px;">{prop['purchase_date']}</td>
    </tr>
    <tr style="background-color:{C_ALT};">
        <td style="padding:5px 12px;font-weight:600;">Garages</td>
        <td style="padding:5px 12px;">{prop['garages']}</td>
        <td style="padding:5px 12px;font-weight:600;">Total Equity</td>
        <td style="padding:5px 12px;">{_fmt_dollar(st.session_state.total_equity)}</td>
    </tr>

    <tr style="height:12px;"><td colspan="4"></td></tr>

    <tr style="background-color:{C_SECTION};color:white;font-weight:700;">
        <td colspan="4" style="padding:8px 12px;letter-spacing:0.5px;">FINANCIAL PERFORMANCE (T-12)</td>
    </tr>''']

    fin_items = [
        ('Effective Gross Income', t12.get('EFFECTIVE GROSS INCOME (EGI)', 0), False),
        ('Total Operating Expenses', t12.get('Total Operating Expenses', 0), False),
        ('NET OPERATING INCOME', noi, True),
        ('Total Debt Service', t12.get('Total Debt Service', 0), False),
        ('CASH FLOW AFTER DEBT SVC', cfads, True),
        ('Total CapEx', t12.get('Total Capital Expenditures', 0), False),
        ('NET CASH FLOW', t12.get('NET CASH FLOW', 0), True),
    ]

    for i, (label, val, is_green) in enumerate(fin_items):
        bg = f"background-color:{C_NOTE_BG};" if is_green else (f"background-color:{C_ALT};" if i % 2 == 0 else "")
        color = f"color:{C_GREEN};font-weight:700;" if is_green else ""
        per_unit = val / UNITS if UNITS else 0
        html.append(f'''
    <tr style="{bg}">
        <td style="padding:5px 12px;font-weight:600;{color}">{label}</td>
        <td style="padding:5px 12px;text-align:right;{color}">{_fmt_dollar(val)}</td>
        <td style="padding:5px 12px;font-weight:600;color:{COLORS["muted"]};">Per Unit</td>
        <td style="padding:5px 12px;text-align:right;">{_fmt_dollar(per_unit)}</td>
    </tr>''')

    # Key Ratios
    ds = t12.get('Total Debt Service', 0)
    egi = t12.get('EFFECTIVE GROSS INCOME (EGI)', 0)
    opex = t12.get('Total Operating Expenses', 0)
    equity = st.session_state.total_equity

    dscr = noi / ds if ds else 0
    cap_rate = noi / pp if pp else 0
    exp_ratio = opex / egi if egi else 0
    coc = cfads / equity if equity else 0

    html.append(f'''
    <tr style="height:12px;"><td colspan="4"></td></tr>
    <tr style="background-color:{C_SECTION};color:white;font-weight:700;">
        <td colspan="4" style="padding:8px 12px;letter-spacing:0.5px;">KEY RATIOS</td>
    </tr>
    <tr style="background-color:{C_ALT};">
        <td style="padding:5px 12px;font-weight:600;">DSCR</td>
        <td style="padding:5px 12px;font-weight:700;">{dscr:.2f}x</td>
        <td style="padding:5px 12px;font-weight:600;">Cap Rate</td>
        <td style="padding:5px 12px;font-weight:700;">{_fmt_pct2(cap_rate)}</td>
    </tr>
    <tr>
        <td style="padding:5px 12px;font-weight:600;">Expense Ratio</td>
        <td style="padding:5px 12px;font-weight:700;">{_fmt_pct(exp_ratio)}</td>
        <td style="padding:5px 12px;font-weight:600;">Cash-on-Cash (CFADS)</td>
        <td style="padding:5px 12px;font-weight:700;">{_fmt_pct2(coc)}</td>
    </tr>''')

    # TIC Ownership
    html.append(f'''
    <tr style="height:12px;"><td colspan="4"></td></tr>
    <tr style="background-color:{C_SECTION};color:white;font-weight:700;">
        <td colspan="4" style="padding:8px 12px;letter-spacing:0.5px;">TIC OWNERSHIP</td>
    </tr>
    <tr style="background-color:{C_TITLE};color:white;font-weight:700;">
        <td style="padding:5px 12px;">Owner</td>
        <td style="padding:5px 12px;text-align:right;">Ownership %</td>
        <td style="padding:5px 12px;text-align:right;">Equity</td>
        <td style="padding:5px 12px;text-align:right;">T-12 CFADS Share</td>
    </tr>''')

    for i, (owner, info) in enumerate(st.session_state.tic.items()):
        bg = f"background-color:{C_ALT};" if i % 2 == 0 else ""
        share = cfads * info['pct']
        html.append(f'''
    <tr style="{bg}">
        <td style="padding:5px 12px;font-weight:600;">{owner}</td>
        <td style="padding:5px 12px;text-align:right;">{_fmt_pct2(info['pct'])}</td>
        <td style="padding:5px 12px;text-align:right;">{_fmt_dollar(info['equity'])}</td>
        <td style="padding:5px 12px;text-align:right;">{_fmt_dollar(share)}</td>
    </tr>''')

    html.append('</table></div>')
    return '\n'.join(html)


def render_distribution(months_list):
    """Render distribution waterfall as styled HTML."""
    # Get monthly data
    accounts_needed = [
        'NET OPERATING INCOME (NOI)', 'Total Debt Service',
        'CASH FLOW AFTER DEBT SERVICE', 'Total Capital Expenditures',
        'NET CASH FLOW', 'Asset Mgmt Fee',
    ]

    monthly = {}
    for acct in accounts_needed:
        monthly[acct] = {}
        for m in months_list:
            match = df[(df['Account'] == acct) & (df['Month'] == pd.Timestamp(m))]
            monthly[acct][m] = match['Amount'].sum() if len(match) > 0 else 0

    month_labels = [pd.Timestamp(m).strftime('%b %y') for m in months_list]

    html = [f'<div style="overflow-x:auto;border:1px solid {COLORS["border"]};border-radius:12px;"><table style="border-collapse:collapse;width:100%;font-family:Inter,system-ui,sans-serif;font-size:0.82rem;">']

    # Header
    html.append(f'<thead><tr style="background-color:{C_TITLE};color:white;font-weight:700;text-align:center;">')
    html.append('<td style="text-align:left;padding:6px 10px;min-width:220px;">Item</td>')
    for label in month_labels:
        html.append(f'<td style="padding:6px 8px;min-width:85px;">{label}</td>')
    html.append(f'<td style="padding:6px 8px;min-width:100px;border-left:2px solid {C_ACCENT};">T-12 Total</td>')
    html.append('</tr></thead><tbody>')

    def _add_row(label, acct_key, is_green=False, is_computed=None):
        bg = f"background-color:{C_NOTE_BG};" if is_green else ""
        color = f"color:{C_GREEN};font-weight:700;" if is_green else ""
        html.append(f'<tr style="{bg}">')
        html.append(f'<td style="padding:5px 10px;font-weight:600;{color}">{label}</td>')
        t12_total = 0
        for m in months_list:
            if is_computed:
                val = is_computed(m)
            else:
                val = monthly.get(acct_key, {}).get(m, 0)
            t12_total += val
            cell_color = f"color:{C_RED};" if val < 0 else ""
            html.append(f'<td style="text-align:right;padding:5px 8px;{color}{cell_color}">{_fmt_dollar(val)}</td>')
        t12_color = f"color:{C_RED};" if t12_total < 0 else ""
        html.append(f'<td style="text-align:right;padding:5px 8px;font-weight:600;border-left:2px solid {C_ACCENT};{color}{t12_color}">{_fmt_dollar(t12_total)}</td>')
        html.append('</tr>')

    # Section: Cash Flow Sources
    html.append(f'<tr style="background-color:{C_SECTION};color:white;font-weight:700;"><td colspan="{len(months_list)+2}" style="padding:8px 12px;">CASH FLOW SOURCES</td></tr>')
    _add_row('NET OPERATING INCOME (NOI)', 'NET OPERATING INCOME (NOI)', is_green=True)
    _add_row('Total Debt Service', 'Total Debt Service')
    _add_row('CASH FLOW AFTER DEBT SERVICE', 'CASH FLOW AFTER DEBT SERVICE', is_green=True)
    _add_row('Total Capital Expenditures', 'Total Capital Expenditures')
    _add_row('NET CASH FLOW', 'NET CASH FLOW', is_green=True)

    html.append(f'<tr style="height:8px;"><td colspan="{len(months_list)+2}"></td></tr>')

    # Section: Distribution Waterfall
    html.append(f'<tr style="background-color:{C_SECTION};color:white;font-weight:700;"><td colspan="{len(months_list)+2}" style="padding:8px 12px;">DISTRIBUTION WATERFALL</td></tr>')
    _add_row('Less: Asset Mgmt Fee', 'Asset Mgmt Fee')

    def free_cash(m):
        ncf = monthly.get('NET CASH FLOW', {}).get(m, 0)
        amf = monthly.get('Asset Mgmt Fee', {}).get(m, 0)
        return ncf - amf

    _add_row('FREE CASH FOR DISTRIBUTION', None, is_green=True, is_computed=free_cash)

    html.append(f'<tr style="height:8px;"><td colspan="{len(months_list)+2}"></td></tr>')

    # Owner distributions
    html.append(f'<tr style="background-color:{C_SECTION};color:white;font-weight:700;"><td colspan="{len(months_list)+2}" style="padding:8px 12px;">OWNER DISTRIBUTIONS</td></tr>')

    for owner, info in st.session_state.tic.items():
        pct = info['pct']

        def owner_share(m, p=pct):
            return free_cash(m) * p

        _add_row(f'{owner} ({pct*100:.3f}%)', None, is_computed=owner_share)

    html.append('</tbody></table></div>')
    return '\n'.join(html)


# ── Page Layout ────────────────────────────────────────────────────
page_header(
    "P&L Viewer",
    "Financial statements from acquisition to present",
    right_text=f"{st.session_state.property['name']}",
)

# Get all months and T-12 months
all_months = sorted(df['Month'].unique())
t12_months = all_months[-12:]
t12 = get_t12_totals(df)

# Format month strings for pivot
all_month_strs = [m.strftime('%Y-%m-%d') if hasattr(m, 'strftime') else str(m) for m in all_months]
t12_month_strs = [m.strftime('%Y-%m-%d') if hasattr(m, 'strftime') else str(m) for m in t12_months]

tab_summary, tab_t12, tab_full, tab_dist = st.tabs([
    "Executive Summary", "T-12 P&L", "Full P&L", "Distribution Model"
])

with tab_summary:
    st.markdown(render_exec_summary(t12), unsafe_allow_html=True)

with tab_t12:
    st.caption("Trailing 12-month P&L with totals, per-unit, per-SF, and % of EGI analysis.")
    rows = build_pl_pivot(t12_month_strs)
    st.markdown(render_pl_table(rows, t12_month_strs), unsafe_allow_html=True)

with tab_full:
    st.caption("Full monthly P&L from acquisition to present.")
    rows = build_pl_pivot(all_month_strs)
    st.markdown(render_pl_table(rows, all_month_strs), unsafe_allow_html=True)

with tab_dist:
    st.caption("Monthly cash flow waterfall from NOI to owner distributions.")
    st.markdown(render_distribution(t12_month_strs), unsafe_allow_html=True)
