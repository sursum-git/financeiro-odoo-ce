from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import re
from typing import Any


class TransformError(ValueError):
    """Raised when a transform spec is invalid or cannot be applied."""


@dataclass(frozen=True)
class FieldMapping:
    source: str
    target: str
    transforms: tuple[dict[str, Any], ...] = ()
    default: Any = None

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "FieldMapping":
        return cls(
            source=values["source"],
            target=values["target"],
            transforms=tuple(values.get("transforms", ())),
            default=values.get("default"),
        )


class EDITransformEngine:
    """Small metadata-driven transform engine for phase 1."""

    def apply(
        self,
        value: Any,
        transforms: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    ) -> Any:
        result = value
        for transform in transforms:
            result = self._apply_one(result, transform)
        return result

    def _apply_one(self, value: Any, transform: dict[str, Any]) -> Any:
        transform_type = transform.get("type")
        if not transform_type:
            raise TransformError("Transform spec must define a 'type'.")

        method_name = f"_transform_{transform_type}"
        method = getattr(self, method_name, None)
        if method is None:
            raise TransformError(f"Unsupported transform type: {transform_type}")
        return method(value, transform)

    def _transform_cast(self, value: Any, transform: dict[str, Any]) -> Any:
        target_type = transform.get("target")
        casters = {
            "str": str,
            "int": int,
            "float": float,
            "decimal": Decimal,
            "bool": self._cast_bool,
        }
        caster = casters.get(target_type)
        if caster is None:
            raise TransformError(f"Unsupported cast target: {target_type}")
        return caster(value)

    def _transform_cast_bool(self, value: Any, transform: dict[str, Any]) -> bool:
        return self._cast_bool(value)

    def _transform_cast_date(self, value: Any, transform: dict[str, Any]) -> datetime.date:
        source_format = transform.get("source_format", "%Y-%m-%d")
        return datetime.strptime(str(value), source_format).date()

    def _transform_cast_datetime(self, value: Any, transform: dict[str, Any]) -> datetime:
        source_format = transform.get("source_format", "%Y-%m-%d %H:%M:%S")
        return datetime.strptime(str(value), source_format)

    def _transform_substring(self, value: Any, transform: dict[str, Any]) -> str:
        start = transform.get("start", 0)
        end = transform.get("end")
        return str(value)[start:end]

    def _transform_left(self, value: Any, transform: dict[str, Any]) -> str:
        length = transform.get("length")
        if length is None:
            raise TransformError("left transform requires 'length'.")
        return str(value)[:length]

    def _transform_right(self, value: Any, transform: dict[str, Any]) -> str:
        length = transform.get("length")
        if length is None:
            raise TransformError("right transform requires 'length'.")
        return str(value)[-length:]

    def _transform_split(self, value: Any, transform: dict[str, Any]) -> Any:
        separator = transform.get("separator")
        index = transform.get("index")
        parts = str(value).split(separator)
        if index is None:
            return parts
        return parts[index]

    def _transform_zfill(self, value: Any, transform: dict[str, Any]) -> str:
        width = transform.get("width")
        if width is None:
            raise TransformError("zfill transform requires 'width'.")
        return str(value).zfill(width)

    def _transform_pad_left(self, value: Any, transform: dict[str, Any]) -> str:
        width = transform.get("width")
        pad_char = transform.get("pad_char", " ")
        if width is None:
            raise TransformError("pad_left transform requires 'width'.")
        return str(value).rjust(width, pad_char)

    def _transform_pad_right(self, value: Any, transform: dict[str, Any]) -> str:
        width = transform.get("width")
        pad_char = transform.get("pad_char", " ")
        if width is None:
            raise TransformError("pad_right transform requires 'width'.")
        return str(value).ljust(width, pad_char)

    def _transform_multiply(self, value: Any, transform: dict[str, Any]) -> Decimal:
        return self._to_decimal(value) * self._to_decimal(transform["factor"])

    def _transform_divide(self, value: Any, transform: dict[str, Any]) -> Decimal:
        return self._to_decimal(value) / self._to_decimal(transform["factor"])

    def _transform_round(self, value: Any, transform: dict[str, Any]) -> Decimal:
        digits = int(transform.get("digits", 0))
        quantum = Decimal("1").scaleb(-digits)
        return self._to_decimal(value).quantize(quantum)

    def _transform_date_format(self, value: Any, transform: dict[str, Any]) -> str:
        source_format = transform.get("source_format")
        target_format = transform.get("target_format")
        if not source_format or not target_format:
            raise TransformError(
                "date_format transform requires 'source_format' and 'target_format'."
            )
        return datetime.strptime(str(value), source_format).strftime(target_format)

    def _transform_date_parse(self, value: Any, transform: dict[str, Any]) -> datetime:
        source_format = transform.get("source_format")
        if not source_format:
            raise TransformError("date_parse transform requires 'source_format'.")
        return datetime.strptime(str(value), source_format)

    def _transform_replace(self, value: Any, transform: dict[str, Any]) -> str:
        old = transform.get("old", "")
        new = transform.get("new", "")
        return str(value).replace(old, new)

    def _transform_strip(self, value: Any, transform: dict[str, Any]) -> str:
        chars = transform.get("chars")
        return str(value).strip(chars)

    def _transform_upper(self, value: Any, transform: dict[str, Any]) -> str:
        return str(value).upper()

    def _transform_lower(self, value: Any, transform: dict[str, Any]) -> str:
        return str(value).lower()

    def _transform_remove_non_digits(self, value: Any, transform: dict[str, Any]) -> str:
        return re.sub(r"\D+", "", str(value))

    def _transform_truncate(self, value: Any, transform: dict[str, Any]) -> str:
        length = transform.get("length")
        if length is None:
            raise TransformError("truncate transform requires 'length'.")
        return str(value)[:length]

    def _transform_concat(self, value: Any, transform: dict[str, Any]) -> str:
        prefix = transform.get("prefix", "")
        suffix = transform.get("suffix", "")
        separator = transform.get("separator", "")
        parts = [part for part in [prefix, str(value), suffix] if part != ""]
        return separator.join(parts) if separator else "".join(parts)

    def _transform_regex_extract(self, value: Any, transform: dict[str, Any]) -> str:
        pattern = transform.get("pattern")
        group = int(transform.get("group", 1))
        if not pattern:
            raise TransformError("regex_extract transform requires 'pattern'.")
        match = re.search(pattern, str(value))
        if not match:
            return transform.get("default", "")
        return match.group(group)

    def _transform_value_map(self, value: Any, transform: dict[str, Any]) -> Any:
        mapping = transform.get("mapping", {})
        default = transform.get("default", value)
        return mapping.get(value, mapping.get(str(value), default))

    def _transform_safe_eval(self, value: Any, transform: dict[str, Any]) -> Any:
        expression = transform.get("expression")
        if not expression:
            raise TransformError("safe_eval transform requires 'expression'.")
        context = {
            "value": value,
            "Decimal": Decimal,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
        }
        return eval(expression, {"__builtins__": {}}, context)

    def _to_decimal(self, value: Any) -> Decimal:
        return Decimal(str(value))

    def _cast_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "sim"}


class MappingPipeline:
    """Maps source rows into a target dataset using declarative field mappings."""

    def __init__(self, transform_engine: EDITransformEngine | None = None) -> None:
        self.transform_engine = transform_engine or EDITransformEngine()

    def run(
        self,
        dataset: list[dict[str, Any]],
        mapping_spec: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    ) -> list[dict[str, Any]]:
        field_mappings = [FieldMapping.from_dict(item) for item in mapping_spec]
        return [self._map_row(row, field_mappings) for row in dataset]

    def _map_row(
        self,
        row: dict[str, Any],
        field_mappings: list[FieldMapping],
    ) -> dict[str, Any]:
        mapped = {}
        for field_mapping in field_mappings:
            value = row.get(field_mapping.source, field_mapping.default)
            mapped[field_mapping.target] = self.transform_engine.apply(
                value,
                field_mapping.transforms,
            )
        return mapped
