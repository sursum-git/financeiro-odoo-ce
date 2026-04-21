from odoo import fields, models


class FinancialPaymentMethod(models.Model):
    _name = "financial.payment.method"
    _description = "Financial Payment Method"
    _order = "name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(index=True)
    type = fields.Selection(
        [
            ("dinheiro", "Dinheiro"),
            ("pix", "PIX"),
            ("boleto", "Boleto"),
            ("cartao_credito", "Cartao de Credito"),
            ("cartao_debito", "Cartao de Debito"),
            ("transferencia", "Transferencia"),
            ("cheque", "Cheque"),
            ("outro", "Outro"),
        ],
        string="Tipo",
        default="outro",
        required=True,
        index=True,
    )
    liquida_imediato = fields.Boolean(default=False)
    permite_parcelamento = fields.Boolean(default=False)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        default=lambda self: self.env.company,
        index=True,
    )

    _financial_payment_method_code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        "O codigo da forma de pagamento deve ser unico por empresa.",
    )
