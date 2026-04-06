# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    loan_deduction_ids = fields.One2many(
        'hr.loan.line', 'payslip_id',
        string='Loan Deductions', readonly=True,
    )
    loan_deduction_count = fields.Integer(
        string='Loan Deductions',
        compute='_compute_loan_deduction_count',
    )
    total_loan_deduction = fields.Monetary(
        string='Total Loan Deduction',
        compute='_compute_total_loan_deduction',
        currency_field='currency_id',
    )

    @api.depends('loan_deduction_ids')
    def _compute_loan_deduction_count(self):
        for slip in self:
            slip.loan_deduction_count = len(slip.loan_deduction_ids)

    @api.depends('loan_deduction_ids.amount')
    def _compute_total_loan_deduction(self):
        for slip in self:
            slip.total_loan_deduction = sum(slip.loan_deduction_ids.mapped('amount'))

    def action_payslip_done(self):
        """
        Override: when payslip is confirmed/done, automatically deduct
        the next unpaid installment for the employee.
        """
        res = super().action_payslip_done()
        for slip in self:
            self._process_loan_deductions(slip)
        return res

    def _process_loan_deductions(self, slip):
        """
        Find the next due installment for the payslip employee
        within the payslip date range and mark it as paid.
        """
        LoanLine = self.env['hr.loan.line']
        due_lines = LoanLine.search([
            ('employee_id', '=', slip.employee_id.id),
            ('paid', '=', False),
            ('date', '>=', slip.date_from),
            ('date', '<=', slip.date_to),
            ('loan_id.state', '=', 'validate'),
        ], order='date asc')

        for line in due_lines:
            line.write({
                'paid': True,
                'paid_date': fields.Date.today(),
                'payslip_id': slip.id,
            })
            _logger.info(
                'Loan installment %s for employee %s marked paid via payslip %s',
                line.id, slip.employee_id.name, slip.name
            )

    def action_view_loan_deductions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Loan Deductions'),
            'res_model': 'hr.loan.line',
            'view_mode': 'tree,form',
            'domain': [('payslip_id', '=', self.id)],
        }


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    @api.model
    def _get_partner_id(self, contract, struct_id, localdict):
        """Ensure loan deduction lines get proper accounting partner."""
        return super()._get_partner_id(contract, struct_id, localdict)


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_loan_deduction = fields.Boolean(
        string='Is Loan Deduction Rule',
        default=False,
        help='Mark this rule as the loan deduction rule so the system knows which line to use.',
    )
