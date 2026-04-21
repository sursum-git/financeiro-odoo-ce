import base64

if __name__.startswith("odoo.addons."):
    from odoo.tests.common import TransactionCase

    class TestTreasuryBank(TransactionCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.treasury_account = cls.env["treasury.account"].create(
                {
                    "name": "Conta Banco",
                    "code": "BANK_TR",
                    "type": "bank",
                    "company_id": cls.env.company.id,
                }
            )
            cls.modality = cls.env["financial.modality"].create(
                {
                    "name": "Cobranca Simples",
                    "code": "COB_SIM",
                    "tipo_operacao": "receber",
                    "company_id": cls.env.company.id,
                }
            )
            cls.currency_xbk = cls.env["res.currency"].create(
                {"name": "XBK", "symbol": "XB$", "rounding": 0.01}
            )
            cls.env["res.currency.rate"].create(
                {
                    "name": "2026-04-20",
                    "currency_id": cls.currency_xbk.id,
                    "company_id": cls.env.company.id,
                    "rate": 0.2,
                }
            )

        def test_create_bank(self):
            bank = self.env["treasury.bank"].create(
                {
                    "name": "Banco Teste",
                    "code": "001",
                }
            )
            self.assertEqual(bank.code, "001")

        def test_create_bank_account(self):
            bank = self.env["treasury.bank"].create(
                {
                    "name": "Banco Conta",
                    "code": "237",
                }
            )
            bank_account = self.env["treasury.bank.account"].create(
                {
                    "name": "Conta Corrente Principal",
                    "bank_id": bank.id,
                    "treasury_account_id": self.treasury_account.id,
                    "agency": "1234",
                    "account_number": "98765",
                    "account_digit": "0",
                    "company_id": self.env.company.id,
                }
            )
            self.assertEqual(bank_account.bank_id, bank)
            self.assertEqual(bank_account.treasury_account_id, self.treasury_account)

        def test_associate_modality_to_bank_account(self):
            bank = self.env["treasury.bank"].create(
                {
                    "name": "Banco Modalidade",
                    "code": "341",
                }
            )
            bank_account = self.env["treasury.bank.account"].create(
                {
                    "name": "Conta Modalidade",
                    "bank_id": bank.id,
                    "account_number": "11111",
                    "company_id": self.env.company.id,
                }
            )
            link = self.env["treasury.bank.account.modality"].create(
                {
                    "bank_account_id": bank_account.id,
                    "modality_id": self.modality.id,
                    "code": "SIMP",
                }
            )
            self.assertEqual(link.modality_id, self.modality)

        def test_create_statement_import(self):
            bank = self.env["treasury.bank"].create(
                {
                    "name": "Banco Extrato",
                    "code": "104",
                }
            )
            bank_account = self.env["treasury.bank.account"].create(
                {
                    "name": "Conta Extrato",
                    "bank_id": bank.id,
                    "account_number": "22222",
                    "company_id": self.env.company.id,
                }
            )
            file_content = "date,description,document_number,amount,type\n2026-04-20,Credito PIX,DOC1,100.00,credit\n"
            statement_import = self.env["treasury.bank.statement.import"].create(
                {
                    "name": "Importacao Teste",
                    "file_name": "statement.csv",
                    "file_data": base64.b64encode(file_content.encode("utf-8")),
                    "company_id": self.env.company.id,
                    "bank_account_id": bank_account.id,
                }
            )
            statement_import.action_import_file()
            self.assertEqual(statement_import.state, "imported")
            self.assertEqual(len(statement_import.line_ids), 1)

        def test_statement_import_uses_bank_account_currency(self):
            bank = self.env["treasury.bank"].create(
                {
                    "name": "Banco FX",
                    "code": "777",
                }
            )
            bank_account = self.env["treasury.bank.account"].create(
                {
                    "name": "Conta FX",
                    "bank_id": bank.id,
                    "account_number": "77777",
                    "company_id": self.env.company.id,
                    "currency_id": self.currency_xbk.id,
                }
            )
            file_content = "date,description,document_number,amount,type\n2026-04-20,Credito FX,DOCX,100.00,credit\n"
            statement_import = self.env["treasury.bank.statement.import"].create(
                {
                    "name": "Importacao FX",
                    "file_name": "statement_fx.csv",
                    "file_data": base64.b64encode(file_content.encode("utf-8")),
                    "company_id": self.env.company.id,
                    "bank_account_id": bank_account.id,
                }
            )
            statement_import.action_import_file()
            self.assertEqual(statement_import.currency_id, self.currency_xbk)
            self.assertEqual(statement_import.line_ids[0].currency_id, self.currency_xbk)

        def test_imported_lines_do_not_change_balance_automatically(self):
            bank = self.env["treasury.bank"].create(
                {
                    "name": "Banco Saldo",
                    "code": "033",
                }
            )
            bank_account = self.env["treasury.bank.account"].create(
                {
                    "name": "Conta Saldo",
                    "bank_id": bank.id,
                    "treasury_account_id": self.treasury_account.id,
                    "account_number": "33333",
                    "company_id": self.env.company.id,
                }
            )
            file_content = (
                "date,description,document_number,amount,type\n"
                "2026-04-20,Debito Tarifa,DOC2,10.00,debit\n"
                "2026-04-20,Credito Deposito,DOC3,50.00,credit\n"
            )
            statement_import = self.env["treasury.bank.statement.import"].create(
                {
                    "name": "Importacao Sem Saldo",
                    "file_name": "statement_balance.csv",
                    "file_data": base64.b64encode(file_content.encode("utf-8")),
                    "company_id": self.env.company.id,
                    "bank_account_id": bank_account.id,
                }
            )
            statement_import.action_import_file()
            balance = self.env["treasury.movement.service"].compute_balance(account=self.treasury_account)
            self.assertEqual(balance, 0.0)
            self.assertFalse(any(statement_import.line_ids.mapped("is_reconciled")))
