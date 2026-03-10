# src/report_data.py — Python-side data engine for PDF investor report
# Unlike the Excel model (which uses formulas), the PDF report computes
# values in Python since the output is static.

import csv
from datetime import datetime, timedelta
from collections import defaultdict

import pandas as pd

from config import (
    PROPERTY, LOAN, TIC, TOTAL_EQUITY, CAPEX_BUDGET,
    VALUATION, SUBTOTAL_FORMULAS, CHART_OF_ACCOUNTS,
)


def _load_pl(path='data/pl_actuals.csv'):
    """Load P&L actuals into {(month_str, account): amount}."""
    raw = defaultdict(float)
    months = set()
    with open(path) as f:
        for row in csv.DictReader(f):
            m = row['Month'].strip()
            acct = row['Account'].strip()
            amt = float(row['Amount']) if row['Amount'] else 0
            raw[(m, acct)] += amt
            months.add(m)
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

        # Metrics
        noi = raw.get((month, 'NET OPERATING INCOME (NOI)'), 0)
        ds = raw.get((month, 'Total Debt Service'), 0)
        egi = raw.get((month, 'EFFECTIVE GROSS INCOME (EGI)'), 0)
        opex = raw.get((month, 'Total Operating Expenses'), 0)
        cfads = raw.get((month, 'CASH FLOW AFTER DEBT SERVICE'), 0)

        raw[(month, 'DSCR')] = noi / ds if ds else 0
        raw[(month, 'Cap Rate')] = (noi * 12) / PROPERTY['purchase_price'] if PROPERTY['purchase_price'] else 0
        raw[(month, 'Expense Ratio')] = opex / egi if egi else 0
        raw[(month, 'Cash-on-Cash')] = (cfads * 12) / TOTAL_EQUITY if TOTAL_EQUITY else 0


def _sum_range(raw, months, account):
    """Sum an account over a list of months."""
    return sum(raw.get((m, account), 0) for m in months)


def load_report_data(report_month=None):
    """Build all data needed for the monthly investor PDF.

    report_month: 'YYYY-MM-DD' string. Defaults to latest month in data.
    Returns a dict with all report sections.
    """
    raw, all_months = _load_pl()
    _compute_subtotals(raw, all_months)

    if report_month is None:
        report_month = all_months[-1]
    elif report_month not in all_months:
        raise ValueError(f"Month {report_month} not found in P&L data")

    idx = all_months.index(report_month)
    prior_month = all_months[idx - 1] if idx > 0 else None

    # T-12 window
    t12_start = max(0, idx - 11)
    t12_months = all_months[t12_start:idx + 1]

    # --- Current month snapshot ---
    def cur(acct):
        return raw.get((report_month, acct), 0)

    def t12(acct):
        return _sum_range(raw, t12_months, acct)

    def prior(acct):
        return raw.get((prior_month, acct), 0) if prior_month else 0

    snapshot = {
        'gross_potential_rent': cur('Gross Potential Rent'),
        'eri': cur('Effective Rental Income'),
        'other_income': cur('Total Other Income'),
        'egi': cur('EFFECTIVE GROSS INCOME (EGI)'),
        'opex': cur('Total Operating Expenses'),
        'noi': cur('NET OPERATING INCOME (NOI)'),
        'debt_service': cur('Total Debt Service'),
        'cfads': cur('CASH FLOW AFTER DEBT SERVICE'),
        'capex': cur('Total Capital Expenditures'),
        'ncf': cur('NET CASH FLOW'),
        'dscr': cur('DSCR'),
        'cap_rate': cur('Cap Rate'),
        'expense_ratio': cur('Expense Ratio'),
        'coc': cur('Cash-on-Cash'),
    }

    snapshot_prior = {
        'noi': prior('NET OPERATING INCOME (NOI)'),
        'egi': prior('EFFECTIVE GROSS INCOME (EGI)'),
        'cfads': prior('CASH FLOW AFTER DEBT SERVICE'),
        'ncf': prior('NET CASH FLOW'),
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

    # --- Monthly trends (for charts) ---
    trend_months = all_months[max(0, idx - 11):idx + 1]
    trends = {
        'months': trend_months,
        'noi': [raw.get((m, 'NET OPERATING INCOME (NOI)'), 0) for m in trend_months],
        'egi': [raw.get((m, 'EFFECTIVE GROSS INCOME (EGI)'), 0) for m in trend_months],
        'opex': [raw.get((m, 'Total Operating Expenses'), 0) for m in trend_months],
        'cfads': [raw.get((m, 'CASH FLOW AFTER DEBT SERVICE'), 0) for m in trend_months],
        'ncf': [raw.get((m, 'NET CASH FLOW'), 0) for m in trend_months],
        'dscr': [raw.get((m, 'DSCR'), 0) for m in trend_months],
    }

    # --- Rent roll ---
    rr = pd.read_csv('data/rent_roll.csv')
    month_cols = [c for c in rr.columns if c != 'Unit']
    # Find the column matching or closest to report_month
    rr_col = report_month if report_month in month_cols else month_cols[-1]
    rr_prior_col = prior_month if prior_month and prior_month in month_cols else (
        month_cols[-2] if len(month_cols) > 1 else month_cols[-1]
    )

    total_units = len(rr)
    occupied = (rr[rr_col] > 0).sum()
    vacant = total_units - occupied
    occupancy = occupied / total_units if total_units else 0
    total_rent = rr[rr_col].sum()
    avg_rent = total_rent / occupied if occupied else 0

    # Occupancy trend
    occ_trend = []
    for col in month_cols:
        occ = (rr[col] > 0).sum() / total_units if total_units else 0
        occ_trend.append(occ)

    rent_roll = {
        'total_units': total_units,
        'occupied': int(occupied),
        'vacant': int(vacant),
        'occupancy': occupancy,
        'total_rent': total_rent,
        'avg_rent': avg_rent,
        'occ_trend_months': month_cols,
        'occ_trend': occ_trend,
    }

    # --- Unit improvements ---
    ui = pd.read_csv('data/unit_improvements.csv')
    renovated = len(ui[ui['Condition'] == 'Renovated'])
    total_reno = len(ui)
    avg_lift = 0
    if 'OrigRent' in ui.columns and 'CurrRent' in ui.columns:
        completed = ui[(ui['Condition'] == 'Renovated') & (ui['CurrRent'].notna()) & (ui['CurrRent'] != '')]
        if len(completed) > 0:
            completed_clean = completed.copy()
            completed_clean['OrigRent'] = pd.to_numeric(completed_clean['OrigRent'], errors='coerce')
            completed_clean['CurrRent'] = pd.to_numeric(completed_clean['CurrRent'], errors='coerce')
            valid = completed_clean.dropna(subset=['OrigRent', 'CurrRent'])
            if len(valid) > 0:
                avg_lift = (valid['CurrRent'] - valid['OrigRent']).mean()

    renovations = {
        'completed': renovated,
        'total_planned': total_reno,
        'avg_rent_lift': avg_lift,
        'budget': CAPEX_BUDGET,
        'spent': t12('Total Capital Expenditures'),
    }

    # --- TIC distributions ---
    tic_dist = {}
    monthly_cfads = snapshot['cfads']
    for owner, info in TIC.items():
        tic_dist[owner] = {
            'pct': info['pct'],
            'equity': info['equity'],
            'monthly_share': monthly_cfads * info['pct'],
            't12_share': t12_totals['cfads'] * info['pct'],
            'coc': (t12_totals['cfads'] * info['pct']) / info['equity'] if info['equity'] else 0,
        }

    # --- Escrow ---
    esc = pd.read_csv('data/escrow_activity.csv')
    escrow = {}
    for name in ['Real Estate Taxes', 'Property Insurance', 'Capital Reserves']:
        sub = esc[esc['EscrowName'] == name]
        escrow[name] = {
            'total_deposits': sub['Deposits'].sum(),
            'total_payments': sub['Payments'].sum(),
            'balance': sub['Deposits'].sum() - sub['Payments'].sum(),
        }

    report_dt = datetime.strptime(report_month, '%Y-%m-%d')

    return {
        'report_month': report_month,
        'report_date': report_dt,
        'report_label': report_dt.strftime('%B %Y'),
        'property': PROPERTY,
        'loan': LOAN,
        'valuation': VALUATION,
        'snapshot': snapshot,
        'snapshot_prior': snapshot_prior,
        't12': t12_totals,
        'trends': trends,
        'rent_roll': rent_roll,
        'renovations': renovations,
        'tic': tic_dist,
        'escrow': escrow,
        't12_months': len(t12_months),
    }
