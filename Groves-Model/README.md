# Groves Apartments — Investor Model Builder

A Python project that builds a fully formatted, formula-driven Excel investor model for The Groves Apartments (120-unit multifamily, Brooklyn Park MN) from raw source data.

## Quick Start

```bash
# Install dependencies
pip install openpyxl

# Build the model from source data
python src/build.py

# Output: output/Groves_Investor_Model.xlsx
```

## Architecture

```
groves-model/
├── CLAUDE.md              ← Claude Code instructions (READ THIS FIRST)
├── README.md              ← This file
├── src/
│   ├── build.py           ← Main build script — orchestrates everything
│   ├── design.py          ← Design system tokens (colors, fonts, fills, helpers)
│   ├── config.py          ← Property config (units, TIC %, loan terms, etc.)
│   ├── engine.py          ← Builds qPL_Fact engine table from Full P&L data
│   ├── sheets/
│   │   ├── assumptions.py
│   │   ├── exec_summary.py
│   │   ├── full_pl.py
│   │   ├── t12_pl.py
│   │   ├── trailing.py
│   │   ├── distribution.py
│   │   ├── tic_ownership.py
│   │   ├── rr_summary.py
│   │   ├── rr_input.py
│   │   ├── unit_improvements.py
│   │   ├── escrow_summary.py
│   │   ├── escrow_input.py
│   │   ├── capex_profile.py
│   │   ├── refi_stress.py
│   │   ├── rent_comps.py
│   │   ├── how_to_use.py
│   │   └── year1_proforma.py
│   └── finalize.py        ← Hide rows/cols, recalc, validate
├── data/
│   ├── pl_actuals.csv     ← Monthly P&L export from AppFolio (or manual)
│   ├── rent_roll.csv      ← Monthly rent grid (units × months)
│   ├── escrow_activity.csv← Monthly escrow deposits & payments
│   ├── unit_improvements.csv ← Renovation tracker
│   └── capex_profile.csv  ← Building systems condition
├── tests/
│   └── test_model.py      ← Validation: formulas, cross-refs, totals
├── docs/
│   └── design_system.md   ← Full formatting specification
└── output/
    └── Groves_Investor_Model.xlsx
```

## How It Works

### Data Flow

```
Raw CSVs (data/)
    ↓
build.py reads CSVs, creates workbook
    ↓
engine.py → qPL_Fact (hidden fact table: Account × Month × Amount)
    ↓
Each sheet module writes its tab:
  - Static sheets: write data directly
  - Formula sheets: write SUMIFS against qPL_Fact or cross-sheet refs
  - All sheets: apply design.py formatting
    ↓
finalize.py → hide empty rows/cols, recalc, validate zero errors
    ↓
output/Groves_Investor_Model.xlsx
```

### Monthly Update Workflow

When you have a new month of data:

1. Append new rows to `data/pl_actuals.csv` (one row per GL line item for the new month)
2. Add a new column to `data/rent_roll.csv` with the new month's rents
3. Add 3 rows to `data/escrow_activity.csv` (taxes, insurance, reserves)
4. Run `python src/build.py`

The entire model rebuilds from scratch. No patching. No broken formulas.

### Formula Strategy

The model uses Excel formulas (not Python-calculated values) so the output xlsx is live and editable:

- **qPL_Fact** is a normalized fact table: every P&L line item × month as a row
- **T12_PL** uses SUMIFS against qPL_Fact with dynamic date ranges
- **Distribution_Model** uses SUMIFS for CFADS and CapEx, cross-refs for escrow
- **TIC Ownership** uses SUMIFS for NOI/CF allocation by ownership %
- **Trailing Analysis** uses SUMIFS with configurable T-1/T-3/T-6/T-12 windows
- **RR Summary** uses COUNTIF/SUMIF against RR Input
- **Escrow_Summary** uses SUMIFS against Escrow_Input

## Design System

See `docs/design_system.md` for the complete specification. Summary:

| Element | Fill | Font |
|---------|------|------|
| Title bar (row 1) | `#0D1B2A` | 14pt Bold White |
| Subtitle (row 2) | `#1A2332` | 9pt `#AEB6BF` |
| Column headers | `#0D1B2A` | 10pt Bold White |
| Section bars | `#1B4F72` | 10pt Bold White |
| Subtotals | `#E8EAED` | 10pt Bold Black |
| NOI/CFADS rows | `#E8F5E9` | 10pt Bold `#1E8449` |
| Input cells | `#FFF9C4` | 10pt Bold `#0000FF` |
| Data rows | Alt `#F7F9FC`/White | 10pt Black |

## Property Details

- **Property:** The Groves Apartments, 6800-6810 63rd Ave N, Brooklyn Park MN
- **Units:** 120 (60×1BR/1BA @ 765sf + 60×2BR/1BA @ 890sf)
- **Acquired:** August 2024 for $12,000,000
- **Loan:** $8,838,399 @ 5.44%, 30yr amort, 5yr term (Freddie Mac)
- **TIC Owners:** Boxwood LLC (61.674%), Groves LP LLC (31.718%), E 2088 (6.608%)
- **Data Range:** August 2024 – present
