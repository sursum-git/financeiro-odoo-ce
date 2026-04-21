from odoo import models
from odoo.exceptions import ValidationError


class TreasuryMovementService(models.AbstractModel):
    _name = "treasury.movement.service"
    _description = "Treasury Movement Service"

    MSG_VALOR_POSITIVO = "O valor do movimento deve ser positivo."
    MSG_MOVIMENTO_CANCELADO = "Movimentos cancelados nao podem ser postados."
    MSG_SALDO_MULTIMOEDA_EXIGE_FILTRO = (
        "Existem movimentos em mais de uma moeda. Informe uma moeda especifica ou use o saldo na moeda da empresa."
    )

    def create_movement(self, vals):
        if vals.get("amount", 0) <= 0:
            raise ValidationError(self.MSG_VALOR_POSITIVO)
        if not vals.get("currency_id") and vals.get("portador_id"):
            portador = self.env["financial.portador"].browse(vals["portador_id"])
            vals["currency_id"] = portador.currency_id.id
        if not vals.get("currency_id") and vals.get("company_id"):
            company = self.env["res.company"].browse(vals["company_id"])
            vals["currency_id"] = company.currency_id.id
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
                "currency_id": movement.currency_id.id,
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

    def _get_balance_domain(self, account=None, portador=None, company=None):
        domain = [("state", "=", "posted")]
        if account:
            domain.append(("account_id", "=", account.id))
        if portador:
            domain.append(("portador_id", "=", portador.id))
        if company:
            domain.append(("company_id", "=", company.id))
        return domain

    def compute_balance(self, account=None, portador=None, company=None, currency=None):
        domain = self._get_balance_domain(account=account, portador=portador, company=company)
        movements = self.env["treasury.movement"].search(domain)
        if currency:
            return sum(
                movements.filtered(lambda movement: movement.currency_id == currency).mapped("signed_amount")
            )
        currencies = movements.mapped("currency_id")
        if len(currencies) > 1:
            return sum(movements.mapped("signed_amount_company_currency"))
        return sum(movements.mapped("signed_amount"))

    def compute_balance_by_currency(self, account=None, portador=None, company=None):
        domain = self._get_balance_domain(account=account, portador=portador, company=company)
        balances = {}
        for movement in self.env["treasury.movement"].search(domain):
            balances.setdefault(movement.currency_id.id, 0.0)
            balances[movement.currency_id.id] += movement.signed_amount
        return balances
