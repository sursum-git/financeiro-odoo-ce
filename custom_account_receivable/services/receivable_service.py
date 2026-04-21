from odoo import fields, models
from odoo.exceptions import ValidationError


class ReceivableService(models.AbstractModel):
    _name = "receivable.service"
    _description = "Receivable Service"

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

    def apply_settlement(self, settlement):
        settlement.ensure_one()
        if settlement.state != "draft":
            raise ValidationError("Only draft settlements can be applied.")
        for line in settlement.line_ids:
            if line.total_amount > line.installment_id.amount_open:
                raise ValidationError("Settlement amount cannot exceed the installment open amount.")
        if "financial.integration.service" in self.env.registry:
            self.env["financial.integration.service"].create_treasury_entry_from_receivable_settlement(settlement)
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
