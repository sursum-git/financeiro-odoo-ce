from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryReconciliationLine(models.Model):
    _name = "treasury.reconciliation.line"
    _description = "Treasury Reconciliation Line"
    _order = "id"

    MSG_LINHA_UNICA = "Uma linha de extrato so pode estar vinculada a uma linha de conciliacao."
    MSG_LINHA_JA_CONCILIADA = "Esta linha de extrato ja esta conciliada."
    MSG_MOEDA_DIVERGENTE = "A conciliacao exige extrato e movimento na mesma moeda."
    MSG_MOVIMENTO_OBRIGATORIO = "Informe um movimento para concluir a conciliacao manual."
    MSG_STATUS_ALTERACAO_INVALIDO = "Somente linhas pendentes ou divergentes podem ser processadas."

    reconciliation_id = fields.Many2one(
        "treasury.reconciliation",
        required=True,
        ondelete="cascade",
        index=True,
    )
    statement_line_id = fields.Many2one(
        "treasury.bank.statement.line",
        required=True,
        ondelete="restrict",
        index=True,
    )
    movement_id = fields.Many2one(
        "treasury.movement",
        ondelete="restrict",
        index=True,
    )
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("matched", "Matched"),
            ("divergent", "Divergent"),
            ("adjusted", "Adjusted"),
        ],
        required=True,
        default="pending",
        index=True,
    )
    difference_amount = fields.Monetary(
        compute="_compute_difference_amount",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="statement_line_id.currency_id",
        string="Moeda do Extrato",
        store=True,
        readonly=True,
    )
    movement_currency_id = fields.Many2one(
        related="movement_id.currency_id",
        string="Moeda do Movimento",
        store=True,
        readonly=True,
    )
    notes = fields.Text()
    adjustment_movement_id = fields.Many2one("treasury.movement", ondelete="restrict")

    _treasury_reconciliation_statement_line_uniq = models.Constraint(
        "unique(statement_line_id)",
        MSG_LINHA_UNICA,
    )

    @api.depends("statement_line_id.amount", "movement_id.signed_amount")
    def _compute_difference_amount(self):
        for line in self:
            movement_amount = abs(line.movement_id.signed_amount) if line.movement_id else 0.0
            line.difference_amount = line.statement_line_id.amount - movement_amount

    @api.constrains("statement_line_id")
    def _check_statement_line_not_already_reconciled(self):
        for line in self:
            if line.statement_line_id.is_reconciled and line.status != "matched":
                raise ValidationError(self.MSG_LINHA_JA_CONCILIADA)

    @api.constrains("statement_line_id", "movement_id")
    def _check_currency_consistency(self):
        for line in self.filtered(lambda rec: rec.statement_line_id and rec.movement_id):
            if line.statement_line_id.currency_id != line.movement_id.currency_id:
                raise ValidationError(self.MSG_MOEDA_DIVERGENTE)

    def action_match_selected(self):
        for line in self:
            if line.status not in {"pending", "divergent"}:
                raise UserError(self.MSG_STATUS_ALTERACAO_INVALIDO)
            if not line.movement_id:
                raise UserError(self.MSG_MOVIMENTO_OBRIGATORIO)
            self.env["treasury.reconciliation.service"].match_line(
                line.statement_line_id,
                line.movement_id,
                reconciliation=line.reconciliation_id,
            )
        return True

    def action_create_adjustment(self):
        for line in self:
            if line.status not in {"pending", "divergent"}:
                raise UserError(self.MSG_STATUS_ALTERACAO_INVALIDO)
            self.env["treasury.reconciliation.service"].create_adjustment(
                line.reconciliation_id,
                line.statement_line_id,
                movement=line.movement_id,
                notes=line.notes,
            )
        return True

    def action_mark_divergent(self):
        for line in self:
            if line.status not in {"pending", "divergent"}:
                raise UserError(self.MSG_STATUS_ALTERACAO_INVALIDO)
            line.status = "divergent"
        return True
