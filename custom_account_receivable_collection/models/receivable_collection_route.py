from odoo import fields, models


class ReceivableCollectionRoute(models.Model):
    _name = "receivable.collection.route"
    _description = "Receivable Collection Route"
    _order = "date desc, id desc"

    name = fields.Char(required=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    assignment_ids = fields.One2many(
        "receivable.collection.assignment",
        "route_id",
        string="Assignments",
    )

    def action_open_assign_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Atribuir Titulos",
            "res_model": "receivable.collection.assign.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_route_id": self.id,
            },
        }
