# src/sheets/escrow_input.py — Raw escrow activity data
import csv
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from design import (apply_title, apply_hdr, apply_subtotal, apply_alt_rows,
                     set_col_widths, hide_beyond,
                     F_BODY, F_BOLD, F_LABEL, F_MUTED,
                     P_ALT, P_WHITE, NF_DOLLAR, NF_NUM, NF_DATE)


def build(wb, cfg, escrow_csv):
    ws = wb.create_sheet('Escrow_Input')
    max_col = 5

    apply_title(ws, max_col,
                'ESCROW INPUT',
                'Monthly escrow deposits and payments. Source: escrow_activity.csv.')

    # Headers
    headers = ['Month', 'Escrow Account', 'Deposits', 'Payments', 'Notes']
    for c, h in enumerate(headers, 1):
        ws.cell(row=3, column=c).value = h
    apply_hdr(ws, 3, max_col)

    set_col_widths(ws, {'A': 12, 'B': 25, 'C': 14, 'D': 14, 'E': 30})

    # Read CSV
    with open(escrow_csv, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    row = 4
    for record in data:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill

        try:
            dt = datetime.strptime(record['Month'].strip(), '%Y-%m-%d')
            ws.cell(row=row, column=1).value = dt
            ws.cell(row=row, column=1).number_format = NF_DATE
        except ValueError:
            ws.cell(row=row, column=1).value = record['Month'].strip()

        ws.cell(row=row, column=2).value = record['EscrowName'].strip()
        ws.cell(row=row, column=2).font = F_LABEL

        deposits = float(record['Deposits']) if record['Deposits'] else 0
        payments = float(record['Payments']) if record['Payments'] else 0

        ws.cell(row=row, column=3).value = deposits
        ws.cell(row=row, column=3).number_format = NF_DOLLAR
        ws.cell(row=row, column=3).font = F_BODY

        ws.cell(row=row, column=4).value = payments
        ws.cell(row=row, column=4).number_format = NF_DOLLAR
        ws.cell(row=row, column=4).font = F_BODY

        notes = record.get('Notes', '').strip()
        if notes:
            ws.cell(row=row, column=5).value = notes
            ws.cell(row=row, column=5).font = F_MUTED

        row += 1

    # Total row
    total_row = row
    apply_subtotal(ws, total_row, max_col)
    ws.cell(row=total_row, column=2).value = 'TOTAL'
    ws.cell(row=total_row, column=2).font = F_BOLD
    ws.cell(row=total_row, column=3).value = f'=SUM(C4:C{total_row - 1})'
    ws.cell(row=total_row, column=3).number_format = NF_DOLLAR
    ws.cell(row=total_row, column=3).font = F_BOLD
    ws.cell(row=total_row, column=4).value = f'=SUM(D4:D{total_row - 1})'
    ws.cell(row=total_row, column=4).number_format = NF_DOLLAR
    ws.cell(row=total_row, column=4).font = F_BOLD

    hide_beyond(ws, max(total_row + 2, 65), max_col)
    return ws
