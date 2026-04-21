from odoo import fields, models


class FinancialHistory(models.Model):
    _name = "financial.history"
    _description = "Financial History"
    _order = "name"

    MSG_CODIGO_UNICO_EMPRESA = "O codigo do historico deve ser unico por empresa."

    name = fields.Char(required=True, index=True)
    code = fields.Char(index=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        default=lambda self: self.env.company,
        index=True,
    )

    _financial_history_code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        MSG_CODIGO_UNICO_EMPRESA,
    )
