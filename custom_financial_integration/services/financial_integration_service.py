from odoo import fields, models
from odoo.exceptions import ValidationError


class FinancialIntegrationService(models.AbstractModel):
    _name = "financial.integration.service"
    _description = "Financial Integration Service"

    MSG_RECEBER_EXIGE_DESTINO = (
        "A liquidacao do contas a receber exige conta de destino ou portador para integracao."
    )
    MSG_PAGAR_EXIGE_ORIGEM = (
        "O pagamento do contas a pagar exige conta de origem ou portador para integracao."
    )
    MSG_EVENTO_INTEGRACAO_NAO_ENCONTRADO = (
        "Nao foi encontrado evento de integracao concluido para o registro de origem."
    )
    MSG_LOG_ENTRADA_CRIADA = "Lancamento de entrada na tesouraria criado a partir da liquidacao."
    MSG_LOG_SAIDA_CRIADA = "Lancamento de saida na tesouraria criado a partir do pagamento."
    MSG_LOG_ESTORNO = "Movimento de tesouraria estornado com id %(movement_id)s."

    @property
    def _movement_service(self):
        return self.env["treasury.movement.service"]

    def _get_or_create_event(
        self,
        event_type,
        source_module,
        source_model,
        source_record_id,
        company,
        name,
        notes=None,
    ):
        event = self.env["financial.integration.event"].search(
            [
                ("event_type", "=", event_type),
                ("source_model", "=", source_model),
                ("source_record_id", "=", source_record_id),
            ],
            limit=1,
        )
        if event:
            return event
        return self.env["financial.integration.event"].create(
            {
                "name": name,
                "company_id": company.id,
                "event_type": event_type,
                "source_module": source_module,
                "source_model": source_model,
                "source_record_id": source_record_id,
                "notes": notes,
            }
        )

    def log_event(self, event, level, message):
        return self.env["financial.integration.log"].create(
            {
                "event_id": event.id,
                "level": level,
                "message": message,
            }
        )

    def create_treasury_entry_from_receivable_settlement(self, settlement):
        settlement.ensure_one()
        event = self._get_or_create_event(
            "receivable_settlement",
            "custom_account_receivable",
            "receivable.settlement",
            settlement.id,
            settlement.company_id,
            settlement.name,
        )
        if event.treasury_movement_id:
            return event.treasury_movement_id
        try:
            if not settlement.target_account_id and not settlement.portador_id:
                raise ValidationError(self.MSG_RECEBER_EXIGE_DESTINO)
            amount = settlement.net_amount_total or sum(settlement.line_ids.mapped("total_amount"))
            movement = self._movement_service.create_movement(
                {
                    "name": settlement.name,
                    "date": settlement.date,
                    "company_id": settlement.company_id.id,
                    "type": "entrada",
                    "amount": amount,
                    "currency_id": settlement.currency_id.id,
                    "account_id": settlement.target_account_id.id,
                    "portador_id": settlement.portador_id.id,
                    "payment_method_id": settlement.payment_method_id.id,
                    "origin_module": "custom_account_receivable",
                    "origin_model": "receivable.settlement",
                    "origin_record_id": settlement.id,
                }
            )
            self._movement_service.post_movement(movement)
            event.write({"treasury_movement_id": movement.id, "state": "done"})
            self.log_event(event, "info", self.MSG_LOG_ENTRADA_CRIADA)
            return movement
        except Exception as exc:
            event.write({"state": "failed"})
            self.log_event(event, "error", str(exc))
            raise

    def create_treasury_exit_from_payable_payment(self, payment):
        payment.ensure_one()
        event = self._get_or_create_event(
            "payable_payment",
            "custom_account_payable",
            "payable.payment",
            payment.id,
            payment.company_id,
            payment.name,
        )
        if event.treasury_movement_id:
            return event.treasury_movement_id
        try:
            if not payment.source_account_id and not payment.source_portador_id:
                raise ValidationError(self.MSG_PAGAR_EXIGE_ORIGEM)
            amount = payment.net_amount_total or sum(payment.line_ids.mapped("total_amount"))
            movement = self._movement_service.create_movement(
                {
                    "name": payment.name,
                    "date": payment.date,
                    "company_id": payment.company_id.id,
                    "type": "saida",
                    "amount": amount,
                    "currency_id": payment.currency_id.id,
                    "account_id": payment.source_account_id.id,
                    "portador_id": payment.source_portador_id.id,
                    "payment_method_id": payment.payment_method_id.id,
                    "origin_module": "custom_account_payable",
                    "origin_model": "payable.payment",
                    "origin_record_id": payment.id,
                }
            )
            self._movement_service.post_movement(movement)
            event.write({"treasury_movement_id": movement.id, "state": "done"})
            self.log_event(event, "info", self.MSG_LOG_SAIDA_CRIADA)
            return movement
        except Exception as exc:
            event.write({"state": "failed"})
            self.log_event(event, "error", str(exc))
            raise

    def reverse_treasury_movement_from_source(self, source_model, source_record_id):
        event = self.env["financial.integration.event"].search(
            [
                ("source_model", "=", source_model),
                ("source_record_id", "=", source_record_id),
                ("state", "=", "done"),
            ],
            limit=1,
        )
        if not event or not event.treasury_movement_id:
            raise ValidationError(self.MSG_EVENTO_INTEGRACAO_NAO_ENCONTRADO)
        reverse_move = self._movement_service.reverse_movement(event.treasury_movement_id)
        self.log_event(event, "info", self.MSG_LOG_ESTORNO % {"movement_id": reverse_move.id})
        return reverse_move
