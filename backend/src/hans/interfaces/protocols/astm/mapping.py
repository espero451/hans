from __future__ import annotations

from dataclasses import field

from pydantic import ConfigDict, TypeAdapter, field_validator
from pydantic.dataclasses import dataclass

from ...config_reader import InterfaceConfig
from .constants import ASTM_MAPPING_KEY
from .models import AstmDelimiters


# --- Mapping ----------------------------------------------------------

@dataclass(config=ConfigDict(extra="ignore"), frozen=True, slots=True)
class AstmQueryMapping:
    barcode_field: int = -1
    component_last: bool = True


@dataclass(config=ConfigDict(extra="ignore"), frozen=True, slots=True)
class AstmOrderInMapping:
    specimen_field: int = -1
    component_last: bool | None = None


@dataclass(config=ConfigDict(extra="ignore"), frozen=True, slots=True)
class AstmOrderOutMapping:
    specimen_field: int = 2
    tests_field: int = 4
    join: str | None = None
    split: str | None = None

    @field_validator("join", "split", mode="before")
    @classmethod
    def _normalize_separator(cls, value: object) -> str | None:
        # Keep separator fields unset when value is empty.
        if value is None:
            return None
        text = str(value).strip()
        return text or None


@dataclass(config=ConfigDict(extra="ignore"), frozen=True, slots=True)
class AstmResultMapping:
    test_code_field: int = 2
    component_last: bool = True
    value_field: int = 3
    units_field: int = 4
    flags_fields: int = 6
    status_fields: int = 8


@dataclass(config=ConfigDict(extra="ignore"), frozen=True, slots=True)
class AstmPatientMapping:
    patient_id_field: int = 3
    first_name_field: int = 6
    last_name_field: int = 5
    dob_field: int = -1


@dataclass(config=ConfigDict(extra="ignore"), frozen=True, slots=True)
class AstmMapping:
    query: AstmQueryMapping = field(default_factory=AstmQueryMapping)
    order_in: AstmOrderInMapping = field(default_factory=AstmOrderInMapping)
    order_out: AstmOrderOutMapping = field(default_factory=AstmOrderOutMapping)
    result: AstmResultMapping = field(default_factory=AstmResultMapping)
    patient_out: AstmPatientMapping | None = None

    @classmethod
    def from_dict(cls, raw: dict | None) -> "AstmMapping":
        # Validate and normalize mapping sections from config.
        adapter = TypeAdapter(cls)
        return adapter.validate_python(raw if isinstance(raw, dict) else {})


def astm_mapping(config: InterfaceConfig) -> AstmMapping:
    # Read ASTM mapping from translation payload.
    translation = config.translation
    if not isinstance(translation, dict):
        return AstmMapping()
    return AstmMapping.from_dict(translation.get(ASTM_MAPPING_KEY))


def resolve_join_separator(delimiters: AstmDelimiters, rule: str | None) -> str:
    # Resolve join separator by name.
    if rule == "component":
        return delimiters.component
    if rule == "field":
        return delimiters.field
    if rule == "record":
        return delimiters.record
    return delimiters.repeat
