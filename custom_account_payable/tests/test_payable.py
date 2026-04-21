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
