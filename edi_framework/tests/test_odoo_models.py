if __name__.startswith("odoo.addons."):
    import json

    from odoo.addons.queue_job.tests.common import trap_jobs
    from odoo.tests.common import TransactionCase

    class TestEdiFrameworkModels(TransactionCase):
        def _create_exchange_fixture(self):
            backend = self.env["edi.backend"].create(
                {
                    "name": "Backend E2E",
                    "code": "E2E",
                    "company_id": self.env.company.id,
                }
            )
            exchange_type = self.env["edi.exchange.type"].create(
                {
                    "name": "Exportação API",
                    "code": "api_out",
                    "category": "api",
                    "direction": "out",
                }
            )
            self.env["edi.exchange.state"].create(
                {
                    "exchange_type_id": exchange_type.id,
                    "name": "Sucesso",
                    "code": "success",
                    "sequence": 20,
                    "state_kind": "success",
                    "is_final": True,
                }
            )
            layout = self.env["edi.layout"].create(
                {
                    "name": "Layout E2E",
                    "code": "LAYOUT_E2E",
                    "backend_id": backend.id,
                    "format_type": "json",
                    "direction": "out",
                }
            )
            source = self.env["edi.data.source"].create(
                {
                    "name": "Fonte Array",
                    "code": "ARRAY_1",
                    "company_id": self.env.company.id,
                    "source_type": "array",
                    "params_json": json.dumps(
                        {
                            "rows": [
                                {"document_number": "42", "amount": "15.75"},
                                {"document_number": "7", "amount": "3.50"},
                            ]
                        }
                    ),
                }
            )
            self.env["edi.layout.source"].create(
                {
                    "layout_id": layout.id,
                    "source_id": source.id,
                    "alias": "docs",
                }
            )
            record = self.env["edi.layout.record"].create(
                {
                    "layout_id": layout.id,
                    "name": "Detalhe",
                    "code": "DET",
                    "record_type": "detail",
                }
            )
            field_doc = self.env["edi.layout.field"].create(
                {
                    "record_id": record.id,
                    "name": "Documento",
                    "code": "document_number",
                    "technical_name": "document_number",
                    "target_path": "doc_number",
                    "field_type": "char",
                }
            )
            field_amount = self.env["edi.layout.field"].create(
                {
                    "record_id": record.id,
                    "name": "Valor",
                    "code": "amount",
                    "technical_name": "amount",
                    "target_path": "amount_cents",
                    "field_type": "float",
                }
            )
            rule_zfill = self.env.ref("edi_framework.edi_transform_rule_zfill")
            rule_multiply = self.env.ref("edi_framework.edi_transform_rule_multiply")
            extract_doc = self.env["edi.extract.map"].create(
                {
                    "layout_id": layout.id,
                    "record_id": record.id,
                    "field_id": field_doc.id,
                    "source_alias": "docs",
                    "source_path": "document_number",
                }
            )
            self.env["edi.map.rule.line"].create(
                {
                    "extract_map_id": extract_doc.id,
                    "transform_rule_id": rule_zfill.id,
                    "params_json": json.dumps({"width": 6}),
                }
            )
            extract_amount = self.env["edi.extract.map"].create(
                {
                    "layout_id": layout.id,
                    "record_id": record.id,
                    "field_id": field_amount.id,
                    "source_alias": "docs",
                    "source_path": "amount",
                }
            )
            self.env["edi.map.rule.line"].create(
                {
                    "extract_map_id": extract_amount.id,
                    "transform_rule_id": rule_multiply.id,
                    "params_json": json.dumps({"factor": "100"}),
                }
            )
            transaction = self.env["edi.transaction"].create(
                {
                    "name": "Transação E2E",
                    "transaction_type": "api_out",
                    "backend_id": backend.id,
                    "exchange_type_id": exchange_type.id,
                    "res_model": "res.partner",
                    "res_id": self.env.ref("base.partner_admin").id,
                    "company_id": self.env.company.id,
                }
            )
            exchange = self.env["edi.exchange"].create(
                {
                    "name": "Exchange E2E",
                    "backend_id": backend.id,
                    "layout_id": layout.id,
                    "exchange_type_id": exchange_type.id,
                    "direction": "out",
                    "transaction_id": transaction.id,
                    "res_model": "res.partner",
                    "res_id": self.env.ref("base.partner_admin").id,
                    "company_id": self.env.company.id,
                }
            )
            return exchange, transaction

        def test_backend_creation_and_unique_constraints_metadata(self):
            backend = self.env["edi.backend"].create(
                {
                    "name": "Backend Fiscal",
                    "code": "FISCAL",
                    "company_id": self.env.company.id,
                }
            )
            self.assertEqual(backend.queue_channel, "root.edi")

        def test_transform_rule_to_pipeline_spec(self):
            rule = self.env.ref("edi_framework.edi_transform_rule_zfill")
            line = self.env["edi.map.rule.line"].new(
                {
                    "transform_rule_id": rule.id,
                    "params_json": '{"width": 8}',
                }
            )
            self.assertEqual(line.to_transform_spec()["width"], 8)

        def test_source_service_executes_python_and_api_providers(self):
            python_source = self.env["edi.data.source"].create(
                {
                    "name": "Fonte Python",
                    "code": "PY_1",
                    "company_id": self.env.company.id,
                    "source_type": "python",
                    "python_code": "result = [{'number': context['exchange_id']}]",
                }
            )
            api_source = self.env["edi.data.source"].create(
                {
                    "name": "Fonte API",
                    "code": "API_1",
                    "company_id": self.env.company.id,
                    "source_type": "api",
                    "params_json": json.dumps({"response_rows": [{"status": "ok"}]}),
                }
            )

            self.assertEqual(
                python_source.execute_source({"exchange_id": 99}),
                [{"number": 99}],
            )
            self.assertEqual(
                api_source.execute_source(),
                [{"status": "ok"}],
            )

        def test_backend_adapter_and_target_providers(self):
            backend = self.env["edi.backend"].create(
                {
                    "name": "Backend API",
                    "code": "BACK_API",
                    "company_id": self.env.company.id,
                    "backend_type": "api",
                    "config_json": json.dumps({"base_url": "https://edi.example.test", "token": "abc"}),
                }
            )
            api_target = self.env["edi.data.target"].create(
                {
                    "name": "Destino API",
                    "code": "TARGET_API",
                    "company_id": self.env.company.id,
                    "target_type": "api",
                    "params_json": json.dumps({"endpoint": "/v1/documents", "method": "POST"}),
                }
            )
            python_target = self.env["edi.data.target"].create(
                {
                    "name": "Destino Python",
                    "code": "TARGET_PY",
                    "company_id": self.env.company.id,
                    "target_type": "python",
                    "python_code": "result = {'status': 'accepted', 'count': len(payload)}",
                }
            )

            from odoo.addons.edi_framework.services import BackendService, TargetService

            backend_settings = BackendService(self.env).get_connection_settings(backend)
            api_result = TargetService(self.env).execute(api_target, [{"id": 1}], context_data={"backend_settings": backend_settings})
            python_result = TargetService(self.env).execute(python_target, [{"id": 1}, {"id": 2}])

            self.assertEqual(backend_settings["base_url"], "https://edi.example.test")
            self.assertEqual(api_result["endpoint"], "/v1/documents")
            self.assertEqual(api_result["payload_count"], 1)
            self.assertEqual(python_result["count"], 2)

        def test_generic_transaction_service_creates_transaction_and_exchange(self):
            exchange, _transaction = self._create_exchange_fixture()

            service = self.env["edi.transaction.service"]
            created = service.start_transaction(
                res_model="res.partner",
                res_id=self.env.ref("base.partner_admin").id,
                backend_code=exchange.backend_id.code,
                exchange_type_code=exchange.exchange_type_id.code,
                layout_code=exchange.layout_id.code,
                name="NF-e 123",
                external_ref="INV-123",
                enqueue=False,
            )

            self.assertEqual(created.transaction_type, exchange.exchange_type_id.code)
            self.assertEqual(created.res_model, "res.partner")
            self.assertEqual(created.external_ref, "INV-123")
            self.assertEqual(len(created.exchange_ids), 1)
            self.assertEqual(created.current_exchange_id, created.exchange_ids[:1])
            self.assertEqual(created.current_exchange_id.layout_id, exchange.layout_id)
            self.assertEqual(created.current_exchange_id.backend_id, exchange.backend_id)
            self.assertEqual(created.current_exchange_id.transaction_id, created)

        def test_process_code_creates_transaction_with_single_identifier(self):
            exchange, _transaction = self._create_exchange_fixture()
            process = self.env["edi.process"].create(
                {
                    "name": "NF-e Saida",
                    "code": "nfe_saida",
                    "company_id": self.env.company.id,
                    "backend_id": exchange.backend_id.id,
                    "exchange_type_id": exchange.exchange_type_id.id,
                    "layout_id": exchange.layout_id.id,
                    "direction": "out",
                    "model_name": "res.partner",
                    "auto_enqueue": False,
                }
            )

            created = self.env["edi.transaction.service"].start_transaction(
                process_code=process.code,
                res_model="res.partner",
                res_id=self.env.ref("base.partner_admin").id,
                external_ref="PARTNER-EDI-1",
            )

            self.assertEqual(created.transaction_type, process.code)
            self.assertEqual(created.backend_id, process.backend_id)
            self.assertEqual(created.exchange_type_id, process.exchange_type_id)
            self.assertEqual(created.current_exchange_id.layout_id, process.layout_id)
            self.assertEqual(created.current_exchange_id.direction, "out")

        def test_process_code_accepts_external_json_payload(self):
            backend = self.env["edi.backend"].create(
                {
                    "name": "Backend Payload",
                    "code": "PAYLOAD",
                    "company_id": self.env.company.id,
                }
            )
            exchange_type = self.env["edi.exchange.type"].create(
                {
                    "name": "Importacao JSON",
                    "code": "json_import",
                    "category": "manual",
                    "direction": "in",
                }
            )
            self.env["edi.exchange.state"].create(
                {
                    "exchange_type_id": exchange_type.id,
                    "name": "Sucesso",
                    "code": "success",
                    "sequence": 20,
                    "state_kind": "success",
                    "is_final": True,
                }
            )
            layout = self.env["edi.layout"].create(
                {
                    "name": "Layout JSON",
                    "code": "LAYOUT_JSON",
                    "backend_id": backend.id,
                    "format_type": "json",
                    "direction": "in",
                }
            )
            source = self.env["edi.data.source"].create(
                {
                    "name": "Fonte JSON Externa",
                    "code": "JSON_EXT",
                    "company_id": self.env.company.id,
                    "source_type": "json",
                }
            )
            self.env["edi.layout.source"].create(
                {
                    "layout_id": layout.id,
                    "source_id": source.id,
                    "alias": "docs",
                }
            )
            record = self.env["edi.layout.record"].create(
                {
                    "layout_id": layout.id,
                    "name": "Detalhe",
                    "code": "DET_JSON",
                    "record_type": "detail",
                }
            )
            field_doc = self.env["edi.layout.field"].create(
                {
                    "record_id": record.id,
                    "name": "Documento",
                    "code": "document_number",
                    "technical_name": "document_number",
                    "target_path": "doc_number",
                    "field_type": "char",
                }
            )
            self.env["edi.extract.map"].create(
                {
                    "layout_id": layout.id,
                    "record_id": record.id,
                    "field_id": field_doc.id,
                    "source_alias": "docs",
                    "source_path": "document_number",
                }
            )
            process = self.env["edi.process"].create(
                {
                    "name": "JSON Entrada",
                    "code": "json_entrada",
                    "company_id": self.env.company.id,
                    "backend_id": backend.id,
                    "exchange_type_id": exchange_type.id,
                    "layout_id": layout.id,
                    "direction": "in",
                    "auto_enqueue": False,
                }
            )

            created = self.env["edi.transaction.service"].start_transaction(
                process_code=process.code,
                payload=[{"document_number": "EXT-1"}],
                payload_format="json",
                payload_name="entrada.json",
                payload_metadata={"source": "api"},
            )
            created.current_exchange_id._job_process_exchange()
            created.invalidate_recordset()

            self.assertEqual(created.res_model, "edi.payload")
            self.assertEqual(created.current_exchange_id.input_payload_format, "json")
            self.assertEqual(created.current_exchange_id.input_filename, "entrada.json")
            self.assertIn('"doc_number": "EXT-1"', created.current_exchange_id.payload_ids.filtered(lambda p: p.payload_type == "normalized").content_text)

        def test_e2e_exchange_processes_array_source_and_updates_transaction(self):
            exchange, transaction = self._create_exchange_fixture()
            exchange._job_process_exchange()
            exchange.invalidate_recordset()
            transaction.invalidate_recordset()

            self.assertEqual(exchange.state_kind, "success")
            self.assertFalse(exchange.has_error)
            self.assertEqual(len(exchange.source_snapshot_ids), 1)
            normalized_payloads = exchange.payload_ids.filtered(lambda p: p.payload_type == "normalized")
            self.assertEqual(len(normalized_payloads), 1)
            self.assertIn('"doc_number": "000042"', normalized_payloads.content_text)
            self.assertIn('"amount_cents": "1575.00"', normalized_payloads.content_text)
            self.assertEqual(transaction.current_exchange_id, exchange)
            self.assertEqual(transaction.technical_state, "success")
            self.assertEqual(transaction.business_state, "success")
            self.assertFalse(transaction.has_error)
            self.assertTrue(transaction.event_ids)
            self.assertTrue(transaction.log_ids)

        def test_e2e_exchange_applies_api_target_via_return_map(self):
            exchange, transaction = self._create_exchange_fixture()
            target = self.env["edi.data.target"].create(
                {
                    "name": "Destino API E2E",
                    "code": "API_E2E",
                    "company_id": self.env.company.id,
                    "target_type": "api",
                    "params_json": json.dumps({"endpoint": "/v1/e2e", "method": "POST"}),
                }
            )
            record = exchange.layout_id.record_ids[:1]
            field_doc = record.field_ids.filtered(lambda f: f.code == "document_number")[:1]
            self.env["edi.return.map"].create(
                {
                    "layout_id": exchange.layout_id.id,
                    "record_id": record.id,
                    "field_id": field_doc.id,
                    "target_id": target.id,
                    "target_alias": "api_main",
                    "target_path": "doc_number",
                }
            )

            exchange._job_process_exchange()
            exchange.invalidate_recordset()
            transaction.invalidate_recordset()

            response_payloads = exchange.payload_ids.filtered(lambda p: p.payload_type == "response")
            self.assertEqual(exchange.state_kind, "success")
            self.assertEqual(len(response_payloads), 1)
            self.assertIn('"target_code": "API_E2E"', response_payloads.content_text)
            self.assertEqual(exchange.api_detail_id[:1].url, "/v1/e2e")
            self.assertEqual(transaction.technical_state, "success")

        def test_demo_reset_clears_artifacts_and_returns_to_draft(self):
            exchange = self.env.ref("edi_framework.edi_exchange_demo")
            transaction = exchange.transaction_id

            exchange.action_run_demo_now()
            exchange.invalidate_recordset()
            transaction.invalidate_recordset()

            self.assertTrue(exchange.payload_ids)
            self.assertTrue(exchange.source_snapshot_ids)
            self.assertEqual(exchange.state_kind, "success")

            exchange.action_reset_demo_state()
            exchange.invalidate_recordset()
            transaction.invalidate_recordset()

            self.assertFalse(exchange.payload_ids)
            self.assertFalse(exchange.source_snapshot_ids)
            self.assertFalse(exchange.api_detail_id)
            self.assertEqual(exchange.state_code, "draft")
            self.assertEqual(exchange.state_kind, "draft")
            self.assertFalse(exchange.has_error)
            self.assertEqual(exchange.job_attempt_count, 0)
            self.assertEqual(transaction.technical_state, "draft")
            self.assertFalse(transaction.event_ids)
            self.assertFalse(transaction.log_ids)

        def test_e2e_exchange_enqueues_queue_job_and_executes_it(self):
            exchange, transaction = self._create_exchange_fixture()

            with trap_jobs() as trap:
                exchange.action_enqueue_process()

                trap.assert_jobs_count(1, only=exchange._job_process_exchange)
                trap.assert_enqueued_job(
                    exchange._job_process_exchange,
                    properties={
                        "channel": "root.edi",
                        "description": f"Processar exchange EDI {exchange.display_name}",
                        "identity_key": f"edi.exchange.process:{exchange.id}",
                    },
                )

                exchange.invalidate_recordset()
                self.assertEqual(exchange.job_channel, "root.edi")
                self.assertEqual(exchange.job_identity_key, f"edi.exchange.process:{exchange.id}")
                self.assertTrue(exchange.job_uuid)

                trap.perform_enqueued_jobs()

            exchange.invalidate_recordset()
            transaction.invalidate_recordset()

            normalized_payloads = exchange.payload_ids.filtered(lambda p: p.payload_type == "normalized")
            self.assertEqual(exchange.state_kind, "success")
            self.assertFalse(exchange.has_error)
            self.assertEqual(len(normalized_payloads), 1)
            self.assertEqual(transaction.current_exchange_id, exchange)
            self.assertEqual(transaction.technical_state, "success")
