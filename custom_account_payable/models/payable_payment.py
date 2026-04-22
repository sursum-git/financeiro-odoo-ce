from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class PayablePayment(models.Model):
    _name = "payable.payment"
    _description = "Payable Payment"
    _order = "date desc, id desc"

    MSG_PAGAMENTO_MOEDA_UNICA = "O pagamento deve conter apenas parcelas na mesma moeda."
    MSG_PAGAMENTO_MOEDA_DIVERGENTE = (
        "A moeda do pagamento deve ser igual a moeda das parcelas selecionadas."
    )
    MSG_TAXA_CAMBIO_POSITIVA = "A taxa de cambio deve ser maior que zero."
    MSG_APLICACAO_SOMENTE_RASCUNHO = "Somente pagamentos em rascunho podem ser aplicados."
    MSG_CANCELAMENTO_SOMENTE_RASCUNHO = "Somente pagamentos em rascunho podem ser cancelados."

    name = fields.Char(required=True, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    payment_method_id = fields.Many2one("financial.payment.method", ondelete="restrict")
    source_account_id = fields.Many2one("treasury.account", ondelete="restrict")
    source_portador_id = fields.Many2one("financial.portador", ondelete="restrict")
    state = fields.Selection(
        [
            ("draft", "Rascunho"),
            ("applied", "Aplicado"),
            ("cancelled", "Cancelado"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    line_ids = fields.One2many(
        "payable.payment.line",
        "payment_id",
        string="Linhas de Pagamento",
    )
    withholding_line_ids = fields.One2many(
        "payable.payment.withholding",
        "payment_id",
        string="Linhas de Retencao",
        readonly=True,
    )
    gross_amount_total = fields.Monetary(
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )
    withholding_amount_total = fields.Monetary(
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )
    net_amount_total = fields.Monetary(
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Moeda da Transacao",
        required=True,
        default=lambda self: self.env.company.currency_id,
        ondelete="restrict",
    )
    company_currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Moeda da Empresa",
        store=True,
        readonly=True,
    )
    exchange_rate = fields.Float(
        compute="_compute_company_amounts",
        store=True,
        digits=(16, 8),
    )
    gross_amount_company_currency = fields.Monetary(
        compute="_compute_company_amounts",
        store=True,
        currency_field="company_currency_id",
    )
    withholding_amount_company_currency = fields.Monetary(
        compute="_compute_company_amounts",
        store=True,
        currency_field="company_currency_id",
    )
    net_amount_company_currency = fields.Monetary(
        compute="_compute_company_amounts",
        store=True,
        currency_field="company_currency_id",
    )

    @api.depends("line_ids.total_amount", "withholding_line_ids.amount")
    def _compute_totals(self):
        for payment in self:
            gross = sum(payment.line_ids.mapped("total_amount"))
            withheld = sum(payment.withholding_line_ids.mapped("amount"))
            payment.gross_amount_total = gross
            payment.withholding_amount_total = withheld
            payment.net_amount_total = gross - withheld

    @api.depends(
        "currency_id",
        "company_id",
        "company_currency_id",
        "date",
        "gross_amount_total",
        "withholding_amount_total",
        "net_amount_total",
    )
    def _compute_company_amounts(self):
        for payment in self:
            company_currency = payment.company_currency_id
            currency = payment.currency_id or company_currency
            date = payment.date or fields.Date.context_today(self)
            if not company_currency or not currency:
                payment.exchange_rate = 1.0
                payment.gross_amount_company_currency = payment.gross_amount_total
                payment.withholding_amount_company_currency = payment.withholding_amount_total
                payment.net_amount_company_currency = payment.net_amount_total
                continue
            payment.gross_amount_company_currency = currency._convert(
                payment.gross_amount_total,
                company_currency,
                payment.company_id,
                date,
            )
            payment.withholding_amount_company_currency = currency._convert(
                payment.withholding_amount_total,
                company_currency,
                payment.company_id,
                date,
            )
            payment.net_amount_company_currency = currency._convert(
                payment.net_amount_total,
                company_currency,
                payment.company_id,
                date,
            )
            if currency == company_currency or not payment.net_amount_total:
                payment.exchange_rate = 1.0
            else:
                payment.exchange_rate = (
                    payment.net_amount_company_currency / payment.net_amount_total
                )

    @api.constrains("line_ids", "currency_id")
    def _check_currency_consistency(self):
        for payment in self:
            line_currencies = payment.line_ids.mapped("currency_id")
            if len(line_currencies) > 1:
                raise ValidationError(self.MSG_PAGAMENTO_MOEDA_UNICA)
            if line_currencies and payment.currency_id and line_currencies[0] != payment.currency_id:
                raise ValidationError(self.MSG_PAGAMENTO_MOEDA_DIVERGENTE)

    @api.constrains("exchange_rate")
    def _check_exchange_rate(self):
        for payment in self:
            if payment.exchange_rate <= 0:
                raise ValidationError(self.MSG_TAXA_CAMBIO_POSITIVA)

    def action_apply(self):
        for payment in self:
            if payment.state != "draft":
                raise UserError(self.MSG_APLICACAO_SOMENTE_RASCUNHO)
            self.env["payable.service"].apply_payment(payment)
        return True

    def action_cancel(self):
        for payment in self:
            if payment.state != "draft":
                raise UserError(self.MSG_CANCELAMENTO_SOMENTE_RASCUNHO)
            payment.state = "cancelled"
        return True
