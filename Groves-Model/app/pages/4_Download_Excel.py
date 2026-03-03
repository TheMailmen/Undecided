"""Download Excel — Generate and download the formatted Excel model."""

import os
import subprocess
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

st.title("Download Excel Model")
st.caption("Generate the formatted Excel workbook with one click.")

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
BUILD_SCRIPT = os.path.join(BASE_DIR, 'src', 'build.py')
OUTPUT_PATH = os.path.join(BASE_DIR, 'output', 'Groves_Investor_Model.xlsx')

# ── Current Assumptions Summary ───────────────────────────────────
with st.expander("Current Assumptions", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Property:**", st.session_state.property['name'])
        st.write("**Units:**", st.session_state.property['units'])
        st.write("**Purchase Price:**", f"${st.session_state.property['purchase_price']:,.0f}")
        st.write("**Loan Rate:**", f"{st.session_state.loan['rate'] * 100:.2f}%")
    with col2:
        st.write("**Loan Balance:**", f"${st.session_state.loan['est_current_balance']:,.0f}")
        for name, v in st.session_state.tic.items():
            st.write(f"**{name}:**", f"{v['pct'] * 100:.3f}%")

st.divider()

# ── Generate Button ───────────────────────────────────────────────
use_session_config = st.checkbox(
    "Use edited assumptions from the Assumptions page",
    value=True,
    help="When checked, the Excel build uses your edited assumptions. "
         "When unchecked, it uses the on-disk config.py defaults.",
)

if st.button("Generate Excel Model", type="primary", use_container_width=True):
    with st.spinner("Building model... This takes a few seconds."):
        if use_session_config:
            # Build using session state config via the cfg_override mechanism
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
            # Subprocess: uses on-disk config.py as-is
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

    st.download_button(
        label="Download Groves_Investor_Model.xlsx",
        data=file_bytes,
        file_name="Groves_Investor_Model.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.caption(f"File size: {len(file_bytes):,} bytes")
else:
    st.info("No model file found. Click 'Generate' above to build one.")
