from odoo import fields, models


class ReceivableInterestRule(models.Model):
    _name = "receivable.interest.rule"
    _description = "Receivable Interest Rule"
    _order = "name"

    name = fields.Char(required=True, index=True)
    interest_type = fields.Selection(
        [("fixed", "Fixo"), ("percent", "Percentual")],
        required=True,
        default="percent",
    )
    interest_value = fields.Float(default=0.0)
    fine_type = fields.Selection(
        [("fixed", "Fixo"), ("percent", "Percentual")],
        required=True,
        default="percent",
    )
    fine_value = fields.Float(default=0.0)
    discount_type = fields.Selection(
        [("fixed", "Fixo"), ("percent", "Percentual")],
        required=True,
        default="fixed",
    )
    discount_value = fields.Float(default=0.0)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    active = fields.Boolean(default=True)
