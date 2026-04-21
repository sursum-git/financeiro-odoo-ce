from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceivableCollectionAgent(models.Model):
    _name = "receivable.collection.agent"
    _description = "Receivable Collection Agent"
    _order = "name"

    MSG_PORTADOR_UNICO_EMPRESA = (
        "Um portador do tipo cobrador so pode ser vinculado uma vez por empresa."
    )
    MSG_PORTADOR_TIPO_INVALIDO = "O portador do cobrador deve ser do tipo cobrador."
    MSG_PORTADOR_EMPRESA_DIFERENTE = "O portador do cobrador deve pertencer a mesma empresa."
    MSG_CONTATO_EMPRESA_DIFERENTE = "O contato do cobrador deve pertencer a mesma empresa."

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
        MSG_PORTADOR_UNICO_EMPRESA,
    )

    @api.constrains("portador_id", "company_id")
    def _check_portador(self):
        for agent in self:
            if agent.portador_id.type != "cobrador":
                raise ValidationError(self.MSG_PORTADOR_TIPO_INVALIDO)
            if agent.portador_id.company_id and agent.portador_id.company_id != agent.company_id:
                raise ValidationError(self.MSG_PORTADOR_EMPRESA_DIFERENTE)

    @api.constrains("partner_id", "company_id")
    def _check_related_company(self):
        for agent in self:
            if agent.partner_id.company_id and agent.partner_id.company_id != agent.company_id:
                raise ValidationError(self.MSG_CONTATO_EMPRESA_DIFERENTE)
