from odoo import api, fields, models


class PayablePayment(models.Model):
    _name = "payable.payment"
    _description = "Payable Payment"
    _order = "date desc, id desc"

    name = fields.Char(required=True, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    payment_method_id = fields.Many2one("financial.payment.method", ondelete="restrict")
    source_account_id = fields.Many2one("treasury.account", ondelete="restrict")
    source_portador_id = fields.Many2one("financial.portador", ondelete="restrict")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("applied", "Applied"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    line_ids = fields.One2many(
        "payable.payment.line",
        "payment_id",
        string="Payment Lines",
    )
    withholding_line_ids = fields.One2many(
        "payable.payment.withholding",
        "payment_id",
        string="Withholding Lines",
        readonly=True,
    )
    gross_amount_total = fields.Monetary(
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )
    withholding_amount_total = fields.Monetary(
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )
    net_amount_total = fields.Monetary(
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends("line_ids.total_amount", "withholding_line_ids.amount")
    def _compute_totals(self):
        for payment in self:
            gross = sum(payment.line_ids.mapped("total_amount"))
            withheld = sum(payment.withholding_line_ids.mapped("amount"))
            payment.gross_amount_total = gross
            payment.withholding_amount_total = withheld
            payment.net_amount_total = gross - withheld
