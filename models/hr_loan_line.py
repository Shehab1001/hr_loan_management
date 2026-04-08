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
    currency_id = fields.Many2one(
        'res.currency', related='loan_id.currency_id', readonly=True,
    )
    date = fields.Date(string='Due Date', required=True)
    amount = fields.Monetary(
        string='Amount', required=True, currency_field='currency_id',
    )
    paid = fields.Boolean(string='Paid', default=False)
    paid_date = fields.Date(string='Payment Date', readonly=True)
    payment_id = fields.Many2one(
        'hr.loan.payment', string='Payment Record',
        readonly=True, ondelete='set null',
    )
    move_id = fields.Many2one(
        'account.move', string='Journal Entry',
        related='payment_id.move_id', readonly=True,
    )
    note = fields.Char(string='Note')

    def action_mark_paid_manual(self):
        """Manual mark without accounting entry — for quick adjustments."""
        for line in self:
            if line.paid:
                raise UserError(_('Already marked as paid.'))
            line.write({'paid': True, 'paid_date': fields.Date.today()})
            line.loan_id.message_post(
                body=_('Installment of %s %s due %s manually marked as paid.',
                        line.currency_id.symbol, line.amount, line.date)
            )
            line.loan_id._check_and_close()

    def action_unmark_paid(self):
        for line in self:
            if not line.paid:
                raise UserError(_('This installment is not paid.'))
            if line.payment_id:
                raise UserError(_(
                    'Cannot unmark: linked to payment %s. Reverse the payment instead.',
                    line.payment_id.name,
                ))
            line.write({'paid': False, 'paid_date': False})
