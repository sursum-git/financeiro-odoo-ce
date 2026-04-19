from odoo.exceptions import ValidationError

from ..components import registry


class SourceService:
    def __init__(self, env):
        self.env = env

    def execute(self, source, context_data=None):
        provider = registry.build(self.env, "source", source.source_type)
        if not provider:
            raise ValidationError(
                f"Tipo de fonte ainda não suportado pela camada de providers: {source.source_type}"
            )
        return provider.fetch(source, context_data=context_data or {})

