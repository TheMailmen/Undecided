# CLAUDE.md — Instructions for Claude Code

## What This Project Is

This is a Python build system that generates an Excel investor model for a 120-unit multifamily property called The Groves Apartments. It reads raw CSV data and outputs a fully formatted, formula-driven .xlsx file.

## Key Principles

1. **Deterministic builds.** Running `python src/build.py` always produces the same output from the same inputs. No interactive steps. No manual patching.

2. **Excel formulas, not Python math.** Never calculate a value in Python and write a static number. Always write an Excel formula string. The output xlsx must be a live, editable model. Example:
   - ❌ `cell.value = df['Amount'].sum()`  
   - ✅ `cell.value = '=SUM(D2:D746)'`

3. **Single source of truth for design.** All colors, fonts, fills, borders, and number formats live in `src/design.py`. Sheet modules import from there. Never hardcode a color hex or Font() object in a sheet module.

4. **Config-driven.** Property-specific values (unit count, TIC ownership %, loan terms, escrow names) live in `src/config.py`. The sheet modules reference config, not magic numbers.

5. **One module per sheet.** Each visible tab has its own file in `src/sheets/`. Each exports a `build(wb, config)` function that creates and populates its sheet.

6. **Zero errors.** The final output must pass `recalc.py` with 0 formula errors. `src/finalize.py` handles this.

## Build Command

```bash
python src/build.py
```

This:
1. Creates a new empty workbook
2. Reads CSV data from `data/`
3. Builds qPL_Fact engine table (hidden)
4. Builds each visible sheet in order
5. Hides rows/columns beyond data boundaries
6. Saves to `output/Groves_Investor_Model.xlsx`

## File Responsibilities

### src/design.py
Exports: color constants, Font objects, PatternFill objects, helper functions.

```python
# Colors
C_TITLE = '0D1B2A'      # Dark navy - title bars
C_SUB = '1A2332'         # Dark navy - subtitle bars
C_HDR = '0D1B2A'         # Column headers (same as title)
C_ACCENT = '1B4F72'      # Steel blue - section bars
C_GREEN = '1E8449'        # Green - NOI/CFADS highlight
C_RED = 'C00000'          # Red - warnings/variance
C_GOLD = 'D4AC0D'         # Gold - special accents
C_SUBTOTAL = 'E8EAED'     # Light gray - subtotal rows
C_ALT = 'F7F9FC'          # Very light blue - alternating rows
C_INPUT_BG = 'FFF9C4'     # Yellow - input cells
C_NOTE_BG = 'E8F5E9'      # Light green - NOI/CFADS rows
C_WARN_BG = 'FDEDEC'      # Light red - variance rows
C_BODY = '000000'          # Black - body text
C_LABEL = '2C3E50'        # Dark blue-gray - row labels
C_MUTED = '7F8C8D'        # Muted gray - GL codes, annotations
C_BLUE = '0000FF'          # Blue - input font
C_CROSS = '548235'        # Green - cross-sheet references

# Font objects (max 10 per sheet target)
F_TITLE    # Calibri 14pt Bold White
F_SUB      # Calibri 9pt #AEB6BF
F_HDR      # Calibri 10pt Bold White
F_SECTION  # Calibri 10pt Bold White
F_LABEL    # Calibri 10pt Bold #2C3E50
F_BODY     # Calibri 10pt #000000
F_BOLD     # Calibri 10pt Bold #000000
F_INPUT    # Calibri 10pt Bold #0000FF
F_MUTED    # Calibri 9pt #7F8C8D
F_GREEN    # Calibri 10pt Bold #1E8449
F_RED      # Calibri 10pt Bold #C00000
F_CROSS    # Calibri 10pt #548235
F_NOTE     # Calibri 9pt Italic #1E8449

# Number formats
NF_DOLLAR = '$#,##0;($#,##0);"-"'
NF_NUM    = '#,##0;(#,##0);"-"'
NF_PCT    = '0.0%'
NF_PCT2   = '0.00%'
NF_DATE   = 'MMM-YY'
NF_DEC2   = '#,##0.00'

# Helper functions
apply_title(ws, max_col)         # Rows 1-2: title + subtitle bars
apply_hdr(ws, row, max_col)      # Dark header row
apply_section(ws, row, max_col)  # Section divider bar
apply_subtotal(ws, row, max_col, green=False)  # Subtotal row
apply_alt_rows(ws, start, end, max_col)        # Alternating fills
hide_beyond(ws, last_row, last_col)            # Hide empty rows/cols
```

### src/config.py
Exports a Config dataclass or dict with all property-specific values:

```python
PROPERTY = {
    'name': 'The Groves Apartments',
    'address': '6800-6810 63rd Ave N, Brooklyn Park MN 55443',
    'units': 120,
    'unit_mix': {'1BR': {'count': 60, 'sf': 765, 'market_rent': 1350},
                 '2BR': {'count': 60, 'sf': 890, 'market_rent': 1550}},
    'year_built': 1967,
    'purchase_price': 12_000_000,
    'purchase_date': '2024-08-01',
    'bov_low': 14_700_000,
    'bov_mid': 15_000_000,
    'bov_high': 15_300_000,
}

LOAN = {
    'original_amount': 8_838_399,
    'rate': 0.0544,
    'amort_years': 30,
    'term_years': 5,
    'start_date': '2024-08-01',
    'est_current_balance': 8_639_141,
}

TIC = {
    'Boxwood LLC':    {'pct': 0.61674, 'equity': 2_799_999.60},
    'Groves LP LLC':  {'pct': 0.31718, 'equity': 1_439_997.20},
    'E 2088':         {'pct': 0.06608, 'equity': 300_003.20},
}

ESCROWS = ['Real Estate Taxes', 'Property Insurance', 'Capital Reserves']

TOTAL_EQUITY = 4_540_000
```

### src/engine.py
Reads `data/pl_actuals.csv` and builds the qPL_Fact hidden sheet.

Input CSV format:
```
Month,GL,Account,Amount
2024-08-01,3090,Gross Potential Rent,167200
2024-08-01,4100,Loss/Gain to Market,-29299.58
...
```

The engine also computes subtotals (Effective Rental Income, Total OpEx, NOI, CFADS, etc.) and writes them as rows in qPL_Fact so downstream SUMIFS can find them.

### src/sheets/*.py
Each module exports `build(wb, config, data)`:
- Creates its sheet
- Writes titles, headers, data, formulas
- Applies formatting via design.py helpers

### src/finalize.py
- Hides rows/columns beyond data on every visible sheet
- Runs LibreOffice recalc
- Validates zero formula errors
- Reports results

## Chart of Accounts

The Full P&L has this exact row structure. Maintain this order:

```
REVENUE
  Gross Potential Rent (3090)
  Loss/Gain to Market (4100)
  Delinquency (4100)
  Vacancy (4100)
  Concessions
  Other Rent Adjustments (4700)
  = Effective Rental Income

OTHER INCOME
  Late Fees (4460)
  Move-In Fees (4490)
  Application Fees (4440)
  Internet Charges (4415)
  Insurance Services (4450)
  Interest Income
  Utility Reimbursement (4730)
  Deposit Forfeit
  NSF Fees (4410)
  = Total Other Income

= EFFECTIVE GROSS INCOME (EGI)

OPERATING EXPENSES
  Real Estate Taxes (6161)
  Property Insurance (6091)
  Payroll (6002)
  Advertising (6003)
  Electricity (6171)
  Gas (6172)
  Water (6173)
  Garbage & Recycling (6175)
  Internet (6176)
  Management Fee 4% (6111)
  General Maint. Labor (6073)
  Landscaping (6074)
  Cleaning & Maint (6076)
  Common Area Cleaning (6077)
  Pest Control (6078)
  Carpet Cleaning (6071)
  Janitorial (6072)
  Painting (6141)
  Plumbing (6142)
  Flooring (6143)
  HVAC (6144)
  Key/Lock (6145)
  Repairs - Other (6147)
  Supplies (6150)
  Legal (6101)
  Accounting (6102)
  Professional - Other (6103)
  Security Service (6105)
  Bank Fees (6106)
  Travel (6107)
  Meals (6108)
  Asset Mgmt Fee (6179)
  = Total Operating Expenses

= NET OPERATING INCOME (NOI)

DEBT SERVICE
  Principal (6119)
  Interest (6121)
  = Total Debt Service

= CASH FLOW AFTER DEBT SERVICE

CAPITAL EXPENDITURES (Below the Line)
  Appliances (7010)
  Equipment/Tools (7020)
  Remodel (7030)
  Labor (7060)
  Flooring (7070)
  Hardware (7080)
  Cabinets (7090)
  Supplies (7100)
  Paint (7110)
  = Total Capital Expenditures

= NET CASH FLOW

KEY METRICS
  DSCR
  Cap Rate
  Expense Ratio
  Cash-on-Cash (CFADS)

Operating Account (Starting/Ending/Change)
Escrow Accounts (Tax/Insurance/Reserves Starting/Ending/Change)
Total Escrow Balance
```

## Formula Patterns

### SUMIFS against qPL_Fact
```python
# Single month
f'=SUMIFS(qPL_Fact!$D$2:$D${n},qPL_Fact!$C$2:$C${n},"{account}",qPL_Fact!$A$2:$A${n},DATE({y},{m},1))'

# Date range (e.g., Jan-25 through Dec-25)
f'=SUMIFS(qPL_Fact!$D$2:$D${n},qPL_Fact!$C$2:$C${n},"{account}",qPL_Fact!$A$2:$A${n},">="&DATE({y1},{m1},1),qPL_Fact!$A$2:$A${n},"<="&DATE({y2},{m2},1))'
```

### TIC allocation
```python
f'=SUMIFS(...,"CASH FLOW AFTER DEBT SERVICE",...)/12*{ownership_pct}'
```

### Distribution waterfall
```python
# Free Cash = CFADS + CapEx - Cushion - Reserves - Holdbacks - AM Fee
f'=B14+B15+B16+B17+B18'
# Owner distribution = Free Cash × ownership %
f'=B19*$B$23'
```

### Escrow rollforward
```python
# Deposits from Escrow_Input via SUMIFS
# End Balance = Start + Deposits - Payments
# Next month Start = Prior End
```

## Testing

`tests/test_model.py` should validate:
- All formulas resolve (0 errors after recalc)
- TIC ownership sums to 100%
- NOI on T12 = NOI on TIC = NOI on Exec Summary
- CFADS on Distribution_Model = CFADS on TIC
- RR Summary total rent = RR Input total row
- Every visible sheet has unified title bar fill (#0D1B2A)
- Font count per sheet ≤ 10 (except Distribution_Model ≤ 15)
- No data in hidden rows/columns

## Common Tasks

### Add a new month of data
1. Append rows to `data/pl_actuals.csv`
2. Add column to `data/rent_roll.csv`
3. Add 3 rows to `data/escrow_activity.csv`
4. Run `python src/build.py`

### Change TIC ownership
Edit `src/config.py` → TIC dict → run build

### Add a new P&L line item
1. Add to chart of accounts in `src/sheets/full_pl.py`
2. Add to `src/engine.py` subtotal logic if it affects a subtotal
3. Run build

### Apply to a different property
1. Create a new config file (or modify `src/config.py`)
2. Provide new CSVs in `data/`
3. Run build
