"""Upload Data — CSV file upload with validation and preview."""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ui.theme import inject_theme
from ui.components import page_header

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
    },
    'rent_roll.csv': {
        'label': 'Rent Roll',
        'desc': 'Unit rent grid. First column: Unit, then one column per month.',
        'required_cols': ['Unit'],
    },
    'escrow_activity.csv': {
        'label': 'Escrow Activity',
        'desc': 'Monthly escrow transactions. Columns: Month, EscrowName, Deposits, Payments, Notes',
        'required_cols': ['Month', 'EscrowName', 'Deposits', 'Payments'],
    },
    'unit_improvements.csv': {
        'label': 'Unit Improvements',
        'desc': 'Renovation tracker. Columns: Unit, Mix, Condition, OrigRent, CurrRent, MktRent, ...',
        'required_cols': ['Unit'],
    },
    'capex_profile.csv': {
        'label': 'CapEx Profile',
        'desc': 'Building systems condition tracker.',
        'required_cols': ['Section'],
    },
    'rent_comps.csv': {
        'label': 'Rent Comparables',
        'desc': 'Market rent and sale comps.',
        'required_cols': ['Section'],
    },
}

for filename, info in CSV_FILES.items():
    with st.expander(f"{info['label']} ({filename})", expanded=False):
        st.caption(info['desc'])

        # Show current file info
        current_path = os.path.join(DATA_DIR, filename)
        if os.path.exists(current_path):
            size = os.path.getsize(current_path)
            st.info(f"Current file: {size:,} bytes")
            try:
                preview = pd.read_csv(current_path, nrows=5)
                st.dataframe(preview, use_container_width=True, hide_index=True)
            except Exception:
                st.warning("Could not preview current file.")
        else:
            st.warning("No file found on disk.")

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
