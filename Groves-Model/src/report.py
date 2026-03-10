# src/report.py -- CLI entry point for generating the quarterly investor report PDF
"""
Usage:
    python src/report.py                       # Latest quarter
    python src/report.py "Q4 2025"             # Specific quarter
    python src/report.py "Q4 2025" out.pdf     # Specific quarter + output path
"""
import sys
import os

# Ensure src/ is on path for config imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_data import load_report_data
from report_charts import generate_all_charts
from report_pdf import build_report


def main():
    quarter = sys.argv[1] if len(sys.argv) > 1 else None
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    print(f'Loading data{f" for {quarter}" if quarter else " (latest quarter)"}...')
    data = load_report_data(quarter)
    print(f'Report period: {data["quarter_label"]}')

    print('Generating charts...')
    charts = generate_all_charts(data)
    print(f'  {len(charts)} charts generated')

    print('Building PDF...')
    path = build_report(data, charts, out_path)
    print(f'Done: {path}')
    return path


if __name__ == '__main__':
    main()
