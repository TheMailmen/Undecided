# src/sheets/exec_summary.py — Executive Summary with KPIs
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from design import (apply_title, apply_hdr, apply_section, apply_subtotal,
                     set_col_widths, hide_beyond,
                     F_BODY, F_BOLD, F_LABEL, F_GREEN, F_MUTED, F_GOLD,
                     P_ALT, P_WHITE, P_GREEN_LT,
                     NF_DOLLAR, NF_PCT, NF_PCT2, NF_NUM, A_LEFT)


def build(wb, cfg):
    ws = wb.create_sheet('Executive Summary')
    max_col = 6
    n = cfg['qpl_rows']

    apply_title(ws, max_col,
                'EXECUTIVE SUMMARY',
                'Key property metrics and performance indicators. All values based on trailing 12 months.')

    set_col_widths(ws, {'A': 4, 'B': 32, 'C': 18, 'D': 4, 'E': 32, 'F': 18})

    sr = f'qPL_Fact!$D$2:$D${n}'
    ac = f'qPL_Fact!$C$2:$C${n}'
    dtr = f'qPL_Fact!$A$2:$A${n}'
    date_gte = '">="&DATE(2025,1,1)'
    date_lte = '"<="&DATE(2025,12,1)'

    def t12_sumifs(account):
        return f'SUMIFS({sr},{ac},"{account}",{dtr},{date_gte},{dtr},{date_lte})'

    row = 3
    # ── PROPERTY OVERVIEW ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'PROPERTY OVERVIEW'
    row += 1

    prop = cfg['property']
    overview = [
        ('Property', prop['name'], None, 'Address', prop['address'], None),
        ('Units', prop['units'], NF_NUM, 'Rentable SF', prop['rentable_sf'], NF_NUM),
        ('Year Built', prop['year_built'], None, 'Structures', prop['structures'], None),
        ('Purchase Price', prop['purchase_price'], NF_DOLLAR, 'Purchase Date', prop['purchase_date'], None),
        ('Garages', prop['garages'], NF_NUM, 'Total Equity', cfg['total_equity'], NF_DOLLAR),
    ]

    for left_lbl, left_val, left_nf, right_lbl, right_val, right_nf in overview:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = left_lbl
        ws.cell(row=row, column=2).font = F_LABEL
        ws.cell(row=row, column=3).value = left_val
        ws.cell(row=row, column=3).font = F_BODY
        if left_nf:
            ws.cell(row=row, column=3).number_format = left_nf
        ws.cell(row=row, column=5).value = right_lbl
        ws.cell(row=row, column=5).font = F_LABEL
        ws.cell(row=row, column=6).value = right_val
        ws.cell(row=row, column=6).font = F_BODY
        if right_nf:
            ws.cell(row=row, column=6).number_format = right_nf
        row += 1

    row += 1  # spacer

    # ── FINANCIAL PERFORMANCE (T-12) ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'FINANCIAL PERFORMANCE (T-12)'
    row += 1

    financials = [
        ('Gross Potential Rent', 'Gross Potential Rent', NF_DOLLAR, False),
        ('Effective Rental Income', 'Effective Rental Income', NF_DOLLAR, False),
        ('Total Other Income', 'Total Other Income', NF_DOLLAR, False),
        ('Effective Gross Income', 'EFFECTIVE GROSS INCOME (EGI)', NF_DOLLAR, False),
        ('Total Operating Expenses', 'Total Operating Expenses', NF_DOLLAR, False),
        ('NET OPERATING INCOME', 'NET OPERATING INCOME (NOI)', NF_DOLLAR, True),
        ('Total Debt Service', 'Total Debt Service', NF_DOLLAR, False),
        ('CASH FLOW AFTER DEBT SVC', 'CASH FLOW AFTER DEBT SERVICE', NF_DOLLAR, True),
        ('Total CapEx', 'Total Capital Expenditures', NF_DOLLAR, False),
        ('NET CASH FLOW', 'NET CASH FLOW', NF_DOLLAR, True),
    ]

    for label, account, nf, is_green in financials:
        if is_green:
            apply_subtotal(ws, row, max_col, green=True)
        else:
            fill = P_ALT if row % 2 == 0 else P_WHITE
            for c in range(1, max_col + 1):
                ws.cell(row=row, column=c).fill = fill

        ws.cell(row=row, column=2).value = label
        ws.cell(row=row, column=2).font = F_GREEN if is_green else F_LABEL
        ws.cell(row=row, column=3).value = f'={t12_sumifs(account)}'
        ws.cell(row=row, column=3).number_format = nf
        ws.cell(row=row, column=3).font = F_GREEN if is_green else F_BODY

        # Per unit
        ws.cell(row=row, column=5).value = 'Per Unit'
        ws.cell(row=row, column=5).font = F_MUTED
        ws.cell(row=row, column=6).value = f'=C{row}/{cfg["property"]["units"]}'
        ws.cell(row=row, column=6).number_format = nf
        ws.cell(row=row, column=6).font = F_BODY
        row += 1

    row += 1  # spacer

    # ── KEY RATIOS ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'KEY RATIOS'
    row += 1

    noi_f = t12_sumifs('NET OPERATING INCOME (NOI)')
    ds_f = t12_sumifs('Total Debt Service')
    egi_f = t12_sumifs('EFFECTIVE GROSS INCOME (EGI)')
    opex_f = t12_sumifs('Total Operating Expenses')
    cfads_f = t12_sumifs('CASH FLOW AFTER DEBT SERVICE')

    ratios = [
        ('DSCR', f'=IF({ds_f}<>0,{noi_f}/{ds_f},0)', NF_PCT2),
        ('Cap Rate', f'={noi_f}/{cfg["purchase_price"]}', NF_PCT2),
        ('Expense Ratio', f'=IF({egi_f}<>0,{opex_f}/{egi_f},0)', NF_PCT),
        ('Cash-on-Cash (CFADS)', f'={cfads_f}/{cfg["total_equity"]}', NF_PCT2),
    ]

    for label, formula, nf in ratios:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = label
        ws.cell(row=row, column=2).font = F_LABEL
        ws.cell(row=row, column=3).value = formula
        ws.cell(row=row, column=3).number_format = nf
        ws.cell(row=row, column=3).font = F_BOLD
        row += 1

    row += 1

    # ── TIC OWNERSHIP ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'TIC OWNERSHIP'
    row += 1

    ws.cell(row=row, column=2).value = 'Owner'
    ws.cell(row=row, column=3).value = 'Ownership %'
    ws.cell(row=row, column=5).value = 'Equity'
    ws.cell(row=row, column=6).value = 'T-12 CFADS Share'
    apply_hdr(ws, row, max_col)
    row += 1

    for owner, info in cfg['tic'].items():
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = owner
        ws.cell(row=row, column=2).font = F_LABEL
        ws.cell(row=row, column=3).value = info['pct']
        ws.cell(row=row, column=3).number_format = NF_PCT2
        ws.cell(row=row, column=5).value = info['equity']
        ws.cell(row=row, column=5).number_format = NF_DOLLAR
        ws.cell(row=row, column=6).value = f'={cfads_f}*{info["pct"]}'
        ws.cell(row=row, column=6).number_format = NF_DOLLAR
        row += 1

    # ── VALUATION ──
    row += 1
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'VALUATION'
    row += 1

    val = cfg['valuation']
    for label, key in [('BOV Low', 'bov_low'), ('BOV Mid', 'bov_mid'), ('BOV High', 'bov_high')]:
        fill = P_ALT if row % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=row, column=c).fill = fill
        ws.cell(row=row, column=2).value = label
        ws.cell(row=row, column=2).font = F_LABEL
        ws.cell(row=row, column=3).value = val[key]
        ws.cell(row=row, column=3).number_format = NF_DOLLAR
        # Implied cap rate
        ws.cell(row=row, column=5).value = 'Implied Cap'
        ws.cell(row=row, column=5).font = F_MUTED
        ws.cell(row=row, column=6).value = f'=IF(C{row}<>0,{noi_f}/C{row},0)'
        ws.cell(row=row, column=6).number_format = NF_PCT2
        row += 1

    hide_beyond(ws, max(row + 2, 45), max_col)
    return ws
