from odoo import fields, models


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
