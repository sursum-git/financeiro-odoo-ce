from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PayablePaymentLine(models.Model):
    _name = "payable.payment.line"
    _description = "Payable Payment Line"
    _order = "id"

    MSG_VALORES_NAO_NEGATIVOS = "Os valores do pagamento nao podem ser negativos."
    MSG_PAGAMENTO_EXCEDE_SALDO = (
        "O valor do pagamento nao pode exceder o saldo em aberto da parcela."
    )

    payment_id = fields.Many2one(
        "payable.payment",
        required=True,
        ondelete="cascade",
        index=True,
    )
    installment_id = fields.Many2one(
        "payable.installment",
        required=True,
        ondelete="restrict",
        index=True,
    )
    principal_amount = fields.Monetary(required=True, currency_field="currency_id", default=0.0)
    interest_amount = fields.Monetary(currency_field="currency_id", default=0.0)
    fine_amount = fields.Monetary(currency_field="currency_id", default=0.0)
    discount_amount = fields.Monetary(currency_field="currency_id", default=0.0)
    total_amount = fields.Monetary(
        compute="_compute_total_amount",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="installment_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends("principal_amount", "interest_amount", "fine_amount", "discount_amount")
    def _compute_total_amount(self):
        for line in self:
            line.total_amount = (
                line.principal_amount + line.interest_amount + line.fine_amount - line.discount_amount
            )

    @api.constrains("principal_amount", "total_amount", "installment_id", "payment_id")
    def _check_amounts(self):
        for line in self:
            if line.principal_amount < 0 or line.total_amount < 0:
                raise ValidationError(self.MSG_VALORES_NAO_NEGATIVOS)
            if line.payment_id.state == "draft" and line.total_amount > line.installment_id.amount_open:
                raise ValidationError(self.MSG_PAGAMENTO_EXCEDE_SALDO)
