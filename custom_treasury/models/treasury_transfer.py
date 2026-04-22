from odoo import fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryTransfer(models.Model):
    _name = "treasury.transfer"
    _description = "Treasury Transfer"
    _order = "date desc, id desc"

    MSG_VALOR_POSITIVO = "O valor da transferencia deve ser positivo."
    MSG_ORIGEM_OBRIGATORIA = "A origem da transferencia e obrigatoria."
    MSG_DESTINO_OBRIGATORIO = "O destino da transferencia e obrigatorio."
    MSG_CONTAS_DIFERENTES = "As contas de origem e destino devem ser diferentes."
    MSG_PORTADORES_DIFERENTES = "Os portadores de origem e destino devem ser diferentes."
    MSG_CANCELAMENTO_SOMENTE_CONFIRMADA = (
        "Somente transferencias confirmadas podem ser canceladas."
    )
    MSG_MOVIMENTOS_NAO_GERADOS = "Os movimentos da transferencia nao foram gerados."

    name = fields.Char(required=True, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
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
            ("draft", "Rascunho"),
            ("confirmed", "Confirmado"),
            ("cancelled", "Cancelado"),
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
                raise ValidationError(self.MSG_VALOR_POSITIVO)
            if not (record.source_account_id or record.source_portador_id):
                raise ValidationError(self.MSG_ORIGEM_OBRIGATORIA)
            if not (record.target_account_id or record.target_portador_id):
                raise ValidationError(self.MSG_DESTINO_OBRIGATORIO)
            if (
                record.source_account_id
                and record.target_account_id
                and record.source_account_id == record.target_account_id
            ):
                raise ValidationError(self.MSG_CONTAS_DIFERENTES)
            if (
                record.source_portador_id
                and record.target_portador_id
                and record.source_portador_id == record.target_portador_id
            ):
                raise ValidationError(self.MSG_PORTADORES_DIFERENTES)

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
                raise UserError(self.MSG_CANCELAMENTO_SOMENTE_CONFIRMADA)
            if not record.out_movement_id or not record.in_movement_id:
                raise UserError(self.MSG_MOVIMENTOS_NAO_GERADOS)
            record._movement_service.reverse_movement(record.out_movement_id)
            record._movement_service.reverse_movement(record.in_movement_id)
            record.state = "cancelled"
