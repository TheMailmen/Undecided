# src/sheets/rent_comps.py — Market rent and sale comparables
import csv
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from design import (apply_title, apply_hdr, apply_section, apply_subtotal,
                     set_col_widths, hide_beyond,
                     F_BODY, F_BOLD, F_LABEL, F_MUTED,
                     P_ALT, P_WHITE,
                     NF_DOLLAR, NF_NUM, NF_PCT, NF_DEC2)


def build(wb, cfg, csv_path):
    ws = wb.create_sheet('Rent Comps')
    max_col = 8

    apply_title(ws, max_col,
                'RENT COMPS & SALE COMPARABLES',
                'Market rent and recent sale comparables. Source: rent_comps.csv.')

    set_col_widths(ws, {'A': 5, 'B': 28, 'C': 30, 'D': 8, 'E': 10, 'F': 12, 'G': 12, 'H': 10})

    # Read CSV
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        data = list(reader)

    row = 3
    current_section = None

    for record in data:
        if not record or not record[0].strip():
            continue

        section = record[0].strip()

        # New section header
        if section != current_section:
            current_section = section
            apply_section(ws, row, max_col, accent=True)
            ws.cell(row=row, column=2).value = section
            row += 1

            # If this row is a sub-header (has column names)
            if record[1].strip() == '#':
                # This is a header row within the CSV
                for c, h in enumerate(record[1:max_col], 2):
                    ws.cell(row=row, column=c).value = h.strip() if h else ''
                apply_hdr(ws, row, max_col)
                row += 1
                continue

        # Data row
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill

        # Skip section name, start from field 1 (#)
        for c, val in enumerate(record[1:max_col], 2):
            val = val.strip() if val else ''
            cell = ws.cell(row=row, column=c)

            # Try to parse as number
            try:
                num = float(val.replace(',', ''))
                cell.value = num
                # Guess format based on column and section
                if section.startswith('SALE') and c == 7:  # Sale Price
                    cell.number_format = NF_DOLLAR
                elif section.startswith('SALE') and c == 8:  # $/Unit
                    cell.number_format = NF_DOLLAR
                elif c == 7 and not section.startswith('SALE'):  # Rent
                    cell.number_format = NF_DOLLAR
                elif c == 8 and not section.startswith('SALE'):  # $/SF or Occ%
                    if num <= 5:
                        cell.number_format = NF_DEC2
                    else:
                        cell.number_format = NF_DOLLAR
                elif c == 6 and not section.startswith('SALE'):  # Avg SF
                    cell.number_format = NF_NUM
                else:
                    cell.number_format = NF_NUM
            except (ValueError, AttributeError):
                cell.value = val
            cell.font = F_BODY

        row += 1

    # Add Groves comparison row
    row += 1
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'THE GROVES — COMPARISON'
    row += 1

    umix = cfg['unit_mix']
    for utype, info in umix.items():
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = f'The Groves — {utype}'
        ws.cell(row=row, column=2).font = F_BOLD
        ws.cell(row=row, column=3).value = cfg['property']['address']
        ws.cell(row=row, column=3).font = F_MUTED
        ws.cell(row=row, column=5).value = cfg['property']['year_built']
        ws.cell(row=row, column=6).value = info['sf']
        ws.cell(row=row, column=6).number_format = NF_NUM
        ws.cell(row=row, column=7).value = info['market_rent']
        ws.cell(row=row, column=7).number_format = NF_DOLLAR
        if info['sf'] > 0:
            ws.cell(row=row, column=8).value = info['market_rent'] / info['sf']
            ws.cell(row=row, column=8).number_format = NF_DEC2
        row += 1

    hide_beyond(ws, max(row + 2, 32), max_col)
    return ws
