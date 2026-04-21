from odoo import fields, models
from odoo.exceptions import ValidationError


class ReceivableCheckCompensationWizard(models.TransientModel):
    _name = "receivable.check.compensation.wizard"
    _description = "Receivable Check Compensation Wizard"

    title_id = fields.Many2one(
        "receivable.title",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(related="title_id.company_id", readonly=True)
    partner_id = fields.Many2one(related="title_id.partner_id", readonly=True)
    amount_open = fields.Monetary(
        related="title_id.amount_open",
        currency_field="currency_id",
        readonly=True,
    )
    currency_id = fields.Many2one(related="title_id.currency_id", readonly=True)
    compensation_date = fields.Date(required=True, default=fields.Date.context_today)
    payment_method_id = fields.Many2one(
        "financial.payment.method",
        required=True,
        default=lambda self: self.env["financial.payment.method"].search([("type", "=", "cheque")], limit=1),
        ondelete="restrict",
    )
    portador_id = fields.Many2one("financial.portador", ondelete="restrict")
    target_account_id = fields.Many2one("treasury.account", ondelete="restrict")
    notes = fields.Text()

    def action_confirm(self):
        self.ensure_one()
        self.title_id._check_open_check_title()
        if not self.portador_id and not self.target_account_id:
            raise ValidationError("Check compensation requires a target account or portador.")
        installment = self.title_id.installment_ids.filtered(lambda inst: inst.amount_open > 0)[:1]
        if not installment:
            raise ValidationError("The check title has no open installment to compensate.")
        settlement = self.env["receivable.service"].create_settlement(
            {
                "name": f"Compensacao Cheque {self.title_id.check_number or self.title_id.name}",
                "date": self.compensation_date,
                "partner_id": self.title_id.partner_id.id,
                "company_id": self.title_id.company_id.id,
                "payment_method_id": self.payment_method_id.id,
                "portador_id": self.portador_id.id,
                "target_account_id": self.target_account_id.id,
                "notes": self.notes,
            },
            [
                {
                    "installment_id": installment.id,
                    "principal_amount": installment.amount_open,
                }
            ],
        )
        self.env["receivable.service"].apply_settlement(settlement)
        self.title_id.write(
            {
                "check_status": "compensated",
                "actual_clearance_date": self.compensation_date,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Third-Party Check",
            "res_model": "receivable.title",
            "res_id": self.title_id.id,
            "view_mode": "form",
            "target": "current",
        }


class ReceivableCheckReturnWizard(models.TransientModel):
    _name = "receivable.check.return.wizard"
    _description = "Receivable Check Return Wizard"

    title_id = fields.Many2one(
        "receivable.title",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(related="title_id.company_id", readonly=True)
    partner_id = fields.Many2one(related="title_id.partner_id", readonly=True)
    amount_open = fields.Monetary(
        related="title_id.amount_open",
        currency_field="currency_id",
        readonly=True,
    )
    currency_id = fields.Many2one(related="title_id.currency_id", readonly=True)
    return_date = fields.Date(required=True, default=fields.Date.context_today)
    return_reason_id = fields.Many2one(
        "financial.check.return.reason",
        required=True,
        ondelete="restrict",
    )
    notes = fields.Text()

    def action_confirm(self):
        self.ensure_one()
        self.title_id._check_open_check_title()
        values = {
            "check_return_reason_id": self.return_reason_id.id,
            "last_return_date": self.return_date,
            "return_count": self.title_id.return_count + 1,
        }
        if self.return_reason_id.is_definitive:
            species_normal = self.env.ref("custom_financial_base.financial_title_species_normal")
            replacement_title = self.env["receivable.service"].open_title(
                {
                    "name": f"Reabertura {self.title_id.name}",
                    "partner_id": self.title_id.partner_id.id,
                    "company_id": self.title_id.company_id.id,
                    "issue_date": self.return_date,
                    "origin_reference": self.title_id.check_number or self.title_id.name,
                    "species_id": species_normal.id,
                    "amount_total": self.title_id.amount_open,
                    "notes": self.notes or f"Cheque devolvido. Motivo {self.return_reason_id.code}.",
                }
            )
            self.env["receivable.service"].generate_installments(
                replacement_title,
                [
                    {
                        "sequence": 1,
                        "due_date": self.return_date,
                        "amount": self.title_id.amount_open,
                    }
                ],
            )
            values.update(
                {
                    "check_status": "definitive_return",
                    "replacement_title_id": replacement_title.id,
                }
            )
            self.title_id.write(values)
            self.title_id.action_cancel_check_title()
        else:
            values["check_status"] = "returned"
            self.title_id.write(values)
        return {
            "type": "ir.actions.act_window",
            "name": "Third-Party Check",
            "res_model": "receivable.title",
            "res_id": self.title_id.id,
            "view_mode": "form",
            "target": "current",
        }
