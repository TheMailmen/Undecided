# src/sheets/capex_profile.py — CapEx Profile sheet builder
"""
Builds the 'CapEx Profile' tab: building system condition assessment
from data/capex_profile.csv.

CSV columns: Section, Detail, Updated, Status
"""
import csv, os

from design import (
    apply_title, apply_hdr, apply_section, hide_beyond,
    F_BOLD, F_BODY, F_LABEL, F_MUTED, F_GREEN, F_RED, F_GOLD,
    P_ALT, P_WHITE, P_GREEN_LT, P_RED_LT,
    A_LEFT,
)

MAX_COL = 5

_STATUS_FILL = {
    'Good':    'P_GREEN_LT',
    'Watch':   'P_ALT',
    'Planned': 'P_ALT',
}


def build(wb, cfg, capex_csv_path=None):
    if capex_csv_path is None:
        capex_csv_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'data', 'capex_profile.csv'
        )

    ws = wb.create_sheet('CapEx Profile')
    prop = cfg['property']

    rows = []
    sections_order = []
    sections_data  = {}   # section_name -> [rows]

    if os.path.exists(capex_csv_path):
        with open(capex_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sec_name = row.get('Section', '').strip()
                if sec_name not in sections_data:
                    sections_data[sec_name] = []
                    sections_order.append(sec_name)
                sections_data[sec_name].append(row)

    apply_title(
        ws, MAX_COL,
        f"{prop['name']}  |  CapEx Profile",
        f"Building system condition assessment  |  Year built: {prop['year_built']}",
    )

    r = 3

    def sec(title):
        nonlocal r
        apply_section(ws, r, MAX_COL, accent=True)
        ws.cell(row=r, column=1).value = title
        r += 1

    apply_hdr(ws, r, MAX_COL)
    ws.cell(row=r, column=1).value = 'Section'
    ws.cell(row=r, column=2).value = 'Detail'
    ws.cell(row=r, column=3).value = 'Updated / Age'
    ws.cell(row=r, column=4).value = 'Status'
    ws.cell(row=r, column=5).value = 'Notes'
    r += 1

    for sec_name in sections_order:
        sec(sec_name)
        for row in sections_data[sec_name]:
            detail  = row.get('Detail', '').strip()
            updated = row.get('Updated', '').strip()
            status  = row.get('Status', '').strip()

            status_lower = status.lower()
            if 'good' in status_lower:
                fill = P_GREEN_LT
                font = F_GREEN
            elif 'planned' in status_lower or 'watch' in status_lower:
                fill = P_ALT if r % 2 == 0 else P_WHITE
                font = F_GOLD
            else:
                fill = P_ALT if r % 2 == 0 else P_WHITE
                font = F_BODY

            for c in range(1, MAX_COL + 1):
                ws.cell(row=r, column=c).fill = fill

            ws.cell(row=r, column=1).value = sec_name
            ws.cell(row=r, column=1).font  = F_MUTED
            ws.cell(row=r, column=2).value = detail
            ws.cell(row=r, column=2).font  = F_BODY
            ws.cell(row=r, column=3).value = updated
            ws.cell(row=r, column=3).font  = F_MUTED
            ws.cell(row=r, column=4).value = status
            ws.cell(row=r, column=4).font  = font
            r += 1

    last_row = r - 1

    ws.column_dimensions['A'].width = 18
    ws.column_dimensions['B'].width = 48
    ws.column_dimensions['C'].width = 14
    ws.column_dimensions['D'].width = 12
    ws.column_dimensions['E'].width = 20

    hide_beyond(ws, last_row, MAX_COL)
    return ws
