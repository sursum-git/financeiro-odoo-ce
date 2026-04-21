from odoo import fields, models


class TreasuryCashSessionLine(models.Model):
    _name = "treasury.cash.session.line"
    _description = "Treasury Cash Session Line"
    _order = "id"

    session_id = fields.Many2one(
        "treasury.cash.session",
        required=True,
        ondelete="cascade",
        index=True,
    )
    movement_id = fields.Many2one(
        "treasury.movement",
        required=True,
        ondelete="restrict",
        index=True,
    )
