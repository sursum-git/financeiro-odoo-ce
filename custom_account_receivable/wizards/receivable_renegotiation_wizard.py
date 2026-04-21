from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceivableRenegotiationWizard(models.TransientModel):
    _name = "receivable.renegotiation.wizard"
    _description = "Receivable Renegotiation Wizard"

    MSG_TITULO_RENEGOCIACAO_INVALIDA = (
        "Somente titulos abertos com saldo pendente podem ser renegociados."
    )
    MSG_EXIGE_PARCELA = "A renegociacao exige ao menos uma nova parcela."
    MSG_TOTAL_POSITIVO = "O valor total da renegociacao deve ser positivo."

    source_title_id = fields.Many2one(
        "receivable.title",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    partner_id = fields.Many2one(
        related="source_title_id.partner_id",
        readonly=True,
    )
    company_id = fields.Many2one(
        related="source_title_id.company_id",
        readonly=True,
    )
    currency_id = fields.Many2one(
        related="source_title_id.currency_id",
        readonly=True,
    )
    source_amount_open = fields.Monetary(
        related="source_title_id.amount_open",
        currency_field="currency_id",
        readonly=True,
    )
    new_title_name = fields.Char(required=True)
    issue_date = fields.Date(required=True, default=fields.Date.context_today)
    origin_reference = fields.Char()
    notes = fields.Text()
    installment_line_ids = fields.One2many(
        "receivable.renegotiation.wizard.line",
        "wizard_id",
        string="New Installments",
    )
    new_amount_total = fields.Monetary(
        compute="_compute_new_amount_total",
        store=True,
        currency_field="currency_id",
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        title = self.env["receivable.title"].browse(self.env.context.get("default_source_title_id"))
        if title:
            values.setdefault("new_title_name", f"Renegociacao - {title.name}")
            values.setdefault("origin_reference", title.name)
            if "installment_line_ids" in fields_list or not fields_list:
                values["installment_line_ids"] = [
                    (
                        0,
                        0,
                        {
                            "sequence": 1,
                            "due_date": fields.Date.context_today(self),
                            "amount": title.amount_open,
                        },
                    )
                ]
        return values

    @api.depends("installment_line_ids.amount")
    def _compute_new_amount_total(self):
        for wizard in self:
            wizard.new_amount_total = sum(wizard.installment_line_ids.mapped("amount"))

    def action_confirm(self):
        self.ensure_one()
        title = self.source_title_id
        if title.state not in {"open", "partial"} or title.amount_open <= 0:
            raise ValidationError(self.MSG_TITULO_RENEGOCIACAO_INVALIDA)
        if not self.installment_line_ids:
            raise ValidationError(self.MSG_EXIGE_PARCELA)
        if self.new_amount_total <= 0:
            raise ValidationError(self.MSG_TOTAL_POSITIVO)
        installment_vals_list = []
        for line in self.installment_line_ids.sorted("sequence"):
            installment_vals_list.append(
                {
                    "sequence": line.sequence,
                    "due_date": line.due_date,
                    "amount": line.amount,
                }
            )
        renegotiation = self.env["receivable.service"].renegotiate_titles(
            title.partner_id,
            title,
            {
                "name": self.new_title_name,
                "company_id": title.company_id.id,
                "issue_date": self.issue_date,
                "origin_reference": self.origin_reference,
                "amount_total": self.new_amount_total,
                "notes": self.notes,
            },
            installment_vals_list,
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Renegociacao",
            "res_model": "receivable.renegotiation",
            "res_id": renegotiation.id,
            "view_mode": "form",
            "target": "current",
        }


class ReceivableRenegotiationWizardLine(models.TransientModel):
    _name = "receivable.renegotiation.wizard.line"
    _description = "Receivable Renegotiation Wizard Line"
    _order = "sequence, id"

    MSG_VALOR_PARCELA_POSITIVO = "O valor da parcela deve ser positivo."

    wizard_id = fields.Many2one(
        "receivable.renegotiation.wizard",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(required=True, default=1)
    due_date = fields.Date(required=True)
    amount = fields.Monetary(
        required=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="wizard_id.currency_id",
        readonly=True,
    )

    @api.constrains("amount")
    def _check_amount(self):
        for line in self:
            if line.amount <= 0:
                raise ValidationError(self.MSG_VALOR_PARCELA_POSITIVO)
