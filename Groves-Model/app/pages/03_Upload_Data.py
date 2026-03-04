"""Upload Data — CSV file upload with validation and preview."""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ui.theme import inject_theme, COLORS
from ui.components import page_header, section_header, spacer, badge, file_status_card

# Ensure session state is initialized
if 'initialized' not in st.session_state:
    st.switch_page("streamlit_app.py")

inject_theme()

page_header(
    "Upload CSV Data",
    "Upload updated CSV files to regenerate the model",
)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

CSV_FILES = {
    'pl_actuals.csv': {
        'label': 'P&L Actuals',
        'desc': 'Monthly P&L export. Columns: Month, GL, Account, Amount',
        'required_cols': ['Month', 'GL', 'Account', 'Amount'],
        'icon': '\U0001f4ca',
    },
    'rent_roll.csv': {
        'label': 'Rent Roll',
        'desc': 'Unit rent grid. First column: Unit, then one column per month.',
        'required_cols': ['Unit'],
        'icon': '\U0001f3e0',
    },
    'escrow_activity.csv': {
        'label': 'Escrow Activity',
        'desc': 'Monthly escrow transactions. Columns: Month, EscrowName, Deposits, Payments, Notes',
        'required_cols': ['Month', 'EscrowName', 'Deposits', 'Payments'],
        'icon': '\U0001f3e6',
    },
    'unit_improvements.csv': {
        'label': 'Unit Improvements',
        'desc': 'Renovation tracker. Columns: Unit, Mix, Condition, OrigRent, CurrRent, MktRent, ...',
        'required_cols': ['Unit'],
        'icon': '\U0001f527',
    },
    'capex_profile.csv': {
        'label': 'CapEx Profile',
        'desc': 'Building systems condition tracker.',
        'required_cols': ['Section'],
        'icon': '\U0001f3d7\ufe0f',
    },
    'rent_comps.csv': {
        'label': 'Rent Comparables',
        'desc': 'Market rent and sale comps.',
        'required_cols': ['Section'],
        'icon': '\U0001f4c8',
    },
}

# ── File Status Overview ─────────────────────────────────────────
section_header("Data Files")

available = 0
for filename, info in CSV_FILES.items():
    current_path = os.path.join(DATA_DIR, filename)
    exists = os.path.exists(current_path)
    size = os.path.getsize(current_path) if exists else 0
    if exists:
        available += 1
    file_status_card(filename, f"{info['icon']} {info['label']}", info['desc'], exists, size)

st.markdown(
    f'<p style="font-size:0.78rem;color:{COLORS["muted"]};margin:8px 0 0 4px;">'
    f'{available}/{len(CSV_FILES)} files available</p>',
    unsafe_allow_html=True,
)

spacer(16)

# ── Upload Section ────────────────────────────────────────────────
section_header("Upload Files")

for filename, info in CSV_FILES.items():
    with st.expander(f"{info['icon']} {info['label']} ({filename})", expanded=False):
        required_str = ", ".join(info['required_cols'])
        st.markdown(
            f'<p style="font-size:0.8rem;color:{COLORS["muted"]};margin:0 0 8px 0;">'
            f'Required columns: <code style="background:{COLORS["border"]};padding:1px 6px;'
            f'border-radius:4px;font-size:0.75rem;">{required_str}</code></p>',
            unsafe_allow_html=True,
        )

        # Preview current file
        current_path = os.path.join(DATA_DIR, filename)
        if os.path.exists(current_path):
            try:
                preview = pd.read_csv(current_path, nrows=5)
                st.dataframe(preview, use_container_width=True, hide_index=True)
            except Exception:
                st.caption("Could not preview current file.")

        uploaded = st.file_uploader(
            f"Upload new {filename}",
            type=['csv'],
            key=f"upload_{filename}",
        )

        if uploaded is not None:
            try:
                check_df = pd.read_csv(uploaded, nrows=1)
                missing = [c for c in info['required_cols'] if c not in check_df.columns]
                if missing:
                    st.error(f"Missing required columns: {missing}")
                else:
                    uploaded.seek(0)
                    dest = os.path.join(DATA_DIR, filename)
                    with open(dest, 'wb') as f:
                        f.write(uploaded.getbuffer())
                    st.success(f"Saved {filename} ({len(uploaded.getbuffer()):,} bytes)")
                    st.session_state.data_version = st.session_state.get('data_version', 0) + 1
            except Exception as e:
                st.error(f"Error reading file: {e}")
