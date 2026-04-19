import json

from .base import BaseProvider
from .registry import registry


class BaseBackendAdapter(BaseProvider):
    usage = "backend"

    def get_connection_settings(self, backend, context_data=None):
        settings = json.loads(backend.config_json or "{}")
        settings.setdefault("backend_code", backend.code)
        settings.setdefault("backend_type", backend.backend_type)
        return settings


class GenericBackendAdapter(BaseBackendAdapter):
    provider_type = "generic"


class ApiBackendAdapter(BaseBackendAdapter):
    provider_type = "api"


class FileBackendAdapter(BaseBackendAdapter):
    provider_type = "file"


registry.register("backend", GenericBackendAdapter.provider_type, GenericBackendAdapter)
registry.register("backend", ApiBackendAdapter.provider_type, ApiBackendAdapter)
registry.register("backend", FileBackendAdapter.provider_type, FileBackendAdapter)

