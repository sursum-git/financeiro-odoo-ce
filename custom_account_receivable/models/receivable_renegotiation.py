from odoo import fields, models


class ReceivableRenegotiation(models.Model):
    _name = "receivable.renegotiation"
    _description = "Receivable Renegotiation"
    _order = "date desc, id desc"

    name = fields.Char(required=True, index=True)
    partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict", index=True)
    source_title_ids = fields.Many2many(
        "receivable.title",
        "receivable_renegotiation_title_rel",
        "renegotiation_id",
        "title_id",
        string="Titulos de Origem",
    )
    new_title_id = fields.Many2one("receivable.title", ondelete="restrict")
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    state = fields.Selection(
        [
            ("draft", "Rascunho"),
            ("done", "Concluido"),
            ("cancelled", "Cancelado"),
        ],
        required=True,
        default="draft",
        index=True,
    )
