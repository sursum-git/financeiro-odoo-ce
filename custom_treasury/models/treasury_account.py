from odoo import fields, models


class TreasuryAccount(models.Model):
    _name = "treasury.account"
    _description = "Treasury Account"
    _order = "name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(index=True)
    type = fields.Selection(
        [
            ("bank", "Bank"),
            ("cash_internal", "Cash Internal"),
            ("treasury", "Treasury"),
            ("other", "Other"),
        ],
        required=True,
        default="other",
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    active = fields.Boolean(default=True)
    modality_link_ids = fields.One2many(
        "treasury.account.modality",
        "account_id",
        string="Modalities",
    )

    _treasury_account_code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        "The treasury account code must be unique per company.",
    )
