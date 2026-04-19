from ..components import registry


class BackendService:
    def __init__(self, env):
        self.env = env

    def get_adapter(self, backend):
        adapter = registry.build(self.env, "backend", backend.backend_type or "generic")
        if adapter:
            return adapter
        return registry.build(self.env, "backend", "generic")

    def get_connection_settings(self, backend, context_data=None):
        adapter = self.get_adapter(backend)
        return adapter.get_connection_settings(backend, context_data=context_data or {})

