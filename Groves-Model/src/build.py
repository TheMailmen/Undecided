# src/build.py — Main build orchestrator
"""
Builds the complete Groves Apartments Investor Model from raw data.

Usage: python src/build.py

Reads CSVs from data/, builds all sheets, applies formatting, saves to output/.
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from openpyxl import Workbook
import config
from engine import build_qpl_fact
from finalize import finalize

# Import sheet builders
from sheets.how_to_use import build as build_how_to_use
from sheets.exec_summary import build as build_exec_summary
from sheets.assumptions import build as build_assumptions
from sheets.full_pl import build as build_full_pl
from sheets.t12_pl import build as build_t12_pl
from sheets.trailing import build as build_trailing
from sheets.distribution import build as build_distribution
from sheets.tic_ownership import build as build_tic
from sheets.rr_summary import build as build_rr_summary
from sheets.rr_input import build as build_rr_input
from sheets.unit_improvements import build as build_unit_improvements
from sheets.escrow_summary import build as build_escrow_summary
from sheets.escrow_input import build as build_escrow_input
from sheets.capex_profile import build as build_capex_profile
from sheets.refi_stress import build as build_refi_stress
from sheets.rent_comps import build as build_rent_comps


def main():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(out_dir, exist_ok=True)

    # CSV paths
    pl_csv = os.path.join(data_dir, 'pl_actuals.csv')
    rr_csv = os.path.join(data_dir, 'rent_roll.csv')
    escrow_csv = os.path.join(data_dir, 'escrow_activity.csv')

    # Validate inputs exist
    for path in [pl_csv, rr_csv, escrow_csv]:
        if not os.path.exists(path):
            print(f"ERROR: Missing data file: {path}")
            print("See README.md for required CSV formats.")
            sys.exit(1)

    # Create workbook
    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Build config dict for passing to modules
    cfg = {
        'property': config.PROPERTY,
        'unit_mix': config.UNIT_MIX,
        'loan': config.LOAN,
        'tic': config.TIC,
        'total_equity': config.TOTAL_EQUITY,
        'valuation': config.VALUATION,
        'escrow_names': config.ESCROW_NAMES,
        'refi': config.REFI,
        'coa': config.CHART_OF_ACCOUNTS,
        'subtotals': config.SUBTOTAL_FORMULAS,
        'purchase_price': config.PROPERTY['purchase_price'],
    }

    # 1. Build engine table (hidden)
    print("Building qPL_Fact engine...")
    qpl_ws, qpl_rows = build_qpl_fact(wb, pl_csv, cfg)
    cfg['qpl_rows'] = qpl_rows
    print(f"  qPL_Fact: {qpl_rows} rows")

    # 2. Build visible sheets in order
    print("Building sheets...")

    print("  How To Use...")
    build_how_to_use(wb, cfg)

    print("  Executive Summary...")
    build_exec_summary(wb, cfg)

    print("  Assumptions...")
    build_assumptions(wb, cfg)

    print("  Full P&L...")
    build_full_pl(wb, cfg, pl_csv)

    print("  T12 P&L...")
    build_t12_pl(wb, cfg)

    print("  Trailing Analysis...")
    build_trailing(wb, cfg)

    print("  Distribution Model...")
    build_distribution(wb, cfg)

    print("  TIC Ownership...")
    build_tic(wb, cfg)

    print("  RR Input...")
    build_rr_input(wb, cfg, rr_csv)

    print("  RR Summary...")
    build_rr_summary(wb, cfg)

    print("  Unit Improvements...")
    build_unit_improvements(wb, cfg, os.path.join(data_dir, 'unit_improvements.csv'))

    print("  Escrow Input...")
    build_escrow_input(wb, cfg, escrow_csv)

    print("  Escrow Summary...")
    build_escrow_summary(wb, cfg)

    print("  CapEx Profile...")
    build_capex_profile(wb, cfg, os.path.join(data_dir, 'capex_profile.csv'))

    print("  Refi Stress Test...")
    build_refi_stress(wb, cfg)

    print("  Rent Comps...")
    build_rent_comps(wb, cfg, os.path.join(data_dir, 'rent_comps.csv'))

    # 3. Finalize — hide empty space, save
    out_path = os.path.join(out_dir, 'Groves_Investor_Model.xlsx')
    print("Finalizing...")
    finalize(wb, out_path)
    print("Done!")


if __name__ == '__main__':
    main()
