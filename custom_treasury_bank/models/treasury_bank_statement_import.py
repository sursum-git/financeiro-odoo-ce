import base64
import csv
import io

from odoo import fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryBankStatementImport(models.Model):
    _name = "treasury.bank.statement.import"
    _description = "Treasury Bank Statement Import"
    _order = "id desc"

    MSG_IMPORTACAO_SOMENTE_RASCUNHO = "Somente importacoes em rascunho podem ser processadas."
    MSG_ARQUIVO_OBRIGATORIO = "E obrigatorio informar um arquivo de extrato."
    MSG_COLUNAS_OBRIGATORIAS = (
        "O arquivo do extrato deve conter as colunas date, description, amount e type."
    )

    name = fields.Char(required=True, index=True)
    file_name = fields.Char()
    file_data = fields.Binary(required=True, attachment=False)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    bank_account_id = fields.Many2one(
        "treasury.bank.account",
        required=True,
        ondelete="restrict",
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("imported", "Imported"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    line_ids = fields.One2many(
        "treasury.bank.statement.line",
        "import_id",
        string="Imported Lines",
    )

    def action_import_file(self):
        for record in self:
            if record.state != "draft":
                raise UserError(self.MSG_IMPORTACAO_SOMENTE_RASCUNHO)
            if not record.file_data:
                raise ValidationError(self.MSG_ARQUIVO_OBRIGATORIO)
            decoded = base64.b64decode(record.file_data)
            content = decoded.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(content))
            required_columns = {"date", "description", "amount", "type"}
            if not reader.fieldnames or not required_columns.issubset(set(reader.fieldnames)):
                raise ValidationError(self.MSG_COLUNAS_OBRIGATORIAS)
            if record.line_ids:
                record.line_ids.unlink()
            for row in reader:
                self.env["treasury.bank.statement.line"].create(
                    {
                        "import_id": record.id,
                        "date": row["date"],
                        "description": row.get("description"),
                        "document_number": row.get("document_number"),
                        "amount": float(row["amount"]),
                        "type": row["type"],
                    }
                )
            record.state = "imported"

    def action_cancel(self):
        for record in self:
            record.state = "cancelled"
