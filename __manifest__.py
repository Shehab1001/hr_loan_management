# -*- coding: utf-8 -*-
{
    'name': 'HR Loan & Advance Salary Management',
    'version': '17.0.2.0.0',
    'category': 'Human Resources',
    'summary': 'Employee loans, advance salary, repayment schedules & accounting journal entries — Community Edition',
    'description': """
HR Loan & Advance Salary Management (Community Edition)
=======================================================
Works with: base, hr, account, mail — NO Enterprise required.

Features:
- Employee Loan & Advance Salary requests
- 3-level approval workflow (Employee → HR → Finance)
- Automatic monthly repayment schedule generation
- Accounting integration: auto journal entries on disbursal & repayments
- Manual payment recording with account.move links
- Loan refusal wizard with mandatory reason
- Printable PDF loan agreement with repayment schedule
- Role-based security (3 groups + record rules)
- Full chatter/audit trail via mail.thread
- Multi-company support
- Dashboard KPI smart buttons
    """,
    'author': 'Shehab Eldin Saeed Zakaria',
    'website': 'https://github.com/Shehab1001',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'account',
        'mail',
    ],
    'data': [
        'security/hr_loan_security.xml',
        'security/ir.model.access.csv',
        'data/hr_loan_sequence.xml',
        'data/hr_loan_data.xml',
        'views/hr_loan_config_views.xml',
        'views/hr_loan_views.xml',
        'views/hr_loan_line_views.xml',
        'views/hr_loan_payment_views.xml',
        'views/hr_loan_menu.xml',
        'report/hr_loan_report_template.xml',
        'report/hr_loan_report.xml',
        'wizard/hr_loan_refuse_wizard_views.xml',
        'wizard/hr_loan_payment_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
