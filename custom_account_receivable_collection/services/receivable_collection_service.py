from odoo import fields, models
from odoo.exceptions import ValidationError


class ReceivableCollectionService(models.AbstractModel):
    _name = "receivable.collection.service"
    _description = "Receivable Collection Service"

    def assign_titles_to_agent(self, route, agent, installments, notes=None):
        assignments = self.env["receivable.collection.assignment"]
        for installment in installments:
            if installment.state not in {"open", "partial"}:
                raise ValidationError("Only open or partial installments can be assigned.")
            assignments |= self.env["receivable.collection.assignment"].create(
                {
                    "route_id": route.id,
                    "agent_id": agent.id,
                    "partner_id": installment.title_id.partner_id.id,
                    "title_id": installment.title_id.id,
                    "installment_id": installment.id,
                    "notes": notes,
                }
            )
        if assignments and route.state == "draft":
            route.state = "in_progress"
        return assignments

    def register_field_collection(
        self,
        assignment,
        payment_method,
        principal_amount=None,
        interest_amount=0.0,
        fine_amount=0.0,
        discount_amount=0.0,
        date=None,
        notes=None,
    ):
        assignment.ensure_one()
        if assignment.state != "assigned":
            raise ValidationError("Only assigned items can register field collection.")
        if not assignment.agent_id.portador_id:
            raise ValidationError("The collection agent requires a portador.")
        installment = assignment.installment_id
        principal_value = principal_amount if principal_amount is not None else installment.amount_open
        if principal_value <= 0:
            raise ValidationError("Collected principal amount must be positive.")
        settlement_date = date or fields.Date.context_today(self)
        settlement_name = f"Cobranca {assignment.agent_id.name} - {assignment.title_id.name}"
        settlement = self.env["receivable.service"].create_settlement(
            {
                "name": settlement_name,
                "date": settlement_date,
                "partner_id": assignment.partner_id.id,
                "company_id": assignment.company_id.id,
                "payment_method_id": payment_method.id if payment_method else False,
                "portador_id": assignment.agent_id.portador_id.id,
                "notes": notes or assignment.notes,
            },
            [
                {
                    "installment_id": installment.id,
                    "principal_amount": principal_value,
                    "interest_amount": interest_amount,
                    "fine_amount": fine_amount,
                    "discount_amount": discount_amount,
                }
            ],
        )
        self.env["receivable.service"].apply_settlement(settlement)
        assignment.write(
            {
                "state": "collected",
                "collection_date": settlement_date,
                "settlement_id": settlement.id,
                "notes": notes or assignment.notes,
            }
        )
        return settlement

    def create_agent_accountability(
        self,
        agent,
        settlement_ids,
        date=None,
        target_account=None,
        target_cash_box=None,
        notes=None,
        name=None,
    ):
        agent.ensure_one()
        settlements = settlement_ids if hasattr(settlement_ids, "ids") else self.env["receivable.settlement"].browse(settlement_ids)
        if not settlements:
            raise ValidationError("Accountability requires tracked settlements.")
        if target_cash_box and not target_cash_box.portador_id:
            raise ValidationError("The target cash box requires a portador.")
        accountability = self.env["receivable.collection.accountability"].create(
            {
                "name": name or f"Prestacao {agent.name} - {date or fields.Date.context_today(self)}",
                "agent_id": agent.id,
                "date": date or fields.Date.context_today(self),
                "target_account_id": target_account.id if target_account else False,
                "target_cash_box_id": target_cash_box.id if target_cash_box else False,
                "notes": notes,
                "settlement_ids": [(6, 0, settlements.ids)],
            }
        )
        target_portador = target_cash_box.portador_id if target_cash_box else False
        out_move, in_move = self.env["treasury.cash.service"].create_accountability(
            accountability.source_portador_id,
            target_account,
            target_portador,
            accountability.amount,
            accountability.company_id,
            accountability.name,
            accountability.date,
        )
        accountability.write(
            {
                "state": "done",
                "out_movement_id": out_move.id,
                "in_movement_id": in_move.id,
            }
        )
        assignments = self.env["receivable.collection.assignment"].search(
            [("settlement_id", "in", settlements.ids)]
        )
        assignments.write(
            {
                "state": "accounted",
                "accountability_id": accountability.id,
            }
        )
        for route in assignments.mapped("route_id"):
            if route.assignment_ids and all(record.state == "accounted" for record in route.assignment_ids):
                route.state = "done"
        return accountability
