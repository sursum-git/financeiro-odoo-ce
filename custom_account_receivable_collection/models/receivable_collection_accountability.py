from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceivableCollectionAccountability(models.Model):
    _name = "receivable.collection.accountability"
    _description = "Receivable Collection Accountability"
    _order = "date desc, id desc"

    name = fields.Char(required=True, index=True)
    agent_id = fields.Many2one(
        "receivable.collection.agent",
        required=True,
        ondelete="restrict",
        index=True,
    )
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    amount = fields.Monetary(
        compute="_compute_amount",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related="agent_id.company_id",
        store=True,
        readonly=True,
    )
    target_account_id = fields.Many2one("treasury.account", ondelete="restrict")
    target_cash_box_id = fields.Many2one("treasury.cash.box", ondelete="restrict")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    settlement_ids = fields.Many2many(
        "receivable.settlement",
        "receivable_collection_accountability_settlement_rel",
        "accountability_id",
        "settlement_id",
        string="Settlements",
    )
    source_portador_id = fields.Many2one(
        related="agent_id.portador_id",
        store=True,
        readonly=True,
    )
    out_movement_id = fields.Many2one("treasury.movement", ondelete="restrict")
    in_movement_id = fields.Many2one("treasury.movement", ondelete="restrict")
    assignment_ids = fields.One2many(
        "receivable.collection.assignment",
        "accountability_id",
        string="Assignments",
    )

    @api.depends("settlement_ids.line_ids.total_amount")
    def _compute_amount(self):
        for accountability in self:
            accountability.amount = sum(accountability.settlement_ids.mapped("line_ids.total_amount"))

    @api.constrains("target_account_id", "target_cash_box_id")
    def _check_target(self):
        for accountability in self:
            if not accountability.target_account_id and not accountability.target_cash_box_id:
                raise ValidationError("Accountability requires a target account or a target cash box.")
            if accountability.target_account_id and accountability.target_cash_box_id:
                raise ValidationError("Choose either a target account or a target cash box.")

    @api.constrains("settlement_ids", "agent_id")
    def _check_settlement_traceability(self):
        for accountability in self:
            if not accountability.settlement_ids:
                raise ValidationError("Accountability requires at least one tracked settlement.")
            if accountability.amount <= 0:
                raise ValidationError("Accountability amount must be positive.")
            done_accountabilities = self.search(
                [
                    ("id", "!=", accountability.id),
                    ("state", "=", "done"),
                    ("settlement_ids", "in", accountability.settlement_ids.ids),
                ]
            )
            if done_accountabilities:
                raise ValidationError("A settlement cannot be accounted for more than once.")
            for settlement in accountability.settlement_ids:
                if settlement.state != "applied":
                    raise ValidationError("Only applied settlements can be accounted for.")
                if settlement.portador_id != accountability.agent_id.portador_id:
                    raise ValidationError("All settlements must belong to the agent portador.")
