from odoo import fields, models


class TreasuryReconciliation(models.Model):
    _name = "treasury.reconciliation"
    _description = "Treasury Reconciliation"
    _order = "date_end desc, id desc"

    name = fields.Char(required=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    bank_account_id = fields.Many2one(
        "treasury.bank.account",
        required=True,
        ondelete="restrict",
        index=True,
    )
    date_start = fields.Date(required=True, index=True)
    date_end = fields.Date(required=True, index=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    line_ids = fields.One2many(
        "treasury.reconciliation.line",
        "reconciliation_id",
        string="Reconciliation Lines",
    )
