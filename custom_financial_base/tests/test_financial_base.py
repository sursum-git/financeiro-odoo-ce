if __name__.startswith("odoo.addons."):
    from odoo.tests.common import TransactionCase

    class TestFinancialBase(TransactionCase):
        def test_create_portador_caixa(self):
            portador = self.env["financial.portador"].create(
                {
                    "name": "Caixa Loja 1",
                    "code": "CX1",
                    "type": "caixa",
                    "company_id": self.env.company.id,
                }
            )
            self.assertEqual(portador.type, "caixa")
            self.assertTrue(portador.controla_saldo)
            self.assertEqual(portador.currency_id, self.env.company.currency_id)

        def test_create_payment_method_pix(self):
            payment_method = self.env["financial.payment.method"].create(
                {
                    "name": "PIX",
                    "code": "PIX",
                    "type": "pix",
                    "liquida_imediato": True,
                    "company_id": self.env.company.id,
                }
            )
            self.assertEqual(payment_method.type, "pix")
            self.assertTrue(payment_method.liquida_imediato)

        def test_create_financial_modality(self):
            modality = self.env["financial.modality"].create(
                {
                    "name": "Carteira",
                    "code": "CART",
                    "tipo_operacao": "receber",
                    "company_id": self.env.company.id,
                }
            )
            self.assertEqual(modality.tipo_operacao, "receber")

        def test_create_company_parameter(self):
            portador = self.env["financial.portador"].create(
                {
                    "name": "Portador Padrao",
                    "code": "PORT_STD",
                    "type": "interno",
                    "company_id": self.env.company.id,
                }
            )
            payment_method = self.env["financial.payment.method"].create(
                {
                    "name": "Transferencia",
                    "code": "TED",
                    "type": "transferencia",
                    "company_id": self.env.company.id,
                }
            )
            parameter = self.env["financial.parameter"].create(
                {
                    "company_id": self.env.company.id,
                    "default_portador_id": portador.id,
                    "default_payment_method_id": payment_method.id,
                }
            )
            self.assertEqual(parameter.company_id, self.env.company)
            self.assertEqual(parameter.default_portador_id, portador)
            self.assertEqual(parameter.default_payment_method_id, payment_method)

        def test_essential_records_read_without_error(self):
            history = self.env["financial.history"].create(
                {
                    "name": "Historico Teste",
                    "code": "HIST",
                    "description": "Historico padrao",
                    "company_id": self.env.company.id,
                }
            )
            reason = self.env["financial.movement.reason"].create(
                {
                    "name": "Ajuste Manual",
                    "code": "AJUSTE",
                    "type": "ajuste",
                    "company_id": self.env.company.id,
                }
            )
            self.assertEqual(history.read(["name"])[0]["name"], "Historico Teste")
            self.assertEqual(reason.read(["type"])[0]["type"], "ajuste")

        def test_create_withholding_code(self):
            code = self.env["financial.withholding.code"].create(
                {
                    "name": "IRRF Servicos",
                    "code": "IRRF",
                    "company_id": self.env.company.id,
                    "due_date": "2026-12-31",
                    "minimum_retention_amount": 10.0,
                    "minimum_payment_amount": 25.0,
                }
            )
            self.assertEqual(code.code, "IRRF")
            self.assertEqual(str(code.due_date), "2026-12-31")
            self.assertEqual(code.minimum_retention_amount, 10.0)
            self.assertEqual(code.minimum_payment_amount, 25.0)

        def test_default_title_species_are_available(self):
            species_normal = self.env.ref("custom_financial_base.financial_title_species_normal")
            species_check = self.env.ref("custom_financial_base.financial_title_species_check")
            self.assertEqual(species_normal.kind, "normal")
            self.assertEqual(species_check.kind, "check")

        def test_create_check_return_reason(self):
            reason = self.env["financial.check.return.reason"].create(
                {
                    "code": "11",
                    "name": "Cheque sem fundos",
                    "description": "Devolvido por insuficiencia de fundos",
                    "is_definitive": True,
                }
            )
            self.assertEqual(reason.code, "11")
            self.assertTrue(reason.is_definitive)

        def test_assign_multiple_withholding_lines_to_partner(self):
            partner = self.env["res.partner"].create({"name": "Fornecedor Com Retencao"})
            receiver_a = self.env["res.partner"].create({"name": "Contato Recebedor A"})
            receiver_b = self.env["res.partner"].create({"name": "Contato Recebedor B"})
            code_a = self.env["financial.withholding.code"].create(
                {
                    "name": "ISS",
                    "code": "ISS",
                    "company_id": self.env.company.id,
                }
            )
            code_b = self.env["financial.withholding.code"].create(
                {
                    "name": "IRRF",
                    "code": "IRRF",
                    "company_id": self.env.company.id,
                }
            )
            line_a = self.env["res.partner.withholding.line"].create(
                {
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                    "withholding_code_id": code_a.id,
                    "retention_percent": 5.0,
                    "supplier_contact_id": receiver_a.id,
                }
            )
            line_b = self.env["res.partner.withholding.line"].create(
                {
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                    "withholding_code_id": code_b.id,
                    "retention_percent": 1.5,
                    "supplier_contact_id": receiver_b.id,
                }
            )
            self.assertEqual(len(partner.withholding_line_ids), 2)
            self.assertEqual(line_a.supplier_contact_id, receiver_a)
            self.assertEqual(line_b.retention_percent, 1.5)
