from odoo import models
from odoo.exceptions import ValidationError


class TreasuryMovementService(models.AbstractModel):
    _name = "treasury.movement.service"
    _description = "Treasury Movement Service"

    MSG_VALOR_POSITIVO = "O valor do movimento deve ser positivo."
    MSG_MOVIMENTO_CANCELADO = "Movimentos cancelados nao podem ser postados."

    def create_movement(self, vals):
        if vals.get("amount", 0) <= 0:
            raise ValidationError(self.MSG_VALOR_POSITIVO)
        return self.env["treasury.movement"].create(vals)

    def post_movement(self, movement):
        movement.ensure_one()
        if movement.state == "cancelled":
            raise ValidationError(self.MSG_MOVIMENTO_CANCELADO)
        if movement.state == "posted":
            return movement
        movement.with_context(skip_post_lock=True).write({"state": "posted"})
        return movement

    def reverse_movement(self, movement, reason=None):
        movement.ensure_one()
        if movement.reverse_move_ids:
            return movement.reverse_move_ids[0]
        reverse_move = self.create_movement(
            {
                "name": f"Estorno - {movement.name}",
                "date": movement.date,
                "company_id": movement.company_id.id,
                "type": "estorno",
                "amount": movement.amount,
                "account_id": movement.account_id.id,
                "portador_id": movement.portador_id.id,
                "payment_method_id": movement.payment_method_id.id,
                "history_id": movement.history_id.id,
                "reason_id": reason.id if reason else movement.reason_id.id,
                "origin_module": movement.origin_module,
                "origin_model": movement.origin_model,
                "origin_record_id": movement.origin_record_id,
                "reversed_movement_id": movement.id,
            }
        )
        self.post_movement(reverse_move)
        return reverse_move

    def compute_balance(self, account=None, portador=None, company=None):
        domain = [("state", "=", "posted")]
        if account:
            domain.append(("account_id", "=", account.id))
        if portador:
            domain.append(("portador_id", "=", portador.id))
        if company:
            domain.append(("company_id", "=", company.id))
        return sum(self.env["treasury.movement"].search(domain).mapped("signed_amount"))
