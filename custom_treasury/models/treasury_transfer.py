from odoo import fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryTransfer(models.Model):
    _name = "treasury.transfer"
    _description = "Treasury Transfer"
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
    source_account_id = fields.Many2one("treasury.account", ondelete="restrict")
    source_portador_id = fields.Many2one("financial.portador", ondelete="restrict")
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
    out_movement_id = fields.Many2one("treasury.movement", ondelete="restrict")
    in_movement_id = fields.Many2one("treasury.movement", ondelete="restrict")
    notes = fields.Text()

    @property
    def _movement_service(self):
        return self.env["treasury.movement.service"]

    def _validate_flow(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError("Transfer amount must be positive.")
            if not (record.source_account_id or record.source_portador_id):
                raise ValidationError("Transfer source is required.")
            if not (record.target_account_id or record.target_portador_id):
                raise ValidationError("Transfer target is required.")
            if (
                record.source_account_id
                and record.target_account_id
                and record.source_account_id == record.target_account_id
            ):
                raise ValidationError("Source and target accounts must be different.")
            if (
                record.source_portador_id
                and record.target_portador_id
                and record.source_portador_id == record.target_portador_id
            ):
                raise ValidationError("Source and target portadores must be different.")

    def action_confirm(self):
        for record in self:
            if record.state != "draft":
                continue
            record._validate_flow()
            out_move = record._movement_service.create_movement(
                {
                    "name": f"{record.name} - Saida",
                    "date": record.date,
                    "company_id": record.company_id.id,
                    "type": "transferencia_saida",
                    "amount": record.amount,
                    "account_id": record.source_account_id.id,
                    "portador_id": record.source_portador_id.id,
                    "origin_module": "custom_treasury",
                    "origin_model": "treasury.transfer",
                    "origin_record_id": record.id,
                }
            )
            in_move = record._movement_service.create_movement(
                {
                    "name": f"{record.name} - Entrada",
                    "date": record.date,
                    "company_id": record.company_id.id,
                    "type": "transferencia_entrada",
                    "amount": record.amount,
                    "account_id": record.target_account_id.id,
                    "portador_id": record.target_portador_id.id,
                    "origin_module": "custom_treasury",
                    "origin_model": "treasury.transfer",
                    "origin_record_id": record.id,
                }
            )
            record._movement_service.post_movement(out_move)
            record._movement_service.post_movement(in_move)
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
                raise UserError("Only confirmed transfers can be cancelled.")
            if not record.out_movement_id or not record.in_movement_id:
                raise UserError("Transfer movements were not generated.")
            record._movement_service.reverse_movement(record.out_movement_id)
            record._movement_service.reverse_movement(record.in_movement_id)
            record.state = "cancelled"
