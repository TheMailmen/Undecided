# src/sheets/capex_profile.py — Building systems condition
import csv
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from design import (apply_title, apply_hdr, apply_section, apply_subtotal,
                     set_col_widths, hide_beyond,
                     F_BODY, F_BOLD, F_LABEL, F_MUTED, F_GREEN,
                     P_ALT, P_WHITE, P_GREEN_LT,
                     NF_NUM)


def build(wb, cfg, csv_path):
    ws = wb.create_sheet('CapEx Profile')
    max_col = 5

    apply_title(ws, max_col,
                'CAPEX PROFILE',
                'Building systems condition assessment. Source: capex_profile.csv.')

    # Headers
    headers = ['Section', 'Detail', 'Updated', 'Status', '']
    for c, h in enumerate(headers, 1):
        ws.cell(row=3, column=c).value = h
    apply_hdr(ws, 3, max_col)

    set_col_widths(ws, {'A': 22, 'B': 55, 'C': 12, 'D': 10, 'E': 5})

    # Read CSV
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    row = 4
    current_section = None
    for record in data:
        section = record['Section'].strip()
        detail = record['Detail'].strip()
        updated = record.get('Updated', '').strip()
        status = record.get('Status', '').strip()

        # Section header
        if section != current_section:
            if section == 'PROPERTY OVERVIEW':
                # Property overview section
                apply_section(ws, row, max_col, accent=True)
                ws.cell(row=row, column=1).value = section
                row += 1
                current_section = section
            elif section and section != current_section:
                apply_section(ws, row, max_col, accent=True)
                ws.cell(row=row, column=1).value = section
                row += 1
                current_section = section

        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill

        ws.cell(row=row, column=2).value = detail
        ws.cell(row=row, column=2).font = F_BODY

        if updated:
            ws.cell(row=row, column=3).value = updated
            ws.cell(row=row, column=3).font = F_MUTED

        if status:
            ws.cell(row=row, column=4).value = status
            ws.cell(row=row, column=4).font = F_BOLD
            # Color-code status
            if status == 'Good':
                ws.cell(row=row, column=4).font = F_GREEN
            elif status in ('Monitor', 'Watch'):
                from design import F_GOLD
                ws.cell(row=row, column=4).font = F_GOLD

        row += 1

    hide_beyond(ws, max(row + 2, 44), max_col)
    return ws
