from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceivableSettlementCheckLine(models.Model):
    _name = "receivable.settlement.check.line"
    _description = "Receivable Settlement Third-Party Check Line"
    _order = "id"

    MSG_VALOR_CHEQUE_POSITIVO = "O valor do cheque de terceiro deve ser positivo."

    settlement_id = fields.Many2one(
        "receivable.settlement",
        required=True,
        ondelete="cascade",
        index=True,
    )
    issuer_name = fields.Char(required=True)
    check_number = fields.Char(required=True, index=True)
    bank_name = fields.Char(required=True)
    branch = fields.Char(required=True)
    account_number = fields.Char(required=True)
    expected_clearance_date = fields.Date(required=True)
    amount = fields.Monetary(required=True, currency_field="currency_id")
    notes = fields.Char()
    currency_id = fields.Many2one(
        related="settlement_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.constrains("amount")
    def _check_amount(self):
        for line in self:
            if line.amount <= 0:
                raise ValidationError(self.MSG_VALOR_CHEQUE_POSITIVO)
