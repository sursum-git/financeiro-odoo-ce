from odoo import fields, models


class FinancialMovementReason(models.Model):
    _name = "financial.movement.reason"
    _description = "Financial Movement Reason"
    _order = "name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(index=True)
    type = fields.Selection(
        [
            ("suprimento", "Suprimento"),
            ("sangria", "Sangria"),
            ("ajuste", "Ajuste"),
            ("tarifa", "Tarifa"),
            ("estorno", "Estorno"),
            ("prestacao_contas", "Prestacao de Contas"),
            ("outro", "Outro"),
        ],
        string="Tipo",
        default="outro",
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

    _financial_movement_reason_code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        "O codigo do motivo deve ser unico por empresa.",
    )
