from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FinancialWithholdingCode(models.Model):
    _name = "financial.withholding.code"
    _description = "Financial Withholding Code"
    _order = "code, name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    description = fields.Text()
    due_date = fields.Date(string="Due Date")
    minimum_retention_amount = fields.Monetary(
        string="Minimum Retention Amount",
        currency_field="currency_id",
        default=0.0,
    )
    minimum_payment_amount = fields.Monetary(
        string="Minimum Payment Amount",
        currency_field="currency_id",
        default=0.0,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )
    active = fields.Boolean(default=True)
    partner_line_ids = fields.One2many(
        "res.partner.withholding.line",
        "withholding_code_id",
        string="Partner Lines",
    )

    _financial_withholding_code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        "The withholding code must be unique per company.",
    )

    @api.constrains("code")
    def _check_code(self):
        for record in self:
            if not record.code.strip():
                raise ValidationError("The withholding code cannot be empty.")

    @api.constrains("minimum_retention_amount", "minimum_payment_amount")
    def _check_minimum_amounts(self):
        for record in self:
            if record.minimum_retention_amount < 0:
                raise ValidationError("The minimum retention amount cannot be negative.")
            if record.minimum_payment_amount < 0:
                raise ValidationError("The minimum payment amount cannot be negative.")


class ResPartnerWithholdingLine(models.Model):
    _name = "res.partner.withholding.line"
    _description = "Partner Withholding Line"
    _order = "company_id, withholding_code_id, id"

    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    withholding_code_id = fields.Many2one(
        "financial.withholding.code",
        required=True,
        ondelete="restrict",
        index=True,
    )
    retention_percent = fields.Float(required=True, digits=(16, 4))
    supplier_contact_id = fields.Many2one(
        "res.partner",
        required=True,
        ondelete="restrict",
        index=True,
    )
    notes = fields.Char()

    _res_partner_withholding_line_uniq = models.Constraint(
        "unique(partner_id, company_id, withholding_code_id)",
        "A contact can only have one line per withholding code and company.",
    )

    @api.constrains("retention_percent")
    def _check_retention_percent(self):
        for line in self:
            if line.retention_percent < 0 or line.retention_percent > 100:
                raise ValidationError("Retention percent must be between 0 and 100.")

    @api.constrains("company_id", "withholding_code_id")
    def _check_code_company(self):
        for line in self:
            if line.withholding_code_id.company_id != line.company_id:
                raise ValidationError("The withholding code must belong to the same company.")
