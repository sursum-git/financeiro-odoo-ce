from odoo import fields, models
from odoo.exceptions import UserError


class TreasuryReconciliation(models.Model):
    _name = "treasury.reconciliation"
    _description = "Treasury Reconciliation"
    _order = "date_end desc, id desc"

    MSG_CONCILIACAO_FINALIZADA = "Conciliacoes finalizadas nao podem receber novos processamentos."

    name = fields.Char(required=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    bank_account_id = fields.Many2one(
        "treasury.bank.account",
        required=True,
        ondelete="restrict",
        index=True,
    )
    date_start = fields.Date(required=True, index=True)
    date_end = fields.Date(required=True, index=True)
    state = fields.Selection(
        [
            ("draft", "Rascunho"),
            ("in_progress", "Em Andamento"),
            ("done", "Concluido"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    line_ids = fields.One2many(
        "treasury.reconciliation.line",
        "reconciliation_id",
        string="Linhas de Conciliacao",
    )

    def _get_statement_line_domain(self):
        self.ensure_one()
        return [
            ("import_id.bank_account_id", "=", self.bank_account_id.id),
            ("date", ">=", self.date_start),
            ("date", "<=", self.date_end),
        ]

    def action_suggest_matches(self):
        line_model = self.env["treasury.reconciliation.line"]
        service = self.env["treasury.reconciliation.service"]
        for reconciliation in self:
            if reconciliation.state == "done":
                raise UserError(self.MSG_CONCILIACAO_FINALIZADA)
            statement_lines = self.env["treasury.bank.statement.line"].search(
                reconciliation._get_statement_line_domain()
            )
            existing_statement_ids = set(reconciliation.line_ids.mapped("statement_line_id").ids)
            pending_vals = []
            for statement_line in statement_lines.filtered(lambda line: not line.is_reconciled):
                if statement_line.id in existing_statement_ids:
                    continue
                pending_vals.append(
                    {
                        "reconciliation_id": reconciliation.id,
                        "statement_line_id": statement_line.id,
                        "status": "pending",
                    }
                )
            for vals in pending_vals:
                line_model.create(vals)
            for statement_line, movement in service.suggest_matches(reconciliation):
                service.match_line(statement_line, movement, reconciliation=reconciliation)
            if reconciliation.state == "draft":
                reconciliation.state = "in_progress"
        return True

    def action_finalize(self):
        for reconciliation in self:
            self.env["treasury.reconciliation.service"].finalize_reconciliation(reconciliation)
        return True
