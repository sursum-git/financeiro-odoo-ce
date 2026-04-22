from odoo import fields, models


class FinancialIntegrationEvent(models.Model):
    _name = "financial.integration.event"
    _description = "Financial Integration Event"
    _order = "id desc"

    MSG_EVENTO_UNICO = (
        "Ja existe um evento de integracao para esse tipo e registro de origem."
    )

    name = fields.Char(required=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    event_type = fields.Selection(
        [
            ("receivable_settlement", "Liquidacao de Contas a Receber"),
            ("payable_payment", "Pagamento de Contas a Pagar"),
            ("reverse_receivable", "Estorno de Contas a Receber"),
            ("reverse_payable", "Estorno de Contas a Pagar"),
            ("transfer_portador", "Transferencia de Portador"),
        ],
        required=True,
        index=True,
    )
    source_module = fields.Char(required=True, index=True)
    source_model = fields.Char(required=True, index=True)
    source_record_id = fields.Integer(required=True, index=True)
    state = fields.Selection(
        [
            ("draft", "Rascunho"),
            ("done", "Concluido"),
            ("failed", "Falha"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    treasury_movement_id = fields.Many2one("treasury.movement", ondelete="restrict")
    log_ids = fields.One2many(
        "financial.integration.log",
        "event_id",
        string="Registros",
    )

    _financial_integration_event_uniq = models.Constraint(
        "unique(event_type, source_model, source_record_id)",
        MSG_EVENTO_UNICO,
    )
