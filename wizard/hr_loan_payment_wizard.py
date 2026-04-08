# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrLoanPaymentWizard(models.TransientModel):
    _name = 'hr.loan.payment.wizard'
    _description = 'Register Loan Repayment Wizard'

    loan_id = fields.Many2one(
        'hr.loan', string='Loan', required=True, readonly=True,
    )
    employee_id = fields.Many2one(
        'hr.employee', related='loan_id.employee_id', readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency', related='loan_id.currency_id', readonly=True,
    )
    total_remaining = fields.Monetary(
        related='loan_id.total_remaining',
        currency_field='currency_id', readonly=True,
    )
    payment_date = fields.Date(
        string='Payment Date', required=True, default=fields.Date.today,
    )
    amount = fields.Monetary(
        string='Amount', required=True, currency_field='currency_id',
    )
    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('cash',          'Cash'),
        ('cheque',        'Cheque'),
        ('other',         'Other'),
    ], string='Payment Method', required=True, default='bank_transfer')
    loan_line_ids = fields.Many2many(
        'hr.loan.line', string='Apply to Installments',
        domain="[('loan_id', '=', loan_id), ('paid', '=', False)]",
    )
    note = fields.Text(string='Notes')

    @api.onchange('loan_id')
    def _onchange_loan_id(self):
        """Pre-fill the next due unpaid installment."""
        if self.loan_id:
            next_line = self.env['hr.loan.line'].search([
                ('loan_id', '=', self.loan_id.id),
                ('paid', '=', False),
            ], order='date asc', limit=1)
            if next_line:
                self.loan_line_ids = next_line
                self.amount = next_line.amount

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('Payment amount must be greater than zero.'))
            if rec.amount > rec.total_remaining:
                raise ValidationError(_(
                    'Payment amount (%.2f) exceeds remaining loan balance (%.2f).',
                    rec.amount, rec.total_remaining,
                ))

    def action_register(self):
        self.ensure_one()
        if not self.loan_line_ids:
            raise UserError(_('Please select at least one installment to apply this payment to.'))

        payment = self.env['hr.loan.payment'].create({
            'loan_id': self.loan_id.id,
            'payment_date': self.payment_date,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'note': self.note,
            'loan_line_ids': [(6, 0, self.loan_line_ids.ids)],
        })
        payment.action_post()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment'),
            'res_model': 'hr.loan.payment',
            'res_id': payment.id,
            'view_mode': 'form',
            'target': 'current',
        }
