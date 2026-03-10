# src/report_pdf.py -- Branded quarterly investor report PDF
import os
from datetime import datetime

from fpdf import FPDF

from config import PROPERTY, TIC

# Brand colors (RGB tuples)
NAVY = (13, 27, 42)
STEEL = (27, 79, 114)
GREEN = (30, 132, 73)
RED = (192, 0, 0)
GOLD = (212, 172, 13)
GRAY = (127, 140, 141)
LIGHT_GRAY = (232, 234, 237)
WHITE = (255, 255, 255)
BODY = (0, 0, 0)
LABEL = (44, 62, 80)


def _sanitize(text):
    """Replace Unicode characters that Helvetica can't render."""
    return text.replace('\u2014', '-').replace('\u2013', '-').replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"').replace('\u2022', '*').replace('\u2713', 'Y').replace('\u00b7', '.')


def _dollar(v, show_sign=False):
    if v is None:
        return '-'
    neg = v < 0
    v = abs(v)
    s = f'${v:,.0f}'
    if neg:
        s = f'({s})'
    elif show_sign and v > 0:
        s = f'+{s}'
    return s


def _pct(v, decimals=1):
    if v is None:
        return '-'
    return f'{v * 100:.{decimals}f}%'


def _x(v, decimals=2):
    if v is None:
        return '-'
    return f'{v:.{decimals}f}x'


def _delta_pct(cur, prior):
    """Compute % change; return formatted string or '-'."""
    if not prior or not cur:
        return '-'
    chg = (cur - prior) / abs(prior)
    sign = '+' if chg >= 0 else ''
    return f'{sign}{chg * 100:.1f}%'


def _kv_grid(pdf, rows, lbl_w=30):
    """Render a 2-column key-value grid. rows: list of (lbl_l, val_l, lbl_r, val_r)."""
    col_w = (pdf.w - 20) / 2
    val_w = col_w - lbl_w
    for (lbl_l, val_l, lbl_r, val_r) in rows:
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(*LABEL)
        pdf.cell(lbl_w, 5.5, lbl_l)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(*BODY)
        pdf.cell(val_w, 5.5, val_l)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(*LABEL)
        pdf.cell(lbl_w, 5.5, lbl_r)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(*BODY)
        pdf.cell(val_w, 5.5, val_r)
        pdf.ln()


class InvestorReport(FPDF):
    """Quarterly investor report PDF."""

    def __init__(self, data):
        super().__init__(orientation='P', unit='mm', format='Letter')
        self.data = data
        self.set_auto_page_break(auto=True, margin=20)

    @property
    def remaining(self):
        """Remaining vertical space before footer (mm)."""
        return self.h - self.get_y() - 20

    def header(self):
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, 22, 'F')

        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(*WHITE)
        self.set_xy(10, 5)
        self.cell(0, 8, PROPERTY['name'].upper(), align='L')

        self.set_font('Helvetica', '', 8)
        self.set_text_color(174, 182, 191)
        self.set_xy(10, 13)
        self.cell(0, 5,
                  f"Quarterly Investor Report  |  {self.data['quarter_label']}",
                  align='L')

        self.set_xy(-70, 13)
        self.cell(60, 5, f"Prepared {datetime.now().strftime('%B %d, %Y')}",
                  align='R')

        self.set_y(26)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', '', 7)
        self.set_text_color(*GRAY)
        self.cell(0, 5, 'CONFIDENTIAL  |  For Authorized Investors Only', align='L')
        self.cell(0, 5, f'Page {self.page_no()}/{{nb}}', align='R')

    # -- Section helpers --

    def section_bar(self, title):
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(*STEEL)
        self.set_text_color(*WHITE)
        self.cell(0, 7, f'  {title}', fill=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)

    def kpi_row(self, items):
        """Render a row of KPI cards. items: list of (label, value, color)."""
        card_w = (self.w - 20) / len(items)
        y_start = self.get_y()
        for i, (label, value, color) in enumerate(items):
            x = 10 + i * card_w
            self.set_fill_color(*LIGHT_GRAY)
            self.rect(x, y_start, card_w - 3, 18, 'F')
            self.set_xy(x + 2, y_start + 2)
            self.set_font('Helvetica', 'B', 14)
            self.set_text_color(*color)
            self.cell(card_w - 7, 8, value, align='C')
            self.set_xy(x + 2, y_start + 10)
            self.set_font('Helvetica', '', 7)
            self.set_text_color(*GRAY)
            self.cell(card_w - 7, 5, label, align='C')
        self.set_y(y_start + 22)

    def table_row(self, cols, widths, bold=False, fill=None, align_list=None):
        self.set_font('Helvetica', 'B' if bold else '', 8)
        self.set_text_color(*BODY)
        if fill:
            self.set_fill_color(*fill)
        if align_list is None:
            align_list = ['L'] + ['R'] * (len(cols) - 1)
        for col, w, a in zip(cols, widths, align_list):
            self.cell(w, 5.5, _sanitize(str(col)), border=0, fill=bool(fill), align=a)
        self.ln()

    def table_header(self, cols, widths, align_list=None):
        self.set_font('Helvetica', 'B', 7)
        self.set_fill_color(*NAVY)
        self.set_text_color(*WHITE)
        if align_list is None:
            align_list = ['L'] + ['R'] * (len(cols) - 1)
        for col, w, a in zip(cols, widths, align_list):
            self.cell(w, 6, _sanitize(str(col)), fill=True, align=a)
        self.ln()

    def ensure_space(self, needed_mm):
        """Add a new page if less than needed_mm remains."""
        if self.remaining < needed_mm:
            self.add_page()

    # -- Page 1: Executive Summary --

    def build_page1(self, charts):
        self.add_page()
        self.alias_nb_pages()

        d = self.data
        s = d['snapshot']
        rr = d['rent_roll']

        # KPI cards
        self.kpi_row([
            ('Quarterly NOI', _dollar(s['noi']), GREEN),
            ('Avg DSCR', _x(s['dscr']), STEEL),
            ('Occupancy', _pct(rr['occupancy'], 1), STEEL),
            ('Cash-on-Cash (Ann.)', _pct(s['coc'], 1), GOLD),
        ])

        # Property overview
        self.section_bar('PROPERTY OVERVIEW')
        p = d['property']
        _kv_grid(self, [
            ('Property', p['name'], 'Purchase Price', _dollar(p['purchase_price'])),
            ('Address', p['address'], 'Year Built', str(p['year_built'])),
            ('Units', str(p['units']), 'Structures', p['structures']),
            ('Rentable SF', f"{p['rentable_sf']:,}", 'Garages', str(p['garages'])),
        ])
        self.ln(3)

        # Quarter-over-quarter performance chart
        if 'quarterly_perf' in charts:
            self.image(charts['quarterly_perf'], x=10, w=self.w - 20)
            self.ln(3)

        # Financial snapshot: month-by-month + quarter total
        self.section_bar(f"FINANCIAL SNAPSHOT - {d['quarter_label'].upper()}")

        md = d.get('month_detail', [])
        prior = d.get('snapshot_prior', {})

        if md:
            # Columns: Label | Month1 | Month2 | Month3 | Q Total | vs Prior Q
            m_labels = [m['label'] for m in md]
            col_w_label = 45
            n_months = len(md)
            col_w_month = 27
            col_w_total = 30
            col_w_delta = 25
            w = [col_w_label] + [col_w_month] * n_months + [col_w_total, col_w_delta]
            headers = [''] + m_labels + [d['quarter_label'], 'vs Prior Q']
            self.table_header(headers, w)

            units = d['property']['units']
            lines = [
                ('Eff. Rental Income', 'egi', None),
                ('Operating Expenses', 'opex', None),
                ('NET OPERATING INCOME', 'noi', 'noi'),
                ('Total Debt Service', 'debt_service', None),
                ('CASH FLOW AFTER DEBT', 'cfads', 'cfads'),
                ('Total CapEx', None, None),
                ('NET CASH FLOW', 'ncf', 'ncf'),
            ]

            green_rows = {'NET OPERATING INCOME', 'CASH FLOW AFTER DEBT', 'NET CASH FLOW'}
            for i, (label, snap_key, prior_key) in enumerate(lines):
                is_green = label in green_rows
                fill_color = (232, 245, 233) if is_green else (
                    LIGHT_GRAY if i % 2 == 0 else None)

                # Get month values
                month_vals = []
                for m in md:
                    # Map label to month_detail key
                    key_map = {
                        'Eff. Rental Income': 'egi',
                        'Operating Expenses': 'opex',
                        'NET OPERATING INCOME': 'noi',
                        'Total Debt Service': 'debt_service',
                        'CASH FLOW AFTER DEBT': 'cfads',
                        'Total CapEx': 'ncf',  # placeholder
                        'NET CASH FLOW': 'ncf',
                    }
                    if label == 'Total CapEx':
                        # CapEx not in month_detail, use snapshot
                        month_vals.append('')
                    else:
                        month_vals.append(_dollar(m.get(key_map.get(label, ''), 0)))

                # Quarter total from snapshot
                snap_map = {
                    'Eff. Rental Income': 'egi',
                    'Operating Expenses': 'opex',
                    'NET OPERATING INCOME': 'noi',
                    'Total Debt Service': 'debt_service',
                    'CASH FLOW AFTER DEBT': 'cfads',
                    'Total CapEx': 'capex',
                    'NET CASH FLOW': 'ncf',
                }
                q_total = s.get(snap_map.get(label, ''), 0)

                # Delta vs prior quarter
                delta = '-'
                if prior_key and prior.get(prior_key):
                    delta = _delta_pct(q_total, prior[prior_key])

                if label == 'Total CapEx':
                    month_vals = [''] * n_months

                row_data = [f'  {label}'] + month_vals + [_dollar(q_total), delta]

                self.set_font('Helvetica', 'B' if is_green else '', 8)
                self.set_text_color(*(GREEN if is_green else BODY))
                self.table_row(row_data, w, bold=is_green, fill=fill_color)
        else:
            # Fallback: simple 3-column table
            w = [70, 35, 35, 35]
            self.table_header(['', 'Quarter Total', 'T-12 Total', '$/Unit (T-12)'], w)
            units = d['property']['units']
            lines = [
                ('Effective Rental Income', s['eri'], d['t12']['eri']),
                ('Total Other Income', s['other_income'], d['t12']['other_income']),
                ('Effective Gross Income', s['egi'], d['t12']['egi']),
                ('Total Operating Expenses', s['opex'], d['t12']['opex']),
                ('NET OPERATING INCOME', s['noi'], d['t12']['noi']),
                ('Total Debt Service', s['debt_service'], d['t12']['debt_service']),
                ('CASH FLOW AFTER DEBT', s['cfads'], d['t12']['cfads']),
                ('Total CapEx', s['capex'], d['t12']['capex']),
                ('NET CASH FLOW', s['ncf'], d['t12']['ncf']),
            ]
            green_rows = {'NET OPERATING INCOME', 'CASH FLOW AFTER DEBT', 'NET CASH FLOW'}
            for i, (label, cur, t12v) in enumerate(lines):
                is_green = label in green_rows
                fill_color = (232, 245, 233) if is_green else (
                    LIGHT_GRAY if i % 2 == 0 else None)
                per_unit = t12v / units if units else 0
                self.set_font('Helvetica', 'B' if is_green else '', 8)
                self.set_text_color(*(GREEN if is_green else BODY))
                self.table_row(
                    [f'  {label}', _dollar(cur), _dollar(t12v), _dollar(per_unit)],
                    w, bold=is_green, fill=fill_color,
                )

    # -- Page 2: Occupancy Deep Dive --

    def build_page2(self, charts):
        self.add_page()
        d = self.data
        rr = d['rent_roll']

        # Occupancy chart
        if 'occupancy' in charts:
            self.image(charts['occupancy'], x=10, w=self.w - 20)
            self.ln(3)

        # Occupancy summary KPIs
        self.section_bar('OCCUPANCY & RENT ROLL')
        _kv_grid(self, [
            ('Total Units', str(rr['total_units']), 'Occupied', str(rr['occupied'])),
            ('Vacant', str(rr['vacant']), 'Occupancy', _pct(rr['occupancy'], 1)),
            ('Total Rent', _dollar(rr['total_rent']), 'Avg Rent', _dollar(rr['avg_rent'])),
        ])
        self.ln(3)

        # Unit mix table
        unit_mix = rr.get('unit_mix', [])
        if unit_mix:
            self.ensure_space(30)
            self.section_bar('UNIT MIX BREAKDOWN')
            mw = [35, 20, 20, 20, 25, 25, 25]
            self.table_header(
                ['Type', 'Units', 'Occupied', 'Vacant', 'Occupancy', 'Avg Rent', 'Avg Market'],
                mw,
            )
            for i, mix in enumerate(unit_mix):
                fill = LIGHT_GRAY if i % 2 == 0 else None
                self.table_row(
                    [mix['type'], str(mix['units']), str(mix['occupied']),
                     str(mix['vacant']), _pct(mix['occupancy'], 1),
                     _dollar(mix['avg_rent']), _dollar(mix['avg_market'])],
                    mw, fill=fill,
                )
            # Totals row
            tot_units = sum(m['units'] for m in unit_mix)
            tot_occ = sum(m['occupied'] for m in unit_mix)
            tot_vac = sum(m['vacant'] for m in unit_mix)
            self.table_row(
                ['Total', str(tot_units), str(tot_occ), str(tot_vac),
                 _pct(rr['occupancy'], 1), _dollar(rr['avg_rent']), ''],
                mw, bold=True, fill=(232, 245, 233),
            )
            self.ln(3)

        # Condition mix (Renovated vs Classic)
        condition_mix = rr.get('condition_mix', [])
        if condition_mix:
            self.ensure_space(30)
            self.section_bar('RENOVATED vs CLASSIC')
            cw = [40, 20, 20, 25, 30, 30]
            self.table_header(
                ['Condition', 'Units', 'Occupied', 'Occupancy', 'Avg Rent', 'Avg Market'],
                cw,
            )
            for i, cond in enumerate(condition_mix):
                fill = LIGHT_GRAY if i % 2 == 0 else None
                self.table_row(
                    [cond['condition'], str(cond['units']), str(cond['occupied']),
                     _pct(cond['occupancy'], 1),
                     _dollar(cond['avg_rent']), _dollar(cond['avg_market'])],
                    cw, fill=fill,
                )
            self.ln(3)

        # Leasing activity & turnover
        self.ensure_space(35)
        self.section_bar('LEASING ACTIVITY & TURNOVER')
        _kv_grid(self, [
            ('Move-Ins (Q)', str(rr.get('q_move_ins', 0)),
             'Move-Outs (Q)', str(rr.get('q_move_outs', 0))),
            ('Ann. Turnover', _pct(rr.get('annualized_turnover', 0), 1),
             'Loss-to-Lease/Mo', _dollar(rr.get('loss_to_lease_total', 0))),
            ('Avg LTL/Unit', _dollar(rr.get('loss_to_lease_avg', 0)),
             '', ''),
        ])
        self.ln(3)

        # Rent growth
        self.ensure_space(25)
        self.section_bar('RENT GROWTH')
        _kv_grid(self, [
            ('Q Rent Growth', _pct(rr.get('rent_growth_q', 0), 1),
             'Since Acquisition', _pct(rr.get('rent_growth_acq', 0), 1)),
            ('Avg Rent (Acq)', _dollar(rr.get('avg_rent_start_acq', 0)),
             'Avg Rent (Now)', _dollar(rr.get('avg_rent_end_acq', 0))),
        ])
        self.ln(3)

    # -- Page 3: Cash Flow & Distributions --

    def build_page3(self, charts):
        self.add_page()
        d = self.data

        # Monthly NOI trend chart
        if 'noi_trend' in charts:
            self.image(charts['noi_trend'], x=10, w=self.w - 20)
            self.ln(3)

        # Waterfall chart
        if 'waterfall' in charts:
            self.ensure_space(60)
            self.image(charts['waterfall'], x=10, w=self.w - 20)
            self.ln(3)

        # Renovation progress
        ren = d['renovations']
        self.ensure_space(35)
        self.section_bar('RENOVATION PROGRESS')
        _kv_grid(self, [
            ('Units Completed', str(ren['completed']),
             'Total Planned', str(ren['total_planned'])),
            ('Avg Rent Lift', _dollar(ren['avg_rent_lift']),
             'CapEx Budget', _dollar(ren['budget'])),
            ('T-12 CapEx Spent', _dollar(ren['spent']),
             'Remaining', _dollar(ren['budget'] - ren['spent'])),
        ])
        self.ln(3)

        # TIC distributions
        num_owners = len(d['tic'])
        table_h = 9 + 6 + (num_owners * 5.5) + 5
        self.ensure_space(table_h)

        self.section_bar('OWNER DISTRIBUTIONS')
        tw = [50, 22, 28, 30, 30, 25]
        self.table_header(
            ['Owner', 'Ownership %', 'Equity', 'Q Share', 'T-12 Share', 'CoC (Ann.)'],
            tw,
        )
        for i, (owner, info) in enumerate(d['tic'].items()):
            fill = LIGHT_GRAY if i % 2 == 0 else None
            self.table_row(
                [owner, _pct(info['pct'], 2), _dollar(info['equity']),
                 _dollar(info['quarterly_share']), _dollar(info['t12_share']),
                 _pct(info['coc'], 1)],
                tw, fill=fill,
            )
        self.ln(3)

        # Escrow
        self.ensure_space(55)
        self._build_escrow()

        # Key metrics + valuation
        self.ensure_space(60)
        self._build_metrics_and_valuation()

    def _build_escrow(self):
        d = self.data
        self.section_bar('ESCROW ACCOUNTS')
        ew = [55, 35, 35, 35]
        self.table_header(['Account', 'Total Deposits', 'Total Payments', 'Est. Balance'], ew)
        total_bal = 0
        for i, (name, info) in enumerate(d['escrow'].items()):
            fill = LIGHT_GRAY if i % 2 == 0 else None
            self.table_row(
                [name, _dollar(info['total_deposits']),
                 _dollar(info['total_payments']), _dollar(info['balance'])],
                ew, fill=fill,
            )
            total_bal += info['balance']
        self.table_row(
            ['Total Escrow Balance', '', '', _dollar(total_bal)],
            ew, bold=True, fill=(232, 245, 233),
        )
        self.ln(5)

    def _build_metrics_and_valuation(self):
        d = self.data
        s = d['snapshot']

        self.section_bar('KEY METRICS')
        _kv_grid(self, [
            ('DSCR (Avg)', _x(s['dscr']), 'Cap Rate', _pct(s['cap_rate'], 2)),
            ('Expense Ratio', _pct(s['expense_ratio'], 1),
             'Cash-on-Cash (Ann.)', _pct(s['coc'], 1)),
            ('BOV (Mid)', _dollar(d['valuation']['bov_mid']),
             'Est. Loan Balance', _dollar(d['loan']['est_current_balance'])),
        ])
        self.ln(5)

        self.section_bar('VALUATION ANALYSIS')
        vw = [55, 35, 35, 35]
        self.table_header(['Scenario', 'Value', 'Implied Cap Rate', 'Equity Above Debt'], vw)
        loan_bal = d['loan']['est_current_balance']
        t12_noi = d['t12']['noi']
        for i, (label, key) in enumerate([
            ('Low', 'bov_low'), ('Mid', 'bov_mid'), ('High', 'bov_high')
        ]):
            val = d['valuation'][key]
            cap = t12_noi / val if val else 0
            equity = val - loan_bal
            fill = LIGHT_GRAY if i % 2 == 0 else None
            self.table_row(
                [f'  {label}', _dollar(val), _pct(cap, 2), _dollar(equity)],
                vw, fill=fill,
            )


    # -- Page 4: Market Comps, OpEx, Property Condition --

    def build_page4(self, charts):
        self.add_page()
        d = self.data
        mc = d.get('market_comps', {})

        # --- Rent Comps: 1BR ---
        comps_1br = mc.get('rent_comps_1br', [])
        if comps_1br:
            self.section_bar('RENT COMPARABLES - ONE BEDROOM')
            rw = [50, 18, 18, 25, 25, 25]
            self.table_header(
                ['Property', 'Built', 'Avg SF', 'Avg Rent', '$/SF', 'Occ %'], rw)
            for i, c in enumerate(comps_1br):
                fill = LIGHT_GRAY if i % 2 == 0 else None
                self.table_row(
                    [c['property'], str(c['built']), f"{c['avg_sf']:,.0f}",
                     _dollar(c['rent']), f"${c['rent_psf']:.2f}",
                     _pct(c['occ'], 0)],
                    rw, fill=fill,
                )
            # Groves row for comparison
            p = d['property']
            groves_1br_rent = d['rent_roll']['avg_rent']  # approximate
            self.table_row(
                ['THE GROVES (Subject)', str(p['year_built']), '765',
                 _dollar(groves_1br_rent), '', _pct(d['rent_roll']['occupancy'], 0)],
                rw, bold=True, fill=(232, 245, 233),
            )
            self.ln(3)

        # --- Rent Comps: 2BR ---
        comps_2br = mc.get('rent_comps_2br', [])
        if comps_2br:
            self.ensure_space(50)
            self.section_bar('RENT COMPARABLES - TWO BEDROOM')
            self.table_header(
                ['Property', 'Built', 'Avg SF', 'Avg Rent', '$/SF', 'Occ %'], rw)
            for i, c in enumerate(comps_2br):
                fill = LIGHT_GRAY if i % 2 == 0 else None
                self.table_row(
                    [c['property'], str(c['built']), f"{c['avg_sf']:,.0f}",
                     _dollar(c['rent']), f"${c['rent_psf']:.2f}",
                     _pct(c['occ'], 0)],
                    rw, fill=fill,
                )
            self.table_row(
                ['THE GROVES (Subject)', str(p['year_built']), '890',
                 _dollar(groves_1br_rent), '', _pct(d['rent_roll']['occupancy'], 0)],
                rw, bold=True, fill=(232, 245, 233),
            )
            self.ln(3)

        # --- Sale Comps ---
        sale_comps = mc.get('sale_comps', [])
        if sale_comps:
            self.ensure_space(50)
            self.section_bar('SALE COMPARABLES')
            sw = [45, 20, 18, 30, 28, 20]
            self.table_header(
                ['Property', 'Close', 'Units', 'Sale Price', '$/Unit', 'Built'], sw)
            for i, c in enumerate(sale_comps):
                fill = LIGHT_GRAY if i % 2 == 0 else None
                self.table_row(
                    [c['property'], c['close_date'], str(c['units']),
                     _dollar(c['sale_price']), _dollar(c['per_unit']),
                     str(c.get('built', ''))],
                    sw, fill=fill,
                )
            # Groves implied value
            bov = d['valuation']['bov_mid']
            per_unit = bov / p['units'] if p['units'] else 0
            self.table_row(
                ['THE GROVES (BOV Mid)', '', str(p['units']),
                 _dollar(bov), _dollar(per_unit), str(p['year_built'])],
                sw, bold=True, fill=(232, 245, 233),
            )
            self.ln(3)

        # --- OpEx Breakdown ---
        ob = d.get('opex_breakdown', {})
        detail = ob.get('detail', [])
        if detail:
            self.ensure_space(70)
            self.section_bar(f"OPERATING EXPENSE BREAKDOWN - {d['quarter_label'].upper()}")
            ow = [55, 30, 28, 28, 20]
            self.table_header(
                ['Expense Category', 'Q Amount', '% of OpEx', '% of EGI', 'Ann.'], ow)
            # Show top 12 items
            for i, item in enumerate(detail[:12]):
                fill = LIGHT_GRAY if i % 2 == 0 else None
                ann = item['amount'] * 4  # annualize quarterly
                self.table_row(
                    [f"  {item['account']}", _dollar(item['amount']),
                     _pct(item['pct_of_opex'], 1), _pct(item['pct_of_egi'], 1),
                     _dollar(ann)],
                    ow, fill=fill,
                )
            # If more items, show "Other" roll-up
            if len(detail) > 12:
                other_amt = sum(x['amount'] for x in detail[12:])
                self.table_row(
                    ['  Other', _dollar(other_amt),
                     _pct(other_amt / ob['total'] if ob['total'] else 0, 1),
                     _pct(other_amt / ob['egi'] if ob['egi'] else 0, 1),
                     _dollar(other_amt * 4)],
                    ow, fill=LIGHT_GRAY,
                )
            self.table_row(
                ['Total Operating Expenses', _dollar(ob['total']),
                 '100.0%', _pct(ob['expense_ratio'], 1),
                 _dollar(ob['total'] * 4)],
                ow, bold=True, fill=(232, 245, 233),
            )
            self.ln(3)

    # -- Page 5: Property Condition --

    def build_page5(self, charts):
        pc = self.data.get('property_condition', [])
        if not pc:
            return

        self.add_page()

        self.section_bar('CAPITAL IMPROVEMENTS & PROPERTY CONDITION')

        pw = [40, 80, 22, 22]
        self.table_header(['System', 'Detail', 'Updated', 'Status'], pw)

        # Color-code status
        status_colors = {
            'Good': (232, 245, 233),      # light green
            'Monitor': (255, 249, 196),     # light yellow
            'Watch': (253, 237, 236),       # light red
            'Planned': (232, 234, 237),     # light gray
        }

        current_system = ''
        for i, item in enumerate(pc):
            status = item['status']
            fill = status_colors.get(status, LIGHT_GRAY if i % 2 == 0 else None)

            # Show system name only on first row of each group
            system_label = item['system'] if item['system'] != current_system else ''
            current_system = item['system']

            # Truncate long detail text
            detail_text = item['detail']
            if len(detail_text) > 55:
                detail_text = detail_text[:52] + '...'

            self.table_row(
                [system_label, detail_text, item['updated'], status],
                pw, fill=fill,
                bold=(system_label != ''),
            )

        self.ln(5)

        # Legend
        self.set_font('Helvetica', '', 7)
        self.set_text_color(*GRAY)
        legend_items = [
            ('Good', (232, 245, 233)),
            ('Monitor', (255, 249, 196)),
            ('Watch', (253, 237, 236)),
            ('Planned', (232, 234, 237)),
        ]
        self.cell(20, 4, 'Legend:', align='L')
        for label, color in legend_items:
            self.set_fill_color(*color)
            self.cell(4, 4, '', fill=True)
            self.cell(1, 4, '')
            self.cell(18, 4, label, align='L')
        self.ln()


def build_report(data, charts, out_path=None):
    """Generate the quarterly investor report PDF."""
    if out_path is None:
        q_label = data['quarter_label'].replace(' ', '_')
        out_path = os.path.join('output', f'Groves_Investor_Report_{q_label}.pdf')

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)

    pdf = InvestorReport(data)
    pdf.build_page1(charts)
    pdf.build_page2(charts)
    pdf.build_page3(charts)
    pdf.build_page4(charts)
    pdf.build_page5(charts)
    pdf.output(out_path)
    return out_path
