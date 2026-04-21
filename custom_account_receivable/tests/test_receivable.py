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
