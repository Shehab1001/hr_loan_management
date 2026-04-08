# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrLoanPayment(models.Model):
    """
    Records each actual repayment against a loan.
    Creates an accounting journal entry on confirmation:
      DR  Repayment Account (Bank/Cash)
      CR  Loan Receivable Account
    """
    _name = 'hr.loan.payment'
    _description = 'Loan Repayment Payment'
    _inherit = ['mail.thread']
    _order = 'payment_date desc, id desc'

    name = fields.Char(
        string='Reference', required=True, copy=False,
        readonly=True, default=lambda self: _('New'),
    )
    loan_id = fields.Many2one(
        'hr.loan', string='Loan', required=True,
        domain=[('state', '=', 'validate')],
        ondelete='restrict', tracking=True,
    )
    employee_id = fields.Many2one(
        'hr.employee', related='loan_id.employee_id',
        store=True, readonly=True,
    )
    company_id = fields.Many2one(
        'res.company', related='loan_id.company_id',
        store=True, readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency', related='loan_id.currency_id', readonly=True,
    )
    payment_date = fields.Date(
        string='Payment Date', required=True,
        default=fields.Date.today, tracking=True,
    )
    amount = fields.Monetary(
        string='Amount', required=True,
        currency_field='currency_id', tracking=True,
    )
    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('cash',          'Cash'),
        ('cheque',        'Cheque'),
        ('other',         'Other'),
    ], string='Payment Method', default='bank_transfer', required=True)
    note = fields.Text(string='Notes')
    state = fields.Selection([
        ('draft',    'Draft'),
        ('posted',   'Posted'),
        ('reversed', 'Reversed'),
    ], default='draft', tracking=True, copy=False)
    move_id = fields.Many2one(
        'account.move', string='Journal Entry',
        readonly=True, copy=False,
    )
    loan_line_ids = fields.Many2many(
        'hr.loan.line', string='Applied Installments',
        domain="[('loan_id', '=', loan_id), ('paid', '=', False)]",
    )

    # ── ORM ───────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan.payment') or _('New')
        return super().create(vals_list)

    # ── Constraints ───────────────────────────────────────────

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('Payment amount must be greater than zero.'))

    # ── Actions ───────────────────────────────────────────────

    def action_post(self):
        """Validate payment: create journal entry and mark installments."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft payments can be posted.'))
            config = self.env['hr.loan.config'].get_config(rec.company_id)
            if not config:
                raise UserError(_(
                    'No loan accounting configuration found for "%s". '
                    'Please set it up under Loan Management → Configuration.',
                    rec.company_id.name
                ))
            move = rec._create_repayment_entry(config)
            rec.move_id = move
            rec.state = 'posted'
            # Mark applied installment lines as paid
            for line in rec.loan_line_ids:
                line.write({
                    'paid': True,
                    'paid_date': rec.payment_date,
                    'payment_id': rec.id,
                })
            rec.loan_id._check_and_close()
            rec.message_post(body=_(
                'Payment of %s %s posted. Journal entry: %s',
                rec.currency_id.symbol, rec.amount, move.name,
            ))

    def action_reverse(self):
        """Reverse payment: reverse the journal entry, unmark installments."""
        for rec in self:
            if rec.state != 'posted':
                raise UserError(_('Only posted payments can be reversed.'))
            if rec.move_id:
                reversal = rec.move_id._reverse_moves(
                    default_values_list=[{'ref': _('Reversal of %s', rec.name)}]
                )
                reversal.action_post()
            for line in rec.loan_line_ids:
                line.write({'paid': False, 'paid_date': False, 'payment_id': False})
            rec.state = 'reversed'
            rec.message_post(body=_('Payment reversed by %s.', self.env.user.name))

    def _create_repayment_entry(self, config):
        """
        Journal Entry for repayment:
          DR  Repayment Account (Bank/Cash)   amount
          CR  Loan Receivable Account          amount
        """
        self.ensure_one()
        move_vals = {
            'move_type': 'entry',
            'journal_id': config.loan_journal_id.id,
            'date': self.payment_date,
            'ref': _('%s — Loan Repayment — %s', self.name, self.loan_id.name),
            'company_id': self.company_id.id,
            'line_ids': [
                # Debit: Repayment account (bank/cash receiving the money back)
                (0, 0, {
                    'name': _('Loan Repayment — %s', self.loan_id.employee_id.name),
                    'account_id': config.repayment_account_id.id,
                    'partner_id': self.loan_id.employee_partner_id.id,
                    'debit': self.amount,
                    'credit': 0.0,
                }),
                # Credit: Loan Receivable (reducing the outstanding balance)
                (0, 0, {
                    'name': _('Loan Repayment — %s', self.loan_id.employee_id.name),
                    'account_id': config.loan_account_id.id,
                    'partner_id': self.loan_id.employee_partner_id.id,
                    'debit': 0.0,
                    'credit': self.amount,
                }),
            ],
        }
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        return move
