# src/report_pdf.py -- Branded monthly investor report PDF
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
    """Monthly investor report PDF."""

    def __init__(self, data):
        super().__init__(orientation='P', unit='mm', format='Letter')
        self.data = data
        self.set_auto_page_break(auto=True, margin=20)

    @property
    def remaining(self):
        """Remaining vertical space before footer (mm)."""
        return self.h - self.get_y() - 20  # 20mm bottom margin

    def header(self):
        # Navy header bar
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, 22, 'F')

        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(*WHITE)
        self.set_xy(10, 5)
        self.cell(0, 8, PROPERTY['name'].upper(), align='L')

        self.set_font('Helvetica', '', 8)
        self.set_text_color(174, 182, 191)
        self.set_xy(10, 13)
        self.cell(0, 5, f"Monthly Investor Report  |  {self.data['report_label']}",
                  align='L')

        # Right side: prepared date
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
            # Value
            self.set_xy(x + 2, y_start + 2)
            self.set_font('Helvetica', 'B', 14)
            self.set_text_color(*color)
            self.cell(card_w - 7, 8, value, align='C')
            # Label
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
            self.cell(w, 5.5, str(col), border=0, fill=bool(fill), align=a)
        self.ln()

    def table_header(self, cols, widths, align_list=None):
        self.set_font('Helvetica', 'B', 7)
        self.set_fill_color(*NAVY)
        self.set_text_color(*WHITE)
        if align_list is None:
            align_list = ['L'] + ['R'] * (len(cols) - 1)
        for col, w, a in zip(cols, widths, align_list):
            self.cell(w, 6, str(col), fill=True, align=a)
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
            ('Net Operating Income', _dollar(s['noi']), GREEN),
            ('DSCR', _x(s['dscr']), STEEL),
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

        # NOI trend chart
        if 'noi_trend' in charts:
            self.image(charts['noi_trend'], x=10, w=self.w - 20)
            self.ln(3)

        # Financial snapshot table
        self.section_bar(f"FINANCIAL SNAPSHOT - {d['report_label'].upper()}")
        w = [70, 35, 35, 35]
        self.table_header(['', 'Current Month', 'T-12 Total', '$/Unit (T-12)'], w)

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
            self.set_font('Helvetica', 'B' if is_green else '', 8)
            self.set_text_color(*(GREEN if is_green else BODY))
            per_unit = t12v / units if units else 0
            self.table_row(
                [f'  {label}', _dollar(cur), _dollar(t12v), _dollar(per_unit)],
                w, bold=is_green, fill=fill_color,
            )

    # -- Page 2: Operations & Distributions --

    def build_page2(self, charts):
        self.add_page()
        d = self.data

        # Occupancy chart
        if 'occupancy' in charts:
            self.image(charts['occupancy'], x=10, w=self.w - 20)
            self.ln(3)

        # Rent roll summary
        rr = d['rent_roll']
        self.section_bar('OCCUPANCY & RENT ROLL')
        _kv_grid(self, [
            ('Total Units', str(rr['total_units']), 'Occupied', str(rr['occupied'])),
            ('Vacant', str(rr['vacant']), 'Occupancy', _pct(rr['occupancy'], 1)),
            ('Total Rent', _dollar(rr['total_rent']), 'Avg Rent', _dollar(rr['avg_rent'])),
        ])
        self.ln(3)

        # Waterfall chart
        if 'waterfall' in charts:
            self.image(charts['waterfall'], x=10, w=self.w - 20)
            self.ln(3)

        # Renovation progress
        ren = d['renovations']
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

        # TIC distributions -- keep the whole table together
        num_owners = len(d['tic'])
        table_h = 9 + 6 + (num_owners * 5.5) + 5  # bar + header + rows + spacing
        self.ensure_space(table_h)

        self.section_bar('OWNER DISTRIBUTIONS')
        tw = [55, 25, 30, 30, 30, 25]
        self.table_header(
            ['Owner', 'Ownership %', 'Equity', 'Monthly Share', 'T-12 Share', 'CoC (Ann.)'],
            tw,
        )
        for i, (owner, info) in enumerate(d['tic'].items()):
            fill = LIGHT_GRAY if i % 2 == 0 else None
            self.table_row(
                [owner, _pct(info['pct'], 2), _dollar(info['equity']),
                 _dollar(info['monthly_share']), _dollar(info['t12_share']),
                 _pct(info['coc'], 1)],
                tw, fill=fill,
            )
        self.ln(3)

        # Escrow -- check if it fits on this page, otherwise new page
        self.ensure_space(55)
        self._build_escrow()

        # Key metrics + valuation -- check space
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
            ('DSCR', _x(s['dscr']), 'Cap Rate', _pct(s['cap_rate'], 2)),
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


def build_report(data, charts, out_path=None):
    """Generate the investor report PDF."""
    if out_path is None:
        month_str = data['report_date'].strftime('%Y-%m')
        out_path = os.path.join('output', f'Groves_Investor_Report_{month_str}.pdf')

    pdf = InvestorReport(data)
    pdf.build_page1(charts)
    pdf.build_page2(charts)
    pdf.output(out_path)
    return out_path
