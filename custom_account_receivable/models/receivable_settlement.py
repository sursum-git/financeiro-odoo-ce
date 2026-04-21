from odoo import api, fields, models


class ReceivableSettlement(models.Model):
    _name = "receivable.settlement"
    _description = "Receivable Settlement"
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
    portador_id = fields.Many2one("financial.portador", ondelete="restrict")
    target_account_id = fields.Many2one("treasury.account", ondelete="restrict")
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
        "receivable.settlement.line",
        "settlement_id",
        string="Settlement Lines",
    )
    withholding_line_ids = fields.One2many(
        "receivable.settlement.withholding",
        "settlement_id",
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
        for settlement in self:
            gross = sum(settlement.line_ids.mapped("total_amount"))
            withheld = sum(settlement.withholding_line_ids.mapped("amount"))
            settlement.gross_amount_total = gross
            settlement.withholding_amount_total = withheld
            settlement.net_amount_total = gross - withheld
