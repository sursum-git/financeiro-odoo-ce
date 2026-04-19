from odoo import fields, models


class EdiBackend(models.Model):
    _name = "edi.backend"
    _description = "EDI Backend"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"

    name = fields.Char(string="Nome", required=True, tracking=True)
    code = fields.Char(string="Código", required=True, index=True, tracking=True)
    active = fields.Boolean(string="Ativo", default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        required=True,
        tracking=True,
        default=lambda self: self.env.company,
    )
    partner_id = fields.Many2one("res.partner", string="Parceiro", tracking=True)
    backend_type = fields.Selection(
        [("generic", "Genérico"), ("api", "API"), ("file", "Arquivo")],
        string="Tipo de Backend",
        default="generic",
        required=True,
        tracking=True,
    )
    config_json = fields.Text(string="Configuração do Backend (JSON)")
    default_layout_id = fields.Many2one("edi.layout", string="Layout Padrão", tracking=True)
    default_exchange_type_id = fields.Many2one(
        "edi.exchange.type",
        string="Tipo de Exchange Padrão",
        tracking=True,
    )
    queue_channel = fields.Char(string="Canal da Fila", default="root.edi", tracking=True)
    auto_use_queue = fields.Boolean(string="Usar Fila Automaticamente", default=True, tracking=True)
    description = fields.Text(string="Descrição", tracking=True)

    _edi_backend_code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        "O código do backend deve ser único por empresa.",
    )


class EdiProcess(models.Model):
    _name = "edi.process"
    _description = "EDI Process"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nome", required=True, tracking=True)
    code = fields.Char(string="Código", required=True, index=True, tracking=True)
    active = fields.Boolean(string="Ativo", default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        required=True,
        tracking=True,
        default=lambda self: self.env.company,
    )
    backend_id = fields.Many2one("edi.backend", string="Backend", required=True, tracking=True)
    exchange_type_id = fields.Many2one("edi.exchange.type", string="Tipo de Exchange", required=True, tracking=True)
    layout_id = fields.Many2one("edi.layout", string="Layout", required=True, tracking=True)
    direction = fields.Selection(
        [("in", "Entrada"), ("out", "Saída"), ("both", "Ambos")],
        string="Direção",
        tracking=True,
    )
    model_name = fields.Char(string="Modelo Permitido", tracking=True)
    auto_enqueue = fields.Boolean(string="Enfileirar Automaticamente", default=True, tracking=True)
    description = fields.Text(string="Descrição", tracking=True)

    _edi_process_code_company_uniq = models.Constraint(
        "unique(code, company_id)",
        "O código do processo EDI deve ser único por empresa.",
    )


class EdiExchangeType(models.Model):
    _name = "edi.exchange.type"
    _description = "EDI Exchange Type"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nome", required=True, tracking=True)
    code = fields.Char(string="Código", required=True, tracking=True)
    category = fields.Selection(
        [
            ("api", "API"),
            ("file_generate", "Geração de Arquivo"),
            ("file_import", "Importação de Arquivo"),
            ("webhook", "Webhook"),
            ("manual", "Manual"),
            ("query", "Consulta"),
        ],
        string="Categoria",
        required=True,
        tracking=True,
    )
    direction = fields.Selection(
        [("in", "Entrada"), ("out", "Saída"), ("both", "Ambos")],
        string="Direção",
        required=True,
        tracking=True,
    )
    detail_model = fields.Char(string="Modelo de Detalhe", tracking=True)
    default_initial_state_id = fields.Many2one("edi.exchange.state", string="Estado Inicial Padrão", tracking=True)
    active = fields.Boolean(string="Ativo", default=True, tracking=True)


class EdiExchangeState(models.Model):
    _name = "edi.exchange.state"
    _description = "EDI Exchange State"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    exchange_type_id = fields.Many2one("edi.exchange.type", string="Tipo de Exchange", required=True, tracking=True)
    name = fields.Char(string="Nome", required=True, tracking=True)
    code = fields.Char(string="Código", required=True, tracking=True)
    sequence = fields.Integer(string="Sequência", default=10)
    state_kind = fields.Selection(
        [
            ("draft", "Rascunho"),
            ("processing", "Processando"),
            ("waiting", "Aguardando"),
            ("success", "Sucesso"),
            ("error", "Erro"),
            ("cancelled", "Cancelado"),
        ],
        string="Tipo de Estado",
        required=True,
        tracking=True,
    )
    is_initial = fields.Boolean(string="É Inicial", default=False)
    is_final = fields.Boolean(string="É Final", default=False)
    is_error = fields.Boolean(string="É Erro", default=False)
    is_waiting = fields.Boolean(string="É Aguardando", default=False)
    message_template = fields.Text(string="Template de Mensagem")
    technical_code = fields.Char(string="Código Técnico")
