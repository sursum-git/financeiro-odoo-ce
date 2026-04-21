from odoo import api, fields, models


class PayableTitle(models.Model):
    _name = "payable.title"
    _description = "Payable Title"
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
        "payable.installment",
        "title_id",
        string="Installments",
    )

    @api.depends("installment_ids.amount_open", "installment_ids.state")
    def _compute_amounts(self):
        for title in self:
            installments = title.installment_ids
            title.amount_open = sum(installments.mapped("amount_open")) if installments else title.amount_total
            if title.state == "cancelled":
                continue
            if not installments:
                title.state = "draft"
            elif all(inst.state == "paid" for inst in installments):
                title.state = "paid"
            elif any(inst.state == "partial" for inst in installments) or (
                any(inst.state == "paid" for inst in installments)
                and any(inst.state in {"open", "partial"} for inst in installments)
            ):
                title.state = "partial"
            elif any(inst.state == "open" for inst in installments):
                title.state = "open"
