from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FinancialWithholdingCode(models.Model):
    _name = "financial.withholding.code"
    _description = "Financial Withholding Code"
    _order = "code, name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    description = fields.Text()
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
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
