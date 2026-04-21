if __name__.startswith("odoo.addons."):
    from odoo.exceptions import ValidationError
    from odoo.tests.common import TransactionCase

    class TestPayable(TransactionCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.partner = cls.env["res.partner"].create({"name": "Fornecedor Teste"})
            cls.payment_method = cls.env["financial.payment.method"].create(
                {
                    "name": "Transferencia",
                    "code": "TRFPAY",
                    "type": "transferencia",
                    "company_id": cls.env.company.id,
                }
            )
            cls.portador = cls.env["financial.portador"].create(
                {
                    "name": "Portador Pagamento",
                    "code": "PRTPAY",
                    "type": "interno",
                    "company_id": cls.env.company.id,
                }
            )
            cls.account = cls.env["treasury.account"].create(
                {
                    "name": "Conta Pagamento",
                    "code": "CTAPAY",
                    "type": "other",
                    "company_id": cls.env.company.id,
                }
            )
            cls.withholding_supplier = cls.env["res.partner"].create({"name": "Favorecido Retencao Pagar"})
            cls.withholding_code = cls.env["financial.withholding.code"].create(
                {
                    "name": "IRRF Pagar",
                    "code": "IRRFPAY",
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
            cls.currency_xpa = cls.env["res.currency"].create(
                {"name": "XPA", "symbol": "XP$", "rounding": 0.01}
            )
            cls.env["res.currency.rate"].create(
                {
                    "name": "2026-05-10",
                    "currency_id": cls.currency_xpa.id,
                    "company_id": cls.env.company.id,
                    "rate": 0.25,
                }
            )

        def _create_title_with_installments(self):
            service = self.env["payable.service"]
            title = service.open_title(
                {
                    "name": "Titulo Fornecedor 1",
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
            service = self.env["payable.service"]
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
            service = self.env["payable.service"]
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

        def test_create_payable_title(self):
            title, _installments = self._create_title_with_installments()
            self.assertEqual(title.partner_id, self.partner)
            self.assertEqual(title.amount_total, 300.0)

        def test_create_installments(self):
            title, installments = self._create_title_with_installments()
            self.assertEqual(len(installments), 3)
            self.assertEqual(sum(installments.mapped("amount")), title.amount_total)

        def test_block_installments_total_different_from_title(self):
            service = self.env["payable.service"]
            title = service.open_title(
                {
                    "name": "Titulo Divergente Pagar",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                    "amount_total": 100.0,
                }
            )
            with self.assertRaises(ValidationError):
                service.generate_installments(
                    title,
                    [
                        {"due_date": "2026-05-10", "amount": 60.0},
                        {"due_date": "2026-06-10", "amount": 30.0},
                    ],
                )

        def test_schedule_payment(self):
            schedule = self.env["payable.service"].schedule_payment(
                {
                    "name": "Agenda Fornecedor",
                    "payment_date": "2026-05-05",
                    "company_id": self.env.company.id,
                    "partner_id": self.partner.id,
                }
            )
            self.assertEqual(schedule.state, "scheduled")

        def test_execute_partial_payment(self):
            _title, installments = self._create_title_with_installments()
            service = self.env["payable.service"]
            payment = service.create_payment(
                {
                    "name": "Pagamento Parcial",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                    "payment_method_id": self.payment_method.id,
                    "source_account_id": self.account.id,
                    "source_portador_id": self.portador.id,
                },
                [
                    {
                        "installment_id": installments[0].id,
                        "principal_amount": 40.0,
                    }
                ],
            )
            service.apply_payment(payment)
            self.assertEqual(payment.state, "applied")
            self.assertEqual(installments[0].amount_open, 60.0)
            self.assertEqual(installments[0].state, "partial")

        def test_block_payment_above_open_amount(self):
            _title, installments = self._create_title_with_installments()
            service = self.env["payable.service"]
            with self.assertRaises(ValidationError):
                payment = service.create_payment(
                    {
                        "name": "Pagamento Indevido",
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
                service.apply_payment(payment)

        def test_monthly_withholding_is_cumulative_on_payments(self):
            service = self.env["payable.service"]
            _first_title, first_installment = self._create_single_installment_title(
                "Titulo Pay Ret 1", 400.0, "2026-05-10"
            )
            _second_title, second_installment = self._create_single_installment_title(
                "Titulo Pay Ret 2", 200.0, "2026-05-15"
            )
            _third_title, third_installment = self._create_single_installment_title(
                "Titulo Pay Ret 3", 100.0, "2026-05-20"
            )

            first = service.create_payment(
                {
                    "name": "Pagamento 1",
                    "date": "2026-05-10",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                },
                [{"installment_id": first_installment.id, "principal_amount": 400.0}],
            )
            service.apply_payment(first)
            self.assertFalse(first.withholding_line_ids)
            self.assertEqual(first.net_amount_total, 400.0)

            second = service.create_payment(
                {
                    "name": "Pagamento 2",
                    "date": "2026-05-15",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                },
                [{"installment_id": second_installment.id, "principal_amount": 200.0}],
            )
            service.apply_payment(second)
            self.assertEqual(second.withholding_amount_total, 60.0)
            self.assertEqual(second.net_amount_total, 140.0)
            self.assertEqual(second.withholding_line_ids[0].base_amount, 600.0)
            self.assertEqual(second.withholding_line_ids[0].previously_withheld_amount, 0.0)

            third = service.create_payment(
                {
                    "name": "Pagamento 3",
                    "date": "2026-05-20",
                    "partner_id": self.partner.id,
                    "company_id": self.env.company.id,
                },
                [{"installment_id": third_installment.id, "principal_amount": 100.0}],
            )
            service.apply_payment(third)
            self.assertEqual(third.withholding_amount_total, 10.0)
            self.assertEqual(third.net_amount_total, 90.0)
            self.assertEqual(third.withholding_line_ids[0].base_amount, 700.0)
            self.assertEqual(third.withholding_line_ids[0].previously_withheld_amount, 60.0)

        def test_apply_payment_in_foreign_currency(self):
            service = self.env["payable.service"]
            partner = self.env["res.partner"].create({"name": "Fornecedor Sem Retencao FX"})
            title = service.open_title(
                {
                    "name": "Titulo Moeda Estrangeira",
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                    "amount_total": 80.0,
                    "currency_id": self.currency_xpa.id,
                }
            )
            installment = service.generate_installments(
                title,
                [{"due_date": "2026-05-10", "amount": 80.0}],
            )[0]
            payment = service.create_payment(
                {
                    "name": "Pagamento Moeda Estrangeira",
                    "date": "2026-05-10",
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                    "currency_id": self.currency_xpa.id,
                },
                [{"installment_id": installment.id, "principal_amount": 80.0}],
            )
            service.apply_payment(payment)
            expected_company_amount = self.currency_xpa._convert(
                80.0,
                self.env.company.currency_id,
                self.env.company,
                payment.date,
            )
            self.assertEqual(payment.currency_id, self.currency_xpa)
            self.assertEqual(payment.gross_amount_total, 80.0)
            self.assertEqual(payment.net_amount_total, 80.0)
            self.assertEqual(payment.gross_amount_company_currency, expected_company_amount)
            self.assertEqual(payment.net_amount_company_currency, expected_company_amount)

        def test_monthly_withholding_uses_company_currency_across_mixed_currencies(self):
            service = self.env["payable.service"]
            partner = self.env["res.partner"].create({"name": "Fornecedor Retencao Multimoeda"})
            withholding_supplier = self.env["res.partner"].create(
                {"name": "Favorecido Retencao Multimoeda Pagar"}
            )
            foreign_company_amount = self.currency_xpa._convert(
                100.0,
                self.env.company.currency_id,
                self.env.company,
                "2026-05-15",
            )
            threshold = 200.0 + (foreign_company_amount / 2.0)
            withholding_code = self.env["financial.withholding.code"].create(
                {
                    "name": "IRRF Multimoeda Pagar",
                    "code": "IRRF_MULTI_PAY",
                    "company_id": self.env.company.id,
                    "minimum_payment_amount": threshold,
                }
            )
            self.env["res.partner.withholding.line"].create(
                {
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                    "withholding_code_id": withholding_code.id,
                    "retention_percent": 10.0,
                    "supplier_contact_id": withholding_supplier.id,
                }
            )
            brl_title = service.open_title(
                {
                    "name": "Titulo BRL Ret Multimoeda Pagar",
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                    "amount_total": 200.0,
                }
            )
            brl_installment = service.generate_installments(
                brl_title,
                [{"due_date": "2026-05-10", "amount": 200.0}],
            )[0]
            foreign_title = service.open_title(
                {
                    "name": "Titulo FX Ret Multimoeda Pagar",
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                    "amount_total": 100.0,
                    "currency_id": self.currency_xpa.id,
                }
            )
            foreign_installment = service.generate_installments(
                foreign_title,
                [{"due_date": "2026-05-15", "amount": 100.0}],
            )[0]

            first = service.create_payment(
                {
                    "name": "Pagamento BRL",
                    "date": "2026-05-10",
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                },
                [{"installment_id": brl_installment.id, "principal_amount": 200.0}],
            )
            service.apply_payment(first)
            self.assertFalse(first.withholding_line_ids)

            second = service.create_payment(
                {
                    "name": "Pagamento FX",
                    "date": "2026-05-15",
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                    "currency_id": self.currency_xpa.id,
                },
                [{"installment_id": foreign_installment.id, "principal_amount": 100.0}],
            )
            service.apply_payment(second)
            expected_company_withholding = (200.0 + foreign_company_amount) * 0.1
            expected_foreign_withholding = self.env.company.currency_id._convert(
                expected_company_withholding,
                self.currency_xpa,
                self.env.company,
                second.date,
            )
            self.assertEqual(second.withholding_amount_company_currency, expected_company_withholding)
            self.assertEqual(second.withholding_amount_total, expected_foreign_withholding)
            self.assertEqual(
                second.withholding_line_ids[0].base_amount_company_currency,
                200.0 + foreign_company_amount,
            )
            self.assertEqual(second.withholding_line_ids[0].previously_withheld_amount_company_currency, 0.0)

        def test_block_payment_with_mixed_currencies(self):
            service = self.env["payable.service"]
            _title_brl, installment_brl = self._create_single_installment_title(
                "Titulo BRL", 50.0, "2026-05-10"
            )
            _title_xpa, installment_xpa = self._create_single_installment_title_in_currency(
                "Titulo XPA", 50.0, "2026-05-10", self.currency_xpa
            )
            with self.assertRaises(ValidationError):
                service.create_payment(
                    {
                        "name": "Pagamento Misto",
                        "date": "2026-05-10",
                        "partner_id": self.partner.id,
                        "company_id": self.env.company.id,
                    },
                    [
                        {"installment_id": installment_brl.id, "principal_amount": 50.0},
                        {"installment_id": installment_xpa.id, "principal_amount": 50.0},
                    ],
                )
