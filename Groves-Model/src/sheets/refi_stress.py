# src/sheets/refi_stress.py — Refinance stress test
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from design import (apply_title, apply_hdr, apply_section, apply_subtotal,
                     set_col_widths, hide_beyond, input_cell,
                     F_BODY, F_BOLD, F_LABEL, F_GREEN, F_MUTED, F_RED,
                     P_ALT, P_WHITE, P_GREEN_LT, P_RED_LT,
                     NF_DOLLAR, NF_PCT, NF_PCT2, NF_NUM, NF_DEC2)


def build(wb, cfg):
    ws = wb.create_sheet('Refi Stress Test')
    max_col = 6
    n = cfg['qpl_rows']
    refi = cfg['refi']

    apply_title(ws, max_col,
                'REFINANCE STRESS TEST',
                'Sensitivity analysis for refinance scenarios. Yellow cells are editable inputs.')

    set_col_widths(ws, {'A': 4, 'B': 32, 'C': 16, 'D': 16, 'E': 16, 'F': 16})

    sr = f'qPL_Fact!$D$2:$D${n}'
    ac = f'qPL_Fact!$C$2:$C${n}'
    dtr = f'qPL_Fact!$A$2:$A${n}'
    date_gte = '">="&DATE(2025,1,1)'
    date_lte = '"<="&DATE(2025,12,1)'

    noi_f = f'SUMIFS({sr},{ac},"NET OPERATING INCOME (NOI)",{dtr},{date_gte},{dtr},{date_lte})'

    row = 3

    # ── CURRENT LOAN ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'CURRENT LOAN'
    row += 1

    loan = cfg['loan']
    current_items = [
        ('Original Amount', loan['original_amount'], NF_DOLLAR),
        ('Interest Rate', loan['rate'], NF_PCT2),
        ('Amort / Term', f"{loan['amort_years']}yr / {loan['term_years']}yr", None),
        ('Est. Current Balance', loan['est_current_balance'], NF_DOLLAR),
        ('Monthly Payment (P&I)', None, NF_DOLLAR),
    ]

    for label, value, nf in current_items:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = label
        ws.cell(row=row, column=2).font = F_LABEL
        if value is not None:
            ws.cell(row=row, column=3).value = value
        else:
            # Monthly P&I = Total Debt Service / 12
            ds_f = f'SUMIFS({sr},{ac},"Total Debt Service",{dtr},{date_gte},{dtr},{date_lte})'
            ws.cell(row=row, column=3).value = f'={ds_f}/12'
        if nf:
            ws.cell(row=row, column=3).number_format = nf
        ws.cell(row=row, column=3).font = F_BODY
        row += 1

    row += 1

    # ── REFINANCE ASSUMPTIONS ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'REFINANCE ASSUMPTIONS'
    row += 1

    refi_start = row
    refi_items = [
        ('Property Value', refi['property_value'], NF_DOLLAR),
        ('LTV', refi['ltv'], NF_PCT),
        ('Loan Amount', None, NF_DOLLAR),  # calculated
        ('Interest Rate', refi['rate'], NF_PCT2),
        ('Amortization (Years)', refi['amort_years'], NF_NUM),
        ('Term (Years)', refi['term_years'], NF_NUM),
        ('Interest Only', 'Yes' if refi['io'] else 'No', None),
    ]

    val_row = rate_row = amort_row = ltv_row = loan_amt_row = io_row = None
    for label, value, nf in refi_items:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = label
        ws.cell(row=row, column=2).font = F_LABEL

        if label == 'Property Value':
            input_cell(ws, row, 3, value, nf)
            val_row = row
        elif label == 'LTV':
            input_cell(ws, row, 3, value, nf)
            ltv_row = row
        elif label == 'Loan Amount':
            ws.cell(row=row, column=3).value = f'=C{val_row}*C{ltv_row}'
            ws.cell(row=row, column=3).number_format = nf
            ws.cell(row=row, column=3).font = F_BOLD
            loan_amt_row = row
        elif label == 'Interest Rate':
            input_cell(ws, row, 3, value, nf)
            rate_row = row
        elif label == 'Amortization (Years)':
            input_cell(ws, row, 3, value, nf)
            amort_row = row
        elif label == 'Interest Only':
            input_cell(ws, row, 3, value, None)
            io_row = row
        else:
            input_cell(ws, row, 3, value, nf)
        row += 1

    row += 1

    # ── REFI RESULTS ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'REFINANCE RESULTS'
    row += 1

    # Monthly IO Payment
    fill = P_ALT if row % 2 == 0 else P_WHITE
    for c in range(1, max_col + 1):
        ws.cell(row=row, column=c).fill = fill
    ws.cell(row=row, column=2).value = 'Monthly IO Payment'
    ws.cell(row=row, column=2).font = F_LABEL
    ws.cell(row=row, column=3).value = f'=C{loan_amt_row}*C{rate_row}/12'
    ws.cell(row=row, column=3).number_format = NF_DOLLAR
    io_pmt_row = row
    row += 1

    # Monthly P&I Payment (amortizing)
    fill = P_ALT if row % 2 == 0 else P_WHITE
    for c in range(1, max_col + 1):
        ws.cell(row=row, column=c).fill = fill
    ws.cell(row=row, column=2).value = 'Monthly P&I Payment'
    ws.cell(row=row, column=2).font = F_LABEL
    ws.cell(row=row, column=3).value = f'=PMT(C{rate_row}/12,C{amort_row}*12,-C{loan_amt_row})'
    ws.cell(row=row, column=3).number_format = NF_DOLLAR
    pi_pmt_row = row
    row += 1

    # Annual Debt Service
    fill = P_ALT if row % 2 == 0 else P_WHITE
    for c in range(1, max_col + 1):
        ws.cell(row=row, column=c).fill = fill
    ws.cell(row=row, column=2).value = 'Annual Debt Service'
    ws.cell(row=row, column=2).font = F_LABEL
    ws.cell(row=row, column=3).value = f'=IF(C{io_row}="Yes",C{io_pmt_row}*12,C{pi_pmt_row}*12)'
    ws.cell(row=row, column=3).number_format = NF_DOLLAR
    ws.cell(row=row, column=3).font = F_BOLD
    ann_ds_row = row
    row += 1

    # DSCR
    fill = P_ALT if row % 2 == 0 else P_WHITE
    for c in range(1, max_col + 1):
        ws.cell(row=row, column=c).fill = fill
    ws.cell(row=row, column=2).value = 'DSCR (Refi)'
    ws.cell(row=row, column=2).font = F_LABEL
    ws.cell(row=row, column=3).value = f'=IF(C{ann_ds_row}<>0,{noi_f}/C{ann_ds_row},0)'
    ws.cell(row=row, column=3).number_format = NF_DEC2
    ws.cell(row=row, column=3).font = F_BOLD
    row += 1

    # Cash Out
    fill = P_ALT if row % 2 == 0 else P_WHITE
    for c in range(1, max_col + 1):
        ws.cell(row=row, column=c).fill = fill
    ws.cell(row=row, column=2).value = 'Cash Out (Refi - Current)'
    ws.cell(row=row, column=2).font = F_LABEL
    ws.cell(row=row, column=3).value = f'=C{loan_amt_row}-{loan["est_current_balance"]}'
    ws.cell(row=row, column=3).number_format = NF_DOLLAR
    ws.cell(row=row, column=3).font = F_GREEN
    cash_out_row = row
    row += 1

    row += 1

    # ── RATE SENSITIVITY ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'RATE SENSITIVITY'
    row += 1

    # Header
    ws.cell(row=row, column=2).value = 'Rate'
    ws.cell(row=row, column=3).value = 'Monthly IO'
    ws.cell(row=row, column=4).value = 'Monthly P&I'
    ws.cell(row=row, column=5).value = 'Annual DS'
    ws.cell(row=row, column=6).value = 'DSCR'
    apply_hdr(ws, row, max_col)
    row += 1

    # Stress rates
    rates = [0.04, 0.045, 0.05, 0.055, 0.06, 0.065, 0.07, 0.075, 0.08]
    for rate in rates:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill

        ws.cell(row=row, column=2).value = rate
        ws.cell(row=row, column=2).number_format = NF_PCT2
        ws.cell(row=row, column=2).font = F_LABEL

        # Monthly IO
        ws.cell(row=row, column=3).value = f'=C{loan_amt_row}*B{row}/12'
        ws.cell(row=row, column=3).number_format = NF_DOLLAR

        # Monthly P&I
        ws.cell(row=row, column=4).value = f'=PMT(B{row}/12,C{amort_row}*12,-C{loan_amt_row})'
        ws.cell(row=row, column=4).number_format = NF_DOLLAR

        # Annual DS (IO)
        ws.cell(row=row, column=5).value = f'=C{row}*12'
        ws.cell(row=row, column=5).number_format = NF_DOLLAR

        # DSCR
        ws.cell(row=row, column=6).value = f'=IF(E{row}<>0,{noi_f}/E{row},0)'
        ws.cell(row=row, column=6).number_format = NF_DEC2
        ws.cell(row=row, column=6).font = F_BOLD
        row += 1

    row += 1

    # ── NOAH / EQUITY WATERFALL ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'NOAH EQUITY WATERFALL'
    row += 1

    noah_items = [
        ('NOAH Equity %', refi['noah_equity_pct'], NF_PCT),
        ('NOAH Pref Return', refi['noah_pref_return'], NF_PCT2),
        ('Cash Out Amount', None, NF_DOLLAR),
        ('NOAH Equity Proceeds', None, NF_DOLLAR),
        ('Owner Retained', None, NF_DOLLAR),
    ]
    noah_pct_row = noah_pref_row = None
    for label, value, nf in noah_items:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = label
        ws.cell(row=row, column=2).font = F_LABEL

        if label == 'NOAH Equity %':
            input_cell(ws, row, 3, value, nf)
            noah_pct_row = row
        elif label == 'NOAH Pref Return':
            input_cell(ws, row, 3, value, nf)
            noah_pref_row = row
        elif label == 'Cash Out Amount':
            ws.cell(row=row, column=3).value = f'=C{cash_out_row}'
            ws.cell(row=row, column=3).number_format = nf
            ws.cell(row=row, column=3).font = F_BOLD
        elif label == 'NOAH Equity Proceeds':
            ws.cell(row=row, column=3).value = f'=C{cash_out_row}*C{noah_pct_row}'
            ws.cell(row=row, column=3).number_format = nf
            ws.cell(row=row, column=3).font = F_BOLD
        elif label == 'Owner Retained':
            ws.cell(row=row, column=3).value = f'=C{cash_out_row}*(1-C{noah_pct_row})'
            ws.cell(row=row, column=3).number_format = nf
            ws.cell(row=row, column=3).font = F_GREEN
        row += 1

    hide_beyond(ws, max(row + 2, 64), max_col)
    return ws
