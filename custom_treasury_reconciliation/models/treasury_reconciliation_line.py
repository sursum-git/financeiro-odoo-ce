from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TreasuryReconciliationLine(models.Model):
    _name = "treasury.reconciliation.line"
    _description = "Treasury Reconciliation Line"
    _order = "id"

    reconciliation_id = fields.Many2one(
        "treasury.reconciliation",
        required=True,
        ondelete="cascade",
        index=True,
    )
    statement_line_id = fields.Many2one(
        "treasury.bank.statement.line",
        required=True,
        ondelete="restrict",
        index=True,
    )
    movement_id = fields.Many2one(
        "treasury.movement",
        ondelete="restrict",
        index=True,
    )
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("matched", "Matched"),
            ("divergent", "Divergent"),
            ("adjusted", "Adjusted"),
        ],
        required=True,
        default="pending",
        index=True,
    )
    difference_amount = fields.Monetary(
        compute="_compute_difference_amount",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="statement_line_id.currency_id",
        store=True,
        readonly=True,
    )
    notes = fields.Text()
    adjustment_movement_id = fields.Many2one("treasury.movement", ondelete="restrict")

    _treasury_reconciliation_statement_line_uniq = models.Constraint(
        "unique(statement_line_id)",
        "A statement line can only be linked to one reconciliation line.",
    )

    @api.depends("statement_line_id.amount", "movement_id.signed_amount")
    def _compute_difference_amount(self):
        for line in self:
            movement_amount = abs(line.movement_id.signed_amount) if line.movement_id else 0.0
            line.difference_amount = line.statement_line_id.amount - movement_amount

    @api.constrains("statement_line_id")
    def _check_statement_line_not_already_reconciled(self):
        for line in self:
            if line.statement_line_id.is_reconciled and line.status != "matched":
                raise ValidationError("This statement line is already reconciled.")
