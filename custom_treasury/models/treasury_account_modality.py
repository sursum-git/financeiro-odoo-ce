from odoo import fields, models


class TreasuryAccountModality(models.Model):
    _name = "treasury.account.modality"
    _description = "Treasury Account Modality"
    _order = "account_id, modality_id"

    MSG_MODALIDADE_UNICA = "Esta conta ja possui a modalidade selecionada."

    account_id = fields.Many2one(
        "treasury.account",
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
        related="account_id.company_id",
        store=True,
        readonly=True,
    )

    _treasury_account_modality_uniq = models.Constraint(
        "unique(account_id, modality_id)",
        MSG_MODALIDADE_UNICA,
    )
