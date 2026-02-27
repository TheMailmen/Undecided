# src/sheets/escrow_input.py — Escrow Input sheet builder
"""
Builds the 'Escrow_Input' tab: raw escrow transaction data.

CSV columns: Month, EscrowName, Deposits, Payments, Notes
"""
import csv, os
from datetime import datetime

from design import (
    apply_title, apply_hdr, apply_section, apply_subtotal,
    hide_beyond,
    F_BOLD, F_BODY, F_LABEL, F_MUTED,
    P_ALT, P_WHITE, P_SUBTOTAL,
    NF_DOLLAR, NF_DATE,
    A_CENTER,
)

MAX_COL = 6


def build(wb, cfg, escrow_csv_path=None):
    if escrow_csv_path is None:
        escrow_csv_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'escrow_activity.csv'
        )

    ws = wb.create_sheet('Escrow_Input')
    prop = cfg['property']

    rows = []
    if os.path.exists(escrow_csv_path):
        with open(escrow_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

    apply_title(
        ws, MAX_COL,
        f"{prop['name']}  |  Escrow Input",
        f"Transaction detail for tax, insurance, and reserve accounts  |  {len(rows)} records",
    )

    # ── Column headers (row 3) ────────────────────────────────────────
    apply_hdr(ws, 3, MAX_COL)
    for i, lbl in enumerate(['Month', 'Account', 'Deposits', 'Payments', 'Net', 'Notes'], 1):
        ws.cell(row=3, column=i).value = lbl
        ws.cell(row=3, column=i).alignment = A_CENTER

    # ── Data rows ─────────────────────────────────────────────────────
    DATA_START = 4
    for idx, row in enumerate(rows):
        r    = DATA_START + idx
        fill = P_ALT if r % 2 == 0 else P_WHITE
        for c in range(1, MAX_COL + 1):
            ws.cell(row=r, column=c).fill = fill

        # Col A: Month (date)
        month_str = row.get('Month', '').strip()
        try:
            dt = datetime.strptime(month_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            dt = month_str
        a_cell = ws.cell(row=r, column=1)
        a_cell.value = dt
        a_cell.number_format = NF_DATE
        a_cell.font = F_MUTED

        # Col B: Account name
        ws.cell(row=r, column=2).value = row.get('EscrowName', '').strip()
        ws.cell(row=r, column=2).font  = F_BODY

        # Col C: Deposits
        try:
            dep = float(row.get('Deposits', 0) or 0)
        except (ValueError, TypeError):
            dep = 0.0
        c_cell = ws.cell(row=r, column=3)
        c_cell.value = dep if dep else ''
        c_cell.number_format = NF_DOLLAR

        # Col D: Payments
        try:
            pay = float(row.get('Payments', 0) or 0)
        except (ValueError, TypeError):
            pay = 0.0
        d_cell = ws.cell(row=r, column=4)
        d_cell.value = pay if pay else ''
        d_cell.number_format = NF_DOLLAR

        # Col E: Net = Deposits - Payments
        ws.cell(row=r, column=5).value = f'=C{r}-D{r}'
        ws.cell(row=r, column=5).number_format = NF_DOLLAR

        # Col F: Notes
        ws.cell(row=r, column=6).value = row.get('Notes', '').strip()
        ws.cell(row=r, column=6).font  = F_MUTED

    n_data  = len(rows)
    end_row = DATA_START + n_data - 1 if n_data else DATA_START

    # ── Totals row ────────────────────────────────────────────────────
    tot_row = end_row + 1
    apply_subtotal(ws, tot_row, MAX_COL)
    ws.cell(row=tot_row, column=1).value = 'TOTAL'
    ws.cell(row=tot_row, column=1).font  = F_BOLD
    for col, ltr in [(3, 'C'), (4, 'D'), (5, 'E')]:
        cell = ws.cell(row=tot_row, column=col)
        cell.value = f'=SUM({ltr}{DATA_START}:{ltr}{end_row})'
        cell.number_format = NF_DOLLAR
        cell.font = F_BOLD

    last_row = tot_row

    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 22
    ws.column_dimensions['C'].width = 14
    ws.column_dimensions['D'].width = 14
    ws.column_dimensions['E'].width = 14
    ws.column_dimensions['F'].width = 24

    hide_beyond(ws, last_row, MAX_COL)
    return ws
