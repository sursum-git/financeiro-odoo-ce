from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceivableSettlementLine(models.Model):
    _name = "receivable.settlement.line"
    _description = "Receivable Settlement Line"
    _order = "id"

    settlement_id = fields.Many2one(
        "receivable.settlement",
        required=True,
        ondelete="cascade",
        index=True,
    )
    installment_id = fields.Many2one(
        "receivable.installment",
        required=True,
        ondelete="restrict",
        index=True,
    )
    title_id = fields.Many2one(
        related="installment_id.title_id",
        store=True,
        readonly=True,
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

    @api.constrains("principal_amount", "total_amount", "installment_id", "settlement_id")
    def _check_amounts(self):
        for line in self:
            if line.principal_amount < 0 or line.total_amount < 0:
                raise ValidationError("Settlement amounts cannot be negative.")
            if line.settlement_id.state == "draft" and line.total_amount > line.installment_id.amount_open:
                raise ValidationError("Settlement amount cannot exceed the installment open amount.")
