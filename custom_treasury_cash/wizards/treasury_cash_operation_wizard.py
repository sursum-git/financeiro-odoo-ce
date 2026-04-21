from odoo import fields, models
from odoo.exceptions import ValidationError


class TreasuryCashOperationWizard(models.TransientModel):
    _name = "treasury.cash.operation.wizard"
    _description = "Treasury Cash Operation Wizard"

    MSG_SESSAO_ABERTA = "Suprimento e sangria exigem uma sessao de caixa aberta."
    MSG_VALOR_POSITIVO = "Informe um valor positivo para a operacao."

    session_id = fields.Many2one(
        "treasury.cash.session",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(related="session_id.company_id", readonly=True)
    currency_id = fields.Many2one(related="session_id.currency_id", readonly=True)
    operation_type = fields.Selection(
        [
            ("supply", "Suprimento"),
            ("withdrawal", "Sangria"),
        ],
        required=True,
        readonly=True,
    )
    amount = fields.Monetary(required=True, currency_field="currency_id")
    history_id = fields.Many2one("financial.history", ondelete="restrict")

    def action_confirm(self):
        self.ensure_one()
        if self.session_id.state != "open":
            raise ValidationError(self.MSG_SESSAO_ABERTA)
        if self.amount <= 0:
            raise ValidationError(self.MSG_VALOR_POSITIVO)
        service = self.env["treasury.cash.service"]
        if self.operation_type == "supply":
            service.register_supply(self.session_id, self.amount, history=self.history_id)
        else:
            service.register_withdrawal(self.session_id, self.amount, history=self.history_id)
        return {
            "type": "ir.actions.act_window",
            "name": "Sessao de Caixa",
            "res_model": "treasury.cash.session",
            "res_id": self.session_id.id,
            "view_mode": "form",
            "target": "current",
        }
