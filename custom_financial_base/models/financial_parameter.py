from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FinancialParameter(models.Model):
    _name = "financial.parameter"
    _description = "Financial Parameter"
    _rec_name = "company_id"

    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    default_portador_id = fields.Many2one("financial.portador", string="Portador Padrao")
    default_payment_method_id = fields.Many2one(
        "financial.payment.method",
        string="Forma de Pagamento Padrao",
    )
    allow_negative_cash = fields.Boolean(string="Permite Caixa Negativo", default=False)
    require_cash_difference_reason = fields.Boolean(
        string="Exigir Motivo para Diferenca de Caixa",
        default=True,
    )
    active = fields.Boolean(default=True)

    _financial_parameter_company_uniq = models.Constraint(
        "unique(company_id)",
        "Ja existe um parametro financeiro para esta empresa.",
    )

    @api.constrains("default_portador_id", "company_id")
    def _check_default_portador_company(self):
        for record in self:
            if (
                record.default_portador_id
                and record.default_portador_id.company_id
                and record.default_portador_id.company_id != record.company_id
            ):
                raise ValidationError("O portador padrao deve pertencer a mesma empresa.")

    @api.constrains("default_payment_method_id", "company_id")
    def _check_default_payment_method_company(self):
        for record in self:
            if (
                record.default_payment_method_id
                and record.default_payment_method_id.company_id
                and record.default_payment_method_id.company_id != record.company_id
            ):
                raise ValidationError(
                    "A forma de pagamento padrao deve pertencer a mesma empresa."
                )
