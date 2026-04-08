# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrLoanConfig(models.Model):
    """
    Per-company configuration for loan accounting.
    Defines which journal and accounts to use for loan journal entries.
    """
    _name = 'hr.loan.config'
    _description = 'HR Loan Accounting Configuration'
    _rec_name = 'company_id'

    company_id = fields.Many2one(
        'res.company', string='Company',
        required=True, ondelete='cascade',
        default=lambda self: self.env.company,
    )
    # Journal used for loan disbursal and repayment entries
    loan_journal_id = fields.Many2one(
        'account.journal', string='Loan Journal',
        required=True,
        domain=[('type', 'in', ['bank', 'cash', 'general'])],
        help='Journal used to post loan disbursal and repayment accounting entries.',
    )
    # Debit account when loan is disbursed (Employee Receivable / Loan Receivable)
    loan_account_id = fields.Many2one(
        'account.account', string='Loan Receivable Account',
        required=True,
        help='Account debited when a loan is disbursed to the employee (e.g. Employee Loans Receivable).',
    )
    # Credit account for the source of funds (e.g. Bank or Cash)
    disbursal_account_id = fields.Many2one(
        'account.account', string='Disbursal / Source Account',
        required=True,
        help='Account credited on loan disbursal (e.g. Bank Account or Cash).',
    )
    # Account credited when repayment is received
    repayment_account_id = fields.Many2one(
        'account.account', string='Repayment Account',
        required=True,
        help='Account credited when an installment is repaid (e.g. Bank, Cash, or a clearing account).',
    )
    max_loan_amount = fields.Monetary(
        string='Max Loan Amount',
        currency_field='currency_id',
        default=50000.0,
        help='Maximum allowed single loan amount per request.',
    )
    max_installments = fields.Integer(
        string='Max Installments (Months)',
        default=24,
        help='Maximum number of monthly installments allowed.',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True,
    )

    _sql_constraints = [
        ('unique_company', 'UNIQUE(company_id)',
         'Only one loan configuration per company is allowed.'),
    ]

    @api.model
    def get_config(self, company=None):
        company = company or self.env.company
        config = self.search([('company_id', '=', company.id)], limit=1)
        return config
