# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, relativedelta
import math


class HrLoan(models.Model):
    _name = 'hr.loan'
    _description = 'Employee Loan & Advance Salary'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc, id desc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────
    name = fields.Char(
        string='Loan Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )
    loan_type = fields.Selection([
        ('loan', 'Employee Loan'),
        ('advance', 'Advance Salary'),
    ], string='Type', required=True, default='loan', tracking=True)

    # ── Employee & Company ─────────────────────────────────────
    employee_id = fields.Many2one(
        'hr.employee', string='Employee',
        required=True, tracking=True,
        domain=[('active', '=', True)],
    )
    department_id = fields.Many2one(
        'hr.department', string='Department',
        related='employee_id.department_id', store=True, readonly=True,
    )
    job_id = fields.Many2one(
        'hr.job', string='Job Position',
        related='employee_id.job_id', store=True, readonly=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        related='company_id.currency_id', readonly=True,
    )

    # ── Financials ─────────────────────────────────────────────
    loan_amount = fields.Monetary(
        string='Loan Amount', required=True, tracking=True,
        currency_field='currency_id',
    )
    installment = fields.Integer(
        string='No. of Installments', required=True, default=12,
        tracking=True,
    )
    installment_amount = fields.Monetary(
        string='Installment Amount',
        compute='_compute_installment_amount',
        currency_field='currency_id', store=True,
    )
    total_paid = fields.Monetary(
        string='Total Paid',
        compute='_compute_totals',
        currency_field='currency_id', store=True,
    )
    total_remaining = fields.Monetary(
        string='Remaining Balance',
        compute='_compute_totals',
        currency_field='currency_id', store=True,
    )
    payment_date = fields.Date(
        string='First Deduction Date', required=True,
        default=fields.Date.today, tracking=True,
    )
    date_request = fields.Date(
        string='Request Date',
        default=fields.Date.today, readonly=True,
    )
    date_approved = fields.Date(
        string='Approval Date', readonly=True, tracking=True,
    )
    date_disbursed = fields.Date(
        string='Disbursement Date', readonly=True, tracking=True,
    )

    # ── State ──────────────────────────────────────────────────
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Waiting Approval'),
        ('validate1', 'Approved by HR'),
        ('validate', 'Approved & Disbursed'),
        ('refuse', 'Refused'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)

    # ── Relations ──────────────────────────────────────────────
    loan_lines = fields.One2many(
        'hr.loan.line', 'loan_id',
        string='Repayment Schedule',
    )
    refuse_reason = fields.Text(string='Refusal Reason', readonly=True)
    refused_by = fields.Many2one('res.users', string='Refused By', readonly=True)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True, tracking=True)

    # ── Notes ──────────────────────────────────────────────────
    notes = fields.Text(string='Notes / Purpose')

    # ── Counts ────────────────────────────────────────────────
    installment_count = fields.Integer(
        string='Installments', compute='_compute_installment_count',
    )
    paid_installment_count = fields.Integer(
        string='Paid', compute='_compute_installment_count',
    )

    # ─────────────────────────────────────────────────────────
    # Compute Methods
    # ─────────────────────────────────────────────────────────

    @api.depends('loan_amount', 'installment')
    def _compute_installment_amount(self):
        for rec in self:
            if rec.installment and rec.installment > 0:
                rec.installment_amount = rec.loan_amount / rec.installment
            else:
                rec.installment_amount = rec.loan_amount

    @api.depends('loan_lines.paid', 'loan_lines.amount')
    def _compute_totals(self):
        for rec in self:
            paid = sum(rec.loan_lines.filtered('paid').mapped('amount'))
            rec.total_paid = paid
            rec.total_remaining = rec.loan_amount - paid

    @api.depends('loan_lines')
    def _compute_installment_count(self):
        for rec in self:
            rec.installment_count = len(rec.loan_lines)
            rec.paid_installment_count = len(rec.loan_lines.filtered('paid'))

    # ─────────────────────────────────────────────────────────
    # ORM Overrides
    # ─────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan') or _('New')
        return super().create(vals_list)

    # ─────────────────────────────────────────────────────────
    # Constraints
    # ─────────────────────────────────────────────────────────

    @api.constrains('loan_amount')
    def _check_loan_amount(self):
        for rec in self:
            if rec.loan_amount <= 0:
                raise ValidationError(_('Loan amount must be greater than zero.'))

    @api.constrains('installment')
    def _check_installment(self):
        for rec in self:
            if rec.installment <= 0:
                raise ValidationError(_('Number of installments must be at least 1.'))

    @api.constrains('employee_id', 'state')
    def _check_active_loan(self):
        for rec in self:
            if rec.state in ('confirm', 'validate1', 'validate'):
                domain = [
                    ('employee_id', '=', rec.employee_id.id),
                    ('state', 'in', ['confirm', 'validate1', 'validate']),
                    ('id', '!=', rec.id),
                    ('loan_type', '=', rec.loan_type),
                ]
                if self.search_count(domain):
                    raise ValidationError(_(
                        'Employee %s already has an active %s in progress.',
                        rec.employee_id.name,
                        dict(self._fields['loan_type'].selection)[rec.loan_type],
                    ))

    # ─────────────────────────────────────────────────────────
    # Action Buttons / Workflow
    # ─────────────────────────────────────────────────────────

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft loans can be confirmed.'))
            rec.state = 'confirm'
            rec.message_post(body=_('Loan request submitted for approval.'))

    def action_validate1(self):
        """HR Manager first approval."""
        for rec in self:
            if rec.state != 'confirm':
                raise UserError(_('Loan must be in Waiting Approval state.'))
            rec.state = 'validate1'
            rec.approved_by = self.env.user
            rec.date_approved = fields.Date.today()
            rec.message_post(body=_('Loan approved by HR Manager. Awaiting final disbursement approval.'))

    def action_validate(self):
        """Finance / Admin final approval & disburse."""
        for rec in self:
            if rec.state != 'validate1':
                raise UserError(_('Loan must be approved by HR first.'))
            rec.state = 'validate'
            rec.date_disbursed = fields.Date.today()
            rec._generate_repayment_schedule()
            rec.message_post(body=_('Loan disbursed. Repayment schedule generated with %d installments.', rec.installment))

    def action_refuse(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Refuse Loan'),
            'res_model': 'hr.loan.refuse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_loan_id': self.id},
        }

    def action_cancel(self):
        for rec in self:
            if rec.state == 'validate':
                raise UserError(_('Disbursed loans cannot be cancelled. Please contact Finance.'))
            rec.state = 'cancel'
            rec.message_post(body=_('Loan request cancelled.'))

    def action_reset_draft(self):
        for rec in self:
            if rec.state not in ('cancel', 'refuse'):
                raise UserError(_('Only cancelled or refused loans can be reset to draft.'))
            rec.state = 'draft'
            rec.loan_lines.unlink()

    def action_view_installments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Repayment Schedule'),
            'res_model': 'hr.loan.line',
            'view_mode': 'tree,form',
            'domain': [('loan_id', '=', self.id)],
            'context': {'default_loan_id': self.id},
        }

    # ─────────────────────────────────────────────────────────
    # Repayment Schedule Generation
    # ─────────────────────────────────────────────────────────

    def _generate_repayment_schedule(self):
        """Auto-generate monthly installment lines."""
        for rec in self:
            rec.loan_lines.unlink()
            installment_amount = rec.loan_amount / rec.installment
            # Handle rounding — last installment absorbs the diff
            lines = []
            deduction_date = rec.payment_date
            running_total = 0.0
            for i in range(rec.installment):
                is_last = (i == rec.installment - 1)
                if is_last:
                    amount = round(rec.loan_amount - running_total, 2)
                else:
                    amount = round(installment_amount, 2)
                running_total += amount
                lines.append({
                    'loan_id': rec.id,
                    'date': deduction_date,
                    'amount': amount,
                    'paid': False,
                })
                deduction_date = deduction_date + relativedelta(months=1)
            self.env['hr.loan.line'].create(lines)

    # ─────────────────────────────────────────────────────────
    # Report
    # ─────────────────────────────────────────────────────────

    def action_print_loan(self):
        return self.env.ref('hr_loan_management.action_report_hr_loan').report_action(self)
