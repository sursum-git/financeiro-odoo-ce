from odoo import fields, models


class ReceivableSettlementWithholding(models.Model):
    _name = "receivable.settlement.withholding"
    _description = "Receivable Settlement Withholding"
    _order = "id"

    settlement_id = fields.Many2one(
        "receivable.settlement",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_withholding_line_id = fields.Many2one(
        "res.partner.withholding.line",
        required=True,
        ondelete="restrict",
        index=True,
    )
    company_id = fields.Many2one(
        related="settlement_id.company_id",
        store=True,
        readonly=True,
    )
    withholding_code_id = fields.Many2one(
        related="partner_withholding_line_id.withholding_code_id",
        store=True,
        readonly=True,
    )
    supplier_contact_id = fields.Many2one(
        related="partner_withholding_line_id.supplier_contact_id",
        store=True,
        readonly=True,
    )
    retention_percent = fields.Float(
        related="partner_withholding_line_id.retention_percent",
        store=True,
        readonly=True,
    )
    base_amount = fields.Monetary(
        required=True,
        currency_field="currency_id",
        readonly=True,
    )
    previously_withheld_amount = fields.Monetary(
        required=True,
        currency_field="currency_id",
        readonly=True,
    )
    amount = fields.Monetary(
        required=True,
        currency_field="currency_id",
        readonly=True,
    )
    currency_id = fields.Many2one(
        related="settlement_id.currency_id",
        store=True,
        readonly=True,
    )
