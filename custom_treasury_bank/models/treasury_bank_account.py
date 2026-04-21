from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TreasuryBankAccount(models.Model):
    _name = "treasury.bank.account"
    _description = "Treasury Bank Account"
    _order = "name"

    MSG_CONTA_UNICA_EMPRESA = "Esta conta bancaria ja existe para a empresa."
    MSG_CONTA_TESOURARIA_EMPRESA = (
        "A conta de tesouraria vinculada deve pertencer a mesma empresa."
    )

    name = fields.Char(required=True, index=True)
    bank_id = fields.Many2one(
        "treasury.bank",
        required=True,
        ondelete="restrict",
        index=True,
    )
    treasury_account_id = fields.Many2one(
        "treasury.account",
        ondelete="restrict",
        index=True,
    )
    agency = fields.Char()
    account_number = fields.Char(required=True, index=True)
    account_digit = fields.Char()
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    active = fields.Boolean(default=True)
    modality_link_ids = fields.One2many(
        "treasury.bank.account.modality",
        "bank_account_id",
        string="Modalities",
    )
    statement_import_ids = fields.One2many(
        "treasury.bank.statement.import",
        "bank_account_id",
        string="Statement Imports",
    )

    _treasury_bank_account_uniq = models.Constraint(
        "unique(bank_id, company_id, agency, account_number, account_digit)",
        MSG_CONTA_UNICA_EMPRESA,
    )

    @api.constrains("treasury_account_id", "company_id")
    def _check_treasury_account_company(self):
        for record in self.filtered("treasury_account_id"):
            if record.treasury_account_id.company_id != record.company_id:
                raise ValidationError(self.MSG_CONTA_TESOURARIA_EMPRESA)
