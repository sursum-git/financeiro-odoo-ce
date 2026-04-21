from odoo.tests.common import TransactionCase


class TestReceivableCollection(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.partner = self.env["res.partner"].create({"name": "Cliente Cobranca"})
        self.agent_partner = self.env["res.partner"].create({"name": "Cobrador Externo"})
        self.agent_portador = self.env["financial.portador"].create(
            {
                "name": "Portador Cobrador",
                "code": "COB001",
                "type": "cobrador",
                "company_id": self.company.id,
            }
        )
        self.cash_portador = self.env["financial.portador"].create(
            {
                "name": "Caixa Central",
                "code": "CX001",
                "type": "caixa",
                "company_id": self.company.id,
            }
        )
        self.payment_method = self.env["financial.payment.method"].create(
            {
                "name": "Dinheiro",
                "code": "DIN",
                "company_id": self.company.id,
            }
        )
        self.target_account = self.env["treasury.account"].create(
            {
                "name": "Conta Corrente",
                "code": "CC001",
                "company_id": self.company.id,
            }
        )
        self.cash_box = self.env["treasury.cash.box"].create(
            {
                "name": "Caixa Loja",
                "code": "CXLOJA",
                "company_id": self.company.id,
                "portador_id": self.cash_portador.id,
            }
        )
        self.agent = self.env["receivable.collection.agent"].create(
            {
                "name": "Cobrador 1",
                "partner_id": self.agent_partner.id,
                "portador_id": self.agent_portador.id,
                "company_id": self.company.id,
            }
        )
        self.route = self.env["receivable.collection.route"].create(
            {
                "name": "Roteiro Centro",
                "company_id": self.company.id,
            }
        )
        self.title = self.env["receivable.service"].open_title(
            {
                "name": "TIT-001",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "amount_total": 100.0,
            }
        )
        self.installment = self.env["receivable.service"].generate_installments(
            self.title,
            [{"due_date": "2026-04-20", "amount": 100.0}],
        )
        self.collection_service = self.env["receivable.collection.service"]
        self.movement_service = self.env["treasury.movement.service"]

    def test_create_collection_agent_with_portador(self):
        self.assertEqual(self.agent.portador_id.type, "cobrador")

    def test_assign_title_to_agent(self):
        assignment = self.collection_service.assign_titles_to_agent(
            self.route,
            self.agent,
            self.installment,
        )
        self.assertEqual(len(assignment), 1)
        self.assertEqual(assignment.partner_id, self.partner)
        self.assertEqual(assignment.state, "assigned")

    def test_assign_title_via_wizard(self):
        wizard = self.env["receivable.collection.assign.wizard"].with_context(
            default_route_id=self.route.id
        ).create(
            {
                "route_id": self.route.id,
                "agent_id": self.agent.id,
                "installment_ids": [(6, 0, self.installment.ids)],
            }
        )
        wizard.action_confirm()
        assignment = self.env["receivable.collection.assignment"].search(
            [("route_id", "=", self.route.id), ("installment_id", "=", self.installment.id)],
            limit=1,
        )
        self.assertTrue(assignment)
        self.assertEqual(assignment.state, "assigned")

    def test_register_field_collection(self):
        assignment = self.collection_service.assign_titles_to_agent(
            self.route,
            self.agent,
            self.installment,
        )
        settlement = self.collection_service.register_field_collection(
            assignment,
            self.payment_method,
        )
        self.assertEqual(settlement.state, "applied")
        self.assertEqual(settlement.portador_id, self.agent_portador)
        self.assertEqual(assignment.state, "collected")

    def test_register_field_collection_via_wizard(self):
        assignment = self.collection_service.assign_titles_to_agent(
            self.route,
            self.agent,
            self.installment,
        )
        wizard = self.env["receivable.collection.field.wizard"].create(
            {
                "assignment_id": assignment.id,
                "payment_method_id": self.payment_method.id,
                "principal_amount": 100.0,
            }
        )
        wizard.action_confirm()
        self.assertEqual(assignment.state, "collected")
        self.assertTrue(assignment.settlement_id)

    def test_execute_accountability(self):
        assignment = self.collection_service.assign_titles_to_agent(
            self.route,
            self.agent,
            self.installment,
        )
        settlement = self.collection_service.register_field_collection(
            assignment,
            self.payment_method,
        )
        accountability = self.collection_service.create_agent_accountability(
            self.agent,
            settlement,
            target_cash_box=self.cash_box,
        )
        self.assertEqual(accountability.state, "done")
        self.assertEqual(accountability.amount, 100.0)
        self.assertEqual(assignment.state, "accounted")
        self.assertTrue(accountability.out_movement_id)
        self.assertTrue(accountability.in_movement_id)

    def test_confirm_accountability_via_model_action(self):
        assignment = self.collection_service.assign_titles_to_agent(
            self.route,
            self.agent,
            self.installment,
        )
        settlement = self.collection_service.register_field_collection(
            assignment,
            self.payment_method,
        )
        accountability = self.env["receivable.collection.accountability"].create(
            {
                "name": "Prestacao via Botao",
                "agent_id": self.agent.id,
                "date": "2026-04-21",
                "target_cash_box_id": self.cash_box.id,
                "settlement_ids": [(6, 0, settlement.ids)],
            }
        )
        accountability.action_confirm()
        self.assertEqual(accountability.state, "done")
        self.assertEqual(assignment.state, "accounted")

    def test_transfer_agent_portador_balance(self):
        assignment = self.collection_service.assign_titles_to_agent(
            self.route,
            self.agent,
            self.installment,
        )
        settlement = self.collection_service.register_field_collection(
            assignment,
            self.payment_method,
        )
        self.assertEqual(
            self.movement_service.compute_balance(portador=self.agent_portador, company=self.company),
            100.0,
        )
        self.collection_service.create_agent_accountability(
            self.agent,
            settlement,
            target_account=self.target_account,
        )
        self.assertEqual(
            self.movement_service.compute_balance(portador=self.agent_portador, company=self.company),
            0.0,
        )
