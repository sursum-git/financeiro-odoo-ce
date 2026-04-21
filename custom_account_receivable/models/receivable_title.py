from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceivableTitle(models.Model):
    _name = "receivable.title"
    _description = "Receivable Title"
    _order = "issue_date desc, id desc"

    MSG_TITULO_RENEGOCIACAO_INVALIDA = (
        "Somente titulos abertos com saldo pendente podem ser renegociados."
    )
    MSG_ACAO_APENAS_CHEQUE = (
        "Esta acao esta disponivel apenas para titulos de cheque de terceiros."
    )
    MSG_CHEQUE_ABERTO_OBRIGATORIO = (
        "Somente cheques de terceiros em aberto podem usar esta acao."
    )

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
    species_id = fields.Many2one(
        "financial.title.species",
        ondelete="restrict",
        default=lambda self: self.env.ref("custom_financial_base.financial_title_species_normal", raise_if_not_found=False),
    )
    species_kind = fields.Selection(
        related="species_id.kind",
        store=True,
        readonly=True,
    )
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
            ("substituted", "Substituted"),
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
    source_settlement_id = fields.Many2one(
        "receivable.settlement",
        ondelete="restrict",
        index=True,
    )
    source_title_id = fields.Many2one(
        "receivable.title",
        ondelete="restrict",
        index=True,
    )
    generated_check_title_ids = fields.One2many(
        "receivable.title",
        "source_title_id",
        string="Generated Check Titles",
    )
    replacement_title_id = fields.Many2one(
        "receivable.title",
        ondelete="restrict",
        index=True,
    )
    check_issuer_name = fields.Char()
    check_number = fields.Char(index=True)
    check_bank_name = fields.Char()
    check_branch = fields.Char()
    check_account_number = fields.Char()
    expected_clearance_date = fields.Date(index=True)
    actual_clearance_date = fields.Date(index=True)
    last_return_date = fields.Date(index=True)
    return_count = fields.Integer(default=0)
    check_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("returned", "Returned"),
            ("compensated", "Compensated"),
            ("definitive_return", "Definitive Return"),
        ],
        index=True,
    )
    check_return_reason_id = fields.Many2one(
        "financial.check.return.reason",
        ondelete="restrict",
    )

    def action_open_renegotiation_wizard(self):
        self.ensure_one()
        if self.state not in {"open", "partial"} or self.amount_open <= 0:
            raise ValidationError(self.MSG_TITULO_RENEGOCIACAO_INVALIDA)
        return {
            "type": "ir.actions.act_window",
            "name": "Renegociar Titulo",
            "res_model": "receivable.renegotiation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_source_title_id": self.id,
            },
        }

    def action_open_check_compensation_wizard(self):
        self.ensure_one()
        self._check_open_check_title()
        return {
            "type": "ir.actions.act_window",
            "name": "Compensar Cheque",
            "res_model": "receivable.check.compensation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_title_id": self.id,
            },
        }

    def action_open_check_return_wizard(self):
        self.ensure_one()
        self._check_open_check_title()
        return {
            "type": "ir.actions.act_window",
            "name": "Devolver Cheque",
            "res_model": "receivable.check.return.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_title_id": self.id,
            },
        }

    def _check_open_check_title(self):
        self.ensure_one()
        if self.species_kind != "check":
            raise ValidationError(self.MSG_ACAO_APENAS_CHEQUE)
        if self.state not in {"open", "partial"}:
            raise ValidationError(self.MSG_CHEQUE_ABERTO_OBRIGATORIO)

    def action_cancel_check_title(self):
        for title in self:
            title.installment_ids.write({"state": "cancelled"})
            title.write({"state": "cancelled"})

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
                check_substitution = title.settlement_line_ids.filtered(
                    lambda line: line.settlement_id.state == "applied"
                    and line.settlement_id.settlement_kind == "third_party_check"
                )
                title.state = "substituted" if check_substitution else "paid"
            elif all(inst.state in {"open", "paid"} for inst in installments) and any(
                inst.state == "paid" for inst in installments
            ):
                title.state = "partial"
            elif any(inst.state == "partial" for inst in installments) or (
                any(inst.state == "paid" for inst in installments)
                and any(inst.state in {"open", "partial"} for inst in installments)
            ):
                title.state = "partial"
            elif any(inst.state in {"open", "partial"} for inst in installments):
                title.state = "open"
