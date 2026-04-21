if __name__.startswith("odoo.addons."):
    from odoo.exceptions import ValidationError
    from odoo.tests.common import TransactionCase

    class TestFinancialIntegration(TransactionCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.partner = cls.env["res.partner"].create({"name": "Parceiro Integracao"})
            cls.payment_method = cls.env["financial.payment.method"].create(
                {
                    "name": "PIX INT",
                    "code": "PIXINT",
                    "type": "pix",
                    "company_id": cls.env.company.id,
                }
            )
            cls.portador = cls.env["financial.portador"].create(
                {
                    "name": "Portador Integracao",
                    "code": "PINT",
                    "type": "interno",
                    "company_id": cls.env.company.id,
                }
            )
            cls.account = cls.env["treasury.account"].create(
                {
                    "name": "Conta Integracao",
                    "code": "CINT",
                    "type": "other",
                    "company_id": cls.env.company.id,
                }
            )
            cls.withholding_supplier = cls.env["res.partner"].create({"name": "Favorecido Retencao Integracao"})
            cls.withholding_code = cls.env["financial.withholding.code"].create(
                {
                    "name": "Retencao Integracao",
                    "code": "RETINT",
                    "company_id": cls.env.company.id,
                    "minimum_payment_amount": 50.0,
                }
            )
            cls.env["res.partner.withholding.line"].create(
                {
                    "partner_id": cls.partner.id,
                    "company_id": cls.env.company.id,
                    "withholding_code_id": cls.withholding_code.id,
                    "retention_percent": 10.0,
                    "supplier_contact_id": cls.withholding_supplier.id,
                }
            )

        def _create_receivable_settlement(self, with_target=True):
            service = self.env["receivable.service"]
            title = service.open_title(
                {
                    "name": "Titulo Int Receber",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                    "amount_total": 100.0,
                }
            )
            installments = service.generate_installments(
                title,
                [{"due_date": "2026-05-10", "amount": 100.0}],
            )
            vals = {
                "name": "Liquidacao Integrada",
                "partner_id": self.partner.id,
                "company_id": self.env.company.id,
                "payment_method_id": self.payment_method.id,
            }
            if with_target:
                vals.update(
                    {
                        "portador_id": self.portador.id,
                        "target_account_id": self.account.id,
                    }
                )
            settlement = service.create_settlement(
                vals,
                [{"installment_id": installments[0].id, "principal_amount": 100.0}],
            )
            return settlement

        def _create_payable_payment(self, with_source=True):
            service = self.env["payable.service"]
            title = service.open_title(
                {
                    "name": "Titulo Int Pagar",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                    "amount_total": 80.0,
                }
            )
            installments = service.generate_installments(
                title,
                [{"due_date": "2026-05-10", "amount": 80.0}],
            )
            vals = {
                "name": "Pagamento Integrado",
                "partner_id": self.partner.id,
                "company_id": self.env.company.id,
                "payment_method_id": self.payment_method.id,
            }
            if with_source:
                vals.update(
                    {
                        "source_account_id": self.account.id,
                        "source_portador_id": self.portador.id,
                    }
                )
            payment = service.create_payment(
                vals,
                [{"installment_id": installments[0].id, "principal_amount": 80.0}],
            )
            return payment

        def test_receivable_settlement_generates_treasury_entry(self):
            settlement = self._create_receivable_settlement()
            self.env["receivable.service"].apply_settlement(settlement)
            event = self.env["financial.integration.event"].search(
                [("source_model", "=", "receivable.settlement"), ("source_record_id", "=", settlement.id)],
                limit=1,
            )
            self.assertEqual(event.state, "done")
            self.assertEqual(event.treasury_movement_id.type, "entrada")
            self.assertEqual(event.treasury_movement_id.amount, 90.0)

        def test_payable_payment_generates_treasury_exit(self):
            payment = self._create_payable_payment()
            self.env["payable.service"].apply_payment(payment)
            event = self.env["financial.integration.event"].search(
                [("source_model", "=", "payable.payment"), ("source_record_id", "=", payment.id)],
                limit=1,
            )
            self.assertEqual(event.state, "done")
            self.assertEqual(event.treasury_movement_id.type, "saida")
            self.assertEqual(event.treasury_movement_id.amount, 72.0)

        def test_failed_integration_blocks_receivable_apply(self):
            settlement = self._create_receivable_settlement(with_target=False)
            with self.assertRaises(ValidationError):
                self.env["receivable.service"].apply_settlement(settlement)
            self.assertEqual(settlement.state, "draft")

        def test_event_and_log_are_created(self):
            settlement = self._create_receivable_settlement()
            self.env["receivable.service"].apply_settlement(settlement)
            event = self.env["financial.integration.event"].search(
                [("source_model", "=", "receivable.settlement"), ("source_record_id", "=", settlement.id)],
                limit=1,
            )
            self.assertTrue(event.log_ids)
            self.assertEqual(event.log_ids[0].level, "info")

        def test_traceability_between_source_and_movement(self):
            payment = self._create_payable_payment()
            self.env["payable.service"].apply_payment(payment)
            event = self.env["financial.integration.event"].search(
                [("source_model", "=", "payable.payment"), ("source_record_id", "=", payment.id)],
                limit=1,
            )
            movement = event.treasury_movement_id
            self.assertEqual(movement.origin_model, "payable.payment")
            self.assertEqual(movement.origin_record_id, payment.id)
