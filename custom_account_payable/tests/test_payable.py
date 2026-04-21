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

        def test_create_payable_title(self):
            title, _installments = self._create_title_with_installments()
            self.assertEqual(title.partner_id, self.partner)
            self.assertEqual(title.amount_total, 300.0)

        def test_create_installments(self):
            title, installments = self._create_title_with_installments()
            self.assertEqual(len(installments), 3)
            self.assertEqual(sum(installments.mapped("amount")), title.amount_total)

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
