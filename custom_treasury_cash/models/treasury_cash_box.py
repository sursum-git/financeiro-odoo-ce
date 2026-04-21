from odoo import fields, models


class TreasuryCashBox(models.Model):
    _name = "treasury.cash.box"
    _description = "Treasury Cash Box"
    _order = "name"

    MSG_CODIGO_UNICO_EMPRESA = "O codigo do caixa deve ser unico por empresa."

    name = fields.Char(required=True, index=True)
    code = fields.Char(index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    portador_id = fields.Many2one(
        "financial.portador",
        ondelete="restrict",
        index=True,
    )
    active = fields.Boolean(default=True)
    session_ids = fields.One2many("treasury.cash.session", "cash_box_id", string="Sessions")

    _treasury_cash_box_code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        MSG_CODIGO_UNICO_EMPRESA,
    )
