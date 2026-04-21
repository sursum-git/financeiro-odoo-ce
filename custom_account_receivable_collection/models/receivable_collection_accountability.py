from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReceivableCollectionAccountability(models.Model):
    _name = "receivable.collection.accountability"
    _description = "Receivable Collection Accountability"
    _order = "date desc, id desc"

    MSG_DESTINO_OBRIGATORIO = (
        "A prestacao de contas exige conta de destino ou caixa de destino."
    )
    MSG_DESTINO_EXCLUSIVO = "Informe apenas conta de destino ou caixa de destino."
    MSG_EXIGE_LIQUIDACOES = "A prestacao de contas exige ao menos uma liquidacao rastreada."
    MSG_VALOR_POSITIVO = "O valor da prestacao de contas deve ser positivo."
    MSG_LIQUIDACAO_UNICA = "Uma liquidacao nao pode ser prestada mais de uma vez."
    MSG_LIQUIDACAO_APLICADA = "Somente liquidacoes aplicadas podem ser prestadas."
    MSG_PORTADOR_COBRADOR = "Todas as liquidacoes devem pertencer ao portador do cobrador."
    MSG_LIQUIDACAO_MOEDA_UNICA = (
        "Todas as liquidacoes da prestacao de contas devem estar na mesma moeda."
    )
    MSG_LIQUIDACAO_MOEDA_PORTADOR = (
        "A moeda das liquidacoes deve ser igual a moeda do portador do cobrador."
    )

    name = fields.Char(required=True, index=True)
    agent_id = fields.Many2one(
        "receivable.collection.agent",
        required=True,
        ondelete="restrict",
        index=True,
    )
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    amount = fields.Monetary(
        compute="_compute_amount",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="source_portador_id.currency_id",
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related="agent_id.company_id",
        store=True,
        readonly=True,
    )
    target_account_id = fields.Many2one("treasury.account", ondelete="restrict")
    target_cash_box_id = fields.Many2one("treasury.cash.box", ondelete="restrict")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    settlement_ids = fields.Many2many(
        "receivable.settlement",
        "receivable_collection_accountability_settlement_rel",
        "accountability_id",
        "settlement_id",
        string="Settlements",
    )
    source_portador_id = fields.Many2one(
        related="agent_id.portador_id",
        store=True,
        readonly=True,
    )
    out_movement_id = fields.Many2one("treasury.movement", ondelete="restrict")
    in_movement_id = fields.Many2one("treasury.movement", ondelete="restrict")
    assignment_ids = fields.One2many(
        "receivable.collection.assignment",
        "accountability_id",
        string="Assignments",
    )

    @api.depends("settlement_ids.net_amount_total")
    def _compute_amount(self):
        for accountability in self:
            accountability.amount = sum(accountability.settlement_ids.mapped("net_amount_total"))

    @api.constrains("target_account_id", "target_cash_box_id")
    def _check_target(self):
        for accountability in self:
            if not accountability.target_account_id and not accountability.target_cash_box_id:
                raise ValidationError(self.MSG_DESTINO_OBRIGATORIO)
            if accountability.target_account_id and accountability.target_cash_box_id:
                raise ValidationError(self.MSG_DESTINO_EXCLUSIVO)

    @api.constrains("settlement_ids", "agent_id")
    def _check_settlement_traceability(self):
        for accountability in self:
            if not accountability.settlement_ids:
                raise ValidationError(self.MSG_EXIGE_LIQUIDACOES)
            if accountability.amount <= 0:
                raise ValidationError(self.MSG_VALOR_POSITIVO)
            done_accountabilities = self.search(
                [
                    ("id", "!=", accountability.id),
                    ("state", "=", "done"),
                    ("settlement_ids", "in", accountability.settlement_ids.ids),
                ]
            )
            if done_accountabilities:
                raise ValidationError(self.MSG_LIQUIDACAO_UNICA)
            for settlement in accountability.settlement_ids:
                if settlement.state != "applied":
                    raise ValidationError(self.MSG_LIQUIDACAO_APLICADA)
                if settlement.portador_id != accountability.agent_id.portador_id:
                    raise ValidationError(self.MSG_PORTADOR_COBRADOR)
            currencies = accountability.settlement_ids.mapped("currency_id")
            if len(currencies) > 1:
                raise ValidationError(self.MSG_LIQUIDACAO_MOEDA_UNICA)
            if currencies and accountability.currency_id and currencies[0] != accountability.currency_id:
                raise ValidationError(self.MSG_LIQUIDACAO_MOEDA_PORTADOR)
