from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryMovement(models.Model):
    _name = "treasury.movement"
    _description = "Treasury Movement"
    _order = "date desc, id desc"

    name = fields.Char(required=True, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
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
            ("draft", "Draft"),
            ("posted", "Posted"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    is_reconciled = fields.Boolean(default=False, index=True)
    reversed_movement_id = fields.Many2one(
        "treasury.movement",
        string="Reversed Movement",
        ondelete="restrict",
    )
    reverse_move_ids = fields.One2many(
        "treasury.movement",
        "reversed_movement_id",
        string="Reverse Movements",
    )
    active = fields.Boolean(default=True)
    payment_line_ids = fields.One2many(
        "treasury.movement.payment.line",
        "movement_id",
        string="Payment Lines",
    )
    signed_amount = fields.Monetary(
        compute="_compute_signed_amount",
        currency_field="currency_id",
    )

    @api.depends("type", "amount")
    def _compute_signed_amount(self):
        for movement in self:
            movement.signed_amount = movement.amount * movement._get_direction_sign()

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
                raise ValidationError("Movement amount must be positive.")

    @api.constrains("account_id", "portador_id")
    def _check_financial_target(self):
        for record in self:
            if not record.account_id and not record.portador_id:
                raise ValidationError("A movement requires an account or a portador.")

    @api.constrains("account_id", "company_id")
    def _check_account_company(self):
        for record in self.filtered("account_id"):
            if record.account_id.company_id != record.company_id:
                raise ValidationError("The account must belong to the same company.")

    @api.constrains("portador_id", "company_id")
    def _check_portador_company(self):
        for record in self.filtered("portador_id"):
            if record.portador_id.company_id and record.portador_id.company_id != record.company_id:
                raise ValidationError("The portador must belong to the same company.")

    def write(self, vals):
        if self.env.context.get("skip_post_lock"):
            return super().write(vals)
        restricted_fields = set(vals) - {"is_reconciled", "active"}
        for record in self:
            if record.is_reconciled and restricted_fields:
                raise UserError("Reconciled movements cannot be edited freely.")
            if record.state == "posted" and restricted_fields:
                raise UserError("Posted movements cannot be edited freely.")
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.state == "posted":
                raise UserError("Posted movements cannot be deleted.")
        return super().unlink()
