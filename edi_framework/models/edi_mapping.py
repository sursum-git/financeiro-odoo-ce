import json

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..core import MappingPipeline
from ..services import SourceService


class EdiTransformRule(models.Model):
    _name = "edi.transform.rule"
    _description = "EDI Transform Rule"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nome", required=True, tracking=True)
    code = fields.Char(string="Código", required=True, tracking=True)
    active = fields.Boolean(string="Ativo", default=True, tracking=True)
    rule_type = fields.Char(string="Tipo de Regra", required=True, tracking=True)
    direction = fields.Selection(
        [("input", "Entrada"), ("output", "Saída"), ("both", "Ambos")],
        string="Direção",
        default="both",
        tracking=True,
    )
    param_schema_json = fields.Text(string="Schema de Parâmetros (JSON)")
    description = fields.Text(string="Descrição", tracking=True)
    allow_safe_eval = fields.Boolean(string="Permitir Safe Eval", default=False, tracking=True)

    _edi_transform_rule_code_uniq = models.Constraint(
        "unique(code)",
        "O código da regra de transformação deve ser único.",
    )

    def to_transform_spec(self, params=None):
        self.ensure_one()
        params = params or {}
        spec = {"type": self.code}
        spec.update(params)
        if self.code.startswith("cast_") and "target" not in spec:
            spec["target"] = self.code.replace("cast_", "", 1)
        return spec


class EdiValueMap(models.Model):
    _name = "edi.value.map"
    _description = "EDI Value Map"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nome", required=True, tracking=True)
    code = fields.Char(string="Código", tracking=True)
    transform_rule_id = fields.Many2one("edi.transform.rule", string="Regra de Transformação")
    source_value = fields.Char(string="Valor de Origem", required=True)
    target_value = fields.Char(string="Valor de Destino", required=True)
    reverse_source_value = fields.Char(string="Valor Reverso de Origem")
    reverse_target_value = fields.Char(string="Valor Reverso de Destino")
    active = fields.Boolean(string="Ativo", default=True)


class EdiExtractMap(models.Model):
    _name = "edi.extract.map"
    _description = "EDI Extract Map"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    layout_id = fields.Many2one("edi.layout", string="Layout", required=True, tracking=True, ondelete="cascade")
    record_id = fields.Many2one("edi.layout.record", string="Registro", required=True, tracking=True, ondelete="cascade")
    field_id = fields.Many2one("edi.layout.field", string="Campo", required=True, tracking=True, ondelete="cascade")
    sequence = fields.Integer(string="Sequência", default=10, tracking=True)
    source_alias = fields.Char(string="Alias da Fonte", tracking=True)
    source_path = fields.Char(string="Caminho da Fonte", tracking=True)
    source_type = fields.Selection(
        [
            ("path", "Caminho"),
            ("fixed", "Fixo"),
            ("context", "Contexto"),
            ("expression", "Expressão"),
            ("sequence", "Sequência"),
            ("aggregate", "Agregação"),
        ],
        string="Tipo de Origem",
        default="path",
        tracking=True,
    )
    expression = fields.Text(string="Expressão")
    required = fields.Boolean(string="Obrigatório", default=False)
    default_value = fields.Char(string="Valor Padrão")
    condition_expression = fields.Text(string="Expressão de Condição")
    rule_line_ids = fields.One2many("edi.map.rule.line", "extract_map_id", string="Linhas de Regra")

    def to_pipeline_mapping(self):
        self.ensure_one()
        transforms = [line.to_transform_spec() for line in self.rule_line_ids.sorted("sequence")]
        return {
            "source": self.source_path or self.field_id.technical_name or self.field_id.code,
            "target": self.field_id.target_path or self.field_id.technical_name or self.field_id.code,
            "default": self.default_value,
            "transforms": transforms,
        }

    def apply_pipeline(self, dataset):
        pipeline = MappingPipeline()
        return pipeline.run(dataset, [mapping.to_pipeline_mapping() for mapping in self.sorted("sequence")])


class EdiReturnMap(models.Model):
    _name = "edi.return.map"
    _description = "EDI Return Map"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    layout_id = fields.Many2one("edi.layout", string="Layout", required=True, tracking=True, ondelete="cascade")
    record_id = fields.Many2one("edi.layout.record", string="Registro", required=True, tracking=True, ondelete="cascade")
    field_id = fields.Many2one("edi.layout.field", string="Campo", required=True, tracking=True, ondelete="cascade")
    sequence = fields.Integer(string="Sequência", default=10, tracking=True)
    target_id = fields.Many2one("edi.data.target", string="Destino", tracking=True)
    target_alias = fields.Char(string="Alias do Destino", tracking=True)
    target_model = fields.Char(string="Modelo de Destino", tracking=True)
    target_field = fields.Char(string="Campo de Destino", tracking=True)
    target_path = fields.Char(string="Caminho de Destino", tracking=True)
    apply_mode = fields.Selection(
        [
            ("stage_only", "Apenas Staging"),
            ("create", "Criar"),
            ("update", "Atualizar"),
            ("match_update", "Localizar e Atualizar"),
            ("upsert", "Upsert"),
            ("call_provider", "Chamar Provider"),
        ],
        string="Modo de Aplicação",
        default="stage_only",
        tracking=True,
    )
    match_rule_code = fields.Char(string="Código da Regra de Correspondência")
    required = fields.Boolean(string="Obrigatório", default=False)
    condition_expression = fields.Text(string="Expressão de Condição")
    rule_line_ids = fields.One2many("edi.map.rule.line", "return_map_id", string="Linhas de Regra")


class EdiMapRuleLine(models.Model):
    _name = "edi.map.rule.line"
    _description = "EDI Map Rule Line"

    extract_map_id = fields.Many2one("edi.extract.map", string="Mapa de Extração", ondelete="cascade")
    return_map_id = fields.Many2one("edi.return.map", string="Mapa de Retorno", ondelete="cascade")
    sequence = fields.Integer(string="Sequência", default=10)
    transform_rule_id = fields.Many2one("edi.transform.rule", string="Regra de Transformação", required=True, ondelete="restrict")
    params_json = fields.Text(string="Parâmetros (JSON)")
    stop_on_error = fields.Boolean(string="Parar em Caso de Erro", default=True)
    condition_expression = fields.Text(string="Expressão de Condição")

    @api.constrains("extract_map_id", "return_map_id")
    def _check_map_pointer(self):
        for record in self:
            if bool(record.extract_map_id) == bool(record.return_map_id):
                raise ValidationError("A linha de regra deve apontar para exatamente um entre extract_map_id e return_map_id.")

    def to_transform_spec(self):
        self.ensure_one()
        params = {}
        if self.params_json:
            params = json.loads(self.params_json)
        return self.transform_rule_id.to_transform_spec(params)


class EdiDataSource(models.Model):
    _name = "edi.data.source"
    _description = "EDI Data Source"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nome", required=True, tracking=True)
    code = fields.Char(string="Código", required=True, tracking=True)
    active = fields.Boolean(string="Ativo", default=True, tracking=True)
    source_type = fields.Selection(
        [
            ("odoo_model", "Modelo Odoo"),
            ("sql_view", "View SQL"),
            ("sql_query", "Consulta SQL"),
            ("sql_procedure", "Procedure SQL"),
            ("api", "API"),
            ("python", "Python"),
            ("csv", "CSV"),
            ("json", "JSON"),
            ("xml", "XML"),
            ("array", "Lista"),
        ],
        string="Tipo de Fonte",
        required=True,
        tracking=True,
    )
    result_mode = fields.Selection(
        [("single", "Único"), ("list", "Lista"), ("tree", "Árvore"), ("tables", "Tabelas")],
        string="Modo de Resultado",
        default="list",
        tracking=True,
    )
    root_alias = fields.Char(string="Alias Raiz", default="root")
    params_json = fields.Text(string="Parâmetros da Fonte (JSON)")
    python_code = fields.Text(string="Código Python da Fonte")
    company_id = fields.Many2one("res.company", string="Empresa", required=True, tracking=True, default=lambda self: self.env.company)
    notes = fields.Text(string="Observações")

    def execute_source(self, context_data=None):
        self.ensure_one()
        return SourceService(self.env).execute(self, context_data=context_data or {})


class EdiDataTarget(models.Model):
    _name = "edi.data.target"
    _description = "EDI Data Target"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Nome", required=True, tracking=True)
    code = fields.Char(string="Código", required=True, tracking=True)
    active = fields.Boolean(string="Ativo", default=True, tracking=True)
    target_type = fields.Selection(
        [
            ("odoo_model", "Modelo Odoo"),
            ("sql_table", "Tabela SQL"),
            ("sql_procedure", "Procedure SQL"),
            ("api", "API"),
            ("python", "Python"),
            ("file", "Arquivo"),
            ("staging", "Staging"),
        ],
        string="Tipo de Destino",
        required=True,
        tracking=True,
    )
    params_json = fields.Text(string="Parâmetros do Destino (JSON)")
    python_code = fields.Text(string="Código Python do Destino")
    company_id = fields.Many2one("res.company", string="Empresa", required=True, tracking=True, default=lambda self: self.env.company)
    notes = fields.Text(string="Observações")
