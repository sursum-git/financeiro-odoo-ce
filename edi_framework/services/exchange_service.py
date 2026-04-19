import json

from odoo import fields

from .backend_service import BackendService
from .source_service import SourceService
from .target_service import TargetService


class ExchangeService:
    def __init__(self, env):
        self.env = env

    def collect_source_results(self, exchange):
        if not exchange.layout_id:
            return {}
        source_service = SourceService(self.env)
        source_results = {}
        payload_data = False
        payload_metadata = {}
        if exchange.input_payload_text:
            payload_format = (exchange.input_payload_format or "").lower()
            if payload_format in {"json", "array", "api"}:
                payload_data = json.loads(exchange.input_payload_text)
            else:
                payload_data = exchange.input_payload_text
        if exchange.input_metadata_json:
            payload_metadata = json.loads(exchange.input_metadata_json)
        for layout_source in exchange.layout_id.source_ids.sorted("sequence"):
            rows = source_service.execute(
                layout_source.source_id,
                {
                    "exchange_id": exchange.id,
                    "res_model": exchange.res_model,
                    "res_id": exchange.res_id,
                    "input_payload": payload_data,
                    "input_payload_format": exchange.input_payload_format,
                    "input_filename": exchange.input_filename,
                    "input_metadata": payload_metadata,
                },
            )
            source_results[layout_source.alias] = rows
        return source_results

    def run_layout_pipeline(self, exchange, source_results):
        if not exchange.layout_id:
            return []
        result_rows = []
        extract_maps = self.env["edi.extract.map"].search(
            [("layout_id", "=", exchange.layout_id.id)],
            order="sequence, id",
        )
        if not extract_maps:
            return []
        groups = {}
        default_alias = exchange.layout_id.source_ids[:1].alias if exchange.layout_id.source_ids else None
        for mapping in extract_maps:
            alias = mapping.source_alias or default_alias
            groups.setdefault(alias, self.env["edi.extract.map"])
            groups[alias] |= mapping
        for alias, mappings in groups.items():
            dataset = source_results.get(alias or "", [])
            if not dataset:
                continue
            transformed = mappings.apply_pipeline(dataset)
            for row in transformed:
                row["_source_alias"] = alias
            result_rows.extend(transformed)
        return result_rows

    def apply_targets(self, exchange, normalized_rows):
        target_service = TargetService(self.env)
        backend_settings = BackendService(self.env).get_connection_settings(
            exchange.backend_id,
            context_data={"exchange_id": exchange.id},
        )
        results = []
        return_maps = self.env["edi.return.map"].search(
            [("layout_id", "=", exchange.layout_id.id)],
            order="sequence, id",
        )
        target_ids = return_maps.mapped("target_id")
        for target in target_ids:
            result = target_service.execute(
                target,
                normalized_rows,
                context_data={
                    "exchange_id": exchange.id,
                    "backend_settings": backend_settings,
                },
            )
            result["target_code"] = target.code
            results.append(result)
        return results

    def store_source_snapshots(self, exchange, source_results):
        exchange.source_snapshot_ids.unlink()
        for layout_source in exchange.layout_id.source_ids:
            rows = source_results.get(layout_source.alias, [])
            payload = json.dumps(rows, ensure_ascii=False)
            self.env["edi.exchange.source.snapshot"].create(
                {
                    "exchange_id": exchange.id,
                    "source_id": layout_source.source_id.id,
                    "params_json": layout_source.source_id.params_json,
                    "raw_payload": payload,
                    "normalized_payload": payload,
                    "payload_hash": str(hash(payload)),
                }
            )

    def store_normalized_payload(self, exchange, normalized_rows):
        content = json.dumps(normalized_rows, ensure_ascii=False, default=str)
        self.env["edi.exchange.payload"].create(
            {
                "exchange_id": exchange.id,
                "payload_type": "normalized",
                "name": f"{exchange.name or 'exchange'}-normalized.json",
                "content_text": content,
                "hash": str(hash(content)),
            }
        )

    def store_target_results(self, exchange, target_results):
        if not target_results:
            return
        content = json.dumps(target_results, ensure_ascii=False, default=str)
        self.env["edi.exchange.payload"].create(
            {
                "exchange_id": exchange.id,
                "payload_type": "response",
                "name": f"{exchange.name or 'exchange'}-target-result.json",
                "content_text": content,
                "hash": str(hash(content)),
            }
        )
        for result in target_results:
            mode = result.get("mode")
            if mode == "api":
                self.env["edi.exchange.api"].create(
                    {
                        "exchange_id": exchange.id,
                        "url": result.get("endpoint"),
                        "http_method": result.get("method"),
                        "request_body": json.dumps(result.get("payload", []), ensure_ascii=False, default=str),
                        "response_body": content,
                        "remote_status": result.get("status"),
                    }
                )
            if mode == "file":
                payload_text = json.dumps(result.get("payload", []), ensure_ascii=False, default=str)
                self.env["edi.exchange.file"].create(
                    {
                        "exchange_id": exchange.id,
                        "file_name": result.get("file_name"),
                        "file_format": "json",
                        "record_count": result.get("payload_count", 0),
                        "file_size": len(payload_text.encode()),
                        "generated_at": fields.Datetime.now(),
                    }
                )

    def store_error_payload(self, exchange, error_message):
        self.env["edi.exchange.payload"].create(
            {
                "exchange_id": exchange.id,
                "payload_type": "error",
                "name": f"{exchange.name or 'exchange'}-error.txt",
                "content_text": error_message,
                "hash": str(hash(error_message)),
            }
        )

    def set_state_by_kind(self, exchange, state_kind):
        state = self.env["edi.exchange.state"].search(
            [
                ("exchange_type_id", "=", exchange.exchange_type_id.id),
                ("state_kind", "=", state_kind),
            ],
            order="sequence, id",
            limit=1,
        )
        if state:
            exchange.write(
                {
                    "current_state_id": state.id,
                    "state_code": state.code,
                    "state_kind": state.state_kind,
                }
            )

    def ensure_transaction(self, exchange):
        if exchange.transaction_id:
            return exchange.transaction_id
        values = {
            "name": exchange.name,
            "transaction_type": exchange.exchange_type_id.code or "edi",
            "backend_id": exchange.backend_id.id,
            "exchange_type_id": exchange.exchange_type_id.id,
            "res_model": exchange.res_model or "edi.exchange",
            "res_id": exchange.res_id or exchange.id,
            "current_exchange_id": exchange.id,
            "company_id": exchange.company_id.id,
            "external_ref": exchange.external_ref,
            "started_at": exchange.started_at,
        }
        transaction = self.env["edi.transaction"].create(values)
        exchange.transaction_id = transaction.id
        return transaction

    def sync_transaction(self, exchange, transaction, normalized_rows, has_error=False, error_message=False):
        if not transaction:
            return
        values = {
            "current_exchange_id": exchange.id,
            "technical_state": exchange.state_code,
            "business_state": exchange.state_kind,
            "current_status_message": exchange.summary_message,
            "last_event_at": fields.Datetime.now(),
            "has_error": has_error,
            "error_message": error_message or False,
            "waiting_return": exchange.direction == "in" and not has_error,
        }
        if not has_error:
            values["current_status_message"] = f"{len(normalized_rows)} registro(s) processado(s)."
            values["finished_at"] = fields.Datetime.now()
        transaction.write(values)

    def create_transaction_event(self, exchange, transaction, event_type, message, is_error=False):
        if not transaction:
            return
        self.env["edi.transaction.event"].create(
            {
                "transaction_id": transaction.id,
                "exchange_id": exchange.id,
                "event_type": event_type,
                "event_code": exchange.state_code,
                "technical_state_to": exchange.state_code,
                "business_state_to": exchange.state_kind,
                "message": message,
                "is_error": is_error,
            }
        )

    def create_transaction_log(self, exchange, transaction, key, value, log_type="info", message=False):
        if not transaction:
            return
        self.env["edi.transaction.log"].create(
            {
                "transaction_id": transaction.id,
                "exchange_id": exchange.id,
                "log_type": log_type,
                "key": key,
                "value": value,
                "message": message,
            }
        )

    def process(self, exchange):
        source_results = self.collect_source_results(exchange)
        normalized = self.run_layout_pipeline(exchange, source_results)
        target_results = self.apply_targets(exchange, normalized)
        self.store_source_snapshots(exchange, source_results)
        self.store_normalized_payload(exchange, normalized)
        self.store_target_results(exchange, target_results)
        self.set_state_by_kind(exchange, "success")
        transaction = self.ensure_transaction(exchange)
        self.sync_transaction(exchange, transaction, normalized, has_error=False)
        self.create_transaction_event(
            exchange,
            transaction,
            event_type="exchange_processed",
            message=f"Exchange processada com {len(normalized)} registro(s).",
            is_error=False,
        )
        self.create_transaction_log(
            exchange,
            transaction,
            key="normalized_count",
            value=str(len(normalized)),
            log_type="technical",
            message="Quantidade de registros normalizados.",
        )
        if target_results:
            self.create_transaction_log(
                exchange,
                transaction,
                key="target_result_count",
                value=str(len(target_results)),
                log_type="technical",
                message="Quantidade de resultados de destino.",
            )
        exchange.write(
            {
                "summary_message": f"Exchange processada com {len(normalized)} registro(s).",
                "has_error": False,
                "error_message": False,
            }
        )
        return normalized, target_results
