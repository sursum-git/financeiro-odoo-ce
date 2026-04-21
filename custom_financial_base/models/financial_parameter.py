from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FinancialParameter(models.Model):
    _name = "financial.parameter"
    _description = "Financial Parameter"
    _rec_name = "company_id"

    MSG_PARAMETRO_UNICO_EMPRESA = "Ja existe um parametro financeiro para esta empresa."
    MSG_PORTADOR_PADRAO_EMPRESA = "O portador padrao deve pertencer a mesma empresa."
    MSG_FORMA_PAGAMENTO_PADRAO_EMPRESA = (
        "A forma de pagamento padrao deve pertencer a mesma empresa."
    )

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
        MSG_PARAMETRO_UNICO_EMPRESA,
    )

    @api.constrains("default_portador_id", "company_id")
    def _check_default_portador_company(self):
        for record in self:
            if (
                record.default_portador_id
                and record.default_portador_id.company_id
                and record.default_portador_id.company_id != record.company_id
            ):
                raise ValidationError(self.MSG_PORTADOR_PADRAO_EMPRESA)

    @api.constrains("default_payment_method_id", "company_id")
    def _check_default_payment_method_company(self):
        for record in self:
            if (
                record.default_payment_method_id
                and record.default_payment_method_id.company_id
                and record.default_payment_method_id.company_id != record.company_id
            ):
                raise ValidationError(self.MSG_FORMA_PAGAMENTO_PADRAO_EMPRESA)
