from datetime import timedelta

from odoo import fields, models
from odoo.exceptions import ValidationError


class PayableService(models.AbstractModel):
    _name = "payable.service"
    _description = "Payable Service"

    MSG_PAGAMENTO_RASCUNHO = "Somente pagamentos em rascunho podem ser aplicados."
    MSG_PAGAMENTO_EXCEDE_SALDO = (
        "O valor do pagamento nao pode exceder o saldo em aberto da parcela."
    )
    MSG_RETENCAO_EXCEDE_BRUTO = (
        "A retencao mensal devida excede o valor bruto do pagamento atual."
    )
    MSG_PAGAMENTO_MOEDA_UNICA = "O pagamento deve conter apenas parcelas na mesma moeda."
    MSG_PAGAMENTO_MOEDA_DIVERGENTE = (
        "A moeda do pagamento deve ser igual a moeda das parcelas selecionadas."
    )
    MSG_TOTAL_PARCELAS_DIVERGENTE = (
        "A soma das parcelas deve ser igual ao valor total do titulo a pagar."
    )

    def _get_month_limits(self, target_date):
        target_date = fields.Date.to_date(target_date)
        month_start = target_date.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        return month_start, month_end

    def _convert_amount(self, amount, from_currency, to_currency, company, date):
        if not from_currency or not to_currency or from_currency == to_currency:
            return amount
        return from_currency._convert(amount, to_currency, company, date)

    def _prepare_payable_withholding_vals(self, payment):
        payment.ensure_one()
        partner_lines = payment.partner_id.withholding_line_ids.filtered(
            lambda line: line.company_id == payment.company_id
        )
        if not partner_lines:
            return []
        month_start, month_end = self._get_month_limits(payment.date)
        prior_payments = self.env["payable.payment"].search(
            [
                ("partner_id", "=", payment.partner_id.id),
                ("company_id", "=", payment.company_id.id),
                ("state", "=", "applied"),
                ("date", ">=", month_start),
                ("date", "<=", month_end),
                ("id", "!=", payment.id),
            ]
        )
        monthly_gross_total_company = (
            sum(prior_payments.mapped("gross_amount_company_currency"))
            + payment.gross_amount_company_currency
        )
        vals_list = []
        for partner_line in partner_lines:
            code = partner_line.withholding_code_id
            if monthly_gross_total_company < code.minimum_payment_amount:
                continue
            monthly_withholding_total_company = monthly_gross_total_company * (
                partner_line.retention_percent / 100.0
            )
            if monthly_withholding_total_company < code.minimum_retention_amount:
                continue
            previous_amount_company = sum(
                prior_payments.mapped("withholding_line_ids")
                .filtered(lambda line: line.withholding_code_id == code)
                .mapped("amount_company_currency")
            )
            current_amount_company = monthly_withholding_total_company - previous_amount_company
            if current_amount_company <= 0:
                continue
            base_amount = self._convert_amount(
                monthly_gross_total_company,
                payment.company_currency_id,
                payment.currency_id,
                payment.company_id,
                payment.date,
            )
            previous_amount = self._convert_amount(
                previous_amount_company,
                payment.company_currency_id,
                payment.currency_id,
                payment.company_id,
                payment.date,
            )
            current_amount = self._convert_amount(
                current_amount_company,
                payment.company_currency_id,
                payment.currency_id,
                payment.company_id,
                payment.date,
            )
            vals_list.append(
                {
                    "partner_withholding_line_id": partner_line.id,
                    "base_amount": base_amount,
                    "previously_withheld_amount": previous_amount,
                    "amount": current_amount,
                    "base_amount_company_currency": monthly_gross_total_company,
                    "previously_withheld_amount_company_currency": previous_amount_company,
                    "amount_company_currency": current_amount_company,
                }
            )
        return vals_list

    def open_title(self, vals):
        title = self.env["payable.title"].create(vals)
        title.state = "open"
        return title

    def generate_installments(self, title, installment_vals_list):
        installments = self.env["payable.installment"]
        for seq, vals in enumerate(installment_vals_list, start=1):
            installments |= self.env["payable.installment"].create(
                {
                    "title_id": title.id,
                    "sequence": vals.get("sequence", seq),
                    "due_date": vals["due_date"],
                    "amount": vals["amount"],
                }
            )
        total_installments = sum(installments.mapped("amount"))
        if title.currency_id.compare_amounts(total_installments, title.amount_total) != 0:
            raise ValidationError(self.MSG_TOTAL_PARCELAS_DIVERGENTE)
        title._compute_amounts()
        return installments

    def schedule_payment(self, vals):
        schedule = self.env["payable.schedule"].create(vals)
        schedule.state = "scheduled"
        return schedule

    def create_payment(self, vals, line_vals_list):
        currency = self._extract_currency_from_installments(
            [line_vals["installment_id"] for line_vals in line_vals_list]
        )
        if currency and not vals.get("currency_id"):
            vals = dict(vals, currency_id=currency.id)
        payment = self.env["payable.payment"].create(vals)
        for line_vals in line_vals_list:
            self.env["payable.payment.line"].create(
                {
                    "payment_id": payment.id,
                    "installment_id": line_vals["installment_id"],
                    "principal_amount": line_vals.get("principal_amount", 0.0),
                    "interest_amount": line_vals.get("interest_amount", 0.0),
                    "fine_amount": line_vals.get("fine_amount", 0.0),
                    "discount_amount": line_vals.get("discount_amount", 0.0),
                }
            )
        return payment

    def _extract_currency_from_installments(self, installment_ids):
        installments = self.env["payable.installment"].browse(list(installment_ids))
        currencies = installments.mapped("currency_id")
        if len(currencies) > 1:
            raise ValidationError(self.MSG_PAGAMENTO_MOEDA_UNICA)
        return currencies[:1]

    def _validate_payment_currency(self, payment):
        line_currencies = payment.line_ids.mapped("currency_id")
        if len(line_currencies) > 1:
            raise ValidationError(self.MSG_PAGAMENTO_MOEDA_UNICA)
        if line_currencies and payment.currency_id != line_currencies[0]:
            raise ValidationError(self.MSG_PAGAMENTO_MOEDA_DIVERGENTE)

    def apply_payment(self, payment):
        payment.ensure_one()
        if payment.state != "draft":
            raise ValidationError(self.MSG_PAGAMENTO_RASCUNHO)
        self._validate_payment_currency(payment)
        payment.withholding_line_ids.unlink()
        for line in payment.line_ids:
            if line.total_amount > line.installment_id.amount_open:
                raise ValidationError(self.MSG_PAGAMENTO_EXCEDE_SALDO)
        withholding_vals_list = self._prepare_payable_withholding_vals(payment)
        for vals in withholding_vals_list:
            self.env["payable.payment.withholding"].create(dict(vals, payment_id=payment.id))
        if payment.withholding_amount_total > payment.gross_amount_total:
            raise ValidationError(self.MSG_RETENCAO_EXCEDE_BRUTO)
        if "financial.integration.service" in self.env.registry:
            self.env["financial.integration.service"].create_treasury_exit_from_payable_payment(payment)
        payment.state = "applied"
        payment.line_ids.mapped("installment_id")._compute_amount_open()
        payment.line_ids.mapped("installment_id.title_id")._compute_amounts()
        return payment
