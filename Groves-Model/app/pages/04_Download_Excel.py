"""Download Excel — Generate and download the formatted Excel model."""

import os
import subprocess
import sys
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from ui.theme import inject_theme, COLORS, fmt_currency
from ui.components import page_header, section_header, spacer, badge, kpi_row, styled_table, page_footer

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

page_header(
    "Download Excel Model",
    "Generate the formatted Excel workbook with one click",
)

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
BUILD_SCRIPT = os.path.join(BASE_DIR, 'src', 'build.py')
OUTPUT_PATH = os.path.join(BASE_DIR, 'output', 'Groves_Investor_Model.xlsx')

# ── Current Assumptions Summary ───────────────────────────────────
section_header("Model Configuration")

kpi_row([
    {"label": "Property", "value": st.session_state.property['name']},
    {"label": "Units", "value": str(st.session_state.property['units'])},
    {"label": "Purchase Price", "value": fmt_currency(st.session_state.property['purchase_price'])},
    {"label": "Loan Rate", "value": f"{st.session_state.loan['rate'] * 100:.2f}%"},
])

with st.expander("Full Assumptions", expanded=False):
    detail_rows = [
        ["<b>Loan Balance</b>", fmt_currency(st.session_state.loan['est_current_balance']),
         "<b>Total Equity</b>", fmt_currency(st.session_state.total_equity)],
    ]
    for name, v in st.session_state.tic.items():
        detail_rows.append([f"<b>{name}</b>", f"{v['pct'] * 100:.3f}%", "", ""])
    styled_table(
        ["Item", "Value", "Item", "Value"],
        detail_rows,
        col_align=["left", "right", "left", "right"],
        compact=True,
    )

spacer(8)

# ── Output Status ────────────────────────────────────────────────
section_header("Output")

file_exists = os.path.exists(OUTPUT_PATH)
if file_exists:
    file_size = os.path.getsize(OUTPUT_PATH)
    mod_time = datetime.fromtimestamp(os.path.getmtime(OUTPUT_PATH))
    status_badge = badge("Ready", "success")
    st.markdown(f"""
    <div style="background:{COLORS['surface']};border:1px solid {COLORS['border']};
                border-radius:12px;padding:16px 20px;margin-bottom:16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <p style="margin:0;font-weight:600;font-size:0.92rem;color:{COLORS['text']};
                          font-family:'Inter',system-ui,sans-serif;">
                    Groves_Investor_Model.xlsx</p>
                <p style="margin:2px 0 0 0;font-size:0.78rem;color:{COLORS['muted']};">
                    Last built: {mod_time.strftime('%b %d, %Y at %I:%M %p')} &bull; {file_size:,} bytes</p>
            </div>
            <div>{status_badge}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style="background:{COLORS['surface']};border:1px solid {COLORS['border']};
                border-radius:12px;padding:24px;margin-bottom:16px;text-align:center;">
        <p style="margin:0;font-size:0.9rem;color:{COLORS['muted']};">
            No model file found. Click <b>Generate</b> below to build one.</p>
    </div>
    """, unsafe_allow_html=True)

spacer(8)

# ── Generate Button ───────────────────────────────────────────────
section_header("Build")

use_session_config = st.checkbox(
    "Use edited assumptions from the Assumptions page",
    value=True,
    help="When checked, the Excel build uses your edited assumptions. "
         "When unchecked, it uses the on-disk config.py defaults.",
)

if st.button("Generate Excel Model", type="primary", use_container_width=True):
    with st.spinner("Building model... This takes a few seconds."):
        if use_session_config:
            try:
                from build import main as build_main

                cfg_override = {
                    'property': st.session_state.property,
                    'unit_mix': st.session_state.unit_mix,
                    'loan': st.session_state.loan,
                    'tic': st.session_state.tic,
                    'total_equity': st.session_state.total_equity,
                    'valuation': st.session_state.valuation,
                    'escrow_names': st.session_state.escrow_names,
                    'refi': st.session_state.refi,
                    'purchase_price': st.session_state.property['purchase_price'],
                }
                build_main(cfg_override=cfg_override)
                st.success("Model built successfully with edited assumptions!")
            except Exception as e:
                st.error(f"Build failed: {e}")
        else:
            result = subprocess.run(
                [sys.executable, BUILD_SCRIPT],
                capture_output=True, text=True,
                cwd=os.path.join(BASE_DIR, 'src'),
                timeout=60,
            )
            if result.returncode == 0:
                st.success("Model built successfully!")
                if result.stdout.strip():
                    st.code(result.stdout, language='text')
            else:
                st.error("Build failed!")
                st.code(result.stderr, language='text')

# ── Download Button ───────────────────────────────────────────────
if os.path.exists(OUTPUT_PATH):
    with open(OUTPUT_PATH, 'rb') as f:
        file_bytes = f.read()

    spacer(8)
    st.download_button(
        label="Download Groves_Investor_Model.xlsx",
        data=file_bytes,
        file_name="Groves_Investor_Model.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

page_footer()
