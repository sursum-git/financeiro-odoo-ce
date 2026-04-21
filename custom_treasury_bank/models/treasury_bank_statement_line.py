from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TreasuryBankStatementLine(models.Model):
    _name = "treasury.bank.statement.line"
    _description = "Treasury Bank Statement Line"
    _order = "date, id"

    import_id = fields.Many2one(
        "treasury.bank.statement.import",
        required=True,
        ondelete="cascade",
        index=True,
    )
    date = fields.Date(required=True, index=True)
    description = fields.Char()
    document_number = fields.Char(index=True)
    amount = fields.Monetary(required=True, currency_field="currency_id")
    currency_id = fields.Many2one(
        related="import_id.company_id.currency_id",
        store=True,
        readonly=True,
    )
    type = fields.Selection(
        [
            ("credit", "Credit"),
            ("debit", "Debit"),
        ],
        required=True,
        index=True,
    )
    is_reconciled = fields.Boolean(default=False, index=True)
    movement_id = fields.Many2one(
        "treasury.movement",
        ondelete="restrict",
        index=True,
    )
    @api.constrains("amount")
    def _check_positive_amount(self):
        for line in self:
            if line.amount <= 0:
                raise ValidationError("Statement line amount must be positive.")
