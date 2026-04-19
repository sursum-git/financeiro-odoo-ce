from odoo.exceptions import ValidationError

from ..components import registry


class TargetService:
    def __init__(self, env):
        self.env = env

    def execute(self, target, payload, context_data=None):
        provider = registry.build(self.env, "target", target.target_type)
        if not provider:
            raise ValidationError(
                f"Tipo de destino ainda não suportado pela camada de providers: {target.target_type}"
            )
        return provider.send(target, payload, context_data=context_data or {})
