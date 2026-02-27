# src/finalize.py — Post-build: hide empty space, recalc, validate
import subprocess
import json
from design import hide_beyond


# Data boundaries per sheet (last_row, last_col)
# Update these if sheet structures change
BOUNDARIES = {
    'How To Use':        (155, 5),
    'Executive Summary': (45, 6),
    'Assumptions':       (84, 5),
    'Full P&L':          (112, 24),
    'T12_PL':            (91, 18),
    'Trailing Analysis': (93, 20),
    'Distribution_Model':(56, 20),
    'TIC Ownership':     (27, 8),
    'RR Summary':        (37, 19),
    'RR Input':          (131, 18),
    'Unit Improvements': (128, 20),
    'Escrow_Summary':    (64, 8),
    'Escrow_Input':      (65, 5),
    'CapEx Profile':     (44, 5),
    'Refi Stress Test':  (64, 6),
    'Rent Comps':        (32, 8),
}


def finalize(wb, out_path, recalc_script=None):
    """Hide empty space, save, recalculate, and validate."""
    
    # 1. Hide rows/cols beyond data on visible sheets
    for name in wb.sheetnames:
        if wb[name].sheet_state != 'visible':
            continue
        if name in BOUNDARIES:
            last_row, last_col = BOUNDARIES[name]
        else:
            # Auto-detect
            ws = wb[name]
            last_row = ws.max_row + 2
            last_col = ws.max_column + 1
        hide_beyond(wb[name], last_row, last_col)
    
    # 2. Save
    wb.save(out_path)
    print(f"Saved: {out_path}")
    
    # 3. Recalculate via LibreOffice
    if recalc_script:
        print("Recalculating formulas...")
        result = subprocess.run(
            ['python3', recalc_script, out_path, '60'],
            capture_output=True, text=True
        )
        try:
            data = json.loads(result.stdout)
            if data.get('status') == 'success':
                print(f"✅ {data['total_formulas']} formulas, 0 errors")
            else:
                print(f"❌ {data['total_errors']} errors found:")
                for err_type, info in data.get('error_summary', {}).items():
                    print(f"   {err_type}: {info['count']} — {info['locations'][:5]}")
            return data
        except (json.JSONDecodeError, KeyError):
            print(f"Recalc output: {result.stdout}")
            return None
    
    return None
