from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryCashSession(models.Model):
    _name = "treasury.cash.session"
    _description = "Treasury Cash Session"
    _order = "opened_at desc, id desc"

    MSG_SESSAO_ABERTA_EXISTENTE = "Ja existe uma sessao aberta para este caixa."
    MSG_CAIXA_EMPRESA_DIFERENTE = "O caixa deve pertencer a mesma empresa."
    MSG_ABERTURA_SOMENTE_RASCUNHO = "Somente sessoes em rascunho podem ser abertas."
    MSG_FECHAMENTO_SOMENTE_ABERTA = "Somente sessoes abertas podem ser fechadas."
    MSG_MOTIVO_DIFERENCA_OBRIGATORIO = "E obrigatorio informar um motivo para diferenca de caixa."
    MSG_SESSAO_FECHADA_SEM_CANCELAMENTO = "Sessoes fechadas nao podem ser canceladas."
    MSG_MOEDA_CAIXA_DIVERGENTE = "A moeda da sessao deve ser igual a moeda do portador do caixa."

    name = fields.Char(required=True, index=True)
    cash_box_id = fields.Many2one(
        "treasury.cash.box",
        required=True,
        ondelete="restrict",
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
        ondelete="restrict",
        index=True,
    )
    opened_at = fields.Datetime()
    opening_amount = fields.Monetary(required=True, currency_field="currency_id", default=0.0)
    closed_at = fields.Datetime()
    closing_amount_informed = fields.Monetary(currency_field="currency_id")
    closing_amount_computed = fields.Monetary(
        compute="_compute_closing_amount_computed",
        store=True,
        currency_field="currency_id",
    )
    difference_amount = fields.Monetary(
        compute="_compute_difference_amount",
        store=True,
        currency_field="currency_id",
    )
    difference_reason = fields.Char()
    state = fields.Selection(
        [
            ("draft", "Rascunho"),
            ("open", "Aberto"),
            ("closed", "Fechado"),
            ("cancelled", "Cancelado"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Moeda da Sessao",
        required=True,
        default=lambda self: self.env.company.currency_id,
        ondelete="restrict",
    )
    line_ids = fields.One2many(
        "treasury.cash.session.line",
        "session_id",
        string="Movimentos da Sessao",
    )

    @api.depends("opening_amount", "line_ids.movement_id.state", "line_ids.movement_id.signed_amount")
    def _compute_closing_amount_computed(self):
        for session in self:
            posted_lines = session.line_ids.filtered(lambda line: line.movement_id.state == "posted")
            session.closing_amount_computed = session.opening_amount + sum(
                posted_lines.mapped("movement_id.signed_amount")
            )

    @api.depends("closing_amount_informed", "closing_amount_computed")
    def _compute_difference_amount(self):
        for session in self:
            session.difference_amount = (
                (session.closing_amount_informed or 0.0) - session.closing_amount_computed
            )

    @api.constrains("cash_box_id", "state")
    def _check_single_open_session(self):
        for session in self.filtered(lambda rec: rec.state == "open"):
            domain = [
                ("id", "!=", session.id),
                ("cash_box_id", "=", session.cash_box_id.id),
                ("state", "=", "open"),
            ]
            if self.search_count(domain):
                raise ValidationError(self.MSG_SESSAO_ABERTA_EXISTENTE)

    @api.constrains("cash_box_id", "company_id")
    def _check_company_consistency(self):
        for session in self:
            if session.cash_box_id.company_id != session.company_id:
                raise ValidationError(self.MSG_CAIXA_EMPRESA_DIFERENTE)

    @api.constrains("cash_box_id", "currency_id")
    def _check_currency_consistency(self):
        for session in self.filtered(lambda rec: rec.cash_box_id.portador_id):
            if session.cash_box_id.portador_id.currency_id != session.currency_id:
                raise ValidationError(self.MSG_MOEDA_CAIXA_DIVERGENTE)

    def action_open(self):
        for session in self:
            if session.state != "draft":
                raise UserError(self.MSG_ABERTURA_SOMENTE_RASCUNHO)
            session.write(
                {
                    "state": "open",
                    "opened_at": fields.Datetime.now(),
                }
            )

    def action_close(self):
        for session in self:
            if session.state != "open":
                raise UserError(self.MSG_FECHAMENTO_SOMENTE_ABERTA)
            parameter = self.env["financial.parameter"].search(
                [("company_id", "=", session.company_id.id)],
                limit=1,
            )
            if (
                parameter.require_cash_difference_reason
                and session.difference_amount
                and not session.difference_reason
            ):
                raise ValidationError(self.MSG_MOTIVO_DIFERENCA_OBRIGATORIO)
            session.write(
                {
                    "state": "closed",
                    "closed_at": fields.Datetime.now(),
                }
            )

    def action_cancel(self):
        for session in self:
            if session.state == "closed":
                raise UserError(self.MSG_SESSAO_FECHADA_SEM_CANCELAMENTO)
            session.state = "cancelled"

    def action_open_supply_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Registrar Suprimento",
            "res_model": "treasury.cash.operation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_session_id": self.id,
                "default_operation_type": "supply",
            },
        }

    def action_open_withdrawal_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Registrar Sangria",
            "res_model": "treasury.cash.operation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_session_id": self.id,
                "default_operation_type": "withdrawal",
            },
        }
