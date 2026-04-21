from odoo import fields, models
from odoo.exceptions import ValidationError


class PayableService(models.AbstractModel):
    _name = "payable.service"
    _description = "Payable Service"

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
            raise ValidationError("Only draft payments can be applied.")
        for line in payment.line_ids:
            if line.total_amount > line.installment_id.amount_open:
                raise ValidationError("Payment amount cannot exceed the installment open amount.")
        if "financial.integration.service" in self.env.registry:
            self.env["financial.integration.service"].create_treasury_exit_from_payable_payment(payment)
        payment.state = "applied"
        payment.line_ids.mapped("installment_id")._compute_amount_open()
        payment.line_ids.mapped("installment_id.title_id")._compute_amounts()
        return payment
