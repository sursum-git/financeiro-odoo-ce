from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceivableCollectionAssignWizard(models.TransientModel):
    _name = "receivable.collection.assign.wizard"
    _description = "Receivable Collection Assign Wizard"

    MSG_EXIGE_PARCELAS = "Selecione ao menos uma parcela para atribuir ao cobrador."

    route_id = fields.Many2one(
        "receivable.collection.route",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(related="route_id.company_id", readonly=True)
    agent_id = fields.Many2one(
        "receivable.collection.agent",
        required=True,
        ondelete="restrict",
        domain="[('company_id', '=', company_id)]",
    )
    installment_ids = fields.Many2many(
        "receivable.installment",
        string="Parcelas",
    )
    notes = fields.Text()

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        route = self.env["receivable.collection.route"].browse(values.get("route_id"))
        if route and ("installment_ids" in fields_list or not fields_list):
            installments = self.env["receivable.installment"].search(
                [
                    ("state", "in", ["open", "partial"]),
                    ("title_id.company_id", "=", route.company_id.id),
                ]
            )
            values.setdefault("installment_ids", [(6, 0, installments.ids)])
        return values

    def action_confirm(self):
        self.ensure_one()
        if not self.installment_ids:
            raise ValidationError(self.MSG_EXIGE_PARCELAS)
        self.env["receivable.collection.service"].assign_titles_to_agent(
            self.route_id,
            self.agent_id,
            self.installment_ids,
            notes=self.notes,
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Roteiro de Cobranca",
            "res_model": "receivable.collection.route",
            "res_id": self.route_id.id,
            "view_mode": "form",
            "target": "current",
        }


class ReceivableCollectionFieldWizard(models.TransientModel):
    _name = "receivable.collection.field.wizard"
    _description = "Receivable Collection Field Wizard"

    MSG_VALOR_PRINCIPAL_POSITIVO = "O valor principal recebido deve ser positivo."

    assignment_id = fields.Many2one(
        "receivable.collection.assignment",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(related="assignment_id.company_id", readonly=True)
    partner_id = fields.Many2one(related="assignment_id.partner_id", readonly=True)
    currency_id = fields.Many2one(related="assignment_id.currency_id", readonly=True)
    amount_open = fields.Monetary(
        related="assignment_id.installment_id.amount_open",
        currency_field="currency_id",
        readonly=True,
    )
    payment_method_id = fields.Many2one(
        "financial.payment.method",
        required=True,
        ondelete="restrict",
    )
    principal_amount = fields.Monetary(
        required=True,
        currency_field="currency_id",
    )
    interest_amount = fields.Monetary(default=0.0, currency_field="currency_id")
    fine_amount = fields.Monetary(default=0.0, currency_field="currency_id")
    discount_amount = fields.Monetary(default=0.0, currency_field="currency_id")
    date = fields.Date(required=True, default=fields.Date.context_today)
    notes = fields.Text()

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        assignment = self.env["receivable.collection.assignment"].browse(values.get("assignment_id"))
        if assignment:
            values.setdefault("principal_amount", assignment.installment_id.amount_open)
            values.setdefault("notes", assignment.notes)
        return values

    def action_confirm(self):
        self.ensure_one()
        if self.principal_amount <= 0:
            raise ValidationError(self.MSG_VALOR_PRINCIPAL_POSITIVO)
        settlement = self.env["receivable.collection.service"].register_field_collection(
            self.assignment_id,
            self.payment_method_id,
            principal_amount=self.principal_amount,
            interest_amount=self.interest_amount,
            fine_amount=self.fine_amount,
            discount_amount=self.discount_amount,
            date=self.date,
            notes=self.notes,
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Liquidacao",
            "res_model": "receivable.settlement",
            "res_id": settlement.id,
            "view_mode": "form",
            "target": "current",
        }
