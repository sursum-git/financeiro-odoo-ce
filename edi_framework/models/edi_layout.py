from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EdiLayout(models.Model):
    _name = "edi.layout"
    _description = "EDI Layout"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nome", required=True, tracking=True)
    code = fields.Char(string="Código", required=True, index=True, tracking=True)
    version = fields.Char(string="Versão", tracking=True)
    active = fields.Boolean(string="Ativo", default=True, tracking=True)
    backend_id = fields.Many2one("edi.backend", string="Backend", tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Empresa",
        related="backend_id.company_id",
        store=True,
        readonly=True,
    )
    format_type = fields.Selection(
        [
            ("fixed", "Fixo"),
            ("delimited", "Delimitado"),
            ("csv", "CSV"),
            ("json", "JSON"),
            ("xml", "XML"),
        ],
        string="Tipo de Formato",
        required=True,
        tracking=True,
    )
    direction = fields.Selection(
        [("in", "Entrada"), ("out", "Saída"), ("both", "Ambos")],
        string="Direção",
        required=True,
        tracking=True,
    )
    record_length = fields.Integer(string="Tamanho do Registro")
    delimiter = fields.Char(string="Delimitador")
    encoding = fields.Char(string="Codificação", default="utf-8")
    line_ending = fields.Selection([("lf", "LF"), ("crlf", "CRLF")], string="Quebra de Linha")
    root_node = fields.Char(string="Nó Raiz")
    notes = fields.Text(string="Observações")
    record_ids = fields.One2many("edi.layout.record", "layout_id", string="Registros")
    source_ids = fields.One2many("edi.layout.source", "layout_id", string="Fontes")

    _edi_layout_code_backend_uniq = models.Constraint(
        "unique(code, backend_id)",
        "O código do layout deve ser único por backend.",
    )


class EdiLayoutSource(models.Model):
    _name = "edi.layout.source"
    _description = "EDI Layout Source"

    layout_id = fields.Many2one("edi.layout", string="Layout", required=True, ondelete="cascade")
    source_id = fields.Many2one("edi.data.source", string="Fonte", required=True, ondelete="restrict")
    alias = fields.Char(string="Alias", required=True)
    sequence = fields.Integer(string="Sequência", default=10)
    required = fields.Boolean(string="Obrigatório", default=True)
    root_path = fields.Char(string="Caminho Raiz")
    notes = fields.Text(string="Observações")

    _edi_layout_source_alias_uniq = models.Constraint(
        "unique(layout_id, alias)",
        "O alias da fonte deve ser único por layout.",
    )


class EdiLayoutRecord(models.Model):
    _name = "edi.layout.record"
    _description = "EDI Layout Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    layout_id = fields.Many2one("edi.layout", string="Layout", required=True, ondelete="cascade", tracking=True)
    parent_id = fields.Many2one("edi.layout.record", string="Registro Pai", ondelete="cascade")
    child_ids = fields.One2many("edi.layout.record", "parent_id", string="Registros Filhos")
    sequence = fields.Integer(string="Sequência", default=10, tracking=True)
    name = fields.Char(string="Nome", required=True, tracking=True)
    code = fields.Char(string="Código", required=True, tracking=True)
    record_type = fields.Selection(
        [
            ("header", "Cabeçalho"),
            ("detail", "Detalhe"),
            ("trailer", "Rodapé"),
            ("segment", "Segmento"),
            ("object", "Objeto"),
            ("array", "Lista"),
        ],
        string="Tipo de Registro",
        required=True,
        tracking=True,
    )
    record_identifier = fields.Char(string="Identificador do Registro")
    identifier_start_pos = fields.Integer(string="Posição Inicial do Identificador")
    identifier_end_pos = fields.Integer(string="Posição Final do Identificador")
    repeat_mode = fields.Selection([("single", "Único"), ("foreach", "Para Cada")], string="Modo de Repetição", default="single")
    source_alias = fields.Char(string="Alias da Fonte")
    source_path = fields.Char(string="Caminho da Fonte")
    condition_expression = fields.Text(string="Expressão de Condição")
    min_occurs = fields.Integer(string="Ocorrências Mínimas")
    max_occurs = fields.Integer(string="Ocorrências Máximas")
    field_ids = fields.One2many("edi.layout.field", "record_id", string="Campos")

    _edi_layout_record_code_uniq = models.Constraint(
        "unique(layout_id, code)",
        "O código do registro deve ser único por layout.",
    )


class EdiLayoutField(models.Model):
    _name = "edi.layout.field"
    _description = "EDI Layout Field"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    record_id = fields.Many2one("edi.layout.record", string="Registro", required=True, ondelete="cascade", tracking=True)
    sequence = fields.Integer(string="Sequência", default=10, tracking=True)
    name = fields.Char(string="Nome", required=True, tracking=True)
    code = fields.Char(string="Código", required=True, tracking=True)
    technical_name = fields.Char(string="Nome Técnico", tracking=True)
    field_type = fields.Selection(
        [
            ("char", "Texto Curto"),
            ("text", "Texto"),
            ("integer", "Inteiro"),
            ("float", "Decimal"),
            ("monetary", "Monetário"),
            ("date", "Data"),
            ("datetime", "Data e Hora"),
            ("boolean", "Booleano"),
            ("json", "JSON"),
            ("xml", "XML"),
        ],
        string="Tipo de Campo",
        required=True,
        tracking=True,
    )
    required = fields.Boolean(string="Obrigatório", default=False)
    fixed_value = fields.Char(string="Valor Fixo")
    default_value = fields.Char(string="Valor Padrão")
    target_path = fields.Char(string="Caminho de Destino")
    start_pos = fields.Integer(string="Posição Inicial")
    end_pos = fields.Integer(string="Posição Final")
    length = fields.Integer(string="Tamanho")
    column_index = fields.Integer(string="Índice da Coluna")
    align = fields.Selection([("left", "Esquerda"), ("right", "Direita")], string="Alinhamento", default="left")
    pad_char = fields.Char(string="Caractere de Preenchimento", default=" ")
    date_format = fields.Char(string="Formato de Data")
    decimal_places = fields.Integer(string="Casas Decimais")
    decimal_separator = fields.Char(string="Separador Decimal")
    thousand_separator = fields.Char(string="Separador de Milhar")
    truncate = fields.Boolean(string="Truncar", default=False)
    notes = fields.Text(string="Observações")

    _edi_layout_field_code_uniq = models.Constraint(
        "unique(record_id, code)",
        "O código do campo deve ser único por registro.",
    )

    @api.constrains("start_pos", "end_pos", "length")
    def _check_positions(self):
        for record in self:
            if record.start_pos and record.end_pos and record.start_pos > record.end_pos:
                raise ValidationError("A posição inicial do campo deve ser menor ou igual à posição final.")
            if record.start_pos and record.end_pos and record.length:
                expected_length = record.end_pos - record.start_pos + 1
                if record.length != expected_length:
                    raise ValidationError("O tamanho do campo deve corresponder ao intervalo entre posição inicial e final.")
