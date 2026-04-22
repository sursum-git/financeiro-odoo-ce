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
            ("check", "Cheque de Terceiros"),
            ("bank_slip", "Boleto"),
            ("promissory_note", "Nota Promissoria"),
            ("customer_advance", "Adiantamento de Cliente"),
            ("supplier_advance", "Adiantamento de Fornecedor"),
            ("other", "Outro"),
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
        string="Devolucao Definitiva",
        help="Quando habilitado, o cheque devolvido nao pode ser reapresentado.",
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
