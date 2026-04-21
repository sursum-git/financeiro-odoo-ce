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
