# src/report_data.py -- Python-side data engine for PDF quarterly investor report
# Computes values in Python since the PDF output is static (not formula-driven).

import csv
import os
from datetime import datetime
from collections import defaultdict

import pandas as pd

from config import (
    PROPERTY, LOAN, TIC, TOTAL_EQUITY, CAPEX_BUDGET,
    VALUATION, SUBTOTAL_FORMULAS, CHART_OF_ACCOUNTS,
)

_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
_DATA_DIR = os.path.join(_BASE_DIR, 'data')


def _data_path(filename):
    return os.path.join(_DATA_DIR, filename)


def _safe_div(num, den, default=0):
    """Safe division -- returns default when denominator is zero or None."""
    if not den:
        return default
    return num / den


# ---------------------------------------------------------------------------
# Quarter helpers
# ---------------------------------------------------------------------------

def _quarter_of(month_str):
    """Return (year, quarter_num) for a 'YYYY-MM-DD' month string."""
    dt = datetime.strptime(month_str, '%Y-%m-%d')
    return dt.year, (dt.month - 1) // 3 + 1


def _quarter_label(year, qnum):
    """'Q4 2025' style label."""
    return f'Q{qnum} {year}'


def _quarter_months(all_months, year, qnum):
    """Return the subset of all_months that fall in the given quarter."""
    return [m for m in all_months if _quarter_of(m) == (year, qnum)]


def _available_quarters(all_months):
    """Return sorted list of (year, qnum) tuples present in data."""
    seen = []
    seen_set = set()
    for m in all_months:
        q = _quarter_of(m)
        if q not in seen_set:
            seen.append(q)
            seen_set.add(q)
    return seen


# ---------------------------------------------------------------------------
# P&L loading and subtotals
# ---------------------------------------------------------------------------

def _load_pl(path=None):
    """Load P&L actuals into {(month_str, account): amount}."""
    if path is None:
        path = _data_path('pl_actuals.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"P&L data file not found: {path}")
    raw = defaultdict(float)
    months = set()
    with open(path) as f:
        for row in csv.DictReader(f):
            m = row['Month'].strip()
            acct = row['Account'].strip()
            amt = float(row['Amount']) if row['Amount'] else 0
            raw[(m, acct)] += amt
            months.add(m)
    if not months:
        raise ValueError("P&L CSV is empty -- no month data found")
    return raw, sorted(months)


def _compute_subtotals(raw, months):
    """Add computed subtotals and metrics to raw dict (mutates in place)."""
    opex_lines = []
    in_opex = False
    for _gl, acct, rtype in CHART_OF_ACCOUNTS:
        if acct == 'OPERATING EXPENSES':
            in_opex = True
            continue
        if acct == 'Total Operating Expenses':
            in_opex = False
            continue
        if in_opex and rtype == 'line':
            opex_lines.append(acct)

    for month in months:
        for sub_name, components in SUBTOTAL_FORMULAS.items():
            if components == 'SUM_RANGE':
                total = sum(raw.get((month, line), 0) for line in opex_lines)
            else:
                total = 0
                for comp in components:
                    if comp.startswith('-'):
                        total -= raw.get((month, comp[1:]), 0)
                    else:
                        total += raw.get((month, comp), 0)
            raw[(month, sub_name)] = total

        noi = raw.get((month, 'NET OPERATING INCOME (NOI)'), 0)
        ds = raw.get((month, 'Total Debt Service'), 0)
        egi = raw.get((month, 'EFFECTIVE GROSS INCOME (EGI)'), 0)
        opex = raw.get((month, 'Total Operating Expenses'), 0)
        cfads = raw.get((month, 'CASH FLOW AFTER DEBT SERVICE'), 0)

        raw[(month, 'DSCR')] = _safe_div(noi, ds)
        raw[(month, 'Cap Rate')] = _safe_div(noi * 12, PROPERTY['purchase_price'])
        raw[(month, 'Expense Ratio')] = _safe_div(opex, egi)
        raw[(month, 'Cash-on-Cash')] = _safe_div(cfads * 12, TOTAL_EQUITY)


def _sum_range(raw, months, account):
    """Sum an account over a list of months."""
    return sum(raw.get((m, account), 0) for m in months)


def _avg_range(raw, months, account):
    """Average an account over months (for ratio-type metrics like DSCR)."""
    vals = [raw.get((m, account), 0) for m in months]
    return _safe_div(sum(vals), len(vals))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def load_report_data(report_quarter=None):
    """Build all data needed for the quarterly investor PDF.

    report_quarter: 'Q4 2025' string, or (year, qnum) tuple.
                    Defaults to the latest quarter with data.
    Returns a dict with all report sections.
    """
    raw, all_months = _load_pl()
    _compute_subtotals(raw, all_months)

    quarters = _available_quarters(all_months)
    if not quarters:
        raise ValueError("No quarters found in data")

    # Resolve which quarter to report on
    if report_quarter is None:
        year, qnum = quarters[-1]
    elif isinstance(report_quarter, tuple):
        year, qnum = report_quarter
    elif isinstance(report_quarter, str):
        # Parse 'Q4 2025' format
        parts = report_quarter.strip().split()
        qnum = int(parts[0][1:])
        year = int(parts[1])
    else:
        raise ValueError(f"Unrecognized report_quarter format: {report_quarter}")

    if (year, qnum) not in set(quarters):
        raise ValueError(
            f"Quarter Q{qnum} {year} not found in data. "
            f"Available: {[_quarter_label(*q) for q in quarters]}"
        )

    q_months = _quarter_months(all_months, year, qnum)
    q_end_month = q_months[-1]  # Last month of the quarter

    # Prior quarter
    q_idx = quarters.index((year, qnum))
    prior_q = quarters[q_idx - 1] if q_idx > 0 else None
    prior_q_months = _quarter_months(all_months, *prior_q) if prior_q else []

    # T-12 window ending at the quarter's last month
    end_idx = all_months.index(q_end_month)
    t12_start = max(0, end_idx - 11)
    t12_months = all_months[t12_start:end_idx + 1]

    # --- Quarter aggregation helpers ---
    def qsum(acct):
        return _sum_range(raw, q_months, acct)

    def qavg_metric(acct):
        return _avg_range(raw, q_months, acct)

    def t12(acct):
        return _sum_range(raw, t12_months, acct)

    def prior_qsum(acct):
        return _sum_range(raw, prior_q_months, acct) if prior_q_months else 0

    # --- Quarterly snapshot (summed for the quarter) ---
    snapshot = {
        'gross_potential_rent': qsum('Gross Potential Rent'),
        'eri': qsum('Effective Rental Income'),
        'other_income': qsum('Total Other Income'),
        'egi': qsum('EFFECTIVE GROSS INCOME (EGI)'),
        'opex': qsum('Total Operating Expenses'),
        'noi': qsum('NET OPERATING INCOME (NOI)'),
        'debt_service': qsum('Total Debt Service'),
        'cfads': qsum('CASH FLOW AFTER DEBT SERVICE'),
        'capex': qsum('Total Capital Expenditures'),
        'ncf': qsum('NET CASH FLOW'),
        # Metrics: average the monthly ratios across the quarter
        'dscr': qavg_metric('DSCR'),
        'cap_rate': qavg_metric('Cap Rate'),
        'expense_ratio': qavg_metric('Expense Ratio'),
        'coc': qavg_metric('Cash-on-Cash'),
        'num_months': len(q_months),
    }

    snapshot_prior = {
        'noi': prior_qsum('NET OPERATING INCOME (NOI)'),
        'egi': prior_qsum('EFFECTIVE GROSS INCOME (EGI)'),
        'cfads': prior_qsum('CASH FLOW AFTER DEBT SERVICE'),
        'ncf': prior_qsum('NET CASH FLOW'),
    }

    t12_totals = {
        'eri': t12('Effective Rental Income'),
        'other_income': t12('Total Other Income'),
        'egi': t12('EFFECTIVE GROSS INCOME (EGI)'),
        'opex': t12('Total Operating Expenses'),
        'noi': t12('NET OPERATING INCOME (NOI)'),
        'debt_service': t12('Total Debt Service'),
        'cfads': t12('CASH FLOW AFTER DEBT SERVICE'),
        'capex': t12('Total Capital Expenditures'),
        'ncf': t12('NET CASH FLOW'),
    }

    # --- Monthly trends (for charts -- show all months up to quarter end) ---
    trend_months = all_months[max(0, end_idx - 11):end_idx + 1]
    trends = {
        'months': trend_months,
        'noi': [raw.get((m, 'NET OPERATING INCOME (NOI)'), 0) for m in trend_months],
        'egi': [raw.get((m, 'EFFECTIVE GROSS INCOME (EGI)'), 0) for m in trend_months],
        'opex': [raw.get((m, 'Total Operating Expenses'), 0) for m in trend_months],
        'cfads': [raw.get((m, 'CASH FLOW AFTER DEBT SERVICE'), 0) for m in trend_months],
        'ncf': [raw.get((m, 'NET CASH FLOW'), 0) for m in trend_months],
        'dscr': [raw.get((m, 'DSCR'), 0) for m in trend_months],
    }

    # --- Quarterly trend (aggregate per quarter for bar chart) ---
    q_trend_labels = []
    q_trend_noi = []
    q_trend_egi = []
    q_trend_cfads = []
    for yq in quarters:
        qm = _quarter_months(all_months, *yq)
        q_trend_labels.append(_quarter_label(*yq))
        q_trend_noi.append(_sum_range(raw, qm, 'NET OPERATING INCOME (NOI)'))
        q_trend_egi.append(_sum_range(raw, qm, 'EFFECTIVE GROSS INCOME (EGI)'))
        q_trend_cfads.append(_sum_range(raw, qm, 'CASH FLOW AFTER DEBT SERVICE'))

    quarterly_trends = {
        'labels': q_trend_labels,
        'noi': q_trend_noi,
        'egi': q_trend_egi,
        'cfads': q_trend_cfads,
    }

    # --- Month-by-month detail for the quarter (for per-month table) ---
    month_detail = []
    for m in q_months:
        dt = datetime.strptime(m, '%Y-%m-%d')
        month_detail.append({
            'label': dt.strftime('%b %Y'),
            'egi': raw.get((m, 'EFFECTIVE GROSS INCOME (EGI)'), 0),
            'opex': raw.get((m, 'Total Operating Expenses'), 0),
            'noi': raw.get((m, 'NET OPERATING INCOME (NOI)'), 0),
            'debt_service': raw.get((m, 'Total Debt Service'), 0),
            'cfads': raw.get((m, 'CASH FLOW AFTER DEBT SERVICE'), 0),
            'ncf': raw.get((m, 'NET CASH FLOW'), 0),
        })

    # --- Rent roll (use last month of quarter) ---
    rr_path = _data_path('rent_roll.csv')
    if os.path.exists(rr_path):
        rr = pd.read_csv(rr_path)
        month_cols = [c for c in rr.columns if c != 'Unit']
        rr_col = q_end_month if q_end_month in month_cols else month_cols[-1]

        total_units = len(rr)
        occupied = int((rr[rr_col] > 0).sum())
        vacant = total_units - occupied
        occupancy = _safe_div(occupied, total_units)
        total_rent = float(rr[rr_col].sum())
        avg_rent = _safe_div(total_rent, occupied)

        occ_trend = []
        for col in month_cols:
            occ = _safe_div((rr[col] > 0).sum(), total_units)
            occ_trend.append(occ)

        rent_roll = {
            'total_units': total_units,
            'occupied': occupied,
            'vacant': vacant,
            'occupancy': occupancy,
            'total_rent': total_rent,
            'avg_rent': avg_rent,
            'occ_trend_months': month_cols,
            'occ_trend': occ_trend,
        }
    else:
        rent_roll = {
            'total_units': PROPERTY['units'],
            'occupied': 0, 'vacant': PROPERTY['units'],
            'occupancy': 0, 'total_rent': 0, 'avg_rent': 0,
            'occ_trend_months': [], 'occ_trend': [],
        }

    # --- Unit improvements ---
    ui_path = _data_path('unit_improvements.csv')
    if os.path.exists(ui_path):
        ui = pd.read_csv(ui_path)
        renovated = int(len(ui[ui['Condition'] == 'Renovated']))
        total_reno = len(ui)
        avg_lift = 0
        if 'OrigRent' in ui.columns and 'CurrRent' in ui.columns:
            completed = ui[
                (ui['Condition'] == 'Renovated')
                & (ui['CurrRent'].notna())
                & (ui['CurrRent'] != '')
            ]
            if len(completed) > 0:
                cc = completed.copy()
                cc['OrigRent'] = pd.to_numeric(cc['OrigRent'], errors='coerce')
                cc['CurrRent'] = pd.to_numeric(cc['CurrRent'], errors='coerce')
                valid = cc.dropna(subset=['OrigRent', 'CurrRent'])
                if len(valid) > 0:
                    avg_lift = float((valid['CurrRent'] - valid['OrigRent']).mean())
    else:
        renovated, total_reno, avg_lift = 0, 0, 0

    renovations = {
        'completed': renovated,
        'total_planned': total_reno,
        'avg_rent_lift': avg_lift,
        'budget': CAPEX_BUDGET,
        'spent': t12('Total Capital Expenditures'),
    }

    # --- TIC distributions (quarterly) ---
    tic_dist = {}
    q_cfads = snapshot['cfads']
    for owner, info in TIC.items():
        tic_dist[owner] = {
            'pct': info['pct'],
            'equity': info['equity'],
            'quarterly_share': q_cfads * info['pct'],
            't12_share': t12_totals['cfads'] * info['pct'],
            'coc': _safe_div(t12_totals['cfads'] * info['pct'], info['equity']),
        }

    # --- Escrow ---
    esc_path = _data_path('escrow_activity.csv')
    escrow = {}
    if os.path.exists(esc_path):
        esc = pd.read_csv(esc_path)
        for name in ['Real Estate Taxes', 'Property Insurance', 'Capital Reserves']:
            sub = esc[esc['EscrowName'] == name]
            escrow[name] = {
                'total_deposits': float(sub['Deposits'].sum()),
                'total_payments': float(sub['Payments'].sum()),
                'balance': float(sub['Deposits'].sum() - sub['Payments'].sum()),
            }
    else:
        for name in ['Real Estate Taxes', 'Property Insurance', 'Capital Reserves']:
            escrow[name] = {'total_deposits': 0, 'total_payments': 0, 'balance': 0}

    # --- Build return dict ---
    q_label = _quarter_label(year, qnum)
    prior_label = _quarter_label(*prior_q) if prior_q else None

    return {
        'report_quarter': (year, qnum),
        'quarter_label': q_label,
        'quarter_months': q_months,
        'prior_quarter_label': prior_label,
        'report_date': datetime.strptime(q_end_month, '%Y-%m-%d'),
        'report_label': q_label,
        'property': PROPERTY,
        'loan': LOAN,
        'valuation': VALUATION,
        'snapshot': snapshot,
        'snapshot_prior': snapshot_prior,
        't12': t12_totals,
        'trends': trends,
        'quarterly_trends': quarterly_trends,
        'month_detail': month_detail,
        'rent_roll': rent_roll,
        'renovations': renovations,
        'tic': tic_dist,
        'escrow': escrow,
        't12_months': len(t12_months),
    }
