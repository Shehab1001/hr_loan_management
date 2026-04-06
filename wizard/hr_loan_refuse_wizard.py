# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class HrLoanRefuseWizard(models.TransientModel):
    _name = 'hr.loan.refuse.wizard'
    _description = 'Refuse Loan Wizard'

    loan_id = fields.Many2one('hr.loan', string='Loan', required=True, readonly=True)
    refuse_reason = fields.Text(string='Reason for Refusal', required=True)

    def action_refuse(self):
        self.ensure_one()
        loan = self.loan_id
        if loan.state not in ('confirm', 'validate1'):
            raise UserError(_('Only loans awaiting approval can be refused.'))
        loan.write({
            'state': 'refuse',
            'refuse_reason': self.refuse_reason,
            'refused_by': self.env.user.id,
        })
        loan.message_post(
            body=_('Loan refused by %s. Reason: %s', self.env.user.name, self.refuse_reason)
        )
        return {'type': 'ir.actions.act_window_close'}
