# src/sheets/how_to_use.py — Static instructional sheet
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from design import (apply_title, apply_hdr, apply_section, set_col_widths,
                     hide_beyond, F_BODY, F_BOLD, F_LABEL, F_MUTED, F_NOTE,
                     P_ALT, P_WHITE, NF_DOLLAR, A_LEFT)

INSTRUCTIONS = [
    ('OVERVIEW', None),
    ('', 'This workbook is the Groves Apartments Investor Model — a fully formula-driven Excel model.'),
    ('', 'All financial data flows from the hidden qPL_Fact table via SUMIFS formulas.'),
    ('', 'Input cells (yellow background, blue font) can be edited directly.'),
    ('', 'Formula cells (white/gray background) should NOT be manually edited.'),
    ('', ''),
    ('SHEET GUIDE', None),
    ('Executive Summary', 'High-level property overview and key performance indicators.'),
    ('Assumptions', 'Editable property details, loan terms, unit mix, and TIC ownership.'),
    ('Full P&L', 'Complete monthly profit & loss from Aug-24 through Dec-25.'),
    ('T12_PL', 'Trailing 12-month P&L with monthly detail and T-12 totals.'),
    ('Trailing Analysis', 'Rolling T-1, T-3, T-6, and T-12 performance windows.'),
    ('Distribution_Model', 'Monthly cash flow waterfall and owner distributions.'),
    ('TIC Ownership', 'Tenancy-in-common ownership allocation and returns.'),
    ('RR Summary', 'Rent roll summary by unit type, occupancy, and trends.'),
    ('RR Input', 'Detailed unit-level rent data by month.'),
    ('Unit Improvements', 'Renovation tracker — condition, rents, and upgrades per unit.'),
    ('Escrow_Summary', 'Escrow account rollforward (taxes, insurance, reserves).'),
    ('Escrow_Input', 'Raw monthly escrow deposits and payments.'),
    ('CapEx Profile', 'Building systems condition and remaining useful life.'),
    ('Refi Stress Test', 'Refinance scenario analysis with rate sensitivity.'),
    ('Rent Comps', 'Market rent and sale comparables for benchmarking.'),
    ('', ''),
    ('HOW TO UPDATE', None),
    ('Step 1', 'Append new rows to data/pl_actuals.csv (one row per GL per month).'),
    ('Step 2', 'Add new month column to data/rent_roll.csv.'),
    ('Step 3', 'Add 3 rows to data/escrow_activity.csv (taxes, insurance, reserves).'),
    ('Step 4', 'Run: python src/build.py'),
    ('Step 5', 'The entire model rebuilds from scratch — no patching needed.'),
    ('', ''),
    ('COLOR LEGEND', None),
    ('Yellow cells', 'Editable input — change these values as needed.'),
    ('White/gray cells', 'Formula-driven — do not overwrite.'),
    ('Green rows', 'Key totals: NOI, CFADS, Net Cash Flow.'),
    ('Dark navy bars', 'Section headers.'),
    ('Steel blue bars', 'Sub-section dividers.'),
    ('', ''),
    ('FORMULA STRATEGY', None),
    ('', 'All financial values are Excel SUMIFS formulas referencing qPL_Fact.'),
    ('', 'Subtotals (ERI, EGI, NOI, CFADS, NCF) are pre-computed in qPL_Fact.'),
    ('', 'Cross-sheet references use direct cell references for consistency.'),
    ('', 'TIC allocations multiply cash flow by each owner\'s percentage.'),
    ('', 'Distribution waterfall: CFADS - CapEx - Reserves - Fees = Free Cash.'),
    ('', ''),
    ('PROPERTY SNAPSHOT', None),
    ('Property', 'The Groves Apartments'),
    ('Address', '6800-6810 63rd Ave N, Brooklyn Park MN 55443'),
    ('Units', '120 (60x1BR + 60x2BR)'),
    ('Acquired', 'August 2024 for $12,000,000'),
    ('Loan', '$8,838,399 @ 5.44%, 30yr amort, 5yr term'),
    ('TIC Owners', 'Boxwood LLC (61.674%), Groves LP LLC (31.718%), E 2088 (6.608%)'),
    ('', ''),
    ('DATA SOURCES', None),
    ('pl_actuals.csv', 'Monthly P&L actuals (Month, GL, Account, Amount)'),
    ('rent_roll.csv', 'Unit rent grid (Unit x Months)'),
    ('escrow_activity.csv', 'Monthly escrow deposits and payments'),
    ('unit_improvements.csv', 'Renovation tracker per unit'),
    ('capex_profile.csv', 'Building systems condition assessment'),
    ('rent_comps.csv', 'Market rent and sale comparables'),
    ('', ''),
    ('CONTACT', None),
    ('', 'For questions about the model, contact the asset management team.'),
    ('', 'For technical issues with the build system, see CLAUDE.md.'),
]


def build(wb, cfg):
    ws = wb.create_sheet('How To Use')
    max_col = 5

    apply_title(ws, max_col,
                'HOW TO USE THIS MODEL',
                'Read this sheet before editing any data or formulas.')

    # Headers
    ws.cell(row=3, column=1).value = 'Topic'
    ws.cell(row=3, column=2).value = 'Description'
    apply_hdr(ws, 3, max_col)

    set_col_widths(ws, {'A': 22, 'B': 70, 'C': 5, 'D': 5, 'E': 5})

    row = 4
    for topic, desc in INSTRUCTIONS:
        if desc is None:
            # Section header
            apply_section(ws, row, max_col, accent=True)
            ws.cell(row=row, column=1).value = topic
            row += 1
            continue
        fill = P_ALT if (row % 2 == 0) else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        if topic:
            ws.cell(row=row, column=1).value = topic
            ws.cell(row=row, column=1).font = F_LABEL
        if desc:
            ws.cell(row=row, column=2).value = desc
            ws.cell(row=row, column=2).font = F_BODY
        row += 1

    hide_beyond(ws, max(row, 155), max_col)
    return ws
