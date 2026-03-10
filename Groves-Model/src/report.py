# src/report.py — CLI entry point for generating the monthly investor report PDF
"""
Usage:
    python src/report.py                    # Latest month
    python src/report.py 2025-12-01         # Specific month
    python src/report.py 2025-12-01 out.pdf # Specific month + output path
"""
import sys
import os

# Ensure src/ is on path for config imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_data import load_report_data
from report_charts import generate_all_charts
from report_pdf import build_report


def main():
    month = sys.argv[1] if len(sys.argv) > 1 else None
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    print(f'Loading data{f" for {month}" if month else " (latest month)"}...')
    data = load_report_data(month)
    print(f'Report period: {data["report_label"]}')

    print('Generating charts...')
    charts = generate_all_charts(data)

    print('Building PDF...')
    path = build_report(data, charts, out_path)
    print(f'Done: {path}')
    return path


if __name__ == '__main__':
    main()
