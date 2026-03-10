"""PDF Report -- One-click quarterly investor report generation with charts."""

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
    "Quarterly Investor Report (PDF)",
    "Generate a professional PDF summary for investors",
)

# -- Data guard --
if no_data_page("pl_actuals.csv"):
    st.stop()

# -- Data loading --
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
t12 = get_t12_totals(df, cfg)


def _fmt(v):
    if v is None or v == 0:
        return "$0"
    if v < 0:
        return f"(${abs(v):,.0f})"
    return f"${v:,.0f}"


def generate_pdf():
    """Generate the branded quarterly investor report PDF with charts."""
    from report_data import load_report_data
    from report_charts import generate_all_charts
    from report_pdf import build_report

    data = load_report_data()

    charts = generate_all_charts(data)

    out_path = os.path.join(tempfile.gettempdir(), 'investor_report.pdf')
    build_report(data, charts, out_path)

    with open(out_path, 'rb') as f:
        return f.read()


# -- Report Preview --
prop = st.session_state.property
noi_str = _fmt(t12['NET OPERATING INCOME (NOI)'])
cfads_str = _fmt(t12['CASH FLOW AFTER DEBT SERVICE'])

st.info(
    f"**Quarterly Report (5 pages) includes:**\n"
    f"- **Pg 1** - KPI Dashboard, Property Overview, Q-over-Q Performance Chart, "
    f"Month-by-Month Financial Snapshot\n"
    f"- **Pg 2** - Occupancy Deep Dive: Unit Mix, Renovated vs Classic, "
    f"Leasing Activity & Turnover, Loss-to-Lease, Rent Growth\n"
    f"- **Pg 3** - NOI Trend, Cash Flow Waterfall, Renovations, "
    f"TIC Distributions, Escrow, Valuation\n"
    f"- **Pg 4** - Rent Comps (1BR & 2BR), Sale Comps, Operating Expense Breakdown\n"
    f"- **Pg 5** - Capital Improvements & Property Condition (color-coded status)"
)

# -- Generate Button --
if st.button("Generate Quarterly PDF Report", type="primary", use_container_width=True):
    with st.spinner("Generating quarterly report with charts..."):
        try:
            pdf_bytes = generate_pdf()
            st.session_state.pdf_bytes = pdf_bytes
            st.success("Quarterly report generated successfully!")
        except ImportError as e:
            st.error(
                f"Missing dependency: {e}. "
                "Install with: `pip install fpdf2 matplotlib`"
            )
        except Exception as e:
            st.error(f"Generation failed: {e}")

if 'pdf_bytes' in st.session_state:
    st.download_button(
        label="Download Quarterly Investor Report (PDF)",
        data=st.session_state.pdf_bytes,
        file_name=f"Groves_Quarterly_Report_{date.today().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
    st.caption(f"File size: {len(st.session_state.pdf_bytes):,} bytes")

page_footer()
