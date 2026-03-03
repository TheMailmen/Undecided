# src/sheets/escrow_summary.py — Escrow account rollforward
import csv
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from design import (apply_title, apply_hdr, apply_section, apply_subtotal,
                     set_col_widths, hide_beyond, input_cell,
                     F_BODY, F_BOLD, F_LABEL, F_GREEN, F_MUTED,
                     P_ALT, P_WHITE, P_GREEN_LT,
                     NF_DOLLAR, NF_NUM, NF_DATE)


def build(wb, cfg):
    ws = wb.create_sheet('Escrow_Summary')
    max_col = 8
    escrow_names = cfg['escrow_names']

    apply_title(ws, max_col,
                'ESCROW SUMMARY',
                'Escrow account rollforward. Deposits & payments via SUMIFS against Escrow_Input.')

    set_col_widths(ws, {'A': 4, 'B': 28, 'C': 14, 'D': 14, 'E': 14, 'F': 14, 'G': 14, 'H': 14})

    # Get months from Escrow_Input
    ei = wb['Escrow_Input']
    months_set = set()
    for r in range(4, 200):
        v = ei.cell(row=r, column=1).value
        if v is None:
            break
        if isinstance(v, datetime):
            months_set.add(v.strftime('%Y-%m-%d'))
    months = sorted(months_set)

    # For each escrow account, show a rollforward section
    # Layout: rows for each account showing Starting, Deposits, Payments, Ending
    # Then a total escrow balance section

    row = 3
    # Column headers
    ws.cell(row=row, column=2).value = 'Account / Period'
    ws.cell(row=row, column=3).value = 'T-12 Deposits'
    ws.cell(row=row, column=4).value = 'T-12 Payments'
    ws.cell(row=row, column=5).value = 'T-12 Net'
    ws.cell(row=row, column=6).value = 'Monthly Avg'
    ws.cell(row=row, column=7).value = 'Annual Run'
    ws.cell(row=row, column=8).value = 'Balance Est.'
    apply_hdr(ws, row, max_col)
    row += 1

    # For SUMIFS, we need to reference Escrow_Input columns
    # Escrow_Input: Col A=Month, Col B=EscrowName, Col C=Deposits, Col D=Payments
    # Find the last row in Escrow_Input
    ei_last = 4
    while ei.cell(row=ei_last, column=1).value is not None:
        ei_last += 1
    ei_last -= 1

    # T-12 date range
    if len(months) >= 12:
        t12_months = months[-12:]
    else:
        t12_months = months
    t12_start = datetime.strptime(t12_months[0], '%Y-%m-%d')
    t12_end = datetime.strptime(t12_months[-1], '%Y-%m-%d')

    date_gte = f'">="&DATE({t12_start.year},{t12_start.month},1)'
    date_lte = f'"<="&DATE({t12_end.year},{t12_end.month},1)'

    dep_range = f"'Escrow_Input'!$C$4:$C${ei_last}"
    pay_range = f"'Escrow_Input'!$D$4:$D${ei_last}"
    name_range = f"'Escrow_Input'!$B$4:$B${ei_last}"
    date_range = f"'Escrow_Input'!$A$4:$A${ei_last}"

    balance_rows = []

    for escrow_name in escrow_names:
        # Section header
        apply_section(ws, row, max_col, accent=True)
        ws.cell(row=row, column=2).value = escrow_name.upper()
        row += 1

        # T-12 Deposits
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = 'Deposits'
        ws.cell(row=row, column=2).font = F_LABEL
        dep_formula = (f'=SUMIFS({dep_range},{name_range},"{escrow_name}",'
                       f'{date_range},{date_gte},{date_range},{date_lte})')
        ws.cell(row=row, column=3).value = dep_formula
        ws.cell(row=row, column=3).number_format = NF_DOLLAR
        dep_row = row
        row += 1

        # T-12 Payments
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = 'Payments'
        ws.cell(row=row, column=2).font = F_LABEL
        pay_formula = (f'=SUMIFS({pay_range},{name_range},"{escrow_name}",'
                       f'{date_range},{date_gte},{date_range},{date_lte})')
        ws.cell(row=row, column=4).value = pay_formula
        ws.cell(row=row, column=4).number_format = NF_DOLLAR
        pay_row = row
        row += 1

        # Net (Deposits - Payments)
        apply_subtotal(ws, row, max_col)
        ws.cell(row=row, column=2).value = 'Net Change'
        ws.cell(row=row, column=2).font = F_BOLD
        ws.cell(row=row, column=5).value = f'=C{dep_row}-D{pay_row}'
        ws.cell(row=row, column=5).number_format = NF_DOLLAR
        ws.cell(row=row, column=5).font = F_BOLD

        # Monthly avg
        num_t12 = len(t12_months)
        ws.cell(row=row, column=6).value = f'=E{row}/{num_t12}'
        ws.cell(row=row, column=6).number_format = NF_DOLLAR

        # Annual run rate
        ws.cell(row=row, column=7).value = f'=C{dep_row}'
        ws.cell(row=row, column=7).number_format = NF_DOLLAR

        # Balance estimate (cumulative deposits - payments, all time)
        all_dep = (f'SUMIFS({dep_range},{name_range},"{escrow_name}")')
        all_pay = (f'SUMIFS({pay_range},{name_range},"{escrow_name}")')
        ws.cell(row=row, column=8).value = f'={all_dep}-{all_pay}'
        ws.cell(row=row, column=8).number_format = NF_DOLLAR
        balance_rows.append(row)
        row += 1

        row += 1  # spacer

    # ── TOTAL ESCROW ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'TOTAL ESCROW BALANCE'
    row += 1

    apply_subtotal(ws, row, max_col, green=True)
    ws.cell(row=row, column=2).value = 'Total Balance'
    ws.cell(row=row, column=2).font = F_GREEN
    bal_refs = '+'.join(f'H{r}' for r in balance_rows)
    ws.cell(row=row, column=8).value = f'={bal_refs}'
    ws.cell(row=row, column=8).number_format = NF_DOLLAR
    ws.cell(row=row, column=8).font = F_GREEN
    row += 1

    # Monthly escrow detail — show most recent months
    row += 1
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'RECENT MONTHLY DETAIL'
    row += 1

    recent_months = months[-6:]
    ws.cell(row=row, column=2).value = 'Month'
    for i, m in enumerate(recent_months):
        dt = datetime.strptime(m, '%Y-%m-%d')
        ws.cell(row=row, column=3 + i).value = dt
        ws.cell(row=row, column=3 + i).number_format = NF_DATE
    apply_hdr(ws, row, max_col)
    row += 1

    for escrow_name in escrow_names:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = escrow_name
        ws.cell(row=row, column=2).font = F_LABEL
        for i, m in enumerate(recent_months):
            dt = datetime.strptime(m, '%Y-%m-%d')
            formula = (f'=SUMIFS({dep_range},{name_range},"{escrow_name}",'
                       f'{date_range},DATE({dt.year},{dt.month},1))')
            ws.cell(row=row, column=3 + i).value = formula
            ws.cell(row=row, column=3 + i).number_format = NF_DOLLAR
        row += 1

    hide_beyond(ws, max(row + 2, 64), max_col)
    return ws
