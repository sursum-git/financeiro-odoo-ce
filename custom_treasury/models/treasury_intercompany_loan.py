from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryIntercompanyLoan(models.Model):
    _name = "treasury.intercompany.loan"
    _description = "Treasury Intercompany Loan"
    _order = "date desc, id desc"

    MSG_VALOR_POSITIVO = "O valor do mutuo deve ser positivo."
    MSG_EMPRESAS_DIFERENTES = "A empresa credora e a empresa devedora devem ser diferentes."
    MSG_MESMO_GRUPO = "O mutuo so pode ser realizado entre empresas do mesmo grupo empresarial."
    MSG_ORIGEM_OBRIGATORIA = "O mutuo exige conta ou portador de origem na empresa credora."
    MSG_DESTINO_OBRIGATORIO = "O mutuo exige conta ou portador de destino na empresa devedora."
    MSG_CONTA_ORIGEM_EMPRESA = "A conta de origem deve pertencer a empresa credora."
    MSG_PORTADOR_ORIGEM_EMPRESA = "O portador de origem deve pertencer a empresa credora."
    MSG_CONTA_DESTINO_EMPRESA = "A conta de destino deve pertencer a empresa devedora."
    MSG_PORTADOR_DESTINO_EMPRESA = "O portador de destino deve pertencer a empresa devedora."
    MSG_MOEDA_BASE_EMPRESA = (
        "Enquanto o controle multimoeda nao estiver implementado, o mutuo exige empresas com a mesma moeda base."
    )
    MSG_MOEDA_MOVIMENTO_EMPRESA = (
        "Enquanto o controle multimoeda nao estiver implementado, a moeda do mutuo deve ser igual a moeda base das empresas."
    )
    MSG_CANCELAMENTO_SOMENTE_CONFIRMADO = "Somente mutuos confirmados podem ser cancelados."
    MSG_MOVIMENTOS_NAO_GERADOS = "Os movimentos do mutuo nao foram gerados."

    name = fields.Char(required=True, index=True)
    date = fields.Date(required=True, default=fields.Date.context_today, index=True)
    lender_company_id = fields.Many2one(
        "res.company",
        string="Empresa Credora",
        required=True,
        default=lambda self: self.env.company,
        ondelete="restrict",
        index=True,
    )
    borrower_company_id = fields.Many2one(
        "res.company",
        string="Empresa Devedora",
        required=True,
        ondelete="restrict",
        index=True,
    )
    source_account_id = fields.Many2one(
        "treasury.account",
        string="Conta de Origem",
        ondelete="restrict",
        index=True,
    )
    source_portador_id = fields.Many2one(
        "financial.portador",
        string="Portador de Origem",
        ondelete="restrict",
        index=True,
    )
    target_account_id = fields.Many2one(
        "treasury.account",
        string="Conta de Destino",
        ondelete="restrict",
        index=True,
    )
    target_portador_id = fields.Many2one(
        "financial.portador",
        string="Portador de Destino",
        ondelete="restrict",
        index=True,
    )
    amount = fields.Monetary(required=True, currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
        ondelete="restrict",
    )
    state = fields.Selection(
        [
            ("draft", "Rascunho"),
            ("confirmed", "Confirmado"),
            ("cancelled", "Cancelado"),
        ],
        required=True,
        default="draft",
        index=True,
    )
    notes = fields.Text()
    out_movement_id = fields.Many2one(
        "treasury.movement",
        string="Movimento de Saida",
        ondelete="restrict",
        index=True,
    )
    in_movement_id = fields.Many2one(
        "treasury.movement",
        string="Movimento de Entrada",
        ondelete="restrict",
        index=True,
    )

    @property
    def _movement_service(self):
        return self.env["treasury.movement.service"]

    def _get_company_group_root(self, company):
        current = company
        while current.parent_id:
            current = current.parent_id
        return current

    def _companies_share_group(self, lender_company, borrower_company):
        return self._get_company_group_root(lender_company) == self._get_company_group_root(
            borrower_company
        )

    @api.constrains(
        "lender_company_id",
        "borrower_company_id",
        "source_account_id",
        "source_portador_id",
        "target_account_id",
        "target_portador_id",
        "amount",
        "currency_id",
    )
    def _check_business_rules(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(self.MSG_VALOR_POSITIVO)
            if record.lender_company_id == record.borrower_company_id:
                raise ValidationError(self.MSG_EMPRESAS_DIFERENTES)
            if not self._companies_share_group(record.lender_company_id, record.borrower_company_id):
                raise ValidationError(self.MSG_MESMO_GRUPO)
            if not record.source_account_id and not record.source_portador_id:
                raise ValidationError(self.MSG_ORIGEM_OBRIGATORIA)
            if not record.target_account_id and not record.target_portador_id:
                raise ValidationError(self.MSG_DESTINO_OBRIGATORIO)
            if (
                record.source_account_id
                and record.source_account_id.company_id != record.lender_company_id
            ):
                raise ValidationError(self.MSG_CONTA_ORIGEM_EMPRESA)
            if (
                record.source_portador_id
                and record.source_portador_id.company_id
                and record.source_portador_id.company_id != record.lender_company_id
            ):
                raise ValidationError(self.MSG_PORTADOR_ORIGEM_EMPRESA)
            if (
                record.target_account_id
                and record.target_account_id.company_id != record.borrower_company_id
            ):
                raise ValidationError(self.MSG_CONTA_DESTINO_EMPRESA)
            if (
                record.target_portador_id
                and record.target_portador_id.company_id
                and record.target_portador_id.company_id != record.borrower_company_id
            ):
                raise ValidationError(self.MSG_PORTADOR_DESTINO_EMPRESA)
            if record.lender_company_id.currency_id != record.borrower_company_id.currency_id:
                raise ValidationError(self.MSG_MOEDA_BASE_EMPRESA)
            if record.currency_id != record.lender_company_id.currency_id:
                raise ValidationError(self.MSG_MOEDA_MOVIMENTO_EMPRESA)

    def action_confirm(self):
        for record in self:
            if record.state != "draft":
                continue
            record._check_business_rules()
            out_move = record._movement_service.create_movement(
                {
                    "name": f"{record.name} - Mutuo Concedido",
                    "date": record.date,
                    "company_id": record.lender_company_id.id,
                    "type": "saida",
                    "amount": record.amount,
                    "currency_id": record.currency_id.id,
                    "account_id": record.source_account_id.id,
                    "portador_id": record.source_portador_id.id,
                    "origin_module": "custom_treasury",
                    "origin_model": "treasury.intercompany.loan",
                    "origin_record_id": record.id,
                }
            )
            in_move = record._movement_service.create_movement(
                {
                    "name": f"{record.name} - Mutuo Recebido",
                    "date": record.date,
                    "company_id": record.borrower_company_id.id,
                    "type": "entrada",
                    "amount": record.amount,
                    "currency_id": record.currency_id.id,
                    "account_id": record.target_account_id.id,
                    "portador_id": record.target_portador_id.id,
                    "origin_module": "custom_treasury",
                    "origin_model": "treasury.intercompany.loan",
                    "origin_record_id": record.id,
                }
            )
            record._movement_service.post_movement(out_move)
            record._movement_service.post_movement(in_move)
            record.write(
                {
                    "state": "confirmed",
                    "out_movement_id": out_move.id,
                    "in_movement_id": in_move.id,
                }
            )

    def action_cancel(self):
        for record in self:
            if record.state != "confirmed":
                raise UserError(self.MSG_CANCELAMENTO_SOMENTE_CONFIRMADO)
            if not record.out_movement_id or not record.in_movement_id:
                raise UserError(self.MSG_MOVIMENTOS_NAO_GERADOS)
            record._movement_service.reverse_movement(record.out_movement_id)
            record._movement_service.reverse_movement(record.in_movement_id)
            record.state = "cancelled"
