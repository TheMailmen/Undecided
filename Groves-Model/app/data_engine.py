"""Data extraction layer for Streamlit dashboards.

Mirrors src/engine.py's computation logic (CSV parsing, subtotals, metrics)
but returns pandas DataFrames instead of writing to openpyxl worksheets.
"""

import csv
import os
import sys

import pandas as pd

# Add src to path so we can import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import CHART_OF_ACCOUNTS, SUBTOTAL_FORMULAS


def _get_opex_lines():
    """Extract operating expense line items from CHART_OF_ACCOUNTS."""
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
    return opex_lines


def _get_opex_gl_codes():
    """Extract GL codes for operating expense line items."""
    gl_codes = set()
    in_opex = False
    for gl, acct, rtype in CHART_OF_ACCOUNTS:
        if acct == 'OPERATING EXPENSES':
            in_opex = True
            continue
        if acct == 'Total Operating Expenses':
            in_opex = False
            continue
        if in_opex and rtype == 'line' and gl:
            gl_codes.add(gl)
    return gl_codes


def load_pl_data(pl_csv_path: str, cfg: dict) -> pd.DataFrame:
    """Read P&L actuals and compute all subtotals and metrics.

    Returns a DataFrame with columns: Month, Account, Amount.
    """
    raw = {}  # {(month_str, account): amount}
    months = set()

    with open(pl_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            month = row['Month'].strip()
            account = row['Account'].strip()
            amount = float(row['Amount']) if row['Amount'] else 0
            months.add(month)
            key = (month, account)
            raw[key] = raw.get(key, 0) + amount

    months = sorted(months)
    opex_lines = _get_opex_lines()

    # Compute subtotals (same logic as engine.py lines 57-68)
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

    # Compute metrics (same logic as engine.py lines 71-84)
    for month in months:
        noi = raw.get((month, 'NET OPERATING INCOME (NOI)'), 0)
        ds = raw.get((month, 'Total Debt Service'), 0)
        egi = raw.get((month, 'EFFECTIVE GROSS INCOME (EGI)'), 0)
        opex = raw.get((month, 'Total Operating Expenses'), 0)
        cfads = raw.get((month, 'CASH FLOW AFTER DEBT SERVICE'), 0)
        ncf = raw.get((month, 'NET CASH FLOW'), 0)
        equity = cfg['total_equity']
        pp = cfg['purchase_price']

        raw[(month, 'DSCR')] = noi / ds if ds != 0 else 0
        raw[(month, 'Cap Rate')] = (noi * 12) / pp if pp != 0 else 0
        raw[(month, 'Expense Ratio')] = opex / egi if egi != 0 else 0
        raw[(month, 'Cash-on-Cash (Ann.)')] = (ncf * 12) / equity if equity != 0 else 0
        raw[(month, 'Cash-on-Cash (CFADS)')] = (cfads * 12) / equity if equity != 0 else 0

    # Convert to DataFrame
    records = [
        {'Month': month, 'Account': account, 'Amount': amount}
        for (month, account), amount in raw.items()
    ]

    df = pd.DataFrame(records)
    df['Month'] = pd.to_datetime(df['Month'])
    return df.sort_values(['Month', 'Account']).reset_index(drop=True)


def get_monthly_series(df: pd.DataFrame, account: str) -> pd.DataFrame:
    """Extract a time series for a specific account."""
    subset = df[df['Account'] == account][['Month', 'Amount']].copy()
    return subset.sort_values('Month').reset_index(drop=True)


def get_t12_totals(df: pd.DataFrame) -> dict:
    """Get trailing 12-month totals for key accounts and latest metrics."""
    last_12 = sorted(df['Month'].unique())[-12:]
    t12 = df[df['Month'].isin(last_12)]

    sum_accounts = [
        'Gross Potential Rent', 'Effective Rental Income',
        'EFFECTIVE GROSS INCOME (EGI)', 'Total Operating Expenses',
        'NET OPERATING INCOME (NOI)', 'Total Debt Service',
        'CASH FLOW AFTER DEBT SERVICE', 'Total Capital Expenditures',
        'NET CASH FLOW',
    ]

    result = {}
    for acct in sum_accounts:
        subset = t12[t12['Account'] == acct]
        result[acct] = subset['Amount'].sum()

    # Metrics: use last month's value (not sum)
    last_month = last_12[-1]
    for metric in ['DSCR', 'Cap Rate', 'Expense Ratio', 'Cash-on-Cash (CFADS)', 'Cash-on-Cash (Ann.)']:
        val = df[(df['Month'] == last_month) & (df['Account'] == metric)]['Amount']
        result[metric] = val.values[0] if len(val) > 0 else 0

    return result


def get_expense_breakdown(df: pd.DataFrame, pl_csv_path: str = None) -> pd.DataFrame:
    """Get T12 expense breakdown for charts.

    Uses GL codes to distinguish OpEx from CapEx for accounts with
    duplicate names (e.g. 'Supplies', 'Flooring').
    """
    opex_gl_codes = _get_opex_gl_codes()
    opex_names = set(_get_opex_lines())
    last_12 = sorted(df['Month'].unique())[-12:]

    # If we have the CSV path, read with GL codes for accurate filtering
    if pl_csv_path and os.path.exists(pl_csv_path):
        totals = {}
        last_12_str = {m.strftime('%Y-%m-%d') for m in last_12}
        with open(pl_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                month = row['Month'].strip()
                gl = row['GL'].strip() if row.get('GL') else ''
                account = row['Account'].strip()
                amount = float(row['Amount']) if row['Amount'] else 0
                if month in last_12_str and account in opex_names and gl in opex_gl_codes:
                    totals[account] = totals.get(account, 0) + amount
        breakdown = pd.DataFrame([
            {'Account': acct, 'Amount': amt}
            for acct, amt in totals.items()
        ])
        if len(breakdown) == 0:
            return breakdown
        return breakdown.sort_values('Amount', ascending=False).reset_index(drop=True)

    # Fallback: use DataFrame filtering (may include CapEx for shared names)
    t12 = df[(df['Month'].isin(last_12)) & (df['Account'].isin(opex_names))]
    breakdown = t12.groupby('Account')['Amount'].sum().sort_values(ascending=False)
    return breakdown.reset_index()


def load_rent_roll(rr_csv_path: str) -> pd.DataFrame:
    """Load rent roll CSV into a DataFrame."""
    return pd.read_csv(rr_csv_path)
