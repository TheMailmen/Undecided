# src/sheets/how_to_use.py — How To Use sheet builder
"""
Builds the 'How To Use' tab: property overview, sheet navigation guide,
data update instructions, and key metrics reference.
"""
from design import (
    apply_title, apply_hdr, apply_section, hide_beyond,
    F_BOLD, F_BODY, F_MUTED, F_NOTE,
    P_ALT, P_WHITE,
    A_LEFT,
)

MAX_COL = 5

_SHEET_NAV = [
    ('How To Use',        'This sheet — model overview and navigation guide',         'As needed'),
    ('Executive Summary', 'One-page KPI dashboard: NOI, CFADS, DSCR, CoC, occupancy', 'Monthly'),
    ('Assumptions',       'Property, loan, and unit-mix inputs — yellow editable cells','As needed'),
    ('Full P&L',          '17-month monthly actuals (Aug 2024 – Dec 2025)',             'Monthly'),
    ('T12_PL',            'Trailing 12-month P&L with T12 total column',               'Monthly'),
    ('Trailing Analysis', 'Period-over-period variance: prior month / 3-mo / 12-mo',   'Monthly'),
    ('Distribution_Model','TIC investor distribution waterfall and payout schedule',    'Monthly'),
    ('TIC Ownership',     'Ownership percentages, equity, and return metrics by entity','As needed'),
    ('RR Summary',        'Rent roll statistics: occupied units, avg rent, vacancy',    'Monthly'),
    ('RR Input',          'Unit-by-unit rent roll detail — monthly snapshots',          'Monthly'),
    ('Unit Improvements', 'Renovation scope, cost, and timeline by unit',               'As needed'),
    ('Escrow_Summary',    'Tax, insurance, and reserve account balances over time',     'Monthly'),
    ('Escrow_Input',      'Escrow transaction detail (deposits and draws)',              'Monthly'),
    ('CapEx Profile',     'Capital expenditure profiling by building system and age',   'Annual'),
    ('Refi Stress Test',  'Refinance scenarios at varying rates, LTVs, and values',     'As needed'),
    ('Rent Comps',        'Market rent comparables from nearby properties',             'Quarterly'),
]

_METRICS = [
    ('NOI',       'Net Operating Income',         'EGI minus all operating expenses'),
    ('EGI',       'Effective Gross Income',        'Gross Potential Rent + Other Income + adjustments'),
    ('ERI',       'Effective Rental Income',       'GPR adjusted for vacancy, delinquency, concessions'),
    ('DSCR',      'Debt Service Coverage Ratio',  'NOI ÷ Total Debt Service  (target ≥ 1.25×)'),
    ('Cap Rate',  'Capitalization Rate',           'Annualized NOI ÷ Purchase Price'),
    ('CFADS',     'Cash Flow After Debt Service',  'NOI minus all debt service payments'),
    ('NCF',       'Net Cash Flow',                 'CFADS minus capital expenditures'),
    ('CoC',       'Cash-on-Cash Return',           'Annualized NCF ÷ Total Equity Invested'),
    ('GPR',       'Gross Potential Rent',          'Max rent if all units occupied at market rate'),
    ('T12 / TTM', 'Trailing Twelve Months',        'Sum of the most recent 12 calendar months'),
    ('TIC',       'Tenants in Common',             'Co-ownership structure used for this property'),
    ('CFADS CoC', 'CFADS Cash-on-Cash',            'Annualized CFADS ÷ Total Equity (pre-capex CoC)'),
]


def build(wb, cfg):
    ws = wb.create_sheet('How To Use')
    prop   = cfg['property']
    loan   = cfg['loan']
    equity = cfg['total_equity']

    apply_title(
        ws, MAX_COL,
        f"{prop['name']}  |  Model Navigation Guide",
        f"{prop['address']}  |  {prop['units']} Units  |  Built {prop['year_built']}",
    )

    r = 3  # next available row (rows 1-2 = title/subtitle)

    # ── helpers ──────────────────────────────────────────────────────

    def sec(title):
        nonlocal r
        apply_section(ws, r, MAX_COL, accent=True)
        ws.cell(row=r, column=2).value = title
        r += 1

    def hdr(*labels):
        nonlocal r
        apply_hdr(ws, r, MAX_COL)
        for i, lbl in enumerate(labels, 1):
            ws.cell(row=r, column=i).value = lbl
        r += 1

    def row(b='', c='', d='', e='', a='', bold=False):
        nonlocal r
        fill = P_ALT if r % 2 == 0 else P_WHITE
        for col in range(1, MAX_COL + 1):
            ws.cell(row=r, column=col).fill = fill
        ws.cell(row=r, column=1).value = a
        ws.cell(row=r, column=1).font  = F_MUTED
        ws.cell(row=r, column=2).value = b
        ws.cell(row=r, column=2).font  = F_BOLD if bold else F_BODY
        ws.cell(row=r, column=3).value = c
        ws.cell(row=r, column=3).font  = F_BODY
        ws.cell(row=r, column=4).value = d
        ws.cell(row=r, column=4).font  = F_MUTED
        ws.cell(row=r, column=5).value = e
        ws.cell(row=r, column=5).font  = F_MUTED
        r += 1

    def blank():
        nonlocal r
        r += 1

    # ── PROPERTY OVERVIEW ────────────────────────────────────────────
    sec('PROPERTY OVERVIEW')
    hdr('', 'Detail', 'Value', 'Notes', '')
    row('Property Name',  prop['name'],                                    bold=True)
    row('Address',        prop['address'])
    row('Total Units',    str(prop['units']),                              '60 × 1BR | 60 × 2BR')
    row('Rentable SF',    f"{prop['rentable_sf']:,} sq ft")
    row('Year Built',     str(prop['year_built']))
    row('Structures',     prop['structures'])
    row('Garages',        f"{prop['garages']} stalls")
    row('Purchase Price', f"${prop['purchase_price']:,.0f}",               str(prop['purchase_date']))
    row('Total Equity',   f"${equity:,.0f}")
    row('Loan Amount',    f"${loan['original_amount']:,.0f}",
        f"{loan['rate']*100:.2f}%  |  {loan['amort_years']}-yr amort")
    row('Loan Balance',   f"${loan['est_current_balance']:,.0f}",          'Estimated current')
    blank()

    # ── SHEET NAVIGATION ─────────────────────────────────────────────
    sec('SHEET NAVIGATION')
    hdr('', 'Sheet Tab', 'Description', 'Update Frequency', '')
    for tab, desc, freq in _SHEET_NAV:
        row(tab, desc, freq, bold=True)
    blank()

    # ── HOW TO UPDATE DATA ───────────────────────────────────────────
    sec('HOW TO UPDATE DATA MONTHLY')
    hdr('Step', 'Action', 'File', 'Column Format', '')
    row('1', 'Export P&L from property management system',
        'data/pl_actuals.csv',     'Month, GL, Account, Amount', bold=True)
    row('2', 'Export end-of-month rent roll snapshot',
        'data/rent_roll.csv',      'Month, Unit, FloorPlan, MarketRent, ActualRent, Occupied')
    row('3', 'Export escrow / reserve transactions',
        'data/escrow_activity.csv','Month, Account, Type, Amount')
    row('4', 'Record any unit renovation activity',
        'data/unit_improvements.csv','Unit, StartDate, EndDate, Scope, Cost')
    row('5', 'Update CapEx profile if systems assessed',
        'data/capex_profile.csv',  'System, Age, Condition, EstReplCost, Priority')
    row('6', 'Run build:  python src/build.py',
        'Regenerates all sheets',  'output/Groves_Investor_Model.xlsx')
    row('7', 'Validate:  python tests/test_model.py <path>',
        'Checks formulas',         'Should report 0 issues')
    blank()
    row('CSV RULES', '', '', '', bold=True)
    row('Date format',   'YYYY-MM-DD  (e.g. 2025-01-01)')
    row('Header row',    'Row 1 must be the header — no blank rows above')
    row('Amounts',       'Positive = income   |   Negative = expense / adjustment / vacancy')
    row('Account names', 'Must match Chart of Accounts exactly (case-sensitive)')
    blank()

    # ── KEY METRICS REFERENCE ────────────────────────────────────────
    sec('KEY METRICS REFERENCE')
    hdr('', 'Abbreviation', 'Full Name', 'Description', '')
    for abbr, full, desc in _METRICS:
        row(abbr, full, desc)
    blank()

    # ── CHART OF ACCOUNTS (line items only) ──────────────────────────
    sec('CHART OF ACCOUNTS — LINE ITEMS')
    hdr('GL Code', 'Account Name', 'Category', '', '')
    coa = cfg['coa']
    current_section = ''
    for gl, acct, rtype in coa:
        if rtype == 'spacer' or acct is None:
            continue
        if rtype == 'section':
            current_section = acct
            continue
        if rtype == 'subtotal':
            continue
        # line and metric rows only
        row(acct, current_section, '', '', a=gl or '')
    blank()

    # ── FORMULA NOTES ────────────────────────────────────────────────
    sec('FORMULA NOTES')
    row('All data cells contain Excel SUMIFS formulas — never edit them directly')
    row('Yellow cells are the only manual inputs (Assumptions sheet)')
    row('Green rows (NOI, CFADS, NCF) are key profitability metrics')
    row('T12 TTM column always sums the 12 most recent months in the dataset')
    row('Cross-sheet references update automatically when build.py is re-run')
    blank()

    last_row = r - 1

    # ── Column widths ─────────────────────────────────────────────────
    ws.column_dimensions['A'].width = 9
    ws.column_dimensions['B'].width = 32
    ws.column_dimensions['C'].width = 42
    ws.column_dimensions['D'].width = 30
    ws.column_dimensions['E'].width = 14

    hide_beyond(ws, last_row, MAX_COL)
    return ws
