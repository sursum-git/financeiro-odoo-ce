from odoo import fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryCashAccountability(models.Model):
    _name = "treasury.cash.accountability"
    _description = "Treasury Cash Accountability"
    _order = "date desc, id desc"

    name = fields.Char(required=True, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    source_portador_id = fields.Many2one(
        "financial.portador",
        required=True,
        ondelete="restrict",
        index=True,
    )
    target_account_id = fields.Many2one("treasury.account", ondelete="restrict")
    target_portador_id = fields.Many2one("financial.portador", ondelete="restrict")
    amount = fields.Monetary(required=True, currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    out_movement_id = fields.Many2one("treasury.movement", ondelete="restrict")
    in_movement_id = fields.Many2one("treasury.movement", ondelete="restrict")

    @property
    def _cash_service(self):
        return self.env["treasury.cash.service"]

    def action_confirm(self):
        for record in self:
            if record.state != "draft":
                continue
            if record.amount <= 0:
                raise ValidationError("Accountability amount must be positive.")
            if not record.target_account_id and not record.target_portador_id:
                raise ValidationError("A target account or target portador is required.")
            out_move, in_move = record._cash_service.create_accountability(
                source_portador=record.source_portador_id,
                target_account=record.target_account_id,
                target_portador=record.target_portador_id,
                amount=record.amount,
                company=record.company_id,
                name=record.name,
                date=record.date,
            )
            record.write(
                {
                    "state": "confirmed",
                    "out_movement_id": out_move.id,
                    "in_movement_id": in_move.id,
                }
            )

    def action_cancel(self):
        for record in self:
            if record.state != "confirmed":
                raise UserError("Only confirmed accountabilities can be cancelled.")
            self.env["treasury.movement.service"].reverse_movement(record.out_movement_id)
            self.env["treasury.movement.service"].reverse_movement(record.in_movement_id)
            record.state = "cancelled"
