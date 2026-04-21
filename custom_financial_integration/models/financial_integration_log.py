from odoo import fields, models


class FinancialIntegrationLog(models.Model):
    _name = "financial.integration.log"
    _description = "Financial Integration Log"
    _order = "created_at desc, id desc"

    event_id = fields.Many2one(
        "financial.integration.event",
        required=True,
        ondelete="cascade",
        index=True,
    )
    level = fields.Selection(
        [
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
        ],
        required=True,
        default="info",
        index=True,
    )
    message = fields.Text(required=True)
    created_at = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
