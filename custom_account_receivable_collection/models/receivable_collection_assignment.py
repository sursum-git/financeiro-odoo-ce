from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceivableCollectionAssignment(models.Model):
    _name = "receivable.collection.assignment"
    _description = "Receivable Collection Assignment"
    _order = "id desc"

    route_id = fields.Many2one(
        "receivable.collection.route",
        required=True,
        ondelete="restrict",
        index=True,
    )
    agent_id = fields.Many2one(
        "receivable.collection.agent",
        required=True,
        ondelete="restrict",
        index=True,
    )
    partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict", index=True)
    title_id = fields.Many2one("receivable.title", required=True, ondelete="restrict", index=True)
    installment_id = fields.Many2one(
        "receivable.installment",
        required=True,
        ondelete="restrict",
        index=True,
    )
    state = fields.Selection(
        [
            ("assigned", "Assigned"),
            ("collected", "Collected"),
            ("accounted", "Accounted"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="assigned",
        index=True,
    )
    notes = fields.Text()
    company_id = fields.Many2one(
        related="route_id.company_id",
        store=True,
        readonly=True,
    )
    collection_date = fields.Date(index=True)
    settlement_id = fields.Many2one("receivable.settlement", ondelete="restrict", index=True)
    accountability_id = fields.Many2one(
        "receivable.collection.accountability",
        ondelete="restrict",
        index=True,
    )
    currency_id = fields.Many2one(
        related="installment_id.currency_id",
        store=True,
        readonly=True,
    )
    amount_collected = fields.Monetary(
        compute="_compute_amount_collected",
        currency_field="currency_id",
    )

    _receivable_collection_assignment_installment_agent_route_uniq = models.Constraint(
        "unique(route_id, agent_id, installment_id)",
        "An installment can only be assigned once per route and agent.",
    )

    @api.constrains("title_id", "installment_id", "partner_id")
    def _check_title_links(self):
        for assignment in self:
            if assignment.installment_id.title_id != assignment.title_id:
                raise ValidationError("The installment must belong to the selected title.")
            if assignment.title_id.partner_id != assignment.partner_id:
                raise ValidationError("The partner must match the receivable title partner.")

    @api.constrains("route_id", "agent_id", "title_id")
    def _check_company_consistency(self):
        for assignment in self:
            if assignment.agent_id.company_id != assignment.route_id.company_id:
                raise ValidationError("The route and agent must belong to the same company.")
            if assignment.title_id.company_id != assignment.route_id.company_id:
                raise ValidationError("The title must belong to the same company as the route.")

    @api.depends("settlement_id.line_ids.total_amount")
    def _compute_amount_collected(self):
        for assignment in self:
            assignment.amount_collected = sum(assignment.settlement_id.line_ids.mapped("total_amount"))
