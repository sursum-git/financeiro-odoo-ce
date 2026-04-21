from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    withholding_line_ids = fields.One2many(
        "res.partner.withholding.line",
        "partner_id",
        string="Withholding Lines",
    )
