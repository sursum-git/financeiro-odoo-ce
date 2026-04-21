from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FinancialTitleSpecies(models.Model):
    _name = "financial.title.species"
    _description = "Financial Title Species"
    _order = "name"

    MSG_CODIGO_UNICO = "O codigo da especie de titulo deve ser unico."
    MSG_CODIGO_OBRIGATORIO = "O codigo da especie de titulo nao pode ficar vazio."

    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    kind = fields.Selection(
        [
            ("normal", "Normal"),
            ("check", "Third-Party Check"),
            ("bank_slip", "Bank Slip"),
            ("promissory_note", "Promissory Note"),
            ("customer_advance", "Customer Advance"),
            ("supplier_advance", "Supplier Advance"),
            ("other", "Other"),
        ],
        required=True,
        default="normal",
        index=True,
    )
    notes = fields.Text()
    active = fields.Boolean(default=True)

    _financial_title_species_code_uniq = models.Constraint(
        "unique(code)",
        MSG_CODIGO_UNICO,
    )

    @api.constrains("code")
    def _check_code(self):
        for record in self:
            if not record.code.strip():
                raise ValidationError(self.MSG_CODIGO_OBRIGATORIO)


class FinancialCheckReturnReason(models.Model):
    _name = "financial.check.return.reason"
    _description = "Financial Check Return Reason"
    _order = "code"

    MSG_CODIGO_UNICO = "O codigo do motivo de devolucao de cheque deve ser unico."
    MSG_CODIGO_OBRIGATORIO = "O codigo do motivo de devolucao de cheque nao pode ficar vazio."

    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    description = fields.Text()
    is_definitive = fields.Boolean(
        string="Definitive Return",
        help="When enabled, the returned check cannot be represented again.",
    )
    active = fields.Boolean(default=True)

    _financial_check_return_reason_code_uniq = models.Constraint(
        "unique(code)",
        MSG_CODIGO_UNICO,
    )

    @api.constrains("code")
    def _check_code(self):
        for record in self:
            if not record.code.strip():
                raise ValidationError(self.MSG_CODIGO_OBRIGATORIO)
