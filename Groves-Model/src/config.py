# src/config.py — Property-specific configuration
# Change these values to adapt the model to a different property.

PROPERTY = {
    'name': 'The Groves Apartments',
    'short_name': 'THE GROVES APARTMENTS',
    'address': '6800-6810 63rd Ave N, Brooklyn Park MN 55443',
    'units': 120,
    'rentable_sf': 99_300,
    'year_built': 1967,
    'purchase_price': 12_000_000,
    'purchase_date': '2024-08-01',
    'structures': '5 residential 24-unit bldgs, 6 garage bldgs, 1 clubhouse',
    'garages': 126,
}

UNIT_MIX = {
    '1BR': {'count': 60, 'sf': 765, 'market_rent': 1350, 'bath': 1},
    '2BR': {'count': 60, 'sf': 890, 'market_rent': 1550, 'bath': 1},
}

LOAN = {
    'original_amount': 8_838_399,
    'rate': 0.0544,
    'amort_years': 30,
    'term_years': 5,
    'start_date': '2024-08-01',
    'est_current_balance': 8_639_141,
    'io': False,
}

TIC = {
    'Boxwood LLC':   {'pct': 0.61674, 'equity': 2_799_999.60},
    'Groves LP LLC': {'pct': 0.31718, 'equity': 1_439_997.20},
    'E 2088':        {'pct': 0.06608, 'equity':   300_003.20},
}

TOTAL_EQUITY = 4_540_000

VALUATION = {
    'bov_low': 14_700_000,
    'bov_mid': 15_000_000,
    'bov_high': 15_300_000,
}

ESCROW_NAMES = ['Real Estate Taxes', 'Property Insurance', 'Capital Reserves']

REFI = {
    'property_value': 15_000_000,
    'ltv': 0.70,
    'rate': 0.0575,
    'amort_years': 30,
    'term_years': 10,
    'io': True,
    'noah_equity_pct': 0.90,
    'noah_pref_return': 0.0525,
}

# Chart of Accounts — defines row order for Full P&L and qPL_Fact
# Format: (GL code or None, Account name, row_type)
# row_type: 'section', 'line', 'subtotal', 'metric', 'spacer'
CHART_OF_ACCOUNTS = [
    (None,   'REVENUE',                               'section'),
    ('3090', 'Gross Potential Rent',                   'line'),
    ('4100', 'Loss/Gain to Market',                    'line'),
    ('4100', 'Delinquency',                            'line'),
    ('4100', 'Vacancy',                                'line'),
    (None,   'Concessions',                            'line'),
    ('4700', 'Other Rent Adjustments',                 'line'),
    (None,   'Effective Rental Income',                'subtotal'),
    (None,   None,                                     'spacer'),
    (None,   'OTHER INCOME',                           'section'),
    ('4460', 'Late Fees',                              'line'),
    ('4490', 'Move-In Fees',                           'line'),
    ('4440', 'Application Fees',                       'line'),
    ('4415', 'Internet Charges',                       'line'),
    ('4450', 'Insurance Services',                     'line'),
    (None,   'Interest Income',                        'line'),
    ('4730', 'Utility Reimbursement',                  'line'),
    (None,   'Deposit Forfeit',                        'line'),
    ('4410', 'NSF Fees',                               'line'),
    (None,   'Total Other Income',                     'subtotal'),
    (None,   None,                                     'spacer'),
    (None,   'EFFECTIVE GROSS INCOME (EGI)',            'subtotal'),
    (None,   None,                                     'spacer'),
    (None,   'OPERATING EXPENSES',                     'section'),
    ('6161', 'Real Estate Taxes',                      'line'),
    ('6091', 'Property Insurance',                     'line'),
    ('6002', 'Payroll',                                'line'),
    ('6003', 'Advertising',                            'line'),
    ('6171', 'Electricity',                            'line'),
    ('6172', 'Gas',                                    'line'),
    ('6173', 'Water',                                  'line'),
    ('6175', 'Garbage & Recycling',                    'line'),
    ('6176', 'Internet',                               'line'),
    ('6111', 'Management Fee (4%)',                     'line'),
    ('6073', 'General Maint. Labor',                   'line'),
    ('6074', 'Landscaping',                            'line'),
    ('6076', 'Cleaning & Maint',                       'line'),
    ('6077', 'Common Area Cleaning',                   'line'),
    ('6078', 'Pest Control',                           'line'),
    ('6071', 'Carpet Cleaning',                        'line'),
    ('6072', 'Janitorial',                             'line'),
    ('6141', 'Painting',                               'line'),
    ('6142', 'Plumbing',                               'line'),
    ('6143', 'Flooring',                               'line'),
    ('6144', 'HVAC',                                   'line'),
    ('6145', 'Key/Lock',                               'line'),
    ('6147', 'Repairs - Other',                        'line'),
    ('6150', 'Supplies',                               'line'),
    ('6101', 'Legal',                                  'line'),
    ('6102', 'Accounting',                             'line'),
    ('6103', 'Professional - Other',                   'line'),
    ('6105', 'Security Service',                       'line'),
    ('6106', 'Bank Fees',                              'line'),
    ('6107', 'Travel',                                 'line'),
    ('6108', 'Meals',                                  'line'),
    ('6179', 'Asset Mgmt Fee',                         'line'),
    (None,   'Total Operating Expenses',               'subtotal'),
    (None,   None,                                     'spacer'),
    (None,   'NET OPERATING INCOME (NOI)',             'subtotal'),
    (None,   None,                                     'spacer'),
    (None,   'DEBT SERVICE',                           'section'),
    ('6119', 'Principal',                              'line'),
    ('6121', 'Interest',                               'line'),
    (None,   'Total Debt Service',                     'subtotal'),
    (None,   None,                                     'spacer'),
    (None,   'CASH FLOW AFTER DEBT SERVICE',           'subtotal'),
    (None,   None,                                     'spacer'),
    (None,   'CAPITAL EXPENDITURES (Below the Line)',  'section'),
    ('7010', 'Appliances',                             'line'),
    ('7020', 'Equipment/Tools',                        'line'),
    ('7030', 'Remodel',                                'line'),
    ('7060', 'Labor',                                  'line'),
    ('7070', 'Flooring',                               'line'),
    ('7080', 'Hardware',                               'line'),
    ('7090', 'Cabinets',                               'line'),
    ('7100', 'Supplies',                               'line'),
    ('7110', 'Paint',                                  'line'),
    (None,   'Total Capital Expenditures',             'subtotal'),
    (None,   None,                                     'spacer'),
    (None,   'NET CASH FLOW',                          'subtotal'),
    (None,   'Cash-on-Cash (Ann.)',                    'metric'),
    (None,   None,                                     'spacer'),
    (None,   'KEY METRICS',                            'section'),
    (None,   'DSCR',                                   'metric'),
    (None,   'Cap Rate',                               'metric'),
    (None,   'Expense Ratio',                          'metric'),
    (None,   'Cash-on-Cash (CFADS)',                   'metric'),
]

# Subtotal formulas — which rows sum to create each subtotal
# Key = subtotal account name, Value = list of line item names to sum
SUBTOTAL_FORMULAS = {
    'Effective Rental Income': [
        'Gross Potential Rent', 'Loss/Gain to Market', 'Delinquency',
        'Vacancy', 'Concessions', 'Other Rent Adjustments',
    ],
    'Total Other Income': [
        'Late Fees', 'Move-In Fees', 'Application Fees', 'Internet Charges',
        'Insurance Services', 'Interest Income', 'Utility Reimbursement',
        'Deposit Forfeit', 'NSF Fees',
    ],
    'EFFECTIVE GROSS INCOME (EGI)': ['Effective Rental Income', 'Total Other Income'],
    'Total Operating Expenses': 'SUM_RANGE',  # Sum all OpEx lines
    'NET OPERATING INCOME (NOI)': ['EFFECTIVE GROSS INCOME (EGI)', '-Total Operating Expenses'],
    'Total Debt Service': ['Principal', 'Interest'],
    'CASH FLOW AFTER DEBT SERVICE': ['NET OPERATING INCOME (NOI)', '-Total Debt Service'],
    'Total Capital Expenditures': [
        'Appliances', 'Equipment/Tools', 'Remodel', 'Labor',
        'Flooring', 'Hardware', 'Cabinets', 'Supplies', 'Paint',
    ],
    'NET CASH FLOW': ['CASH FLOW AFTER DEBT SERVICE', '-Total Capital Expenditures'],
}
