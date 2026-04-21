from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TreasuryBankStatementLine(models.Model):
    _name = "treasury.bank.statement.line"
    _description = "Treasury Bank Statement Line"
    _order = "date, id"

    MSG_VALOR_POSITIVO = "O valor da linha do extrato deve ser positivo."

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
        "res.currency",
        required=True,
        string="Moeda da Linha",
        ondelete="restrict",
    )
    company_currency_id = fields.Many2one(
        related="import_id.company_id.currency_id",
        string="Moeda da Empresa",
        store=True,
        readonly=True,
    )
    amount_company_currency = fields.Monetary(
        compute="_compute_company_amount",
        store=True,
        currency_field="company_currency_id",
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

    @api.depends("amount", "currency_id", "company_currency_id", "date", "import_id.company_id")
    def _compute_company_amount(self):
        for line in self:
            currency = line.currency_id or line.company_currency_id
            company_currency = line.company_currency_id
            if not currency or not company_currency:
                line.amount_company_currency = line.amount
                continue
            line.amount_company_currency = currency._convert(
                line.amount,
                company_currency,
                line.import_id.company_id,
                line.date,
            )

    @api.constrains("amount")
    def _check_positive_amount(self):
        for line in self:
            if line.amount <= 0:
                raise ValidationError(self.MSG_VALOR_POSITIVO)
