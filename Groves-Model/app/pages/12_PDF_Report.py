"""PDF Report — One-click investor report generation."""

import os
import sys
import tempfile
from datetime import date

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_engine import get_t12_totals, load_pl_data
from ui.theme import inject_theme
from ui.components import page_header, no_data_page, page_footer

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

page_header(
    "Investor Report (PDF)",
    "Generate a professional PDF summary for investors",
)

# ── Data guard ────────────────────────────────────────────────
if no_data_page("pl_actuals.csv"):
    st.stop()

# ── Data loading ──────────────────────────────────────────────────
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
PL_CSV = os.path.join(BASE_DIR, 'data', 'pl_actuals.csv')

cfg = {
    'total_equity': st.session_state.total_equity,
    'purchase_price': st.session_state.property['purchase_price'],
}


@st.cache_data(show_spinner="Loading financial data...")
def load_data(_version, csv_path, total_equity, purchase_price):
    return load_pl_data(csv_path, {
        'total_equity': total_equity,
        'purchase_price': purchase_price,
    })


df = load_data(
    st.session_state.data_version, PL_CSV,
    cfg['total_equity'], cfg['purchase_price'],
)
t12 = get_t12_totals(df)


def _fmt(v):
    if v < 0:
        return f"(${abs(v):,.0f})"
    return f"${v:,.0f}"


def generate_pdf():
    """Generate investor report PDF and return bytes."""
    from fpdf import FPDF

    prop = st.session_state.property
    loan = st.session_state.loan

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Page 1: Executive Summary ─────────────────────────────
    pdf.add_page()

    # Title bar — Lakeshore navy #0B1F3B
    pdf.set_fill_color(11, 31, 59)  # #0B1F3B
    pdf.rect(0, 0, 210, 30, 'F')
    # Accent stripe
    pdf.set_fill_color(47, 143, 157)  # #2F8F9D
    pdf.rect(0, 28, 210, 2, 'F')
    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(10, 6)
    pdf.cell(190, 10, prop['name'], align='L')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_xy(10, 17)
    pdf.set_text_color(200, 210, 220)
    pdf.cell(190, 6, f"Lakeshore Management  |  Investor Report  |  {date.today().strftime('%B %d, %Y')}", align='L')

    # Reset text color
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(35)

    # Property Overview section
    pdf.set_fill_color(11, 31, 59)  # #0B1F3B
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(190, 8, '  PROPERTY OVERVIEW', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Helvetica', '', 10)
    pdf.ln(2)

    overview_items = [
        ('Property', prop['name']),
        ('Address', prop['address']),
        ('Units', str(prop['units'])),
        ('Rentable SF', f"{prop['rentable_sf']:,}"),
        ('Year Built', str(prop['year_built'])),
        ('Purchase Price', _fmt(prop['purchase_price'])),
        ('Purchase Date', prop['purchase_date']),
        ('Total Equity', _fmt(st.session_state.total_equity)),
    ]

    for label, value in overview_items:
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(55, 6, f"  {label}:", border=0)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(135, 6, value, border=0, ln=True)

    pdf.ln(4)

    # Financial Performance section
    pdf.set_fill_color(27, 79, 114)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(190, 8, '  FINANCIAL PERFORMANCE (T-12)', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    noi = t12['NET OPERATING INCOME (NOI)']
    cfads = t12['CASH FLOW AFTER DEBT SERVICE']
    ncf = t12['NET CASH FLOW']
    units = prop['units']

    fin_items = [
        ('Effective Gross Income', t12.get('EFFECTIVE GROSS INCOME (EGI)', 0), False),
        ('Total Operating Expenses', t12.get('Total Operating Expenses', 0), False),
        ('NET OPERATING INCOME', noi, True),
        ('Total Debt Service', t12.get('Total Debt Service', 0), False),
        ('CASH FLOW AFTER DEBT SVC', cfads, True),
        ('Total Capital Expenditures', t12.get('Total Capital Expenditures', 0), False),
        ('NET CASH FLOW', ncf, True),
    ]

    for label, val, is_key in fin_items:
        if is_key:
            pdf.set_fill_color(224, 242, 254)  # #E0F2FE — accent tint
            pdf.set_text_color(47, 143, 157)  # #2F8F9D
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(80, 7, f"  {label}", border=0, fill=True)
            pdf.cell(55, 7, _fmt(val), align='R', border=0, fill=True)
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(127, 140, 141)
            per_unit = val / units if units else 0
            pdf.cell(55, 7, f"${per_unit:,.0f}/unit", align='R', border=0, fill=True, ln=True)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(80, 6, f"  {label}", border=0)
            pdf.cell(55, 6, _fmt(val), align='R', border=0)
            per_unit = val / units if units else 0
            pdf.set_text_color(127, 140, 141)
            pdf.cell(55, 6, f"${per_unit:,.0f}/unit", align='R', border=0, ln=True)
            pdf.set_text_color(0, 0, 0)

    pdf.ln(4)

    # Key Ratios
    pdf.set_fill_color(27, 79, 114)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(190, 8, '  KEY RATIOS', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    ds = t12.get('Total Debt Service', 0)
    egi = t12.get('EFFECTIVE GROSS INCOME (EGI)', 0)
    opex = t12.get('Total Operating Expenses', 0)
    equity = st.session_state.total_equity
    pp = prop['purchase_price']

    ratios = [
        ('DSCR', f"{noi/ds:.2f}x" if ds else "N/A"),
        ('Cap Rate', f"{noi/pp*100:.2f}%" if pp else "N/A"),
        ('Expense Ratio', f"{opex/egi*100:.1f}%" if egi else "N/A"),
        ('Cash-on-Cash (CFADS)', f"{cfads/equity*100:.2f}%" if equity else "N/A"),
        ('Cash-on-Cash (NCF)', f"{ncf/equity*100:.2f}%" if equity else "N/A"),
    ]

    for label, value in ratios:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(80, 7, f"  {label}", border=0)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(110, 7, value, align='L', border=0, ln=True)

    pdf.ln(4)

    # Loan Summary
    pdf.set_fill_color(27, 79, 114)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(190, 8, '  LOAN SUMMARY', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    loan_items = [
        ('Original Amount', _fmt(loan['original_amount'])),
        ('Est. Current Balance', _fmt(loan['est_current_balance'])),
        ('Interest Rate', f"{loan['rate']*100:.2f}%"),
        ('Amortization', f"{loan['amort_years']} years"),
        ('Term', f"{loan['term_years']} years"),
        ('Type', 'Interest Only' if loan['io'] else 'Amortizing'),
    ]

    for label, value in loan_items:
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(55, 6, f"  {label}:", border=0)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(135, 6, value, border=0, ln=True)

    # ── Page 2: TIC Ownership ─────────────────────────────────
    pdf.add_page()

    # Title bar — Lakeshore navy
    pdf.set_fill_color(11, 31, 59)
    pdf.rect(0, 0, 210, 22, 'F')
    pdf.set_fill_color(47, 143, 157)
    pdf.rect(0, 20, 210, 2, 'F')
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(10, 5)
    pdf.cell(190, 10, 'TIC Ownership & Distributions', align='L')
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(27)

    # TIC table header
    pdf.set_fill_color(11, 31, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(50, 7, '  Owner', fill=True)
    pdf.cell(30, 7, 'Ownership %', align='C', fill=True)
    pdf.cell(40, 7, 'Equity', align='R', fill=True)
    pdf.cell(40, 7, 'T-12 CFADS', align='R', fill=True)
    pdf.cell(30, 7, 'CoC', align='R', fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)

    for i, (owner, info) in enumerate(st.session_state.tic.items()):
        pct = info['pct']
        eq = info['equity']
        owner_cfads = cfads * pct
        coc = owner_cfads / eq * 100 if eq else 0

        if i % 2 == 0:
            pdf.set_fill_color(247, 249, 252)
            fill = True
        else:
            fill = False

        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(50, 6, f"  {owner}", fill=fill)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(30, 6, f"{pct*100:.3f}%", align='C', fill=fill)
        pdf.cell(40, 6, _fmt(eq), align='R', fill=fill)
        pdf.cell(40, 6, _fmt(owner_cfads), align='R', fill=fill)
        pdf.cell(30, 6, f"{coc:.2f}%", align='R', fill=fill, ln=True)

    pdf.ln(8)

    # Valuation
    pdf.set_fill_color(27, 79, 114)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(190, 8, '  VALUATION (BOV)', ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    val = st.session_state.valuation
    for label, key in [('Low', 'bov_low'), ('Mid', 'bov_mid'), ('High', 'bov_high')]:
        v = val[key]
        implied_cap = noi / v * 100 if v else 0
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(30, 6, f"  {label}:", border=0)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(50, 6, _fmt(v), border=0)
        pdf.set_text_color(127, 140, 141)
        pdf.cell(50, 6, f"(Implied Cap: {implied_cap:.2f}%)", border=0, ln=True)
        pdf.set_text_color(0, 0, 0)

    pdf.ln(6)

    # Footer
    pdf.set_y(-25)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(127, 140, 141)
    pdf.cell(190, 5, f"Generated {date.today().strftime('%B %d, %Y')}  |  Confidential — For Investor Use Only", align='C')

    return pdf.output()


# ── Report Preview ────────────────────────────────────────────────
prop = st.session_state.property
st.info(
    f"**Report will include:**\n"
    f"- Property Overview ({prop['name']}, {prop['units']} units)\n"
    f"- T-12 Financial Performance (NOI: {_fmt(t12['NET OPERATING INCOME (NOI)'])})\n"
    f"- Key Ratios (DSCR, Cap Rate, Cash-on-Cash)\n"
    f"- Loan Summary\n"
    f"- TIC Ownership & Distributions\n"
    f"- Valuation (BOV)"
)

# ── Generate Button ───────────────────────────────────────────────
if st.button("Generate PDF Report", type="primary", use_container_width=True):
    with st.spinner("Generating report..."):
        try:
            pdf_bytes = generate_pdf()
            st.session_state.pdf_bytes = pdf_bytes
            st.success("Report generated successfully!")
        except ImportError:
            st.error("fpdf2 package required. Install with: `pip install fpdf2`")
        except Exception as e:
            st.error(f"Generation failed: {e}")

if 'pdf_bytes' in st.session_state:
    st.download_button(
        label="Download Investor Report (PDF)",
        data=st.session_state.pdf_bytes,
        file_name=f"Groves_Investor_Report_{date.today().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
    st.caption(f"File size: {len(st.session_state.pdf_bytes):,} bytes")

page_footer()
