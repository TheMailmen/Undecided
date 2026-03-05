# src/sheets/tic_ownership.py — TIC ownership allocation
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from design import (apply_title, apply_hdr, apply_section, apply_subtotal,
                     set_col_widths, hide_beyond, input_cell,
                     F_BODY, F_BOLD, F_LABEL, F_GREEN, F_CROSS,
                     P_ALT, P_WHITE, P_GREEN_LT,
                     NF_DOLLAR, NF_PCT, NF_PCT2, NF_NUM, A_LEFT)


def build(wb, cfg):
    ws = wb.create_sheet('TIC Ownership')
    max_col = 8
    n = cfg['qpl_rows']

    apply_title(ws, max_col,
                'TIC OWNERSHIP',
                'Ownership allocation and return analysis. Distributions based on T-12 CFADS.')

    # Headers
    headers = ['', 'Owner', 'Ownership %', 'Equity Invested',
               'T-12 NOI Share', 'T-12 CFADS Share', 'Annual CoC', 'Monthly Dist.']
    for c, h in enumerate(headers, 1):
        ws.cell(row=3, column=c).value = h
    apply_hdr(ws, 3, max_col)

    set_col_widths(ws, {'A': 4, 'B': 22, 'C': 14, 'D': 16, 'E': 16, 'F': 16, 'G': 12, 'H': 14})

    # SUMIFS range refs
    sr = f'qPL_Fact!$D$2:$D${n}'
    ac = f'qPL_Fact!$C$2:$C${n}'
    dt = f'qPL_Fact!$A$2:$A${n}'

    # T-12 date range from actual data
    qpl = wb['qPL_Fact']
    months = set()
    for r in range(2, n + 2):
        v = qpl.cell(row=r, column=1).value
        if v:
            if isinstance(v, datetime):
                months.add(v.strftime('%Y-%m-%d'))
            else:
                months.add(str(v))
    months = sorted(months)
    t12_months = months[-12:]
    t12_start = datetime.strptime(t12_months[0], '%Y-%m-%d')
    t12_end = datetime.strptime(t12_months[-1], '%Y-%m-%d')
    date_gte = f'">="&DATE({t12_start.year},{t12_start.month},1)'
    date_lte = f'"<="&DATE({t12_end.year},{t12_end.month},1)'

    # T-12 NOI formula (used in col E)
    noi_formula = f'SUMIFS({sr},{ac},"NET OPERATING INCOME (NOI)",{dt},{date_gte},{dt},{date_lte})'
    # T-12 CFADS formula (used in col F)
    cfads_formula = f'SUMIFS({sr},{ac},"CASH FLOW AFTER DEBT SERVICE",{dt},{date_gte},{dt},{date_lte})'

    owners = list(cfg['tic'].items())
    row = 4
    for i, (owner, info) in enumerate(owners):
        r = row + i
        fill = P_ALT if r % 2 == 0 else P_WHITE
        for c in range(1, max_col + 1):
            ws.cell(row=r, column=c).fill = fill

        ws.cell(row=r, column=2).value = owner
        ws.cell(row=r, column=2).font = F_LABEL
        ws.cell(row=r, column=3).value = info['pct']
        ws.cell(row=r, column=3).number_format = NF_PCT2
        ws.cell(row=r, column=4).value = info['equity']
        ws.cell(row=r, column=4).number_format = NF_DOLLAR

        pct_cell = f'$C${r}'
        # Col E: T-12 NOI share = NOI * ownership%
        ws.cell(row=r, column=5).value = f'={noi_formula}*{pct_cell}'
        ws.cell(row=r, column=5).number_format = NF_DOLLAR
        ws.cell(row=r, column=5).font = F_BODY

        # Col F: T-12 CFADS share = CFADS * ownership%
        ws.cell(row=r, column=6).value = f'={cfads_formula}*{pct_cell}'
        ws.cell(row=r, column=6).number_format = NF_DOLLAR
        ws.cell(row=r, column=6).font = F_BODY

        # Col G: Annual Cash-on-Cash = CFADS share / equity
        ws.cell(row=r, column=7).value = f'=IF(D{r}<>0,F{r}/D{r},0)'
        ws.cell(row=r, column=7).number_format = NF_PCT2
        ws.cell(row=r, column=7).font = F_BODY

        # Col H: Monthly distribution = CFADS share / 12
        ws.cell(row=r, column=8).value = f'=F{r}/12'
        ws.cell(row=r, column=8).number_format = NF_DOLLAR
        ws.cell(row=r, column=8).font = F_BODY

    # Row 7: Totals
    total_row = 7
    apply_subtotal(ws, total_row, max_col)
    ws.cell(row=total_row, column=2).value = 'Total'
    ws.cell(row=total_row, column=2).font = F_BOLD
    ws.cell(row=total_row, column=3).value = f'=SUM(C4:C6)'
    ws.cell(row=total_row, column=3).number_format = NF_PCT2
    ws.cell(row=total_row, column=3).font = F_BOLD
    ws.cell(row=total_row, column=4).value = f'=SUM(D4:D6)'
    ws.cell(row=total_row, column=4).number_format = NF_DOLLAR
    ws.cell(row=total_row, column=4).font = F_BOLD
    ws.cell(row=total_row, column=5).value = f'=SUM(E4:E6)'
    ws.cell(row=total_row, column=5).number_format = NF_DOLLAR
    ws.cell(row=total_row, column=5).font = F_BOLD
    ws.cell(row=total_row, column=6).value = f'=SUM(F4:F6)'
    ws.cell(row=total_row, column=6).number_format = NF_DOLLAR
    ws.cell(row=total_row, column=6).font = F_BOLD
    ws.cell(row=total_row, column=7).value = f'=IF(D7<>0,F7/D7,0)'
    ws.cell(row=total_row, column=7).number_format = NF_PCT2
    ws.cell(row=total_row, column=7).font = F_BOLD
    ws.cell(row=total_row, column=8).value = f'=SUM(H4:H6)'
    ws.cell(row=total_row, column=8).number_format = NF_DOLLAR
    ws.cell(row=total_row, column=8).font = F_BOLD

    # Spacer
    row = 9

    # ── KEY METRICS SECTION ──
    apply_section(ws, row, max_col, accent=True)
    ws.cell(row=row, column=2).value = 'KEY PROPERTY METRICS (T-12)'
    row += 1

    # Metrics using SUMIFS
    metrics = [
        ('Gross Potential Rent', 'Gross Potential Rent', NF_DOLLAR),
        ('Effective Rental Income', 'Effective Rental Income', NF_DOLLAR),
        ('Total Other Income', 'Total Other Income', NF_DOLLAR),
        ('Effective Gross Income', 'EFFECTIVE GROSS INCOME (EGI)', NF_DOLLAR),
        ('Total Operating Expenses', 'Total Operating Expenses', NF_DOLLAR),
        ('', None, None),  # spacer
        ('Expense Ratio', None, NF_PCT),
        ('', None, None),  # spacer
        ('Total Debt Service', 'Total Debt Service', NF_DOLLAR),
        ('Total Capital Expenditures', 'Total Capital Expenditures', NF_DOLLAR),
        ('', None, None),  # spacer
        ('NET OPERATING INCOME (NOI)', 'NET OPERATING INCOME (NOI)', NF_DOLLAR),
        ('CASH FLOW AFTER DEBT SERVICE', 'CASH FLOW AFTER DEBT SERVICE', NF_DOLLAR),
        ('NET CASH FLOW', 'NET CASH FLOW', NF_DOLLAR),
        ('', None, None),  # spacer
        ('DSCR (T-12)', None, NF_PCT2),
        ('Cap Rate', None, NF_PCT2),
        ('Cash-on-Cash (CFADS)', None, NF_PCT2),
    ]

    for label, account, nf in metrics:
        if not label:
            row += 1
            continue

        fill = P_ALT if row % 2 == 0 else P_WHITE
        is_green = label in ('NET OPERATING INCOME (NOI)', 'CASH FLOW AFTER DEBT SERVICE', 'NET CASH FLOW')

        if is_green:
            apply_subtotal(ws, row, max_col, green=True)
        else:
            for c in range(1, max_col + 1):
                ws.cell(row=row, column=c).fill = fill

        ws.cell(row=row, column=2).value = label
        ws.cell(row=row, column=2).font = F_GREEN if is_green else F_LABEL

        if account:
            formula = f'=SUMIFS({sr},{ac},"{account}",{dt},{date_gte},{dt},{date_lte})'
            ws.cell(row=row, column=3).value = formula
        elif label == 'Expense Ratio':
            # Find rows for OpEx and EGI
            egi_f = f'SUMIFS({sr},{ac},"EFFECTIVE GROSS INCOME (EGI)",{dt},{date_gte},{dt},{date_lte})'
            opex_f = f'SUMIFS({sr},{ac},"Total Operating Expenses",{dt},{date_gte},{dt},{date_lte})'
            ws.cell(row=row, column=3).value = f'=IF({egi_f}<>0,{opex_f}/{egi_f},0)'
        elif label == 'DSCR (T-12)':
            noi_f = f'SUMIFS({sr},{ac},"NET OPERATING INCOME (NOI)",{dt},{date_gte},{dt},{date_lte})'
            ds_f = f'SUMIFS({sr},{ac},"Total Debt Service",{dt},{date_gte},{dt},{date_lte})'
            ws.cell(row=row, column=3).value = f'=IF({ds_f}<>0,{noi_f}/{ds_f},0)'
        elif label == 'Cap Rate':
            noi_f = f'SUMIFS({sr},{ac},"NET OPERATING INCOME (NOI)",{dt},{date_gte},{dt},{date_lte})'
            ws.cell(row=row, column=3).value = f'={noi_f}/{cfg["purchase_price"]}'
        elif label == 'Cash-on-Cash (CFADS)':
            cfads_f = f'SUMIFS({sr},{ac},"CASH FLOW AFTER DEBT SERVICE",{dt},{date_gte},{dt},{date_lte})'
            ws.cell(row=row, column=3).value = f'={cfads_f}/{cfg["total_equity"]}'

        if nf:
            ws.cell(row=row, column=3).number_format = nf
        ws.cell(row=row, column=3).font = F_GREEN if is_green else F_BODY

        row += 1

    hide_beyond(ws, max(row, 27), max_col)
    return ws
