if __name__.startswith("odoo.addons."):
    from odoo import fields
    from odoo.tests.common import TransactionCase
    from odoo.exceptions import ValidationError

    class TestTreasury(TransactionCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.history = cls.env["financial.history"].create(
                {
                    "name": "Historico Tesouraria",
                    "code": "HIST_TR",
                    "company_id": cls.env.company.id,
                }
            )
            cls.reason = cls.env["financial.movement.reason"].create(
                {
                    "name": "Ajuste",
                    "code": "AJ_TR",
                    "type": "ajuste",
                    "company_id": cls.env.company.id,
                }
            )
            cls.portador = cls.env["financial.portador"].create(
                {
                    "name": "Portador Caixa",
                    "code": "PORT_CAIXA",
                    "type": "caixa",
                    "company_id": cls.env.company.id,
                }
            )

        def _create_account(self, code="CTA1", name="Conta Financeira", company=None):
            company = company or self.env.company
            return self.env["treasury.account"].create(
                {
                    "name": name,
                    "code": code,
                    "type": "treasury",
                    "company_id": company.id,
                }
            )

        def test_create_financial_account(self):
            account = self._create_account()
            self.assertEqual(account.type, "treasury")

        def test_create_inbound_movement(self):
            account = self._create_account(code="CTA_IN")
            movement = self.env["treasury.movement.service"].create_movement(
                {
                    "name": "Entrada Inicial",
                    "type": "entrada",
                    "amount": 100.0,
                    "account_id": account.id,
                    "portador_id": self.portador.id,
                    "history_id": self.history.id,
                    "reason_id": self.reason.id,
                    "company_id": self.env.company.id,
                }
            )
            self.env["treasury.movement.service"].post_movement(movement)
            self.assertEqual(movement.state, "posted")
            self.assertEqual(movement.signed_amount, 100.0)

        def test_create_outbound_movement(self):
            account = self._create_account(code="CTA_OUT")
            movement = self.env["treasury.movement.service"].create_movement(
                {
                    "name": "Saida Operacional",
                    "type": "saida",
                    "amount": 40.0,
                    "account_id": account.id,
                    "portador_id": self.portador.id,
                    "history_id": self.history.id,
                    "reason_id": self.reason.id,
                    "company_id": self.env.company.id,
                }
            )
            self.env["treasury.movement.service"].post_movement(movement)
            self.assertEqual(movement.signed_amount, -40.0)

        def test_transfer_generates_two_movements(self):
            source = self._create_account(code="SRC", name="Origem")
            target = self._create_account(code="DST", name="Destino")
            transfer = self.env["treasury.transfer"].create(
                {
                    "name": "Transferencia Interna",
                    "amount": 55.0,
                    "source_account_id": source.id,
                    "target_account_id": target.id,
                    "company_id": self.env.company.id,
                }
            )
            transfer.action_confirm()
            self.assertEqual(transfer.state, "confirmed")
            self.assertEqual(transfer.out_movement_id.state, "posted")
            self.assertEqual(transfer.in_movement_id.state, "posted")
            self.assertEqual(transfer.out_movement_id.type, "transferencia_saida")
            self.assertEqual(transfer.in_movement_id.type, "transferencia_entrada")

        def test_reverse_movement_links_original(self):
            account = self._create_account(code="REV")
            movement = self.env["treasury.movement.service"].create_movement(
                {
                    "name": "Movimento Original",
                    "type": "saida",
                    "amount": 30.0,
                    "account_id": account.id,
                    "portador_id": self.portador.id,
                    "history_id": self.history.id,
                    "reason_id": self.reason.id,
                    "company_id": self.env.company.id,
                }
            )
            self.env["treasury.movement.service"].post_movement(movement)
            reverse = self.env["treasury.movement.service"].reverse_movement(movement)
            self.assertEqual(reverse.reversed_movement_id, movement)
            self.assertEqual(reverse.state, "posted")
            self.assertEqual(movement.state, "posted")

        def test_compute_balance_per_account(self):
            account = self._create_account(code="BAL")
            service = self.env["treasury.movement.service"]
            in_move = service.create_movement(
                {
                    "name": "Entrada Saldo",
                    "type": "entrada",
                    "amount": 120.0,
                    "account_id": account.id,
                    "portador_id": self.portador.id,
                    "history_id": self.history.id,
                    "reason_id": self.reason.id,
                    "company_id": self.env.company.id,
                }
            )
            out_move = service.create_movement(
                {
                    "name": "Saida Saldo",
                    "type": "saida",
                    "amount": 20.0,
                    "account_id": account.id,
                    "portador_id": self.portador.id,
                    "history_id": self.history.id,
                    "reason_id": self.reason.id,
                    "company_id": self.env.company.id,
                }
            )
            service.post_movement(in_move)
            service.post_movement(out_move)
            self.assertEqual(service.compute_balance(account=account), 100.0)

        def test_intercompany_loan_generates_two_movements(self):
            borrower_company = self.env["res.company"].create(
                {
                    "name": "Filial Mutuo",
                    "parent_id": self.env.company.id,
                    "currency_id": self.env.company.currency_id.id,
                }
            )
            lender_account = self._create_account(code="MUT_OUT", company=self.env.company)
            borrower_account = self._create_account(
                code="MUT_IN",
                name="Conta Filial",
                company=borrower_company,
            )
            loan = self.env["treasury.intercompany.loan"].create(
                {
                    "name": "Mutuo Grupo",
                    "date": fields.Date.context_today(self),
                    "lender_company_id": self.env.company.id,
                    "borrower_company_id": borrower_company.id,
                    "source_account_id": lender_account.id,
                    "target_account_id": borrower_account.id,
                    "currency_id": self.env.company.currency_id.id,
                    "amount": 150.0,
                }
            )
            loan.action_confirm()
            self.assertEqual(loan.state, "confirmed")
            self.assertEqual(loan.out_movement_id.state, "posted")
            self.assertEqual(loan.in_movement_id.state, "posted")
            self.assertEqual(loan.out_movement_id.company_id, self.env.company)
            self.assertEqual(loan.in_movement_id.company_id, borrower_company)
            self.assertEqual(loan.out_movement_id.type, "saida")
            self.assertEqual(loan.in_movement_id.type, "entrada")

        def test_intercompany_loan_blocks_company_outside_group(self):
            outsider_company = self.env["res.company"].create(
                {
                    "name": "Empresa Externa",
                    "currency_id": self.env.company.currency_id.id,
                }
            )
            lender_account = self._create_account(code="MUT_EXT_OUT", company=self.env.company)
            outsider_account = self._create_account(
                code="MUT_EXT_IN",
                name="Conta Externa",
                company=outsider_company,
            )
            with self.assertRaises(ValidationError):
                self.env["treasury.intercompany.loan"].create(
                    {
                        "name": "Mutuo Externo",
                        "date": fields.Date.context_today(self),
                        "lender_company_id": self.env.company.id,
                        "borrower_company_id": outsider_company.id,
                        "source_account_id": lender_account.id,
                        "target_account_id": outsider_account.id,
                        "currency_id": self.env.company.currency_id.id,
                        "amount": 90.0,
                    }
                )
