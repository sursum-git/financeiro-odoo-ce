from odoo.exceptions import ValidationError
import json


class TransactionService:
    def __init__(self, env):
        self.env = env

    def _resolve_process(self, process=None, process_code=None, company=None):
        if process:
            return process
        if process_code:
            domain = [("code", "=", process_code)]
            if company:
                domain = ["&", ("code", "=", process_code), "|", ("company_id", "=", company.id), ("company_id", "=", False)]
            found = self.env["edi.process"].search(domain, limit=1)
            if found:
                return found
        return self.env["edi.process"]

    def _resolve_backend(self, backend=None, backend_code=None):
        if backend:
            return backend
        if backend_code:
            found = self.env["edi.backend"].search([("code", "=", backend_code)], limit=1)
            if found:
                return found
        return self.env["edi.backend"]

    def _resolve_exchange_type(self, exchange_type=None, exchange_type_code=None, backend=None):
        if exchange_type:
            return exchange_type
        if exchange_type_code:
            found = self.env["edi.exchange.type"].search([("code", "=", exchange_type_code)], limit=1)
            if found:
                return found
        if backend and backend.default_exchange_type_id:
            return backend.default_exchange_type_id
        return self.env["edi.exchange.type"]

    def _resolve_layout(self, layout=None, layout_code=None, backend=None):
        if layout:
            return layout
        if layout_code:
            found = self.env["edi.layout"].search([("code", "=", layout_code)], limit=1)
            if found:
                return found
        if backend and backend.default_layout_id:
            return backend.default_layout_id
        return self.env["edi.layout"]

    def start_transaction(
        self,
        *,
        record=None,
        res_model=None,
        res_id=None,
        company=None,
        name=None,
        transaction_type=None,
        external_ref=None,
        process=None,
        process_code=None,
        backend=None,
        backend_code=None,
        exchange_type=None,
        exchange_type_code=None,
        layout=None,
        layout_code=None,
        direction=None,
        payload=None,
        payload_format=None,
        payload_name=None,
        payload_metadata=None,
        enqueue=True,
    ):
        if record:
            res_model = record._name
            res_id = record.id
            company = company or getattr(record, "company_id", False)
            if not name:
                name = getattr(record, "display_name", False) or getattr(record, "name", False)

        if not payload and (not res_model or not res_id):
            raise ValidationError(
                "Informe `record`, `res_model` + `res_id` ou um `payload` para iniciar a transação EDI."
            )

        process = self._resolve_process(process=process, process_code=process_code, company=company or self.env.company)
        if process and process.model_name and process.model_name != res_model:
            raise ValidationError(
                f"O processo EDI {process.display_name} só pode ser usado com o modelo {process.model_name}."
            )

        if process:
            backend = backend or process.backend_id
            exchange_type = exchange_type or process.exchange_type_id
            layout = layout or process.layout_id
            direction = direction or process.direction
            enqueue = process.auto_enqueue if enqueue is True else enqueue
            transaction_type = transaction_type or process.code

        backend = self._resolve_backend(backend=backend, backend_code=backend_code)
        if not backend:
            raise ValidationError("Nenhum backend EDI encontrado para iniciar a transação.")

        exchange_type = self._resolve_exchange_type(
            exchange_type=exchange_type,
            exchange_type_code=exchange_type_code,
            backend=backend,
        )
        if not exchange_type:
            raise ValidationError("Nenhum tipo de exchange EDI encontrado para iniciar a transação.")

        layout = self._resolve_layout(layout=layout, layout_code=layout_code, backend=backend)
        if not layout:
            raise ValidationError("Nenhum layout EDI encontrado para iniciar a transação.")

        company = company or backend.company_id or self.env.company
        direction = direction or exchange_type.direction or layout.direction
        transaction_type = transaction_type or exchange_type.code or "edi"
        if res_model and res_id:
            default_name = f"{res_model},{res_id}"
        else:
            default_name = payload_name or process_code or transaction_type
        name = name or default_name
        payload_text = False
        if payload is not None:
            if isinstance(payload, str):
                payload_text = payload
            else:
                payload_text = json.dumps(payload, ensure_ascii=False)
        payload_metadata_json = json.dumps(payload_metadata, ensure_ascii=False) if payload_metadata else False

        transaction = self.env["edi.transaction"].create(
            {
                "name": name,
                "transaction_type": transaction_type,
                "backend_id": backend.id,
                "exchange_type_id": exchange_type.id,
                "res_model": res_model or "edi.payload",
                "res_id": res_id or 0,
                "company_id": company.id,
                "external_ref": external_ref,
                "current_status_message": "Transação EDI criada.",
            }
        )

        exchange = self.env["edi.exchange"].create(
            {
                "name": name,
                "backend_id": backend.id,
                "layout_id": layout.id,
                "exchange_type_id": exchange_type.id,
                "direction": direction,
                "transaction_id": transaction.id,
                "res_model": res_model or "edi.payload",
                "res_id": res_id or 0,
                "company_id": company.id,
                "external_ref": external_ref,
                "input_payload_text": payload_text,
                "input_payload_format": payload_format,
                "input_filename": payload_name,
                "input_metadata_json": payload_metadata_json,
                "summary_message": "Exchange EDI criada.",
            }
        )

        transaction.write({"current_exchange_id": exchange.id})

        if enqueue:
            exchange.action_enqueue_process()

        return transaction
