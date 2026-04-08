# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class HrLoan(models.Model):
    _name = 'hr.loan'
    _description = 'Employee Loan & Advance Salary'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc, id desc'
    _rec_name = 'name'

    # ── Identity ──────────────────────────────────────────────
    name = fields.Char(
        string='Loan Reference', required=True, copy=False,
        readonly=True, default=lambda self: _('New'), tracking=True,
    )
    loan_type = fields.Selection([
        ('loan', 'Employee Loan'),
        ('advance', 'Advance Salary'),
    ], string='Type', required=True, default='loan', tracking=True)

    # ── Employee Info ──────────────────────────────────────────
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        tracking=True, domain=[('active', '=', True)],
    )
    department_id = fields.Many2one(
        'hr.department', string='Department',
        related='employee_id.department_id', store=True, readonly=True,
    )
    job_id = fields.Many2one(
        'hr.job', string='Job Position',
        related='employee_id.job_id', store=True, readonly=True,
    )
    employee_partner_id = fields.Many2one(
        'res.partner',
        string='Employee Partner',
        related='employee_id.work_contact_id',
        store=True,
        readonly=True,
    )

    # ── Company ────────────────────────────────────────────────
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', readonly=True,
    )

    # ── Financials ─────────────────────────────────────────────
    loan_amount = fields.Monetary(
        string='Loan Amount', required=True, tracking=True,
        currency_field='currency_id',
    )
    installment = fields.Integer(
        string='No. of Installments', required=True, default=12, tracking=True,
    )
    installment_amount = fields.Monetary(
        string='Monthly Installment',
        compute='_compute_installment_amount', store=True,
        currency_field='currency_id',
    )
    total_paid = fields.Monetary(
        string='Total Paid',
        compute='_compute_totals', store=True,
        currency_field='currency_id',
    )
    total_remaining = fields.Monetary(
        string='Remaining Balance',
        compute='_compute_totals', store=True,
        currency_field='currency_id',
    )
    payment_start_date = fields.Date(
        string='First Repayment Date', required=True,
        default=fields.Date.today, tracking=True,
    )
    date_request = fields.Date(
        string='Request Date', default=fields.Date.today,
        readonly=True,
    )
    date_approved = fields.Date(string='Approval Date', readonly=True, tracking=True)
    date_disbursed = fields.Date(string='Disbursement Date', readonly=True, tracking=True)

    # ── State ──────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',     'Draft'),
        ('confirm',   'Waiting Approval'),
        ('validate1', 'Approved by HR'),
        ('validate',  'Disbursed'),
        ('close',     'Closed / Fully Paid'),
        ('refuse',    'Refused'),
        ('cancel',    'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)

    # ── Accounting ─────────────────────────────────────────────
    move_id = fields.Many2one(
        'account.move', string='Disbursal Journal Entry',
        readonly=True, copy=False,
    )
    payment_ids = fields.One2many(
        'hr.loan.payment', 'loan_id', string='Payments',
    )
    payment_count = fields.Integer(
        string='Payments', compute='_compute_payment_count',
    )

    # ── Relations ──────────────────────────────────────────────
    loan_lines = fields.One2many(
        'hr.loan.line', 'loan_id', string='Repayment Schedule',
    )
    installment_count = fields.Integer(
        string='Installments', compute='_compute_installment_count',
    )
    paid_installment_count = fields.Integer(
        string='Paid', compute='_compute_installment_count',
    )

    # ── Approval trail ─────────────────────────────────────────
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True, tracking=True)
    refused_by  = fields.Many2one('res.users', string='Refused By', readonly=True)
    refuse_reason = fields.Text(string='Refusal Reason', readonly=True)
    notes = fields.Text(string='Notes / Purpose')

    # ─────────────────────────────────────────────────────────
    # Compute
    # ─────────────────────────────────────────────────────────

    @api.depends('loan_amount', 'installment')
    def _compute_installment_amount(self):
        for rec in self:
            if rec.installment and rec.installment > 0:
                rec.installment_amount = round(rec.loan_amount / rec.installment, 2)
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

    @api.depends('payment_ids')
    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = len(rec.payment_ids)

    # ─────────────────────────────────────────────────────────
    # ORM
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

    @api.constrains('employee_id', 'state', 'loan_type')
    def _check_one_active_loan(self):
        for rec in self:
            if rec.state in ('confirm', 'validate1', 'validate'):
                existing = self.search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('loan_type',   '=', rec.loan_type),
                    ('state', 'in', ['confirm', 'validate1', 'validate']),
                    ('id', '!=', rec.id),
                ])
                if existing:
                    raise ValidationError(_(
                        'Employee "%s" already has an active %s request.',
                        rec.employee_id.name,
                        dict(self._fields['loan_type'].selection)[rec.loan_type],
                    ))

    # ─────────────────────────────────────────────────────────
    # Workflow Actions
    # ─────────────────────────────────────────────────────────

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only Draft loans can be submitted.'))
            rec.state = 'confirm'
            rec.message_post(body=_('Loan request submitted for HR approval by %s.', self.env.user.name))

    def action_validate1(self):
        """HR Manager — first level approval."""
        for rec in self:
            if rec.state != 'confirm':
                raise UserError(_('Loan must be in Waiting Approval state.'))
            rec.write({
                'state': 'validate1',
                'approved_by': self.env.user.id,
                'date_approved': fields.Date.today(),
            })
            rec.message_post(body=_(
                'Loan approved by HR Manager (%s). Awaiting Finance disbursement.',
                self.env.user.name
            ))

    def action_validate(self):
        """Finance — final approval, disburse funds, create journal entry."""
        for rec in self:
            if rec.state != 'validate1':
                raise UserError(_('Loan must be HR-approved before disbursement.'))
            rec._create_disbursal_entry()
            rec._generate_repayment_schedule()
            rec.write({
                'state': 'validate',
                'date_disbursed': fields.Date.today(),
            })
            rec.message_post(body=_(
                'Loan disbursed by %s. Journal entry created. '
                'Repayment schedule of %d installments generated.',
                self.env.user.name, rec.installment,
            ))

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
                raise UserError(_('Disbursed loans cannot be cancelled directly. Contact Finance.'))
            rec.state = 'cancel'
            rec.message_post(body=_('Loan request cancelled by %s.', self.env.user.name))

    def action_reset_draft(self):
        for rec in self:
            if rec.state not in ('cancel', 'refuse'):
                raise UserError(_('Only cancelled or refused loans can be reset to Draft.'))
            rec.loan_lines.unlink()
            rec.state = 'draft'
            rec.message_post(body=_('Loan reset to Draft by %s.', self.env.user.name))

    def action_register_payment(self):
        """Open payment wizard to manually register an installment repayment."""
        self.ensure_one()
        if self.state != 'validate':
            raise UserError(_('Only active (Disbursed) loans can receive payments.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Register Repayment'),
            'res_model': 'hr.loan.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_loan_id': self.id},
        }

    # ─────────────────────────────────────────────────────────
    # Smart Button Actions
    # ─────────────────────────────────────────────────────────

    def action_view_installments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Repayment Schedule'),
            'res_model': 'hr.loan.line',
            'view_mode': 'tree,form',
            'domain': [('loan_id', '=', self.id)],
        }

    def action_view_payments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payments'),
            'res_model': 'hr.loan.payment',
            'view_mode': 'tree,form',
            'domain': [('loan_id', '=', self.id)],
        }

    def action_view_journal_entry(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Disbursal Journal Entry'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.move_id.id,
        }

    def action_print_loan(self):
        return self.env.ref('hr_loan_management.action_report_hr_loan').report_action(self)

    # ─────────────────────────────────────────────────────────
    # Accounting: Disbursal Journal Entry
    # ─────────────────────────────────────────────────────────

    def _create_disbursal_entry(self):
        """
        On disbursal, create an account.move:
          DR  Loan Receivable Account    (loan_account_id)
          CR  Disbursal / Source Account (disbursal_account_id)
        """
        self.ensure_one()
        config = self.env['hr.loan.config'].get_config(self.company_id)
        if not config:
            raise UserError(_(
                'No loan accounting configuration found for company "%s". '
                'Please configure it under Loan Management → Configuration.',
                self.company_id.name,
            ))

        move_vals = {
            'move_type': 'entry',
            'journal_id': config.loan_journal_id.id,
            'date': fields.Date.today(),
            'ref': self.name,
            'company_id': self.company_id.id,
            'line_ids': [
                # Debit: Loan Receivable
                (0, 0, {
                    'name': _('Loan Disbursed — %s — %s', self.employee_id.name, self.name),
                    'account_id': config.loan_account_id.id,
                    'partner_id': self.employee_partner_id.id,
                    'debit': self.loan_amount,
                    'credit': 0.0,
                    'currency_id': self.currency_id.id,
                }),
                # Credit: Bank / Cash / Source
                (0, 0, {
                    'name': _('Loan Disbursed — %s — %s', self.employee_id.name, self.name),
                    'account_id': config.disbursal_account_id.id,
                    'partner_id': self.employee_partner_id.id,
                    'debit': 0.0,
                    'credit': self.loan_amount,
                    'currency_id': self.currency_id.id,
                }),
            ],
        }
        move = self.env['account.move'].create(move_vals)
        move.action_post()
        self.move_id = move

    # ─────────────────────────────────────────────────────────
    # Repayment Schedule
    # ─────────────────────────────────────────────────────────

    def _generate_repayment_schedule(self):
        for rec in self:
            rec.loan_lines.unlink()
            lines = []
            running = 0.0
            base_amount = round(rec.loan_amount / rec.installment, 2)
            deduction_date = rec.payment_start_date
            for i in range(rec.installment):
                is_last = (i == rec.installment - 1)
                amount = round(rec.loan_amount - running, 2) if is_last else base_amount
                running += amount
                lines.append({
                    'loan_id': rec.id,
                    'date': deduction_date,
                    'amount': amount,
                    'paid': False,
                })
                deduction_date = deduction_date + relativedelta(months=1)
            self.env['hr.loan.line'].create(lines)

    # ─────────────────────────────────────────────────────────
    # Auto-close when fully paid
    # ─────────────────────────────────────────────────────────

    def _check_and_close(self):
        for rec in self:
            if rec.state == 'validate' and rec.total_remaining <= 0:
                rec.state = 'close'
                rec.message_post(body=_('Loan fully repaid and automatically closed.'))
