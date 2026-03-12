from __future__ import annotations

from typing import Iterable

from .codec import _extract_barcode, _first_nonempty, _parse_result_datetime
from .constants import (
    R_COMPLETED_FIELDS,
)
from .mapping import AstmResultMapping
from .models import AstmDelimiters, AstmRecord, ResultPayload


# --- Results ----------------------------------------------------------

def parse_results(
    records: list[AstmRecord],
    delimiters: AstmDelimiters,
    barcode_indexes: Iterable[int],
    allow_component_split: bool,
    result_fields: AstmResultMapping | None = None,
) -> list[ResultPayload]:
    # Parse O/R records into payloads.
    # Apply mapping overrides for result fields.
    fields = result_fields or AstmResultMapping()
    test_code_field = fields.test_code_field
    test_code_component_last = fields.component_last
    value_field = fields.value_field
    units_field = fields.units_field
    flags_field = fields.flags_fields
    status_field = fields.status_fields

    current_specimen = ""
    parsed = {}

    for record in records:
        if record.record_type == "O":
            current_specimen = _extract_barcode(
                record,
                delimiters,
                barcode_indexes,
                allow_component_split,
            )
            continue

        if record.record_type != "R":
            continue

        if not current_specimen:
            continue

        test_code = _extract_barcode(
            record,
            delimiters,
            [test_code_field],
            test_code_component_last,
        )
        if not test_code:
            continue

        value = record.get(value_field).strip() or None
        units = record.get(units_field).strip() or None
        flags = record.get(flags_field).strip() or None
        status = record.get(status_field).strip()
        completed_at = _parse_result_datetime(_first_nonempty(record, R_COMPLETED_FIELDS))
        verified = status.upper() in {"F", "C"} if status else False

        payload = ResultPayload(
            specimen_id=current_specimen,
            test_code=test_code,
            value=value,
            units=units,
            flags=flags,
            completed_at=completed_at,
            verified=verified,
        )
        parsed[(payload.specimen_id, payload.test_code)] = payload

    return list(parsed.values())


def result_payload_as_dom(payload: ResultPayload) -> dict[str, object]:
    # Convert ASTM result payloads to protocol-agnostic domain dicts.
    return {
        "specimen_id": payload.specimen_id,
        "test_code": payload.test_code,
        "value": payload.value,
        "units": payload.units,
        "flags": payload.flags,
        "completed_at": payload.completed_at,
        "verified": payload.verified,
    }
