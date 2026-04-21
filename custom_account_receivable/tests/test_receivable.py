if __name__.startswith("odoo.addons."):
    from odoo.exceptions import ValidationError
    from odoo.tests.common import TransactionCase

    class TestReceivable(TransactionCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.partner = cls.env["res.partner"].create({"name": "Cliente Teste"})
            cls.payment_method = cls.env["financial.payment.method"].create(
                {
                    "name": "PIX",
                    "code": "PIXREC",
                    "type": "pix",
                    "company_id": cls.env.company.id,
                }
            )
            cls.portador = cls.env["financial.portador"].create(
                {
                    "name": "Portador Recebimento",
                    "code": "PRTREC",
                    "type": "interno",
                    "company_id": cls.env.company.id,
                }
            )
            cls.account = cls.env["treasury.account"].create(
                {
                    "name": "Conta Recebimento",
                    "code": "CTAREC",
                    "type": "other",
                    "company_id": cls.env.company.id,
                }
            )
            cls.withholding_supplier = cls.env["res.partner"].create({"name": "Favorecido Retencao Receber"})
            cls.withholding_code = cls.env["financial.withholding.code"].create(
                {
                    "name": "IRRF Receber",
                    "code": "IRRFREC",
                    "company_id": cls.env.company.id,
                    "minimum_payment_amount": 500.0,
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
            cls.check_payment_method = cls.env["financial.payment.method"].create(
                {
                    "name": "Cheque",
                    "code": "CHEQREC",
                    "type": "cheque",
                    "company_id": cls.env.company.id,
                }
            )
            cls.check_return_reason = cls.env["financial.check.return.reason"].create(
                {
                    "code": "11",
                    "name": "Cheque sem fundos",
                    "is_definitive": True,
                }
            )
            cls.currency_xre = cls.env["res.currency"].create(
                {"name": "XRE", "symbol": "XR$", "rounding": 0.01}
            )
            cls.env["res.currency.rate"].create(
                {
                    "name": "2026-05-10",
                    "currency_id": cls.currency_xre.id,
                    "company_id": cls.env.company.id,
                    "rate": 0.2,
                }
            )

        def _create_title_with_installments(self):
            service = self.env["receivable.service"]
            title = service.open_title(
                {
                    "name": "Titulo Cliente 1",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                    "amount_total": 300.0,
                }
            )
            installments = service.generate_installments(
                title,
                [
                    {"due_date": "2026-05-10", "amount": 100.0},
                    {"due_date": "2026-06-10", "amount": 100.0},
                    {"due_date": "2026-07-10", "amount": 100.0},
                ],
            )
            return title, installments

        def _create_single_installment_title(self, name, amount, due_date):
            service = self.env["receivable.service"]
            title = service.open_title(
                {
                    "name": name,
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                    "amount_total": amount,
                }
            )
            installment = service.generate_installments(
                title,
                [{"due_date": due_date, "amount": amount}],
            )
            return title, installment[0]

        def _create_single_installment_title_in_currency(self, name, amount, due_date, currency):
            service = self.env["receivable.service"]
            title = service.open_title(
                {
                    "name": name,
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                    "amount_total": amount,
                    "currency_id": currency.id,
                }
            )
            installment = service.generate_installments(
                title,
                [{"due_date": due_date, "amount": amount}],
            )
            return title, installment[0]

        def _substitute_title_with_third_party_check(self, amount=100.0):
            service = self.env["receivable.service"]
            title, installment = self._create_single_installment_title(
                f"Titulo Cheque {amount}", amount, "2026-05-10"
            )
            settlement = service.create_settlement(
                {
                    "name": "Substituicao por Cheque",
                    "date": "2026-05-10",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                    "settlement_kind": "third_party_check",
                    "payment_method_id": self.check_payment_method.id,
                },
                [{"installment_id": installment.id, "principal_amount": amount}],
            )
            self.env["receivable.settlement.check.line"].create(
                {
                    "settlement_id": settlement.id,
                    "issuer_name": "Cliente do Cliente",
                    "check_number": f"CHK{int(amount)}",
                    "bank_name": "Banco 1",
                    "branch": "0001",
                    "account_number": "12345-6",
                    "expected_clearance_date": "2026-05-20",
                    "amount": amount,
                }
            )
            service.apply_settlement(settlement)
            return title, settlement, settlement.line_ids.title_id.generated_check_title_ids[:1]

        def test_create_receivable_title(self):
            title, _installments = self._create_title_with_installments()
            self.assertEqual(title.partner_id, self.partner)
            self.assertEqual(title.amount_total, 300.0)

        def test_create_installments(self):
            title, installments = self._create_title_with_installments()
            self.assertEqual(len(installments), 3)
            self.assertEqual(sum(installments.mapped("amount")), title.amount_total)

        def test_create_partial_settlement(self):
            _title, installments = self._create_title_with_installments()
            service = self.env["receivable.service"]
            settlement = service.create_settlement(
                {
                    "name": "Liquidacao Parcial",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                    "payment_method_id": self.payment_method.id,
                    "portador_id": self.portador.id,
                    "target_account_id": self.account.id,
                },
                [
                    {
                        "installment_id": installments[0].id,
                        "principal_amount": 40.0,
                    }
                ],
            )
            service.apply_settlement(settlement)
            self.assertEqual(settlement.state, "applied")
            self.assertEqual(installments[0].amount_open, 60.0)
            self.assertEqual(installments[0].state, "partial")

        def test_update_open_amount(self):
            title, installments = self._create_title_with_installments()
            service = self.env["receivable.service"]
            settlement = service.create_settlement(
                {
                    "name": "Liquidacao Parcial 2",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                },
                [
                    {
                        "installment_id": installments[0].id,
                        "principal_amount": 50.0,
                    }
                ],
            )
            service.apply_settlement(settlement)
            self.assertEqual(title.amount_open, 250.0)

        def test_block_over_settlement(self):
            _title, installments = self._create_title_with_installments()
            service = self.env["receivable.service"]
            with self.assertRaises(ValidationError):
                settlement = service.create_settlement(
                    {
                        "name": "Liquidacao Indevida",
                        "partner_id": self.partner.id,
                        "company_id": self.env.company.id,
                    },
                    [
                        {
                            "installment_id": installments[0].id,
                            "principal_amount": 150.0,
                        }
                    ],
                )
                service.apply_settlement(settlement)

        def test_create_renegotiation(self):
            title, installments = self._create_title_with_installments()
            service = self.env["receivable.service"]
            renegotiation = service.renegotiate_titles(
                self.partner,
                title,
                {
                    "name": "Titulo Renegociado",
                    "amount_total": 250.0,
                    "company_id": self.env.company.id,
                },
                [
                    {"due_date": "2026-08-10", "amount": 125.0},
                    {"due_date": "2026-09-10", "amount": 125.0},
                ],
            )
            self.assertEqual(renegotiation.state, "done")
            self.assertEqual(renegotiation.new_title_id.amount_total, 250.0)
            self.assertEqual(title.state, "renegotiated")

        def test_wizard_creates_operational_renegotiation(self):
            title, installments = self._create_title_with_installments()
            service = self.env["receivable.service"]
            settlement = service.create_settlement(
                {
                    "name": "Liquidacao Antes da Renegociacao",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                },
                [{"installment_id": installments[0].id, "principal_amount": 50.0}],
            )
            service.apply_settlement(settlement)
            self.assertEqual(title.amount_open, 250.0)

            action = title.action_open_renegotiation_wizard()
            wizard = self.env[action["res_model"]].with_context(action["context"]).create({})
            wizard.installment_line_ids.unlink()
            self.env["receivable.renegotiation.wizard.line"].create(
                {
                    "wizard_id": wizard.id,
                    "sequence": 1,
                    "due_date": "2026-08-10",
                    "amount": 125.0,
                }
            )
            self.env["receivable.renegotiation.wizard.line"].create(
                {
                    "wizard_id": wizard.id,
                    "sequence": 2,
                    "due_date": "2026-09-10",
                    "amount": 125.0,
                }
            )
            result = wizard.action_confirm()
            renegotiation = self.env["receivable.renegotiation"].browse(result["res_id"])
            self.assertEqual(renegotiation.state, "done")
            self.assertEqual(renegotiation.new_title_id.amount_total, 250.0)
            self.assertEqual(len(renegotiation.new_title_id.installment_ids), 2)
            self.assertEqual(title.state, "renegotiated")

        def test_substitute_receivable_with_third_party_checks(self):
            title, settlement, check_title = self._substitute_title_with_third_party_check(100.0)
            self.assertEqual(settlement.state, "applied")
            self.assertEqual(title.state, "substituted")
            self.assertEqual(check_title.species_kind, "check")
            self.assertEqual(check_title.check_status, "pending")
            self.assertEqual(check_title.amount_open, 100.0)
            self.assertEqual(check_title.source_title_id, title)

        def test_compensate_third_party_check(self):
            _title, _settlement, check_title = self._substitute_title_with_third_party_check(120.0)
            action = check_title.action_open_check_compensation_wizard()
            wizard = self.env[action["res_model"]].with_context(action["context"]).create(
                {
                    "payment_method_id": self.check_payment_method.id,
                    "portador_id": self.portador.id,
                    "target_account_id": self.account.id,
                    "compensation_date": "2026-05-20",
                }
            )
            wizard.action_confirm()
            check_title.invalidate_recordset()
            self.assertEqual(check_title.state, "paid")
            self.assertEqual(check_title.check_status, "compensated")
            self.assertEqual(str(check_title.actual_clearance_date), "2026-05-20")

        def test_definitive_check_return_creates_normal_title(self):
            _title, _settlement, check_title = self._substitute_title_with_third_party_check(130.0)
            action = check_title.action_open_check_return_wizard()
            wizard = self.env[action["res_model"]].with_context(action["context"]).create(
                {
                    "return_reason_id": self.check_return_reason.id,
                    "return_date": "2026-05-22",
                }
            )
            wizard.action_confirm()
            check_title.invalidate_recordset()
            self.assertEqual(check_title.state, "cancelled")
            self.assertEqual(check_title.check_status, "definitive_return")
            self.assertTrue(check_title.replacement_title_id)
            self.assertEqual(check_title.replacement_title_id.species_kind, "normal")
            self.assertEqual(check_title.replacement_title_id.amount_open, 130.0)

        def test_monthly_withholding_is_cumulative_on_receipts(self):
            service = self.env["receivable.service"]
            first_title, first_installment = self._create_single_installment_title(
                "Titulo Ret 1", 400.0, "2026-05-10"
            )
            second_title, second_installment = self._create_single_installment_title(
                "Titulo Ret 2", 200.0, "2026-05-15"
            )
            _third_title, third_installment = self._create_single_installment_title(
                "Titulo Ret 3", 100.0, "2026-05-20"
            )

            first = service.create_settlement(
                {
                    "name": "Liquidacao 1",
                    "date": "2026-05-10",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                },
                [{"installment_id": first_installment.id, "principal_amount": 400.0}],
            )
            service.apply_settlement(first)
            self.assertFalse(first.withholding_line_ids)
            self.assertEqual(first.net_amount_total, 400.0)

            second = service.create_settlement(
                {
                    "name": "Liquidacao 2",
                    "date": "2026-05-15",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                },
                [{"installment_id": second_installment.id, "principal_amount": 200.0}],
            )
            service.apply_settlement(second)
            self.assertEqual(second.withholding_amount_total, 60.0)
            self.assertEqual(second.net_amount_total, 140.0)
            self.assertEqual(second.withholding_line_ids[0].base_amount, 600.0)
            self.assertEqual(second.withholding_line_ids[0].previously_withheld_amount, 0.0)

            third = service.create_settlement(
                {
                    "name": "Liquidacao 3",
                    "date": "2026-05-20",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                },
                [{"installment_id": third_installment.id, "principal_amount": 100.0}],
            )
            service.apply_settlement(third)
            self.assertEqual(third.withholding_amount_total, 10.0)
            self.assertEqual(third.net_amount_total, 90.0)
            self.assertEqual(third.withholding_line_ids[0].base_amount, 700.0)
            self.assertEqual(third.withholding_line_ids[0].previously_withheld_amount, 60.0)
            self.assertEqual(first_title.amount_open, 0.0)
            self.assertEqual(second_title.amount_open, 0.0)

        def test_apply_settlement_in_foreign_currency(self):
            service = self.env["receivable.service"]
            _title, installment = self._create_single_installment_title_in_currency(
                "Titulo Moeda Estrangeira", 100.0, "2026-05-10", self.currency_xre
            )
            settlement = service.create_settlement(
                {
                    "name": "Liquidacao Moeda Estrangeira",
                    "date": "2026-05-10",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                    "currency_id": self.currency_xre.id,
                },
                [{"installment_id": installment.id, "principal_amount": 100.0}],
            )
            service.apply_settlement(settlement)
            expected_company_amount = self.currency_xre._convert(
                100.0,
                self.env.company.currency_id,
                self.env.company,
                settlement.date,
            )
            self.assertEqual(settlement.currency_id, self.currency_xre)
            self.assertEqual(settlement.gross_amount_total, 100.0)
            self.assertEqual(settlement.net_amount_total, 100.0)
            self.assertEqual(settlement.gross_amount_company_currency, expected_company_amount)
            self.assertEqual(settlement.net_amount_company_currency, expected_company_amount)

        def test_block_settlement_with_mixed_currencies(self):
            service = self.env["receivable.service"]
            _title_brl, installment_brl = self._create_single_installment_title(
                "Titulo BRL", 50.0, "2026-05-10"
            )
            _title_xre, installment_xre = self._create_single_installment_title_in_currency(
                "Titulo XRE", 50.0, "2026-05-10", self.currency_xre
            )
            with self.assertRaises(ValidationError):
                service.create_settlement(
                    {
                        "name": "Liquidacao Mista",
                        "date": "2026-05-10",
                        "partner_id": self.partner.id,
                        "company_id": self.env.company.id,
                    },
                    [
                        {"installment_id": installment_brl.id, "principal_amount": 50.0},
                        {"installment_id": installment_xre.id, "principal_amount": 50.0},
                    ],
                )
