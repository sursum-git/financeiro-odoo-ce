from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceivableTitle(models.Model):
    _name = "receivable.title"
    _description = "Receivable Title"
    _order = "issue_date desc, id desc"

    name = fields.Char(required=True, index=True)
    partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    issue_date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    origin_reference = fields.Char(index=True)
    amount_total = fields.Monetary(required=True, currency_field="currency_id")
    amount_open = fields.Monetary(
        compute="_compute_amounts",
        store=True,
        currency_field="currency_id",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("open", "Open"),
            ("partial", "Partial"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
            ("renegotiated", "Renegotiated"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    installment_ids = fields.One2many(
        "receivable.installment",
        "title_id",
        string="Installments",
    )
    settlement_line_ids = fields.One2many(
        "receivable.settlement.line",
        "title_id",
        string="Settlement Lines",
    )

    def action_open_renegotiation_wizard(self):
        self.ensure_one()
        if self.state not in {"open", "partial"} or self.amount_open <= 0:
            raise ValidationError("Only open titles with outstanding balance can be renegotiated.")
        return {
            "type": "ir.actions.act_window",
            "name": "Renegotiate Title",
            "res_model": "receivable.renegotiation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_source_title_id": self.id,
            },
        }

    @api.depends("installment_ids.amount_open", "installment_ids.state")
    def _compute_amounts(self):
        for title in self:
            installments = title.installment_ids
            if installments:
                title.amount_open = sum(installments.mapped("amount_open"))
            else:
                title.amount_open = title.amount_total

            if title.state in {"cancelled", "renegotiated"}:
                continue
            if not installments:
                title.state = "draft"
            elif all(inst.state == "paid" for inst in installments):
                title.state = "paid"
            elif all(inst.state in {"open", "paid"} for inst in installments) and any(
                inst.state == "paid" for inst in installments
            ):
                title.state = "partial"
            elif any(inst.state in {"open", "partial"} for inst in installments):
                title.state = "open"
