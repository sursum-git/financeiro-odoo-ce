from odoo.tests.common import TransactionCase


class TestFinancialReports(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.partner_customer = self.env["res.partner"].create({"name": "Cliente Relatorio"})
        self.partner_vendor = self.env["res.partner"].create({"name": "Fornecedor Relatorio"})
        self.payment_method = self.env["financial.payment.method"].create(
            {"name": "PIX", "code": "PIX", "company_id": self.company.id}
        )
        self.portador = self.env["financial.portador"].create(
            {"name": "Portador Relatorio", "code": "PR001", "type": "interno", "company_id": self.company.id}
        )
        self.account = self.env["treasury.account"].create(
            {"name": "Conta Relatorio", "code": "CR001", "company_id": self.company.id}
        )
        self.currency_xrp = self.env["res.currency"].create(
            {"name": "XRP", "symbol": "XP$", "rounding": 0.01}
        )
        self.env["res.currency.rate"].create(
            {
                "name": "2026-04-21",
                "currency_id": self.currency_xrp.id,
                "company_id": self.company.id,
                "rate": 0.2,
            }
        )
        self.env["treasury.movement.service"].post_movement(
            self.env["treasury.movement.service"].create_movement(
                {
                    "name": "Movimento Relatorio",
                    "date": "2026-04-21",
                    "company_id": self.company.id,
                    "type": "entrada",
                    "amount": 150.0,
                    "currency_id": self.company.currency_id.id,
                    "account_id": self.account.id,
                    "portador_id": self.portador.id,
                    "payment_method_id": self.payment_method.id,
                }
            )
        )
        self.receivable_title = self.env["receivable.service"].open_title(
            {
                "name": "REC-REP-1",
                "partner_id": self.partner_customer.id,
                "company_id": self.company.id,
                "amount_total": 200.0,
            }
        )
        self.receivable_installment = self.env["receivable.service"].generate_installments(
            self.receivable_title,
            [{"due_date": "2026-04-10", "amount": 200.0}],
        )
        self.payable_title = self.env["payable.service"].open_title(
            {
                "name": "PAY-REP-1",
                "partner_id": self.partner_vendor.id,
                "company_id": self.company.id,
                "amount_total": 300.0,
            }
        )
        self.env["payable.service"].generate_installments(
            self.payable_title,
            [{"due_date": "2026-04-25", "amount": 300.0}],
        )
        self.schedule = self.env["payable.service"].schedule_payment(
            {
                "name": "Agenda Relatorio",
                "payment_date": "2026-04-22",
                "company_id": self.company.id,
                "partner_id": self.partner_vendor.id,
                "state": "scheduled",
            }
        )
        self.helper = self.env["financial.report.helper"].create(
            {
                "company_id": self.company.id,
                "account_id": self.account.id,
                "portador_id": self.portador.id,
                "partner_id": self.partner_customer.id,
                "currency_id": self.company.currency_id.id,
                "date_from": "2026-04-01",
                "date_to": "2026-04-30",
                "reference_date": "2026-04-21",
            }
        )

    def test_open_account_statement(self):
        action = self.helper.action_open_treasury_statement_by_account()
        self.assertEqual(action["res_model"], "treasury.movement")
        self.assertIn(("account_id", "=", self.account.id), action["domain"])
        self.assertIn(("currency_id", "=", self.company.currency_id.id), action["domain"])

    def test_open_receivable_position(self):
        action = self.helper.action_open_receivable_open_position()
        self.assertEqual(action["res_model"], "receivable.title")
        self.assertIn(("partner_id", "=", self.partner_customer.id), action["domain"])

    def test_open_payable_position(self):
        self.helper.partner_id = self.partner_vendor
        action = self.helper.action_open_payable_open_position()
        self.assertEqual(action["res_model"], "payable.title")
        self.assertIn(("partner_id", "=", self.partner_vendor.id), action["domain"])

    def test_reports_do_not_modify_records(self):
        receivable_before = (self.receivable_title.amount_open, self.receivable_title.state)
        payable_before = (self.payable_title.amount_open, self.payable_title.state)
        schedule_before = self.schedule.state
        self.helper.action_open_treasury_statement_by_account()
        self.helper.action_open_receivable_open_position()
        self.helper.partner_id = self.partner_vendor
        self.helper.action_open_payable_open_position()
        self.receivable_title.invalidate_recordset()
        self.payable_title.invalidate_recordset()
        self.schedule.invalidate_recordset()
        self.assertEqual((self.receivable_title.amount_open, self.receivable_title.state), receivable_before)
        self.assertEqual((self.payable_title.amount_open, self.payable_title.state), payable_before)
        self.assertEqual(self.schedule.state, schedule_before)

    def test_open_balance_by_account_groups_by_currency(self):
        action = self.helper.action_open_balance_by_account()
        self.assertEqual(action["res_model"], "treasury.movement")
        self.assertEqual(
            action["context"]["group_by"],
            ["account_id", "currency_id"],
        )
