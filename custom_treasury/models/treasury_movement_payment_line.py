from odoo import fields, models


class TreasuryMovementPaymentLine(models.Model):
    _name = "treasury.movement.payment.line"
    _description = "Treasury Movement Payment Line"
    _order = "id"

    movement_id = fields.Many2one(
        "treasury.movement",
        required=True,
        ondelete="cascade",
        index=True,
    )
    payment_method_id = fields.Many2one(
        "financial.payment.method",
        ondelete="restrict",
        index=True,
    )
    portador_id = fields.Many2one("financial.portador", ondelete="restrict", index=True)
    amount = fields.Monetary(required=True, currency_field="currency_id")
    currency_id = fields.Many2one(
        related="movement_id.currency_id",
        store=True,
        readonly=True,
    )
    details = fields.Char()
