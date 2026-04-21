from odoo import fields, models


class PayableSchedule(models.Model):
    _name = "payable.schedule"
    _description = "Payable Schedule"
    _order = "payment_date, id desc"

    name = fields.Char(required=True, index=True)
    payment_date = fields.Date(required=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict", index=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
