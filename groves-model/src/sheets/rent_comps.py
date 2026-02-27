# src/sheets/rent_comps.py — Rent Comparables sheet builder
"""
Builds the 'Rent Comps' tab: market rent comparables and sale comps
from data/rent_comps.csv.

CSV columns: Section, Num, Property, Address, Built, AvgSF, Rent,
             RentPerSF  (rent comps) / sale price fields (sale comps)
"""
import csv, os

from design import (
    apply_title, apply_hdr, apply_section, apply_subtotal,
    hide_beyond,
    F_BOLD, F_BODY, F_LABEL, F_MUTED, F_GREEN, F_GOLD,
    P_ALT, P_WHITE, P_SUBTOTAL, P_ACCENT,
    NF_DOLLAR, NF_DEC2, NF_PCT,
    A_CENTER,
)

MAX_COL = 9


def build(wb, cfg, comps_csv_path=None):
    if comps_csv_path is None:
        comps_csv_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'rent_comps.csv'
        )

    ws = wb.create_sheet('Rent Comps')
    prop = cfg['property']

    # ── Read CSV ──────────────────────────────────────────────────────
    sections_order = []
    sections_data  = {}
    raw_headers    = []

    if os.path.exists(comps_csv_path):
        with open(comps_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            raw_headers = next(reader, [])
            for row in reader:
                if not row or not row[0]:
                    continue
                sec_name = row[0].strip()
                if sec_name not in sections_data:
                    sections_data[sec_name] = []
                    sections_order.append(sec_name)
                sections_data[sec_name].append(row)

    apply_title(
        ws, MAX_COL,
        f"{prop['name']}  |  Rent & Sale Comparables",
        f"Market rent and sales comps  |  {prop['address']}",
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

    def blank():
        nonlocal r
        r += 1

    # ── SUBJECT PROPERTY ─────────────────────────────────────────────
    sec('SUBJECT PROPERTY')
    hdr('#', 'Property', 'Address', 'Built', 'Avg SF', 'Avg Rent', '$/SF', 'Occ %', '')
    fill = P_ALT
    for c in range(1, MAX_COL + 1):
        ws.cell(row=r, column=c).fill = fill
    ws.cell(row=r, column=1).value = '*'
    ws.cell(row=r, column=1).font  = F_GOLD
    ws.cell(row=r, column=2).value = prop['name']
    ws.cell(row=r, column=2).font  = F_BOLD
    ws.cell(row=r, column=3).value = prop['address']
    ws.cell(row=r, column=4).value = prop['year_built']
    ws.cell(row=r, column=5).value = int(prop['rentable_sf'] / prop['units'])
    ws.cell(row=r, column=5).number_format = '#,##0'
    # Avg rent from config unit mix
    um = cfg['unit_mix']
    avg_mkt = sum(v['market_rent'] * v['count'] for v in um.values()) / prop['units']
    ws.cell(row=r, column=6).value = avg_mkt
    ws.cell(row=r, column=6).number_format = NF_DOLLAR
    ws.cell(row=r, column=7).value = avg_mkt / (prop['rentable_sf'] / prop['units'])
    ws.cell(row=r, column=7).number_format = NF_DEC2
    r += 1
    blank()

    # ── COMPS FROM CSV ────────────────────────────────────────────────
    for sec_name in sections_order:
        # Skip the header row that appears as first data row in CSV
        data_rows = [row for row in sections_data[sec_name]
                     if row[1] != 'Property' and row[1] != '#']

        if not data_rows:
            continue

        sec(sec_name)
        # Determine column headers based on section type
        if 'RENT' in sec_name.upper():
            hdr('#', 'Property', 'Address', 'Built', 'Avg SF',
                'Avg Rent', '$/SF', 'Occ %', '')
        else:
            hdr('#', 'Property', 'Address', 'Sale Date', 'Units',
                'Sale Price', '$/Unit', 'Year Built', '')

        is_sale = 'SALE' in sec_name.upper()
        for data_row in data_rows:
            fill = P_ALT if r % 2 == 0 else P_WHITE
            for c in range(1, MAX_COL + 1):
                ws.cell(row=r, column=c).fill = fill

            # Map CSV cols: Section(0), Num(1), Property(2), Address(3),
            #               Built/Date(4), AvgSF/Units(5), Rent/Price(6),
            #               RentPerSF/PricePerUnit(7), Occ(8)
            for col_idx, csv_idx in enumerate(range(1, min(len(data_row), 9)), 1):
                if csv_idx < len(data_row):
                    val  = data_row[csv_idx].strip()
                    cell = ws.cell(row=r, column=col_idx)

                    # Try numeric conversion for financial columns
                    if col_idx in (5, 6, 7, 8):
                        try:
                            num = float(val.replace(',', '').replace('$', ''))
                            cell.value = num
                            if col_idx == 8 and not is_sale:
                                cell.number_format = NF_PCT
                            elif col_idx in (6, 7):
                                cell.number_format = NF_DOLLAR
                            elif col_idx == 7 and not is_sale:
                                cell.number_format = NF_DEC2
                            else:
                                cell.number_format = '#,##0'
                        except (ValueError, AttributeError):
                            cell.value = val
                    else:
                        cell.value = val

                    cell.font = F_BOLD if col_idx == 2 else (
                        F_MUTED if col_idx == 1 else F_BODY
                    )

            r += 1

        blank()

    last_row = r - 1

    ws.column_dimensions['A'].width = 4
    ws.column_dimensions['B'].width = 28
    ws.column_dimensions['C'].width = 32
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 8
    ws.column_dimensions['F'].width = 12
    ws.column_dimensions['G'].width = 10
    ws.column_dimensions['H'].width = 10
    ws.column_dimensions['I'].width = 8

    hide_beyond(ws, last_row, MAX_COL)
    return ws
