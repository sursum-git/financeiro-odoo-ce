from odoo import fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryReconciliationService(models.AbstractModel):
    _name = "treasury.reconciliation.service"
    _description = "Treasury Reconciliation Service"

    MSG_LINHA_JA_CONCILIADA = "A linha do extrato ja esta conciliada."
    MSG_MOVIMENTO_JA_CONCILIADO = "O movimento ja esta conciliado."
    MSG_CONCILIACAO_OBRIGATORIA = "E obrigatorio informar uma conciliacao para vincular as linhas."
    MSG_DIFERENCA_POSITIVA = "O ajuste exige uma diferenca remanescente positiva."
    MSG_PENDENCIAS_FINALIZACAO = (
        "As linhas pendentes da conciliacao devem ser resolvidas antes da finalizacao."
    )
    MSG_VINCULO_AUTOMATICO = "Vinculado pelo servico de conciliacao."
    MSG_AJUSTE_CRIADO = "Ajuste criado durante a conciliacao."
    MSG_MOEDA_DIVERGENTE = "Extrato e movimento precisam usar a mesma moeda na conciliacao."

    @property
    def _movement_service(self):
        return self.env["treasury.movement.service"]

    def suggest_matches(self, reconciliation):
        reconciliation.ensure_one()
        domain = [
            ("import_id.bank_account_id", "=", reconciliation.bank_account_id.id),
            ("date", ">=", reconciliation.date_start),
            ("date", "<=", reconciliation.date_end),
        ]
        statement_lines = self.env["treasury.bank.statement.line"].search(domain)
        matches = []
        for statement_line in statement_lines.filtered(lambda line: not line.is_reconciled):
            movement = self.env["treasury.movement"].search(
                [
                    ("company_id", "=", reconciliation.company_id.id),
                    ("state", "=", "posted"),
                    ("is_reconciled", "=", False),
                    ("account_id", "=", reconciliation.bank_account_id.treasury_account_id.id),
                    ("currency_id", "=", statement_line.currency_id.id),
                    ("date", "=", statement_line.date),
                ],
                limit=1,
            )
            if movement and abs(abs(movement.signed_amount) - statement_line.amount) < 0.00001:
                matches.append((statement_line, movement))
        return matches

    def match_line(self, statement_line, movement, reconciliation=None):
        if statement_line.is_reconciled:
            raise ValidationError(self.MSG_LINHA_JA_CONCILIADA)
        if movement.is_reconciled:
            raise ValidationError(self.MSG_MOVIMENTO_JA_CONCILIADO)
        if statement_line.currency_id != movement.currency_id:
            raise ValidationError(self.MSG_MOEDA_DIVERGENTE)
        line_vals = {
            "statement_line_id": statement_line.id,
            "movement_id": movement.id,
            "status": "matched",
            "notes": self.MSG_VINCULO_AUTOMATICO,
        }
        if reconciliation:
            line_vals["reconciliation_id"] = reconciliation.id
        else:
            raise ValidationError(self.MSG_CONCILIACAO_OBRIGATORIA)
        line = self.env["treasury.reconciliation.line"].create(line_vals)
        statement_line.write({"is_reconciled": True, "movement_id": movement.id})
        movement.with_context(skip_post_lock=True).write({"is_reconciled": True})
        return line

    def create_adjustment(self, reconciliation, statement_line, movement=None, notes=None):
        reconciliation.ensure_one()
        if statement_line.is_reconciled:
            raise ValidationError(self.MSG_LINHA_JA_CONCILIADA)
        if movement and statement_line.currency_id != movement.currency_id:
            raise ValidationError(self.MSG_MOEDA_DIVERGENTE)
        difference = statement_line.amount - (abs(movement.signed_amount) if movement else 0.0)
        if difference <= 0:
            raise ValidationError(self.MSG_DIFERENCA_POSITIVA)
        reason = self.env["financial.movement.reason"].search(
            [("company_id", "=", reconciliation.company_id.id), ("type", "=", "ajuste")],
            limit=1,
        )
        if not reason:
            reason = self.env["financial.movement.reason"].create(
                {
                    "name": "Ajuste Conciliacao",
                    "code": "AJ_CONC",
                    "type": "ajuste",
                    "company_id": reconciliation.company_id.id,
                }
            )
        adjustment = self._movement_service.create_movement(
            {
                "name": f"Ajuste {statement_line.description or statement_line.document_number or statement_line.id}",
                "date": statement_line.date,
                "company_id": reconciliation.company_id.id,
                "type": "ajuste",
                "amount": difference,
                "currency_id": statement_line.currency_id.id,
                "account_id": reconciliation.bank_account_id.treasury_account_id.id,
                "reason_id": reason.id,
                "origin_module": "custom_treasury_reconciliation",
                "origin_model": "treasury.reconciliation",
                "origin_record_id": reconciliation.id,
            }
        )
        self._movement_service.post_movement(adjustment)
        line = self.env["treasury.reconciliation.line"].create(
            {
                "reconciliation_id": reconciliation.id,
                "statement_line_id": statement_line.id,
                "movement_id": movement.id if movement else False,
                "status": "adjusted",
                "notes": notes or self.MSG_AJUSTE_CRIADO,
                "adjustment_movement_id": adjustment.id,
            }
        )
        statement_line.write({"is_reconciled": True, "movement_id": adjustment.id})
        adjustment.with_context(skip_post_lock=True).write({"is_reconciled": True})
        return line

    def finalize_reconciliation(self, reconciliation):
        reconciliation.ensure_one()
        if any(line.status == "pending" for line in reconciliation.line_ids):
            raise UserError(self.MSG_PENDENCIAS_FINALIZACAO)
        reconciliation.state = "done"
        return reconciliation
