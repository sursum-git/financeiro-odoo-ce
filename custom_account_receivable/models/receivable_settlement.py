from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceivableSettlement(models.Model):
    _name = "receivable.settlement"
    _description = "Receivable Settlement"
    _order = "date desc, id desc"

    MSG_CHEQUE_EXIGE_LINHAS = (
        "Liquidacoes com cheque de terceiros exigem ao menos uma linha de cheque."
    )
    MSG_CHEQUE_TITULO_UNICO = (
        "A substituicao por cheque de terceiros so pode ser aplicada a parcelas de um unico titulo."
    )
    MSG_CHEQUE_TOTAL_DIVERGENTE = (
        "A soma dos cheques de terceiros deve ser igual ao valor total substituido."
    )

    name = fields.Char(required=True, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    partner_id = fields.Many2one("res.partner", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    payment_method_id = fields.Many2one("financial.payment.method", ondelete="restrict")
    portador_id = fields.Many2one("financial.portador", ondelete="restrict")
    target_account_id = fields.Many2one("treasury.account", ondelete="restrict")
    settlement_kind = fields.Selection(
        [
            ("standard", "Standard"),
            ("third_party_check", "Third-Party Check"),
        ],
        required=True,
        default="standard",
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("applied", "Applied"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    line_ids = fields.One2many(
        "receivable.settlement.line",
        "settlement_id",
        string="Settlement Lines",
    )
    third_party_check_line_ids = fields.One2many(
        "receivable.settlement.check.line",
        "settlement_id",
        string="Third-Party Checks",
    )
    withholding_line_ids = fields.One2many(
        "receivable.settlement.withholding",
        "settlement_id",
        string="Withholding Lines",
        readonly=True,
    )
    gross_amount_total = fields.Monetary(
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )
    withholding_amount_total = fields.Monetary(
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )
    net_amount_total = fields.Monetary(
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends("line_ids.total_amount", "withholding_line_ids.amount")
    def _compute_totals(self):
        for settlement in self:
            gross = sum(settlement.line_ids.mapped("total_amount"))
            withheld = sum(settlement.withholding_line_ids.mapped("amount"))
            if settlement.settlement_kind == "third_party_check":
                withheld = 0.0
            settlement.gross_amount_total = gross
            settlement.withholding_amount_total = withheld
            settlement.net_amount_total = gross - withheld

    @api.constrains("settlement_kind", "third_party_check_line_ids", "line_ids")
    def _check_third_party_checks(self):
        for settlement in self:
            if settlement.settlement_kind != "third_party_check":
                continue
            if settlement.state == "draft":
                continue
            if not settlement.third_party_check_line_ids:
                raise ValidationError(self.MSG_CHEQUE_EXIGE_LINHAS)
            title_ids = settlement.line_ids.mapped("title_id")
            if len(title_ids) != 1:
                raise ValidationError(self.MSG_CHEQUE_TITULO_UNICO)
            check_total = sum(settlement.third_party_check_line_ids.mapped("amount"))
            if round(check_total - settlement.gross_amount_total, 2) != 0:
                raise ValidationError(self.MSG_CHEQUE_TOTAL_DIVERGENTE)
