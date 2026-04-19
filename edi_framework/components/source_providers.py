import json
import csv
from io import StringIO
from xml.etree import ElementTree as ET

from odoo.exceptions import ValidationError

from .base import BaseSourceProvider
from .registry import registry


def _context_payload(context_data):
    context_data = context_data or {}
    return context_data.get("input_payload")


def _context_payload_format(context_data):
    context_data = context_data or {}
    return context_data.get("input_payload_format")


class ArraySourceProvider(BaseSourceProvider):
    provider_type = "array"

    def fetch(self, source, context_data=None):
        payload_override = _context_payload(context_data)
        if payload_override is not None:
            if not isinstance(payload_override, list):
                raise ValidationError("O payload externo para fonte array deve ser uma lista.")
            return payload_override
        payload = json.loads(source.params_json or "{}")
        rows = payload.get("rows", [])
        if not isinstance(rows, list):
            raise ValidationError("A fonte do tipo lista deve fornecer 'rows' como lista.")
        return rows


class PythonSourceProvider(BaseSourceProvider):
    provider_type = "python"

    def fetch(self, source, context_data=None):
        localdict = {"context": context_data or {}, "result": []}
        safe_globals = {"__builtins__": {}, "json": json}
        exec(source.python_code or "result = []", safe_globals, localdict)
        result = localdict.get("result", [])
        if not isinstance(result, list):
            raise ValidationError("A fonte Python deve preencher a variável 'result' com uma lista.")
        return result


class ApiSourceProvider(BaseSourceProvider):
    provider_type = "api"

    def fetch(self, source, context_data=None):
        payload_override = _context_payload(context_data)
        if payload_override is not None:
            if not isinstance(payload_override, list):
                raise ValidationError("O payload externo para fonte API deve ser uma lista de registros.")
            return payload_override
        payload = json.loads(source.params_json or "{}")
        rows = payload.get("rows")
        if rows is None:
            rows = payload.get("response_rows", [])
        if not isinstance(rows, list):
            raise ValidationError(
                "A fonte do tipo API deve fornecer 'rows' ou 'response_rows' como lista."
            )
        return rows


class JsonSourceProvider(BaseSourceProvider):
    provider_type = "json"

    def fetch(self, source, context_data=None):
        payload_override = _context_payload(context_data)
        if payload_override is None:
            payload = json.loads(source.params_json or "{}")
            payload_override = payload.get("rows", payload.get("data", payload))
        if isinstance(payload_override, str):
            payload_override = json.loads(payload_override)
        if isinstance(payload_override, dict):
            rows = payload_override.get("rows", payload_override.get("data", [payload_override]))
        elif isinstance(payload_override, list):
            rows = payload_override
        else:
            raise ValidationError("A fonte JSON deve resultar em um objeto ou lista.")
        if not isinstance(rows, list):
            raise ValidationError("A fonte JSON deve produzir uma lista de registros.")
        return rows


class CsvSourceProvider(BaseSourceProvider):
    provider_type = "csv"

    def fetch(self, source, context_data=None):
        payload_override = _context_payload(context_data)
        if payload_override is None:
            payload = json.loads(source.params_json or "{}")
            payload_override = payload.get("content", "")
        if not isinstance(payload_override, str):
            raise ValidationError("A fonte CSV precisa de conteúdo textual.")
        if not payload_override.strip():
            return []
        reader = csv.DictReader(StringIO(payload_override))
        return list(reader)


class XmlSourceProvider(BaseSourceProvider):
    provider_type = "xml"

    def fetch(self, source, context_data=None):
        payload_override = _context_payload(context_data)
        if payload_override is None:
            payload = json.loads(source.params_json or "{}")
            payload_override = payload.get("content", "")
        if not isinstance(payload_override, str):
            raise ValidationError("A fonte XML precisa de conteúdo textual.")
        if not payload_override.strip():
            return []
        root = ET.fromstring(payload_override)
        rows = []
        row_nodes = root.findall(".//row")
        if not row_nodes:
            row_nodes = list(root)
        for node in row_nodes:
            row = {}
            children = list(node)
            if children:
                for child in children:
                    row[child.tag] = child.text or ""
            else:
                row[node.tag] = node.text or ""
            rows.append(row)
        return rows


registry.register("source", ArraySourceProvider.provider_type, ArraySourceProvider)
registry.register("source", PythonSourceProvider.provider_type, PythonSourceProvider)
registry.register("source", ApiSourceProvider.provider_type, ApiSourceProvider)
registry.register("source", JsonSourceProvider.provider_type, JsonSourceProvider)
registry.register("source", CsvSourceProvider.provider_type, CsvSourceProvider)
registry.register("source", XmlSourceProvider.provider_type, XmlSourceProvider)
