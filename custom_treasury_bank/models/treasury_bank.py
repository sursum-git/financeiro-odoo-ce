from odoo import fields, models


class TreasuryBank(models.Model):
    _name = "treasury.bank"
    _description = "Treasury Bank"
    _order = "name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    account_ids = fields.One2many("treasury.bank.account", "bank_id", string="Bank Accounts")

    _treasury_bank_code_uniq = models.Constraint(
        "unique(code)",
        "The bank code must be unique.",
    )
