from odoo import fields, models


class FinancialModality(models.Model):
    _name = "financial.modality"
    _description = "Financial Modality"
    _order = "name"

    MSG_CODIGO_UNICO_EMPRESA = "O codigo da modalidade deve ser unico por empresa."

    name = fields.Char(required=True, index=True)
    code = fields.Char(index=True)
    tipo_operacao = fields.Selection(
        [
            ("receber", "Receber"),
            ("pagar", "Pagar"),
            ("tesouraria", "Tesouraria"),
            ("misto", "Misto"),
        ],
        string="Tipo de Operacao",
        default="misto",
        required=True,
        index=True,
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        default=lambda self: self.env.company,
        index=True,
    )

    _financial_modality_code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        MSG_CODIGO_UNICO_EMPRESA,
    )
