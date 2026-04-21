from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PayableInstallment(models.Model):
    _name = "payable.installment"
    _description = "Payable Installment"
    _order = "due_date, sequence, id"

    title_id = fields.Many2one(
        "payable.title",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(required=True, default=1)
    due_date = fields.Date(required=True, index=True)
    amount = fields.Monetary(required=True, currency_field="currency_id")
    amount_open = fields.Monetary(
        compute="_compute_amount_open",
        store=True,
        currency_field="currency_id",
    )
    state = fields.Selection(
        [
            ("open", "Open"),
            ("partial", "Partial"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="open",
        index=True,
    )
    currency_id = fields.Many2one(
        related="title_id.currency_id",
        store=True,
        readonly=True,
    )
    payment_line_ids = fields.One2many(
        "payable.payment.line",
        "installment_id",
        string="Payment Lines",
    )

    @api.depends("amount", "payment_line_ids.total_amount", "payment_line_ids.payment_id.state")
    def _compute_amount_open(self):
        for installment in self:
            paid_amount = sum(
                installment.payment_line_ids.filtered(
                    lambda line: line.payment_id.state == "applied"
                ).mapped("total_amount")
            )
            installment.amount_open = installment.amount - paid_amount
            if installment.state == "cancelled":
                continue
            if installment.amount_open <= 0:
                installment.amount_open = 0.0
                installment.state = "paid"
            elif paid_amount > 0:
                installment.state = "partial"
            else:
                installment.state = "open"

    @api.constrains("amount")
    def _check_positive_amount(self):
        for installment in self:
            if installment.amount <= 0:
                raise ValidationError("Installment amount must be positive.")
