from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryCashSession(models.Model):
    _name = "treasury.cash.session"
    _description = "Treasury Cash Session"
    _order = "opened_at desc, id desc"

    name = fields.Char(required=True, index=True)
    cash_box_id = fields.Many2one(
        "treasury.cash.box",
        required=True,
        ondelete="restrict",
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
        ondelete="restrict",
        index=True,
    )
    opened_at = fields.Datetime()
    opening_amount = fields.Monetary(required=True, currency_field="currency_id", default=0.0)
    closed_at = fields.Datetime()
    closing_amount_informed = fields.Monetary(currency_field="currency_id")
    closing_amount_computed = fields.Monetary(
        compute="_compute_closing_amount_computed",
        store=True,
        currency_field="currency_id",
    )
    difference_amount = fields.Monetary(
        compute="_compute_difference_amount",
        store=True,
        currency_field="currency_id",
    )
    difference_reason = fields.Char()
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("open", "Open"),
            ("closed", "Closed"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    line_ids = fields.One2many(
        "treasury.cash.session.line",
        "session_id",
        string="Session Movements",
    )

    @api.depends("opening_amount", "line_ids.movement_id.state", "line_ids.movement_id.signed_amount")
    def _compute_closing_amount_computed(self):
        for session in self:
            posted_lines = session.line_ids.filtered(lambda line: line.movement_id.state == "posted")
            session.closing_amount_computed = session.opening_amount + sum(
                posted_lines.mapped("movement_id.signed_amount")
            )

    @api.depends("closing_amount_informed", "closing_amount_computed")
    def _compute_difference_amount(self):
        for session in self:
            session.difference_amount = (
                (session.closing_amount_informed or 0.0) - session.closing_amount_computed
            )

    @api.constrains("cash_box_id", "state")
    def _check_single_open_session(self):
        for session in self.filtered(lambda rec: rec.state == "open"):
            domain = [
                ("id", "!=", session.id),
                ("cash_box_id", "=", session.cash_box_id.id),
                ("state", "=", "open"),
            ]
            if self.search_count(domain):
                raise ValidationError("There is already an open session for this cash box.")

    @api.constrains("cash_box_id", "company_id")
    def _check_company_consistency(self):
        for session in self:
            if session.cash_box_id.company_id != session.company_id:
                raise ValidationError("The cash box must belong to the same company.")

    def action_open(self):
        for session in self:
            if session.state != "draft":
                raise UserError("Only draft sessions can be opened.")
            session.write(
                {
                    "state": "open",
                    "opened_at": fields.Datetime.now(),
                }
            )

    def action_close(self):
        for session in self:
            if session.state != "open":
                raise UserError("Only open sessions can be closed.")
            parameter = self.env["financial.parameter"].search(
                [("company_id", "=", session.company_id.id)],
                limit=1,
            )
            if (
                parameter.require_cash_difference_reason
                and session.difference_amount
                and not session.difference_reason
            ):
                raise ValidationError("A reason is required for cash differences.")
            session.write(
                {
                    "state": "closed",
                    "closed_at": fields.Datetime.now(),
                }
            )

    def action_cancel(self):
        for session in self:
            if session.state == "closed":
                raise UserError("Closed sessions cannot be cancelled.")
            session.state = "cancelled"
