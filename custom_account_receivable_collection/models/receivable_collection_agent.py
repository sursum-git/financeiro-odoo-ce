from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceivableCollectionAgent(models.Model):
    _name = "receivable.collection.agent"
    _description = "Receivable Collection Agent"
    _order = "name"

    name = fields.Char(required=True, index=True)
    partner_id = fields.Many2one("res.partner", ondelete="restrict", index=True)
    user_id = fields.Many2one("res.users", ondelete="restrict", index=True)
    portador_id = fields.Many2one("financial.portador", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    active = fields.Boolean(default=True)
    assignment_ids = fields.One2many(
        "receivable.collection.assignment",
        "agent_id",
        string="Assignments",
    )
    accountability_ids = fields.One2many(
        "receivable.collection.accountability",
        "agent_id",
        string="Accountabilities",
    )

    @staticmethod
    def _get_open_assignment_states():
        return ["assigned", "collected"]

    _receivable_collection_agent_portador_company_uniq = models.Constraint(
        "unique(portador_id, company_id)",
        "A cobrador portador can only be linked once per company.",
    )

    @api.constrains("portador_id", "company_id")
    def _check_portador(self):
        for agent in self:
            if agent.portador_id.type != "cobrador":
                raise ValidationError("The agent portador must be of type cobrador.")
            if agent.portador_id.company_id and agent.portador_id.company_id != agent.company_id:
                raise ValidationError("The agent portador must belong to the same company.")

    @api.constrains("partner_id", "company_id")
    def _check_related_company(self):
        for agent in self:
            if agent.partner_id.company_id and agent.partner_id.company_id != agent.company_id:
                raise ValidationError("The agent partner must belong to the same company.")
