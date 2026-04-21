from odoo import fields, models


class TreasuryBankAccountModality(models.Model):
    _name = "treasury.bank.account.modality"
    _description = "Treasury Bank Account Modality"
    _order = "bank_account_id, modality_id"

    bank_account_id = fields.Many2one(
        "treasury.bank.account",
        required=True,
        ondelete="cascade",
        index=True,
    )
    modality_id = fields.Many2one(
        "financial.modality",
        required=True,
        ondelete="restrict",
        index=True,
    )
    code = fields.Char(index=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        related="bank_account_id.company_id",
        store=True,
        readonly=True,
    )

    _treasury_bank_account_modality_uniq = models.Constraint(
        "unique(bank_account_id, modality_id)",
        "This bank account already has the selected modality.",
    )
