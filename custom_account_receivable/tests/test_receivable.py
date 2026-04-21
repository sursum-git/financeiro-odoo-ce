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
