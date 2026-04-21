import base64

if __name__.startswith("odoo.addons."):
    from odoo.exceptions import ValidationError
    from odoo.tests.common import TransactionCase

    class TestTreasuryReconciliation(TransactionCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.bank = cls.env["treasury.bank"].create({"name": "Banco Conc", "code": "900"})
            cls.account = cls.env["treasury.account"].create(
                {
                    "name": "Conta Banco Conc",
                    "code": "TBREC",
                    "type": "bank",
                    "company_id": cls.env.company.id,
                }
            )
            cls.bank_account = cls.env["treasury.bank.account"].create(
                {
                    "name": "Conta Conciliacao",
                    "bank_id": cls.bank.id,
                    "treasury_account_id": cls.account.id,
                    "agency": "0001",
                    "account_number": "12345",
                    "company_id": cls.env.company.id,
                }
            )
            content = (
                "date,description,document_number,amount,type\n"
                "2026-04-20,Credito Teste,DOC1,100.00,credit\n"
                "2026-04-21,Credito Ajuste,DOC2,50.00,credit\n"
            )
            cls.statement_import = cls.env["treasury.bank.statement.import"].create(
                {
                    "name": "Extrato Conc",
                    "file_name": "conc.csv",
                    "file_data": base64.b64encode(content.encode("utf-8")),
                    "company_id": cls.env.company.id,
                    "bank_account_id": cls.bank_account.id,
                }
            )
            cls.statement_import.action_import_file()
            cls.reason = cls.env["financial.movement.reason"].create(
                {
                    "name": "Conciliacao",
                    "code": "CONC",
                    "type": "ajuste",
                    "company_id": cls.env.company.id,
                }
            )
            cls.movement = cls.env["treasury.movement.service"].create_movement(
                {
                    "name": "Movimento Banco",
                    "date": "2026-04-20",
                    "company_id": cls.env.company.id,
                    "type": "entrada",
                    "amount": 100.0,
                    "account_id": cls.account.id,
                    "reason_id": cls.reason.id,
                }
            )
            cls.env["treasury.movement.service"].post_movement(cls.movement)
            cls.currency_xrc = cls.env["res.currency"].create(
                {"name": "XRC", "symbol": "XR$", "rounding": 0.01}
            )
            cls.env["res.currency.rate"].create(
                {
                    "name": "2026-04-20",
                    "currency_id": cls.currency_xrc.id,
                    "company_id": cls.env.company.id,
                    "rate": 0.2,
                }
            )
            cls.fx_movement = cls.env["treasury.movement.service"].create_movement(
                {
                    "name": "Movimento Banco FX",
                    "date": "2026-04-20",
                    "company_id": cls.env.company.id,
                    "type": "entrada",
                    "amount": 100.0,
                    "currency_id": cls.currency_xrc.id,
                    "account_id": cls.account.id,
                    "reason_id": cls.reason.id,
                }
            )
            cls.env["treasury.movement.service"].post_movement(cls.fx_movement)

        def _create_reconciliation(self):
            return self.env["treasury.reconciliation"].create(
                {
                    "name": "Conciliacao Abril",
                    "company_id": self.env.company.id,
                    "bank_account_id": self.bank_account.id,
                    "date_start": "2026-04-01",
                    "date_end": "2026-04-30",
                    "state": "in_progress",
                }
            )

        def test_create_reconciliation(self):
            reconciliation = self._create_reconciliation()
            self.assertEqual(reconciliation.bank_account_id, self.bank_account)

        def test_match_statement_line_to_movement(self):
            reconciliation = self._create_reconciliation()
            line = self.env["treasury.reconciliation.service"].match_line(
                self.statement_import.line_ids[0],
                self.movement,
                reconciliation=reconciliation,
            )
            self.assertEqual(line.status, "matched")
            self.assertTrue(self.statement_import.line_ids[0].is_reconciled)
            self.assertTrue(self.movement.is_reconciled)

        def test_prevent_double_reconciliation(self):
            reconciliation = self._create_reconciliation()
            self.env["treasury.reconciliation.service"].match_line(
                self.statement_import.line_ids[0],
                self.movement,
                reconciliation=reconciliation,
            )
            reconciliation2 = self.env["treasury.reconciliation"].create(
                {
                    "name": "Conciliacao Abril 2",
                    "company_id": self.env.company.id,
                    "bank_account_id": self.bank_account.id,
                    "date_start": "2026-04-01",
                    "date_end": "2026-04-30",
                    "state": "in_progress",
                }
            )
            with self.assertRaises(ValidationError):
                self.env["treasury.reconciliation.service"].match_line(
                    self.statement_import.line_ids[0],
                    self.env["treasury.movement"].search([("id", "=", self.movement.id)]),
                    reconciliation=reconciliation2,
                )

        def test_create_reconciliation_adjustment(self):
            reconciliation = self._create_reconciliation()
            line = self.env["treasury.reconciliation.service"].create_adjustment(
                reconciliation,
                self.statement_import.line_ids[1],
            )
            self.assertEqual(line.status, "adjusted")
            self.assertTrue(line.adjustment_movement_id)
            self.assertTrue(self.statement_import.line_ids[1].is_reconciled)

        def test_mark_movement_reconciled(self):
            reconciliation = self._create_reconciliation()
            self.env["treasury.reconciliation.service"].match_line(
                self.statement_import.line_ids[0],
                self.movement,
                reconciliation=reconciliation,
            )
            self.assertTrue(self.movement.is_reconciled)

        def test_block_reconciliation_with_different_currency(self):
            reconciliation = self._create_reconciliation()
            with self.assertRaises(ValidationError):
                self.env["treasury.reconciliation.service"].match_line(
                    self.statement_import.line_ids[0],
                    self.fx_movement,
                    reconciliation=reconciliation,
                )
