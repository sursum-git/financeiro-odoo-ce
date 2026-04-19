import json

from odoo.exceptions import ValidationError

from .base import BaseTargetProvider
from .registry import registry


class StagingTargetProvider(BaseTargetProvider):
    provider_type = "staging"

    def send(self, target, payload, context_data=None):
        return {
            "target_type": target.target_type,
            "mode": "staging",
            "status": "accepted",
            "payload_count": len(payload or []),
            "payload": payload or [],
        }


class ApiTargetProvider(BaseTargetProvider):
    provider_type = "api"

    def send(self, target, payload, context_data=None):
        params = json.loads(target.params_json or "{}")
        return {
            "target_type": target.target_type,
            "mode": "api",
            "status": "accepted",
            "endpoint": params.get("endpoint"),
            "method": params.get("method", "POST"),
            "payload_count": len(payload or []),
            "payload": payload or [],
        }


class FileTargetProvider(BaseTargetProvider):
    provider_type = "file"

    def send(self, target, payload, context_data=None):
        params = json.loads(target.params_json or "{}")
        return {
            "target_type": target.target_type,
            "mode": "file",
            "status": "generated",
            "file_name": params.get("file_name", "edi_payload.json"),
            "payload_count": len(payload or []),
            "payload": payload or [],
        }


class PythonTargetProvider(BaseTargetProvider):
    provider_type = "python"

    def send(self, target, payload, context_data=None):
        localdict = {"payload": payload or [], "context": context_data or {}, "result": {}}
        safe_globals = {"__builtins__": {}, "json": json, "len": len}
        exec(target.python_code or "result = {'status': 'accepted', 'payload': payload}", safe_globals, localdict)
        result = localdict.get("result", {})
        if not isinstance(result, dict):
            raise ValidationError("O destino Python deve preencher a variável 'result' com um dicionário.")
        result.setdefault("target_type", target.target_type)
        result.setdefault("payload", payload or [])
        return result


registry.register("target", StagingTargetProvider.provider_type, StagingTargetProvider)
registry.register("target", ApiTargetProvider.provider_type, ApiTargetProvider)
registry.register("target", FileTargetProvider.provider_type, FileTargetProvider)
registry.register("target", PythonTargetProvider.provider_type, PythonTargetProvider)
