# src/sheets/assumptions.py — Assumptions sheet builder
"""
Builds the 'Assumptions' tab: all property, loan, unit-mix, and TIC
inputs displayed as editable yellow cells. No formulas — pure config.
"""
from design import (
    apply_title, apply_hdr, apply_section, hide_beyond, input_cell,
    F_BOLD, F_BODY, F_LABEL, F_MUTED,
    P_ALT, P_WHITE,
    NF_DOLLAR, NF_PCT, NF_DEC2, NF_DATE,
    A_LEFT,
)

MAX_COL = 5


def build(wb, cfg):
    ws = wb.create_sheet('Assumptions')
    prop   = cfg['property']
    loan   = cfg['loan']
    tic    = cfg['tic']
    um     = cfg['unit_mix']
    val    = cfg['valuation']
    equity = cfg['total_equity']
    refi   = cfg['refi']

    apply_title(
        ws, MAX_COL,
        f"{prop['name']}  |  Model Assumptions",
        'Edit yellow cells to update property, loan, and unit-mix inputs.',
    )

    r = 3

    def sec(title):
        nonlocal r
        apply_section(ws, r, MAX_COL, accent=True)
        ws.cell(row=r, column=1).value = title
        r += 1

    def hdr(*labels):
        nonlocal r
        apply_hdr(ws, r, MAX_COL)
        for i, lbl in enumerate(labels, 1):
            ws.cell(row=r, column=i).value = lbl
        r += 1

    def row(label, value, nf=None, note=''):
        nonlocal r
        fill = P_ALT if r % 2 == 0 else P_WHITE
        for c in range(1, MAX_COL + 1):
            ws.cell(row=r, column=c).fill = fill
        ws.cell(row=r, column=1).value = label
        ws.cell(row=r, column=1).font  = F_LABEL
        ic = input_cell(ws, r, 2, value=value, nf=nf)
        if note:
            ws.cell(row=r, column=3).value = note
            ws.cell(row=r, column=3).font  = F_MUTED
        r += 1

    def static_row(label, value, note=''):
        nonlocal r
        fill = P_ALT if r % 2 == 0 else P_WHITE
        for c in range(1, MAX_COL + 1):
            ws.cell(row=r, column=c).fill = fill
        ws.cell(row=r, column=1).value = label
        ws.cell(row=r, column=1).font  = F_LABEL
        ws.cell(row=r, column=2).value = value
        ws.cell(row=r, column=2).font  = F_BODY
        if note:
            ws.cell(row=r, column=3).value = note
            ws.cell(row=r, column=3).font  = F_MUTED
        r += 1

    def blank():
        nonlocal r
        r += 1

    # ── PROPERTY ──────────────────────────────────────────────────────
    sec('PROPERTY')
    hdr('Input', 'Value', 'Notes', '', '')
    row('Property Name',   prop['name'])
    row('Address',         prop['address'])
    row('Total Units',     prop['units'],                  None, 'Residential units')
    row('Rentable SF',     prop['rentable_sf'],            NF_DEC2)
    row('Year Built',      prop['year_built'])
    row('Purchase Price',  prop['purchase_price'],         NF_DOLLAR)
    row('Purchase Date',   prop['purchase_date'])
    row('Total Equity',    equity,                         NF_DOLLAR)
    row('Structures',      prop['structures'])
    row('Garage Stalls',   prop['garages'])
    blank()

    # ── UNIT MIX ──────────────────────────────────────────────────────
    sec('UNIT MIX')
    hdr('Type', 'Count', 'SF', 'Market Rent', 'Baths')
    for unit_type, v in um.items():
        fill = P_ALT if r % 2 == 0 else P_WHITE
        for c in range(1, MAX_COL + 1):
            ws.cell(row=r, column=c).fill = fill
        ws.cell(row=r, column=1).value = unit_type
        ws.cell(row=r, column=1).font  = F_LABEL
        input_cell(ws, r, 2, value=v['count'])
        input_cell(ws, r, 3, value=v['sf'],          nf=NF_DEC2)
        input_cell(ws, r, 4, value=v['market_rent'], nf=NF_DOLLAR)
        input_cell(ws, r, 5, value=v['bath'],        nf='0.0')
        r += 1
    blank()

    # ── LOAN ──────────────────────────────────────────────────────────
    sec('LOAN')
    hdr('Input', 'Value', 'Notes', '', '')
    row('Original Amount',   loan['original_amount'],       NF_DOLLAR)
    row('Interest Rate',     loan['rate'],                  NF_PCT)
    row('Amortization',      loan['amort_years'],           None, 'Years')
    row('Loan Term',         loan['term_years'],            None, 'Years')
    row('Start Date',        loan['start_date'])
    row('Est. Current Balance', loan['est_current_balance'], NF_DOLLAR)
    row('Interest Only',     'Yes' if loan['io'] else 'No', None, 'I/O period')
    blank()

    # ── TIC OWNERSHIP ─────────────────────────────────────────────────
    sec('TIC OWNERSHIP')
    hdr('Entity', 'Ownership %', 'Equity Invested', '', '')
    for name, v in tic.items():
        fill = P_ALT if r % 2 == 0 else P_WHITE
        for c in range(1, MAX_COL + 1):
            ws.cell(row=r, column=c).fill = fill
        ws.cell(row=r, column=1).value = name
        ws.cell(row=r, column=1).font  = F_LABEL
        input_cell(ws, r, 2, value=v['pct'],    nf=NF_PCT)
        input_cell(ws, r, 3, value=v['equity'], nf=NF_DOLLAR)
        r += 1
    blank()

    # ── VALUATION ─────────────────────────────────────────────────────
    sec('VALUATION')
    hdr('Scenario', 'Value', 'Notes', '', '')
    row('BOV Low',  val['bov_low'],  NF_DOLLAR)
    row('BOV Mid',  val['bov_mid'],  NF_DOLLAR, 'Used in TIC Ownership Est. Value')
    row('BOV High', val['bov_high'], NF_DOLLAR)
    blank()

    # ── REFINANCE ASSUMPTIONS ─────────────────────────────────────────
    sec('REFINANCE ASSUMPTIONS')
    hdr('Input', 'Value', 'Notes', '', '')
    row('Projected Value',  refi['property_value'],  NF_DOLLAR)
    row('Target LTV',       refi['ltv'],             NF_PCT)
    row('New Rate',         refi['rate'],            NF_PCT)
    row('Amortization',     refi['amort_years'],     None, 'Years')
    row('Term',             refi['term_years'],      None, 'Years')
    row('Interest Only',    'Yes' if refi['io'] else 'No')
    row('NOAH Equity %',    refi['noah_equity_pct'], NF_PCT)
    row('NOAH Pref Return', refi['noah_pref_return'],NF_PCT)
    blank()

    last_row = r - 1

    ws.column_dimensions['A'].width = 24
    ws.column_dimensions['B'].width = 22
    ws.column_dimensions['C'].width = 28
    ws.column_dimensions['D'].width = 14
    ws.column_dimensions['E'].width = 12

    hide_beyond(ws, last_row, MAX_COL)
    return ws
