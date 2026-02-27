# src/engine.py — Builds the qPL_Fact engine table from raw P&L data
import csv
from datetime import datetime


def build_qpl_fact(wb, pl_csv_path, config):
    """Read P&L actuals from CSV and write qPL_Fact hidden sheet.
    
    CSV format: Month,GL,Account,Amount
    
    This also computes subtotal rows (ERI, EGI, NOI, CFADS, etc.)
    so downstream SUMIFS can reference them directly.
    """
    ws = wb.create_sheet('qPL_Fact')
    ws.sheet_state = 'hidden'
    
    # Headers
    ws['A1'] = 'Month_Start'
    ws['B1'] = 'GL'
    ws['C1'] = 'Account'
    ws['D1'] = 'NetAmount'
    
    # Read raw data
    raw = {}  # {(month, account): amount}
    months = set()
    accounts = set()
    
    with open(pl_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            month = row['Month'].strip()
            account = row['Account'].strip()
            amount = float(row['Amount']) if row['Amount'] else 0
            months.add(month)
            accounts.add(account)
            key = (month, account)
            raw[key] = raw.get(key, 0) + amount
    
    months = sorted(months)
    
    # Compute subtotals per month
    from config import SUBTOTAL_FORMULAS, CHART_OF_ACCOUNTS
    
    # Get OpEx line items for SUM_RANGE
    opex_lines = []
    in_opex = False
    for gl, acct, rtype in CHART_OF_ACCOUNTS:
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
    
    # Also compute metrics
    for month in months:
        noi = raw.get((month, 'NET OPERATING INCOME (NOI)'), 0)
        ds = raw.get((month, 'Total Debt Service'), 0)
        egi = raw.get((month, 'EFFECTIVE GROSS INCOME (EGI)'), 0)
        opex = raw.get((month, 'Total Operating Expenses'), 0)
        cfads = raw.get((month, 'CASH FLOW AFTER DEBT SERVICE'), 0)
        
        ncf   = raw.get((month, 'NET CASH FLOW'), 0)
        equity = config['total_equity']
        raw[(month, 'DSCR')]                  = noi / ds if ds != 0 else 0
        raw[(month, 'Cap Rate')]              = (noi * 12) / config['purchase_price'] if config['purchase_price'] != 0 else 0
        raw[(month, 'Expense Ratio')]         = opex / egi if egi != 0 else 0
        raw[(month, 'Cash-on-Cash (Ann.)')]   = (ncf * 12) / equity if equity != 0 else 0
        raw[(month, 'Cash-on-Cash (CFADS)')]  = (cfads * 12) / equity if equity != 0 else 0
    
    # Write all rows
    r = 2
    for month in months:
        for key in sorted(raw.keys()):
            if key[0] == month:
                m, acct = key
                amt = raw[key]
                # Parse month to date
                if isinstance(m, str):
                    dt = datetime.strptime(m, '%Y-%m-%d')
                else:
                    dt = m
                ws.cell(row=r, column=1, value=dt)
                ws.cell(row=r, column=2, value='')  # GL (optional for subtotals)
                ws.cell(row=r, column=3, value=acct)
                ws.cell(row=r, column=4, value=amt)
                r += 1
    
    return ws, r - 1  # return sheet and row count
