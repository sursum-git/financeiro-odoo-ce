from odoo import fields, models


class FinancialPortador(models.Model):
    _name = "financial.portador"
    _description = "Financial Portador"
    _order = "name"

    MSG_CODIGO_UNICO_EMPRESA = "O codigo do portador deve ser unico por empresa."

    name = fields.Char(required=True, index=True)
    code = fields.Char(index=True)
    type = fields.Selection(
        [
            ("caixa", "Caixa"),
            ("banco", "Banco"),
            ("cobrador", "Cobrador"),
            ("adquirente", "Adquirente"),
            ("gateway", "Gateway"),
            ("interno", "Interno"),
        ],
        string="Tipo",
        default="interno",
        required=True,
        index=True,
    )
    controla_saldo = fields.Boolean(default=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        default=lambda self: self.env.company,
        index=True,
    )

    _financial_portador_code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        MSG_CODIGO_UNICO_EMPRESA,
    )
