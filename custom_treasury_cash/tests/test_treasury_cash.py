if __name__.startswith("odoo.addons."):
    from odoo.exceptions import ValidationError
    from odoo.tests.common import TransactionCase

    class TestTreasuryCash(TransactionCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.portador = cls.env["financial.portador"].create(
                {
                    "name": "Caixa Operacional",
                    "code": "CX_OP",
                    "type": "caixa",
                    "company_id": cls.env.company.id,
                }
            )
            cls.target_portador = cls.env["financial.portador"].create(
                {
                    "name": "Tesouraria Central",
                    "code": "TES_CENT",
                    "type": "interno",
                    "company_id": cls.env.company.id,
                }
            )
            cls.account = cls.env["treasury.account"].create(
                {
                    "name": "Conta Central",
                    "code": "CCENT",
                    "type": "treasury",
                    "company_id": cls.env.company.id,
                }
            )
            cls.parameter = cls.env["financial.parameter"].create(
                {
                    "company_id": cls.env.company.id,
                    "require_cash_difference_reason": True,
                }
            )
            cls.cash_box = cls.env["treasury.cash.box"].create(
                {
                    "name": "Caixa Loja 1",
                    "code": "CX1",
                    "company_id": cls.env.company.id,
                    "portador_id": cls.portador.id,
                }
            )

        def test_create_cash_box(self):
            self.assertEqual(self.cash_box.portador_id, self.portador)

        def test_open_session(self):
            session = self.env["treasury.cash.service"].open_session(
                self.cash_box,
                self.env.user,
                100.0,
            )
            self.assertEqual(session.state, "open")
            self.assertEqual(session.opening_amount, 100.0)

        def test_block_second_open_session(self):
            self.env["treasury.cash.service"].open_session(self.cash_box, self.env.user, 50.0)
            with self.assertRaises(ValidationError):
                self.env["treasury.cash.service"].open_session(self.cash_box, self.env.user, 10.0)

        def test_register_supply(self):
            session = self.env["treasury.cash.service"].open_session(self.cash_box, self.env.user, 0.0)
            movement = self.env["treasury.cash.service"].register_supply(session, 25.0)
            self.assertEqual(movement.state, "posted")
            self.assertEqual(movement.signed_amount, 25.0)
            self.assertEqual(len(session.line_ids), 1)

        def test_register_withdrawal(self):
            session = self.env["treasury.cash.service"].open_session(self.cash_box, self.env.user, 100.0)
            movement = self.env["treasury.cash.service"].register_withdrawal(session, 30.0)
            self.assertEqual(movement.state, "posted")
            self.assertEqual(movement.signed_amount, -30.0)

        def test_close_session_and_compute_difference(self):
            session = self.env["treasury.cash.service"].open_session(self.cash_box, self.env.user, 100.0)
            self.env["treasury.cash.service"].register_supply(session, 20.0)
            self.env["treasury.cash.service"].close_session(session, 118.0, reason="Moedas faltantes")
            self.assertEqual(session.state, "closed")
            self.assertEqual(session.closing_amount_computed, 120.0)
            self.assertEqual(session.difference_amount, -2.0)

        def test_create_accountability(self):
            accountability = self.env["treasury.cash.accountability"].create(
                {
                    "name": "Prestacao Caixa Loja 1",
                    "company_id": self.env.company.id,
                    "source_portador_id": self.portador.id,
                    "target_account_id": self.account.id,
                    "amount": 80.0,
                }
            )
            accountability.action_confirm()
            self.assertEqual(accountability.state, "confirmed")
            self.assertEqual(accountability.out_movement_id.state, "posted")
            self.assertEqual(accountability.in_movement_id.state, "posted")
