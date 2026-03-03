# src/sheets/assumptions.py — Property assumptions and configuration
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from design import (apply_title, apply_hdr, apply_section, apply_subtotal,
                     set_col_widths, hide_beyond, input_cell,
                     F_BODY, F_BOLD, F_LABEL, F_MUTED,
                     P_ALT, P_WHITE, NF_DOLLAR, NF_PCT, NF_PCT2, NF_NUM, NF_DEC2, A_LEFT)


def build(wb, cfg):
    ws = wb.create_sheet('Assumptions')
    max_col = 5

    apply_title(ws, max_col,
                'ASSUMPTIONS',
                'Property details, loan terms, and ownership. Yellow cells are editable inputs.')

    set_col_widths(ws, {'A': 5, 'B': 35, 'C': 18, 'D': 18, 'E': 18})

    prop = cfg['property']
    loan = cfg['loan']
    tic = cfg['tic']
    umix = cfg['unit_mix']
    val = cfg['valuation']
    refi = cfg['refi']

    row = 3

    # ── PROPERTY DETAILS ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'PROPERTY DETAILS'
    row += 1

    details = [
        ('Property Name', prop['name'], None),
        ('Address', prop['address'], None),
        ('Total Units', prop['units'], NF_NUM),
        ('Rentable SF', prop['rentable_sf'], NF_NUM),
        ('Year Built', prop['year_built'], None),
        ('Purchase Price', prop['purchase_price'], NF_DOLLAR),
        ('Purchase Date', prop['purchase_date'], None),
        ('Structures', prop['structures'], None),
        ('Garages', prop['garages'], NF_NUM),
    ]
    for label, value, nf in details:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = label
        ws.cell(row=row, column=2).font = F_LABEL
        input_cell(ws, row, 3, value, nf)
        row += 1

    row += 1  # spacer

    # ── UNIT MIX ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'UNIT MIX'
    row += 1

    # Sub-headers
    ws.cell(row=row, column=2).value = 'Type'
    ws.cell(row=row, column=3).value = 'Count'
    ws.cell(row=row, column=4).value = 'Avg SF'
    ws.cell(row=row, column=5).value = 'Market Rent'
    apply_hdr(ws, row, max_col)
    row += 1

    for utype, info in umix.items():
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = utype
        ws.cell(row=row, column=2).font = F_LABEL
        input_cell(ws, row, 3, info['count'], NF_NUM)
        input_cell(ws, row, 4, info['sf'], NF_NUM)
        input_cell(ws, row, 5, info['market_rent'], NF_DOLLAR)
        row += 1

    # Total row
    apply_subtotal(ws, row, max_col)
    ws.cell(row=row, column=2).value = 'Total'
    ws.cell(row=row, column=2).font = F_BOLD
    ws.cell(row=row, column=3).value = f'=SUM(C{row-len(umix)}:C{row-1})'
    ws.cell(row=row, column=3).number_format = NF_NUM
    row += 1
    row += 1  # spacer

    # ── LOAN TERMS ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'LOAN TERMS'
    row += 1

    loan_items = [
        ('Original Amount', loan['original_amount'], NF_DOLLAR),
        ('Interest Rate', loan['rate'], NF_PCT2),
        ('Amortization (Years)', loan['amort_years'], NF_NUM),
        ('Term (Years)', loan['term_years'], NF_NUM),
        ('Start Date', loan['start_date'], None),
        ('Est. Current Balance', loan['est_current_balance'], NF_DOLLAR),
        ('Interest Only', 'Yes' if loan['io'] else 'No', None),
    ]
    for label, value, nf in loan_items:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = label
        ws.cell(row=row, column=2).font = F_LABEL
        input_cell(ws, row, 3, value, nf)
        row += 1

    row += 1  # spacer

    # ── TIC OWNERSHIP ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'TIC OWNERSHIP'
    row += 1

    ws.cell(row=row, column=2).value = 'Owner'
    ws.cell(row=row, column=3).value = 'Ownership %'
    ws.cell(row=row, column=4).value = 'Equity'
    apply_hdr(ws, row, max_col)
    row += 1

    for owner, info in tic.items():
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = owner
        ws.cell(row=row, column=2).font = F_LABEL
        input_cell(ws, row, 3, info['pct'], NF_PCT2)
        input_cell(ws, row, 4, info['equity'], NF_DOLLAR)
        row += 1

    apply_subtotal(ws, row, max_col)
    ws.cell(row=row, column=2).value = 'Total'
    ws.cell(row=row, column=2).font = F_BOLD
    ws.cell(row=row, column=3).value = f'=SUM(C{row-len(tic)}:C{row-1})'
    ws.cell(row=row, column=3).number_format = NF_PCT2
    ws.cell(row=row, column=4).value = cfg['total_equity']
    ws.cell(row=row, column=4).number_format = NF_DOLLAR
    ws.cell(row=row, column=4).font = F_BOLD
    row += 1
    row += 1

    # ── VALUATION ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'VALUATION (BOV)'
    row += 1

    for label, key in [('Low', 'bov_low'), ('Mid', 'bov_mid'), ('High', 'bov_high')]:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = label
        ws.cell(row=row, column=2).font = F_LABEL
        input_cell(ws, row, 3, val[key], NF_DOLLAR)
        row += 1

    row += 1

    # ── REFINANCE ASSUMPTIONS ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'REFINANCE ASSUMPTIONS'
    row += 1

    refi_items = [
        ('Property Value', refi['property_value'], NF_DOLLAR),
        ('LTV', refi['ltv'], NF_PCT),
        ('Interest Rate', refi['rate'], NF_PCT2),
        ('Amortization (Years)', refi['amort_years'], NF_NUM),
        ('Term (Years)', refi['term_years'], NF_NUM),
        ('Interest Only', 'Yes' if refi['io'] else 'No', None),
        ('NOAH Equity %', refi['noah_equity_pct'], NF_PCT),
        ('NOAH Pref Return', refi['noah_pref_return'], NF_PCT2),
    ]
    for label, value, nf in refi_items:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = label
        ws.cell(row=row, column=2).font = F_LABEL
        input_cell(ws, row, 3, value, nf)
        row += 1

    hide_beyond(ws, max(row, 84), max_col)
    return ws
