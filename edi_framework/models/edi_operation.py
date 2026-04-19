import json

from odoo import fields, models

from ..services import ExchangeService


class EdiExchange(models.Model):
    _name = "edi.exchange"
    _description = "Exchange EDI"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Nome", required=True, tracking=True)
    backend_id = fields.Many2one("edi.backend", string="Backend", required=True, tracking=True)
    layout_id = fields.Many2one("edi.layout", string="Layout", tracking=True)
    exchange_type_id = fields.Many2one("edi.exchange.type", string="Tipo de Exchange", required=True, tracking=True)
    direction = fields.Selection([("in", "Entrada"), ("out", "Saída"), ("both", "Ambos")], string="Direção", tracking=True)
    transaction_id = fields.Many2one("edi.transaction", string="Transação", tracking=True)
    res_model = fields.Char(string="Modelo de Recurso", tracking=True)
    res_id = fields.Integer(string="ID do Recurso", tracking=True)
    current_state_id = fields.Many2one("edi.exchange.state", string="Estado Atual", tracking=True)
    state_code = fields.Char(string="Código do Estado", tracking=True)
    state_kind = fields.Char(string="Tipo do Estado", tracking=True)
    requested_by_id = fields.Many2one("res.users", string="Solicitado por", default=lambda self: self.env.user)
    processed_by_id = fields.Many2one("res.users", string="Processado por")
    started_at = fields.Datetime(string="Iniciado em", default=fields.Datetime.now)
    finished_at = fields.Datetime(string="Finalizado em")
    last_event_at = fields.Datetime(string="Último Evento em")
    has_error = fields.Boolean(string="Com Erro", default=False, tracking=True)
    error_message = fields.Text(string="Mensagem de Erro")
    summary_message = fields.Text(string="Mensagem Resumo")
    external_ref = fields.Char(string="Referência Externa", index=True, tracking=True)
    input_payload_text = fields.Text(string="Payload de Entrada")
    input_payload_format = fields.Char(string="Formato do Payload de Entrada")
    input_filename = fields.Char(string="Nome do Arquivo de Entrada")
    input_metadata_json = fields.Text(string="Metadados do Payload de Entrada")
    company_id = fields.Many2one("res.company", string="Empresa", required=True, tracking=True, default=lambda self: self.env.company)
    job_uuid = fields.Char(string="UUID do Job", index=True)
    job_channel = fields.Char(string="Canal do Job")
    job_identity_key = fields.Char(string="Chave de Idempotência do Job", index=True)
    job_attempt_count = fields.Integer(string="Tentativas do Job", default=0)
    job_started_at = fields.Datetime(string="Job Iniciado em")
    job_finished_at = fields.Datetime(string="Job Finalizado em")
    job_duration_ms = fields.Integer(string="Duração do Job (ms)")
    api_detail_id = fields.One2many("edi.exchange.api", "exchange_id", string="Detalhes de API")
    file_detail_id = fields.One2many("edi.exchange.file", "exchange_id", string="Detalhes de Arquivo")
    payload_ids = fields.One2many("edi.exchange.payload", "exchange_id", string="Payloads")
    source_snapshot_ids = fields.One2many("edi.exchange.source.snapshot", "exchange_id", string="Snapshots de Fonte")
    payload_count = fields.Integer(string="Qtd. Payloads", compute="_compute_dashboard_metrics")
    snapshot_count = fields.Integer(string="Qtd. Snapshots", compute="_compute_dashboard_metrics")
    api_detail_count = fields.Integer(string="Qtd. APIs", compute="_compute_dashboard_metrics")
    file_detail_count = fields.Integer(string="Qtd. Arquivos", compute="_compute_dashboard_metrics")
    log_count = fields.Integer(string="Qtd. Logs", compute="_compute_dashboard_metrics")
    event_count = fields.Integer(string="Qtd. Eventos", compute="_compute_dashboard_metrics")
    last_result_label = fields.Char(string="Último Resultado", compute="_compute_dashboard_metrics")

    def action_enqueue_process(self):
        for exchange in self:
            delay = getattr(exchange, "with_delay", None)
            if callable(delay):
                job = exchange.with_delay(
                    channel=exchange.backend_id.queue_channel or "root.edi",
                    description=f"Processar exchange EDI {exchange.display_name}",
                    identity_key=f"edi.exchange.process:{exchange.id}",
                )._job_process_exchange()
                exchange.write(
                    {
                        "job_uuid": getattr(job, "uuid", False),
                        "job_channel": getattr(job, "channel", False),
                        "job_identity_key": getattr(job, "identity_key", False),
                    }
                )
            else:
                exchange._job_process_exchange()
        return True

    def _compute_dashboard_metrics(self):
        for exchange in self:
            exchange.payload_count = len(exchange.payload_ids)
            exchange.snapshot_count = len(exchange.source_snapshot_ids)
            exchange.api_detail_count = len(exchange.api_detail_id)
            exchange.file_detail_count = len(exchange.file_detail_id)
            exchange.log_count = len(exchange.transaction_id.log_ids)
            exchange.event_count = len(exchange.transaction_id.event_ids)
            if exchange.has_error:
                exchange.last_result_label = "Erro"
            elif exchange.state_kind == "success":
                exchange.last_result_label = "Sucesso"
            elif exchange.state_kind == "processing":
                exchange.last_result_label = "Processando"
            elif exchange.state_kind == "draft":
                exchange.last_result_label = "Rascunho"
            else:
                exchange.last_result_label = exchange.state_kind or "Sem execução"

    def action_run_demo_now(self):
        self.ensure_one()
        self._job_process_exchange()
        return {
            "type": "ir.actions.act_window",
            "name": "Exchange EDI",
            "res_model": "edi.exchange",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def action_open_demo_reset_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Resetar Demo EDI",
            "res_model": "edi.demo.reset.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_exchange_id": self.id,
            },
        }

    def action_reset_demo_state(self, reset_logs=True):
        for exchange in self:
            exchange.payload_ids.unlink()
            exchange.api_detail_id.unlink()
            exchange.file_detail_id.unlink()
            exchange.source_snapshot_ids.unlink()

            transaction = exchange.transaction_id
            if transaction and reset_logs:
                transaction.event_ids.unlink()
                transaction.log_ids.unlink()

            initial_state = exchange.env["edi.exchange.state"].search(
                [
                    ("exchange_type_id", "=", exchange.exchange_type_id.id),
                    ("is_initial", "=", True),
                ],
                order="sequence, id",
                limit=1,
            )
            if not initial_state:
                initial_state = exchange.env["edi.exchange.state"].search(
                    [
                        ("exchange_type_id", "=", exchange.exchange_type_id.id),
                        ("state_kind", "=", "draft"),
                    ],
                    order="sequence, id",
                    limit=1,
                )

            exchange_values = {
                "current_state_id": initial_state.id if initial_state else False,
                "state_code": initial_state.code if initial_state else False,
                "state_kind": initial_state.state_kind if initial_state else False,
                "has_error": False,
                "error_message": False,
                "summary_message": "Cenário demo resetado.",
                "processed_by_id": False,
                "finished_at": False,
                "last_event_at": fields.Datetime.now(),
                "job_uuid": False,
                "job_channel": False,
                "job_identity_key": False,
                "job_attempt_count": 0,
                "job_started_at": False,
                "job_finished_at": False,
                "job_duration_ms": 0,
            }
            exchange.write(exchange_values)

            if transaction:
                transaction.write(
                    {
                        "current_exchange_id": exchange.id,
                        "technical_state": exchange_values["state_code"],
                        "business_state": exchange_values["state_kind"],
                        "current_status_message": "Cenário demo resetado.",
                        "has_error": False,
                        "error_message": False,
                        "waiting_return": False,
                        "last_event_at": fields.Datetime.now(),
                        "finished_at": False,
                    }
                )
        return True

    def _job_process_exchange(self):
        for exchange in self:
            start = fields.Datetime.now()
            service = ExchangeService(self.env)
            exchange.write(
                {
                    "job_attempt_count": exchange.job_attempt_count + 1,
                    "job_started_at": start,
                    "processed_by_id": self.env.user.id,
                    "last_event_at": start,
                }
            )
            try:
                service.process(exchange)
            except Exception as exc:
                service.set_state_by_kind(exchange, "error")
                transaction = service.ensure_transaction(exchange)
                service.sync_transaction(exchange, transaction, [], has_error=True, error_message=str(exc))
                service.store_error_payload(exchange, str(exc))
                service.create_transaction_event(
                    exchange,
                    transaction,
                    event_type="exchange_error",
                    message=str(exc),
                    is_error=True,
                )
                service.create_transaction_log(
                    exchange,
                    transaction,
                    key="processing_error",
                    value=str(exc),
                    log_type="error",
                    message="Erro no processamento da exchange.",
                )
                exchange.write(
                    {
                        "summary_message": "Exchange finalizada com erro.",
                        "has_error": True,
                        "error_message": str(exc),
                    }
                )
                raise
            finally:
                finish = fields.Datetime.now()
                duration = int((finish - start).total_seconds() * 1000)
                exchange.write(
                    {
                        "finished_at": finish,
                        "job_finished_at": finish,
                        "job_duration_ms": duration,
                        "last_event_at": finish,
                    }
                )
        return True

    def _collect_source_results(self):
        self.ensure_one()
        return ExchangeService(self.env).collect_source_results(self)

    def _run_layout_pipeline(self, source_results):
        self.ensure_one()
        return ExchangeService(self.env).run_layout_pipeline(self, source_results)

    def _store_source_snapshots(self, source_results):
        self.ensure_one()
        return ExchangeService(self.env).store_source_snapshots(self, source_results)

    def _store_normalized_payload(self, normalized_rows):
        self.ensure_one()
        return ExchangeService(self.env).store_normalized_payload(self, normalized_rows)

    def _store_error_payload(self, error_message):
        self.ensure_one()
        return ExchangeService(self.env).store_error_payload(self, error_message)

    def _set_state_by_kind(self, state_kind):
        self.ensure_one()
        return ExchangeService(self.env).set_state_by_kind(self, state_kind)

    def _ensure_transaction(self):
        self.ensure_one()
        return ExchangeService(self.env).ensure_transaction(self)

    def _sync_transaction(self, transaction, normalized_rows, has_error=False, error_message=False):
        self.ensure_one()
        return ExchangeService(self.env).sync_transaction(self, transaction, normalized_rows, has_error=has_error, error_message=error_message)

    def _create_transaction_event(self, transaction, event_type, message, is_error=False):
        self.ensure_one()
        return ExchangeService(self.env).create_transaction_event(self, transaction, event_type, message, is_error=is_error)

    def _create_transaction_log(self, transaction, key, value, log_type="info", message=False):
        self.ensure_one()
        return ExchangeService(self.env).create_transaction_log(self, transaction, key, value, log_type=log_type, message=message)


class EdiExchangeApi(models.Model):
    _name = "edi.exchange.api"
    _description = "Detalhe de Exchange API"

    exchange_id = fields.Many2one("edi.exchange", string="Exchange", required=True, ondelete="cascade")
    url = fields.Char(string="URL")
    http_method = fields.Char(string="Método HTTP")
    request_headers = fields.Text(string="Headers da Requisição")
    request_body = fields.Text(string="Body da Requisição")
    response_headers = fields.Text(string="Headers da Resposta")
    response_body = fields.Text(string="Body da Resposta")
    http_status_code = fields.Integer(string="Status HTTP")
    response_time_ms = fields.Integer(string="Tempo de Resposta (ms)")
    content_type = fields.Char(string="Tipo de Conteúdo")
    auth_type = fields.Char(string="Tipo de Autenticação")
    remote_status = fields.Char(string="Status Remoto")
    callback_url = fields.Char(string="URL de Callback")
    protocol_number = fields.Char(string="Número de Protocolo")


class EdiExchangeFile(models.Model):
    _name = "edi.exchange.file"
    _description = "Detalhe de Exchange Arquivo"

    exchange_id = fields.Many2one("edi.exchange", string="Exchange", required=True, ondelete="cascade")
    file_name = fields.Char(string="Nome do Arquivo")
    file_path = fields.Char(string="Caminho do Arquivo")
    file_binary = fields.Binary(string="Arquivo")
    file_size = fields.Integer(string="Tamanho do Arquivo")
    file_hash = fields.Char(string="Hash do Arquivo", index=True)
    file_format = fields.Char(string="Formato do Arquivo")
    encoding = fields.Char(string="Codificação")
    line_count = fields.Integer(string="Quantidade de Linhas")
    record_count = fields.Integer(string="Quantidade de Registros")
    generated_at = fields.Datetime(string="Gerado em")
    sent_at = fields.Datetime(string="Enviado em")
    received_at = fields.Datetime(string="Recebido em")
    processed_at = fields.Datetime(string="Processado em")


class EdiExchangePayload(models.Model):
    _name = "edi.exchange.payload"
    _description = "Payload de Exchange"

    exchange_id = fields.Many2one("edi.exchange", string="Exchange", required=True, ondelete="cascade")
    payload_type = fields.Selection(
        [
            ("request", "Requisição"),
            ("response", "Resposta"),
            ("generated_file", "Arquivo Gerado"),
            ("raw_input", "Entrada Bruta"),
            ("normalized", "Normalizado"),
            ("error", "Erro"),
            ("authorized_xml", "XML Autorizado"),
        ],
        string="Tipo de Payload",
        required=True,
    )
    name = fields.Char(string="Nome")
    content_text = fields.Text(string="Conteúdo Texto")
    content_binary = fields.Binary(string="Conteúdo Binário")
    mimetype = fields.Char(string="Mimetype")
    hash = fields.Char(string="Hash")
    created_at = fields.Datetime(string="Criado em", default=fields.Datetime.now)
    user_id = fields.Many2one("res.users", string="Usuário", default=lambda self: self.env.user)


class EdiExchangeSourceSnapshot(models.Model):
    _name = "edi.exchange.source.snapshot"
    _description = "Snapshot de Fonte da Exchange"

    exchange_id = fields.Many2one("edi.exchange", string="Exchange", required=True, ondelete="cascade")
    source_id = fields.Many2one("edi.data.source", string="Fonte", required=True)
    params_json = fields.Text(string="Parâmetros (JSON)")
    raw_payload = fields.Text(string="Payload Bruto")
    normalized_payload = fields.Text(string="Payload Normalizado")
    payload_hash = fields.Char(string="Hash do Payload", index=True)
    user_id = fields.Many2one("res.users", string="Usuário", default=lambda self: self.env.user)
    captured_at = fields.Datetime(string="Capturado em", default=fields.Datetime.now)


class EdiTransaction(models.Model):
    _name = "edi.transaction"
    _description = "Transação EDI"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Nome", required=True, tracking=True)
    transaction_type = fields.Char(string="Tipo de Transação", required=True, tracking=True)
    backend_id = fields.Many2one("edi.backend", string="Backend", tracking=True)
    exchange_type_id = fields.Many2one("edi.exchange.type", string="Tipo de Exchange", tracking=True)
    res_model = fields.Char(string="Modelo de Recurso", required=True, tracking=True)
    res_id = fields.Integer(string="ID do Recurso", required=True, tracking=True)
    current_exchange_id = fields.Many2one("edi.exchange", string="Exchange Atual", tracking=True)
    exchange_ids = fields.One2many("edi.exchange", "transaction_id", string="Exchanges")
    technical_state = fields.Char(string="Estado Técnico", tracking=True)
    business_state = fields.Char(string="Estado de Negócio", tracking=True)
    external_ref = fields.Char(string="Referência Externa", index=True, tracking=True)
    current_status_message = fields.Text(string="Mensagem de Status Atual")
    waiting_return = fields.Boolean(string="Aguardando Retorno", default=False, tracking=True)
    has_error = fields.Boolean(string="Com Erro", default=False, tracking=True)
    error_message = fields.Text(string="Mensagem de Erro")
    lock_delete = fields.Boolean(string="Bloquear Exclusão", default=False, tracking=True)
    lock_manual_payment = fields.Boolean(string="Bloquear Pagamento Manual", default=False, tracking=True)
    lock_edit = fields.Boolean(string="Bloquear Edição", default=False, tracking=True)
    lock_cancel = fields.Boolean(string="Bloquear Cancelamento", default=False, tracking=True)
    company_id = fields.Many2one("res.company", string="Empresa", required=True, tracking=True, default=lambda self: self.env.company)
    created_by_id = fields.Many2one("res.users", string="Criado por", default=lambda self: self.env.user)
    started_at = fields.Datetime(string="Iniciado em", default=fields.Datetime.now, tracking=True)
    last_event_at = fields.Datetime(string="Último Evento em", tracking=True)
    finished_at = fields.Datetime(string="Finalizado em", tracking=True)
    event_ids = fields.One2many("edi.transaction.event", "transaction_id", string="Eventos")
    log_ids = fields.One2many("edi.transaction.log", "transaction_id", string="Logs")
    exchange_count = fields.Integer(string="Qtd. Exchanges", compute="_compute_audit_metrics")
    event_count = fields.Integer(string="Qtd. Eventos", compute="_compute_audit_metrics")
    log_count = fields.Integer(string="Qtd. Logs", compute="_compute_audit_metrics")

    def _compute_audit_metrics(self):
        for transaction in self:
            transaction.exchange_count = len(transaction.exchange_ids)
            transaction.event_count = len(transaction.event_ids)
            transaction.log_count = len(transaction.log_ids)

    def action_open_exchanges(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Exchanges",
            "res_model": "edi.exchange",
            "view_mode": "list,form",
            "domain": [("transaction_id", "=", self.id)],
            "context": {"default_transaction_id": self.id},
        }

    def action_open_events(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Eventos da Transação",
            "res_model": "edi.transaction.event",
            "view_mode": "list,form",
            "domain": [("transaction_id", "=", self.id)],
            "context": {"default_transaction_id": self.id},
        }

    def action_open_logs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Logs da Transação",
            "res_model": "edi.transaction.log",
            "view_mode": "list,form",
            "domain": [("transaction_id", "=", self.id)],
            "context": {"default_transaction_id": self.id},
        }


class EdiTransactionEvent(models.Model):
    _name = "edi.transaction.event"
    _description = "Evento da Transação EDI"
    _order = "event_datetime desc"

    transaction_id = fields.Many2one("edi.transaction", string="Transação", required=True, index=True, ondelete="cascade")
    exchange_id = fields.Many2one("edi.exchange", string="Exchange", index=True)
    event_type = fields.Char(string="Tipo de Evento", required=True, index=True)
    event_code = fields.Char(string="Código do Evento", index=True)
    technical_state_from = fields.Char(string="Estado Técnico Origem")
    technical_state_to = fields.Char(string="Estado Técnico Destino")
    business_state_from = fields.Char(string="Estado de Negócio Origem")
    business_state_to = fields.Char(string="Estado de Negócio Destino")
    message = fields.Text(string="Mensagem", required=True)
    event_datetime = fields.Datetime(string="Data/Hora do Evento", default=fields.Datetime.now, required=True, index=True)
    user_id = fields.Many2one("res.users", string="Usuário", default=lambda self: self.env.user)
    is_error = fields.Boolean(string="É Erro", default=False)


class EdiTransactionLog(models.Model):
    _name = "edi.transaction.log"
    _description = "Log da Transação EDI"
    _order = "log_datetime desc"

    transaction_id = fields.Many2one("edi.transaction", string="Transação", required=True, index=True, ondelete="cascade")
    exchange_id = fields.Many2one("edi.exchange", string="Exchange", index=True)
    log_type = fields.Selection(
        [
            ("info", "Informação"),
            ("warning", "Aviso"),
            ("error", "Erro"),
            ("state", "Estado"),
            ("payload", "Payload"),
            ("business", "Negócio"),
            ("technical", "Técnico"),
        ],
        string="Tipo de Log",
        default="info",
        index=True,
    )
    key = fields.Char(string="Chave", required=True, index=True)
    value = fields.Text(string="Valor")
    value_type = fields.Selection(
        [
            ("char", "Texto Curto"),
            ("text", "Texto"),
            ("int", "Inteiro"),
            ("float", "Decimal"),
            ("bool", "Booleano"),
            ("json", "JSON"),
            ("xml", "XML"),
            ("date", "Data"),
            ("datetime", "Data e Hora"),
        ],
        string="Tipo de Valor",
        default="char",
    )
    log_datetime = fields.Datetime(string="Data/Hora do Log", default=fields.Datetime.now, index=True)
    user_id = fields.Many2one("res.users", string="Usuário", default=lambda self: self.env.user)
    message = fields.Char(string="Mensagem")
