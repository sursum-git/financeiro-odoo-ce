from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryMovement(models.Model):
    _name = "treasury.movement"
    _description = "Treasury Movement"
    _order = "date desc, id desc"

    MSG_VALOR_POSITIVO = "O valor do movimento deve ser positivo."
    MSG_EXIGE_CONTA_OU_PORTADOR = "O movimento exige uma conta ou um portador."
    MSG_CONTA_EMPRESA_DIFERENTE = "A conta deve pertencer a mesma empresa."
    MSG_PORTADOR_EMPRESA_DIFERENTE = "O portador deve pertencer a mesma empresa."
    MSG_MOEDA_PORTADOR_DIFERENTE = "A moeda do movimento deve ser igual a moeda do portador."
    MSG_TAXA_CAMBIO_POSITIVA = "A taxa de cambio deve ser positiva."
    MSG_CONCILIADO_SEM_EDICAO = "Movimentos conciliados nao podem ser editados livremente."
    MSG_POSTADO_SEM_EDICAO = "Movimentos postados nao podem ser editados livremente."
    MSG_POSTADO_SEM_EXCLUSAO = "Movimentos postados nao podem ser excluidos."

    name = fields.Char(required=True, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    type = fields.Selection(
        [
            ("entrada", "Entrada"),
            ("saida", "Saida"),
            ("transferencia_entrada", "Transferencia Entrada"),
            ("transferencia_saida", "Transferencia Saida"),
            ("ajuste", "Ajuste"),
            ("estorno", "Estorno"),
            ("tarifa", "Tarifa"),
            ("deposito", "Deposito"),
            ("saque", "Saque"),
        ],
        required=True,
        default="ajuste",
        index=True,
    )
    amount = fields.Monetary(required=True, currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    company_currency_id = fields.Many2one(
        "res.currency",
        string="Moeda da Empresa",
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )
    exchange_rate = fields.Float(
        string="Taxa de Cambio",
        compute="_compute_company_amounts",
        store=True,
        digits=(16, 8),
    )
    amount_company_currency = fields.Monetary(
        string="Valor na Moeda da Empresa",
        compute="_compute_company_amounts",
        store=True,
        currency_field="company_currency_id",
    )
    account_id = fields.Many2one("treasury.account", ondelete="restrict", index=True)
    portador_id = fields.Many2one("financial.portador", ondelete="restrict", index=True)
    payment_method_id = fields.Many2one(
        "financial.payment.method",
        ondelete="restrict",
        index=True,
    )
    history_id = fields.Many2one("financial.history", ondelete="restrict")
    reason_id = fields.Many2one("financial.movement.reason", ondelete="restrict")
    origin_module = fields.Char(index=True)
    origin_model = fields.Char(index=True)
    origin_record_id = fields.Integer(index=True)
    state = fields.Selection(
        [
            ("draft", "Rascunho"),
            ("posted", "Postado"),
            ("cancelled", "Cancelado"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    is_reconciled = fields.Boolean(default=False, index=True)
    reversed_movement_id = fields.Many2one(
        "treasury.movement",
        string="Movimento Estornado",
        ondelete="restrict",
    )
    reverse_move_ids = fields.One2many(
        "treasury.movement",
        "reversed_movement_id",
        string="Movimentos de Estorno",
    )
    active = fields.Boolean(default=True)
    payment_line_ids = fields.One2many(
        "treasury.movement.payment.line",
        "movement_id",
        string="Linhas de Pagamento",
    )
    signed_amount = fields.Monetary(
        compute="_compute_signed_amount",
        currency_field="currency_id",
    )
    signed_amount_company_currency = fields.Monetary(
        string="Saldo Assinado na Moeda da Empresa",
        compute="_compute_signed_amount_company_currency",
        currency_field="company_currency_id",
    )

    @api.depends("type", "amount")
    def _compute_signed_amount(self):
        for movement in self:
            movement.signed_amount = movement.amount * movement._get_direction_sign()

    @api.depends("amount", "currency_id", "company_id", "date")
    def _compute_company_amounts(self):
        for movement in self:
            company_currency = movement.company_currency_id
            transaction_currency = movement.currency_id
            if not movement.amount or not company_currency or not transaction_currency:
                movement.amount_company_currency = 0.0
                movement.exchange_rate = 1.0
                continue
            converted_amount = transaction_currency._convert(
                movement.amount,
                company_currency,
                movement.company_id,
                movement.date or fields.Date.context_today(movement),
            )
            movement.amount_company_currency = converted_amount
            movement.exchange_rate = converted_amount / movement.amount if movement.amount else 1.0

    @api.depends("type", "amount_company_currency")
    def _compute_signed_amount_company_currency(self):
        for movement in self:
            movement.signed_amount_company_currency = (
                movement.amount_company_currency * movement._get_direction_sign()
            )

    def _get_direction_sign(self):
        self.ensure_one()
        if self.type == "estorno" and self.reversed_movement_id:
            return -self.reversed_movement_id._get_direction_sign()
        if self.type in {"entrada", "transferencia_entrada", "deposito"}:
            return 1
        return -1

    @api.constrains("amount")
    def _check_amount_positive(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(self.MSG_VALOR_POSITIVO)

    @api.constrains("account_id", "portador_id")
    def _check_financial_target(self):
        for record in self:
            if not record.account_id and not record.portador_id:
                raise ValidationError(self.MSG_EXIGE_CONTA_OU_PORTADOR)

    @api.constrains("account_id", "company_id")
    def _check_account_company(self):
        for record in self.filtered("account_id"):
            if record.account_id.company_id != record.company_id:
                raise ValidationError(self.MSG_CONTA_EMPRESA_DIFERENTE)

    @api.constrains("portador_id", "company_id")
    def _check_portador_company(self):
        for record in self.filtered("portador_id"):
            if record.portador_id.company_id and record.portador_id.company_id != record.company_id:
                raise ValidationError(self.MSG_PORTADOR_EMPRESA_DIFERENTE)

    @api.constrains("portador_id", "currency_id")
    def _check_portador_currency(self):
        for record in self.filtered("portador_id"):
            if record.portador_id.currency_id != record.currency_id:
                raise ValidationError(self.MSG_MOEDA_PORTADOR_DIFERENTE)

    @api.constrains("exchange_rate")
    def _check_exchange_rate(self):
        for record in self:
            if record.exchange_rate <= 0:
                raise ValidationError(self.MSG_TAXA_CAMBIO_POSITIVA)

    def write(self, vals):
        if self.env.context.get("skip_post_lock"):
            return super().write(vals)
        restricted_fields = set(vals) - {"is_reconciled", "active"}
        for record in self:
            if record.is_reconciled and restricted_fields:
                raise UserError(self.MSG_CONCILIADO_SEM_EDICAO)
            if record.state == "posted" and restricted_fields:
                raise UserError(self.MSG_POSTADO_SEM_EDICAO)
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.state == "posted":
                raise UserError(self.MSG_POSTADO_SEM_EXCLUSAO)
        return super().unlink()
