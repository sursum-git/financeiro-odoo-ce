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

    def _get_month_limits(self, target_date):
        target_date = fields.Date.to_date(target_date)
        month_start = target_date.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        return month_start, month_end

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
        monthly_gross_total = sum(prior_payments.mapped("gross_amount_total")) + payment.gross_amount_total
        vals_list = []
        for partner_line in partner_lines:
            code = partner_line.withholding_code_id
            if monthly_gross_total < code.minimum_payment_amount:
                continue
            monthly_withholding_total = monthly_gross_total * (partner_line.retention_percent / 100.0)
            if monthly_withholding_total < code.minimum_retention_amount:
                continue
            previous_amount = sum(
                prior_payments.mapped("withholding_line_ids")
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
        title._compute_amounts()
        return installments

    def schedule_payment(self, vals):
        schedule = self.env["payable.schedule"].create(vals)
        schedule.state = "scheduled"
        return schedule

    def create_payment(self, vals, line_vals_list):
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

    def apply_payment(self, payment):
        payment.ensure_one()
        if payment.state != "draft":
            raise ValidationError(self.MSG_PAGAMENTO_RASCUNHO)
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
