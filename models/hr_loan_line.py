# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrLoanLine(models.Model):
    _name = 'hr.loan.line'
    _description = 'Loan Repayment Schedule Line'
    _order = 'date asc'

    loan_id = fields.Many2one(
        'hr.loan', string='Loan', required=True, ondelete='cascade',
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Employee',
        related='loan_id.employee_id', store=True, readonly=True,
    )
    date = fields.Date(string='Scheduled Date', required=True)
    amount = fields.Monetary(
        string='Installment Amount', required=True,
        currency_field='currency_id',
    )
    paid = fields.Boolean(string='Paid', default=False)
    paid_date = fields.Date(string='Paid On', readonly=True)
    payslip_id = fields.Many2one(
        'hr.payslip', string='Payslip',
        readonly=True, ondelete='set null',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='loan_id.currency_id', readonly=True,
    )
    note = fields.Char(string='Note')

    def action_mark_paid(self):
        for line in self:
            if line.paid:
                raise UserError(_('This installment is already marked as paid.'))
            line.paid = True
            line.paid_date = fields.Date.today()
            line.loan_id.message_post(
                body=_('Installment of %s on %s manually marked as paid.',
                       line.currency_id.symbol + str(line.amount), line.date)
            )

    def action_mark_unpaid(self):
        for line in self:
            if not line.paid:
                raise UserError(_('This installment is not paid yet.'))
            if line.payslip_id:
                raise UserError(_(
                    'Cannot unmark: this installment was deducted via payslip %s.',
                    line.payslip_id.name
                ))
            line.paid = False
            line.paid_date = False
