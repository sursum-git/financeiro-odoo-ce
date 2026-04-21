from odoo import fields, models


class FinancialReportHelper(models.TransientModel):
    _name = "financial.report.helper"
    _description = "Financial Report Helper"

    name = fields.Char(default="Financial Report")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    date_from = fields.Date()
    date_to = fields.Date(default=fields.Date.context_today)
    reference_date = fields.Date(default=fields.Date.context_today)
    account_id = fields.Many2one("treasury.account", ondelete="restrict")
    portador_id = fields.Many2one("financial.portador", ondelete="restrict")
    partner_id = fields.Many2one("res.partner", ondelete="restrict")
    agent_id = fields.Many2one("receivable.collection.agent", ondelete="restrict")
    route_id = fields.Many2one("receivable.collection.route", ondelete="restrict")

    def _append_date_domain(self, domain, field_name="date"):
        self.ensure_one()
        if self.date_from:
            domain.append((field_name, ">=", self.date_from))
        if self.date_to:
            domain.append((field_name, "<=", self.date_to))
        return domain

    def _readonly_action(self, name, res_model, domain, view_mode="list,form", context=None):
        action_context = {"create": False, "edit": False, "delete": False}
        if context:
            action_context.update(context)
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": res_model,
            "view_mode": view_mode,
            "target": "current",
            "domain": domain,
            "context": action_context,
        }

    def action_open_treasury_statement_by_account(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id), ("account_id", "=", self.account_id.id)]
        domain = self._append_date_domain(domain)
        return self._readonly_action("Extrato por Conta", "treasury.movement", domain)

    def action_open_treasury_statement_by_portador(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id), ("portador_id", "=", self.portador_id.id)]
        domain = self._append_date_domain(domain)
        return self._readonly_action("Extrato por Portador", "treasury.movement", domain)

    def action_open_balance_by_account(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id), ("state", "=", "posted")]
        if self.account_id:
            domain.append(("account_id", "=", self.account_id.id))
        domain = self._append_date_domain(domain)
        return self._readonly_action(
            "Saldo por Conta",
            "treasury.movement",
            domain,
            view_mode="list,pivot,graph,form",
            context={"group_by": ["account_id"], "pivot_measures": ["signed_amount"]},
        )

    def action_open_balance_by_portador(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id), ("state", "=", "posted")]
        if self.portador_id:
            domain.append(("portador_id", "=", self.portador_id.id))
        domain = self._append_date_domain(domain)
        return self._readonly_action(
            "Saldo por Portador",
            "treasury.movement",
            domain,
            view_mode="list,pivot,graph,form",
            context={"group_by": ["portador_id"], "pivot_measures": ["signed_amount"]},
        )

    def action_open_cash_flow_realized(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id), ("state", "=", "posted")]
        domain = self._append_date_domain(domain)
        return self._readonly_action(
            "Fluxo de Caixa Realizado",
            "treasury.movement",
            domain,
            view_mode="list,pivot,graph,form",
            context={"group_by": ["date", "type"], "pivot_measures": ["signed_amount"]},
        )

    def action_open_receivable_open_position(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id), ("state", "in", ["open", "partial"])]
        if self.partner_id:
            domain.append(("partner_id", "=", self.partner_id.id))
        return self._readonly_action(
            "Posicao em Aberto a Receber",
            "receivable.title",
            domain,
            view_mode="list,pivot,graph,form",
            context={"group_by": ["partner_id"], "pivot_measures": ["amount_open"]},
        )

    def action_open_receivable_aging(self):
        self.ensure_one()
        domain = [
            ("title_id.company_id", "=", self.company_id.id),
            ("state", "in", ["open", "partial"]),
            ("due_date", "<", self.reference_date),
        ]
        if self.partner_id:
            domain.append(("title_id.partner_id", "=", self.partner_id.id))
        return self._readonly_action(
            "Aging de Vencidos",
            "receivable.installment",
            domain,
            view_mode="list,pivot,graph,form",
            context={"group_by": ["title_id", "due_date"], "pivot_measures": ["amount_open"]},
        )

    def action_open_receivable_settlement_history(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id)]
        if self.partner_id:
            domain.append(("partner_id", "=", self.partner_id.id))
        domain = self._append_date_domain(domain)
        return self._readonly_action("Historico de Liquidacoes", "receivable.settlement", domain)

    def action_open_payable_open_position(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id), ("state", "in", ["open", "partial"])]
        if self.partner_id:
            domain.append(("partner_id", "=", self.partner_id.id))
        return self._readonly_action(
            "Posicao em Aberto a Pagar",
            "payable.title",
            domain,
            view_mode="list,pivot,graph,form",
            context={"group_by": ["partner_id"], "pivot_measures": ["amount_open"]},
        )

    def action_open_payment_schedule(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id), ("state", "=", "scheduled")]
        if self.partner_id:
            domain.append(("partner_id", "=", self.partner_id.id))
        domain = self._append_date_domain(domain, field_name="payment_date")
        return self._readonly_action("Agenda de Pagamentos", "payable.schedule", domain)

    def action_open_payment_history(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id)]
        if self.partner_id:
            domain.append(("partner_id", "=", self.partner_id.id))
        domain = self._append_date_domain(domain)
        return self._readonly_action("Historico de Pagamentos", "payable.payment", domain)

    def action_open_reconciled_items(self):
        self.ensure_one()
        domain = [("reconciliation_id.company_id", "=", self.company_id.id), ("status", "in", ["matched", "adjusted"])]
        return self._readonly_action("Itens Conciliados", "treasury.reconciliation.line", domain)

    def action_open_divergent_items(self):
        self.ensure_one()
        domain = [("reconciliation_id.company_id", "=", self.company_id.id), ("status", "=", "divergent")]
        return self._readonly_action("Itens Divergentes", "treasury.reconciliation.line", domain)

    def action_open_collection_accountability(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id)]
        if self.agent_id:
            domain.append(("agent_id", "=", self.agent_id.id))
        domain = self._append_date_domain(domain)
        return self._readonly_action("Prestacao de Contas por Cobrador", "receivable.collection.accountability", domain)

    def action_open_titles_in_route(self):
        self.ensure_one()
        domain = [("company_id", "=", self.company_id.id), ("state", "in", ["assigned", "collected"])]
        if self.route_id:
            domain.append(("route_id", "=", self.route_id.id))
        if self.agent_id:
            domain.append(("agent_id", "=", self.agent_id.id))
        return self._readonly_action("Titulos em Rota", "receivable.collection.assignment", domain)
