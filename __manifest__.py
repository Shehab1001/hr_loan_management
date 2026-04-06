# -*- coding: utf-8 -*-
{
    'name': 'HR Loan & Advance Salary Management',
    'version': '17.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Manage employee loans, advance salary requests, and automatic payroll deductions',
    'description': """
HR Loan & Advance Salary Management
=====================================
A comprehensive module to manage:
- Employee loan requests with multi-level approval workflow
- Advance salary requests
- Automatic EMI deduction integration with Odoo Payroll
- Loan repayment schedules and tracking
- Dashboard with KPIs
- Detailed reports for HR and Finance teams

Integrates with:
- hr.payslip (Odoo Payroll)
- hr.employee
- res.company
- mail.thread (Chatter & notifications)
    """,
    'author': 'Shehab Eldin Saeed Zakaria',
    'website': 'https://github.com/Shehab1001',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'hr_payroll',
        'mail',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_loan_security.xml',
        'data/hr_loan_sequence.xml',
        'data/hr_loan_salary_rule.xml',
        'views/hr_loan_views.xml',
        'views/hr_loan_line_views.xml',
        'views/hr_loan_menu.xml',
        'report/hr_loan_report_template.xml',
        'report/hr_loan_report.xml',
        'wizard/hr_loan_refuse_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_loan_management/static/description/icon.png',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
