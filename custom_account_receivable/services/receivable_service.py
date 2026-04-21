from datetime import timedelta

from odoo import fields, models
from odoo.exceptions import ValidationError


class ReceivableService(models.AbstractModel):
    _name = "receivable.service"
    _description = "Receivable Service"

    MSG_LIQUIDACAO_RASCUNHO = "Somente liquidacoes em rascunho podem ser aplicadas."
    MSG_LIQUIDACAO_EXCEDE_SALDO = (
        "O valor da liquidacao nao pode exceder o saldo em aberto da parcela."
    )
    MSG_RETENCAO_EXCEDE_BRUTO = (
        "A retencao mensal devida excede o valor bruto da liquidacao atual."
    )
    MSG_CHEQUE_EXIGE_LINHAS = (
        "Liquidacoes com cheque de terceiros exigem ao menos uma linha de cheque."
    )
    MSG_CHEQUE_TITULO_UNICO = (
        "A substituicao por cheque de terceiros exige parcelas de um unico titulo."
    )
    MSG_CHEQUE_NAO_PERMITE_CHEQUE = (
        "A substituicao por cheque de terceiros nao pode ser aplicada a titulos de cheque."
    )
    MSG_CHEQUE_TOTAL_DIVERGENTE = (
        "Os valores dos cheques de terceiros devem ser iguais ao saldo substituido."
    )
    MSG_LIQUIDACAO_MOEDA_UNICA = (
        "A liquidacao deve conter apenas parcelas na mesma moeda."
    )
    MSG_LIQUIDACAO_MOEDA_DIVERGENTE = (
        "A moeda da liquidacao deve ser igual a moeda das parcelas selecionadas."
    )

    def _get_month_limits(self, target_date):
        target_date = fields.Date.to_date(target_date)
        month_start = target_date.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        return month_start, month_end

    def _prepare_receivable_withholding_vals(self, settlement):
        settlement.ensure_one()
        partner_lines = settlement.partner_id.withholding_line_ids.filtered(
            lambda line: line.company_id == settlement.company_id
        )
        if not partner_lines:
            return []
        month_start, month_end = self._get_month_limits(settlement.date)
        prior_settlements = self.env["receivable.settlement"].search(
            [
                ("partner_id", "=", settlement.partner_id.id),
                ("company_id", "=", settlement.company_id.id),
                ("currency_id", "=", settlement.currency_id.id),
                ("state", "=", "applied"),
                ("date", ">=", month_start),
                ("date", "<=", month_end),
                ("id", "!=", settlement.id),
            ]
        )
        monthly_gross_total = sum(prior_settlements.mapped("gross_amount_total")) + settlement.gross_amount_total
        vals_list = []
        for partner_line in partner_lines:
            code = partner_line.withholding_code_id
            if monthly_gross_total < code.minimum_payment_amount:
                continue
            monthly_withholding_total = monthly_gross_total * (partner_line.retention_percent / 100.0)
            if monthly_withholding_total < code.minimum_retention_amount:
                continue
            previous_amount = sum(
                prior_settlements.mapped("withholding_line_ids")
                .filtered(lambda line: line.withholding_code_id == code)
                .mapped("amount")
            )
            current_amount = monthly_withholding_total - previous_amount
            if current_amount <= 0:
                continue
            vals_list.append(
                {
                    "partner_withholding_line_id": partner_line.id,
                    "base_amount": monthly_gross_total,
                    "previously_withheld_amount": previous_amount,
                    "amount": current_amount,
                }
            )
        return vals_list

    def open_title(self, vals):
        title = self.env["receivable.title"].create(vals)
        title.state = "open"
        return title

    def generate_installments(self, title, installment_vals_list):
        installments = self.env["receivable.installment"]
        for seq, vals in enumerate(installment_vals_list, start=1):
            values = {
                "title_id": title.id,
                "sequence": vals.get("sequence", seq),
                "due_date": vals["due_date"],
                "amount": vals["amount"],
            }
            installments |= self.env["receivable.installment"].create(values)
        title._compute_amounts()
        return installments

    def create_settlement(self, vals, line_vals_list):
        currency = self._extract_currency_from_installments(
            [line_vals["installment_id"] for line_vals in line_vals_list]
        )
        if currency and not vals.get("currency_id"):
            vals = dict(vals, currency_id=currency.id)
        settlement = self.env["receivable.settlement"].create(vals)
        for line_vals in line_vals_list:
            self.env["receivable.settlement.line"].create(
                {
                    "settlement_id": settlement.id,
                    "installment_id": line_vals["installment_id"],
                    "principal_amount": line_vals.get("principal_amount", 0.0),
                    "interest_amount": line_vals.get("interest_amount", 0.0),
                    "fine_amount": line_vals.get("fine_amount", 0.0),
                    "discount_amount": line_vals.get("discount_amount", 0.0),
                }
            )
        return settlement

    def _extract_currency_from_installments(self, installment_ids):
        installments = self.env["receivable.installment"].browse(list(installment_ids))
        currencies = installments.mapped("currency_id")
        if len(currencies) > 1:
            raise ValidationError(self.MSG_LIQUIDACAO_MOEDA_UNICA)
        return currencies[:1]

    def _validate_settlement_currency(self, settlement):
        line_currencies = settlement.line_ids.mapped("currency_id")
        if len(line_currencies) > 1:
            raise ValidationError(self.MSG_LIQUIDACAO_MOEDA_UNICA)
        if line_currencies and settlement.currency_id != line_currencies[0]:
            raise ValidationError(self.MSG_LIQUIDACAO_MOEDA_DIVERGENTE)

    def apply_settlement(self, settlement):
        settlement.ensure_one()
        if settlement.state != "draft":
            raise ValidationError(self.MSG_LIQUIDACAO_RASCUNHO)
        self._validate_settlement_currency(settlement)
        if settlement.settlement_kind == "third_party_check":
            return self._apply_third_party_check_settlement(settlement)
        settlement.withholding_line_ids.unlink()
        for line in settlement.line_ids:
            if line.total_amount > line.installment_id.amount_open:
                raise ValidationError(self.MSG_LIQUIDACAO_EXCEDE_SALDO)
        title_species_kinds = set(settlement.line_ids.mapped("title_id.species_kind"))
        if "check" not in title_species_kinds:
            withholding_vals_list = self._prepare_receivable_withholding_vals(settlement)
            for vals in withholding_vals_list:
                self.env["receivable.settlement.withholding"].create(
                    dict(vals, settlement_id=settlement.id)
                )
            if settlement.withholding_amount_total > settlement.gross_amount_total:
                raise ValidationError(self.MSG_RETENCAO_EXCEDE_BRUTO)
        if "financial.integration.service" in self.env.registry:
            self.env["financial.integration.service"].create_treasury_entry_from_receivable_settlement(settlement)
        settlement.state = "applied"
        settlement.line_ids.mapped("installment_id")._compute_amount_open()
        settlement.line_ids.mapped("title_id")._compute_amounts()
        return settlement

    def _apply_third_party_check_settlement(self, settlement):
        settlement.ensure_one()
        if not settlement.third_party_check_line_ids:
            raise ValidationError(self.MSG_CHEQUE_EXIGE_LINHAS)
        source_titles = settlement.line_ids.mapped("title_id")
        if len(source_titles) != 1:
            raise ValidationError(self.MSG_CHEQUE_TITULO_UNICO)
        source_title = source_titles[0]
        if source_title.species_kind == "check":
            raise ValidationError(self.MSG_CHEQUE_NAO_PERMITE_CHEQUE)
        for line in settlement.line_ids:
            if line.total_amount > line.installment_id.amount_open:
                raise ValidationError(self.MSG_LIQUIDACAO_EXCEDE_SALDO)
        check_total = sum(settlement.third_party_check_line_ids.mapped("amount"))
        if round(check_total - settlement.gross_amount_total, 2) != 0:
            raise ValidationError(self.MSG_CHEQUE_TOTAL_DIVERGENTE)
        species_check = self.env.ref("custom_financial_base.financial_title_species_check")
        for check_line in settlement.third_party_check_line_ids:
            check_title = self.open_title(
                {
                    "name": f"Cheque {check_line.check_number}",
                    "partner_id": settlement.partner_id.id,
                    "company_id": settlement.company_id.id,
                    "issue_date": settlement.date,
                    "origin_reference": source_title.name,
                    "species_id": species_check.id,
                    "amount_total": check_line.amount,
                    "currency_id": settlement.currency_id.id,
                    "notes": check_line.notes or settlement.notes,
                    "source_settlement_id": settlement.id,
                    "source_title_id": source_title.id,
                    "check_issuer_name": check_line.issuer_name,
                    "check_number": check_line.check_number,
                    "check_bank_name": check_line.bank_name,
                    "check_branch": check_line.branch,
                    "check_account_number": check_line.account_number,
                    "expected_clearance_date": check_line.expected_clearance_date,
                    "check_status": "pending",
                }
            )
            self.generate_installments(
                check_title,
                [
                    {
                        "sequence": 1,
                        "due_date": check_line.expected_clearance_date,
                        "amount": check_line.amount,
                    }
                ],
            )
        settlement.state = "applied"
        settlement.line_ids.mapped("installment_id")._compute_amount_open()
        settlement.line_ids.mapped("title_id")._compute_amounts()
        return settlement

    def renegotiate_titles(self, partner, source_titles, new_title_vals, installment_vals_list):
        renegotiation = self.env["receivable.renegotiation"].create(
            {
                "name": new_title_vals["name"],
                "partner_id": partner.id,
                "source_title_ids": [(6, 0, source_titles.ids)],
                "date": fields.Date.context_today(self),
            }
        )
        new_title = self.open_title(
            {
                "name": new_title_vals["name"],
                "partner_id": partner.id,
                "company_id": new_title_vals.get("company_id", partner.company_id.id if partner.company_id else self.env.company.id),
                "issue_date": new_title_vals.get("issue_date", fields.Date.context_today(self)),
                "origin_reference": new_title_vals.get("origin_reference"),
                "amount_total": new_title_vals["amount_total"],
                "notes": new_title_vals.get("notes"),
            }
        )
        self.generate_installments(new_title, installment_vals_list)
        source_titles.write({"state": "renegotiated"})
        renegotiation.write({"new_title_id": new_title.id, "state": "done"})
        return renegotiation
