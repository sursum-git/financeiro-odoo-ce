from odoo import fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryCashService(models.AbstractModel):
    _name = "treasury.cash.service"
    _description = "Treasury Cash Service"

    MSG_SESSAO_ABERTA_EXISTENTE = "Ja existe uma sessao aberta para este caixa."
    MSG_FECHAMENTO_SOMENTE_ABERTA = "Somente sessoes abertas podem ser fechadas."
    MSG_MOVIMENTO_EXIGE_SESSAO_ABERTA = "Movimentos de caixa exigem uma sessao aberta."
    MSG_VALOR_POSITIVO = "O valor da prestacao de contas deve ser positivo."

    @property
    def _movement_service(self):
        return self.env["treasury.movement.service"]

    def open_session(self, cash_box, user, opening_amount):
        if self.env["treasury.cash.session"].search_count(
            [("cash_box_id", "=", cash_box.id), ("state", "=", "open")]
        ):
            raise ValidationError(self.MSG_SESSAO_ABERTA_EXISTENTE)
        return self.env["treasury.cash.session"].create(
            {
                "name": f"{cash_box.name} - {fields.Date.today()}",
                "cash_box_id": cash_box.id,
                "company_id": cash_box.company_id.id,
                "user_id": user.id,
                "opening_amount": opening_amount,
                "state": "open",
                "opened_at": fields.Datetime.now(),
            }
        )

    def close_session(self, session, informed_amount, reason=None):
        if session.state != "open":
            raise UserError(self.MSG_FECHAMENTO_SOMENTE_ABERTA)
        session.write(
            {
                "closing_amount_informed": informed_amount,
                "difference_reason": reason,
            }
        )
        session.action_close()
        return session

    def _create_session_movement(self, session, movement_type, amount, reason_type, history=None):
        if session.state != "open":
            raise UserError(self.MSG_MOVIMENTO_EXIGE_SESSAO_ABERTA)
        reason = self.env["financial.movement.reason"].search(
            [("company_id", "=", session.company_id.id), ("type", "=", reason_type)],
            limit=1,
        )
        if not reason:
            reason = self.env["financial.movement.reason"].create(
                {
                    "name": reason_type.replace("_", " ").title(),
                    "code": reason_type.upper()[:10],
                    "type": reason_type,
                    "company_id": session.company_id.id,
                }
            )
        movement = self._movement_service.create_movement(
            {
                "name": f"{session.name} - {movement_type.title()}",
                "date": fields.Date.context_today(self),
                "company_id": session.company_id.id,
                "type": movement_type,
                "amount": amount,
                "portador_id": session.cash_box_id.portador_id.id,
                "history_id": history.id if history else False,
                "reason_id": reason.id,
                "origin_module": "custom_treasury_cash",
                "origin_model": "treasury.cash.session",
                "origin_record_id": session.id,
            }
        )
        self._movement_service.post_movement(movement)
        self.env["treasury.cash.session.line"].create(
            {
                "session_id": session.id,
                "movement_id": movement.id,
            }
        )
        return movement

    def register_supply(self, session, amount, history=None):
        return self._create_session_movement(session, "entrada", amount, "suprimento", history=history)

    def register_withdrawal(self, session, amount, history=None):
        return self._create_session_movement(session, "saida", amount, "sangria", history=history)

    def create_accountability(
        self,
        source_portador,
        target_account,
        target_portador,
        amount,
        company,
        name,
        date,
    ):
        if amount <= 0:
            raise ValidationError(self.MSG_VALOR_POSITIVO)
        out_reason = self.env["financial.movement.reason"].search(
            [("company_id", "=", company.id), ("type", "=", "prestacao_contas")],
            limit=1,
        )
        if not out_reason:
            out_reason = self.env["financial.movement.reason"].create(
                {
                    "name": "Prestacao de Contas",
                    "code": "PREST_CONT",
                    "type": "prestacao_contas",
                    "company_id": company.id,
                }
            )
        out_move = self._movement_service.create_movement(
            {
                "name": f"{name} - Saida",
                "date": date,
                "company_id": company.id,
                "type": "saida",
                "amount": amount,
                "portador_id": source_portador.id,
                "reason_id": out_reason.id,
                "origin_module": "custom_treasury_cash",
                "origin_model": "treasury.cash.accountability",
            }
        )
        in_move = self._movement_service.create_movement(
            {
                "name": f"{name} - Entrada",
                "date": date,
                "company_id": company.id,
                "type": "entrada",
                "amount": amount,
                "account_id": target_account.id if target_account else False,
                "portador_id": target_portador.id if target_portador else False,
                "reason_id": out_reason.id,
                "origin_module": "custom_treasury_cash",
                "origin_model": "treasury.cash.accountability",
            }
        )
        self._movement_service.post_movement(out_move)
        self._movement_service.post_movement(in_move)
        return out_move, in_move
