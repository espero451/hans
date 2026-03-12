from __future__ import annotations

from typing import Iterable

from .codec import _extract_barcode
from .mapping import AstmMapping, AstmPatientMapping, resolve_join_separator
from .models import AstmDelimiters, AstmMessage, AstmRecord, QueryResponseContext
from .utils import optional_str


# --- Query ------------------------------------------------------------

def extract_query_barcodes(
    queries: list[AstmRecord],
    delimiters: AstmDelimiters,
    indexes: Iterable[int],
    allow_component_split: bool,
) -> list[str]:
    # Extract barcodes from Q records.
    barcodes = []
    for query in queries:
        barcode = _extract_barcode(query, delimiters, indexes, allow_component_split)
        if not barcode:
            return []
        barcodes.append(barcode)
    return barcodes


def split_patient_name(name: str | None, component_sep: str) -> tuple[str, str]:
    # Split patient name into first/last when provided as components.
    if not name:
        return "", ""
    if component_sep and component_sep in name:
        parts = [part for part in name.split(component_sep) if part]
        if len(parts) >= 2:
            return parts[1], parts[0]
        return "", parts[0] if parts else ""
    return "", name


def build_patient_record(
    patient_id: str,
    patient_name: str,
    patient_out: AstmPatientMapping,
    delimiters: AstmDelimiters,
) -> AstmRecord:
    # Build a P record using mapping fields.
    record = AstmRecord("P", ["P"])
    record.set(1, "1")

    patient_id_field = patient_out.patient_id_field
    if patient_id_field >= 0:
        record.set(patient_id_field, str(patient_id))

    first_name, last_name = split_patient_name(patient_name, delimiters.component)
    first_name_field = patient_out.first_name_field
    last_name_field = patient_out.last_name_field
    if last_name_field >= 0:
        record.set(last_name_field, last_name)
    if first_name_field >= 0:
        record.set(first_name_field, first_name)

    dob_field = patient_out.dob_field
    if dob_field >= 0:
        record.set(dob_field, "")

    return record


def build_query_response(
    contexts: list[QueryResponseContext],
    delimiters: AstmDelimiters,
    include_patient: bool,
    mapping: AstmMapping | None = None,
) -> AstmMessage:
    # Build ASTM query response message.
    # Resolve mapping overrides for response fields.
    mapping = mapping or AstmMapping()
    order_out = mapping.order_out
    patient_out = mapping.patient_out
    tests_field = order_out.tests_field
    specimen_field = order_out.specimen_field
    join_rule = order_out.join or order_out.split
    join_sep = resolve_join_separator(delimiters, join_rule)

    message = AstmMessage(delimiters=delimiters)
    message.add(AstmRecord("H", ["H", delimiters.header_field(), "", "", "", "", "", "", "", "P", "1"]))

    if include_patient and contexts and contexts[0].patient_id:
        context = contexts[0]
        patient_id = context.patient_id or ""
        patient_name = context.patient_name or ""
        if patient_out:
            message.add(build_patient_record(patient_id, patient_name, patient_out, delimiters))
        else:
            message.add(AstmRecord("P", ["P", "1", "", str(patient_id), "", patient_name]))

    for idx, context in enumerate(contexts, start=1):
        test_list = join_sep.join(context.test_codes)
        order_record = AstmRecord("O", ["O"])
        order_record.set(1, str(idx))
        order_record.set(specimen_field, context.specimen_id)
        order_record.set(tests_field, test_list)
        message.add(order_record)

    message.add(AstmRecord("L", ["L", "1", "N"]))
    return message


def query_response_contexts(
    contexts: list[dict[str, object]],
) -> list[QueryResponseContext]:
    # Convert domain dict payloads to ASTM response context records.
    response_contexts = []
    for context in contexts:
        specimen_id = str(context.get("specimen_id", "")).strip()
        if not specimen_id:
            continue

        raw_codes = context.get("test_codes", [])
        if isinstance(raw_codes, list):
            test_codes = [str(code).strip() for code in raw_codes if str(code).strip()]
        else:
            one_code = str(raw_codes).strip()
            test_codes = [one_code] if one_code else []

        response_contexts.append(
            QueryResponseContext(
                specimen_id=specimen_id,
                test_codes=test_codes,
                patient_id=optional_str(context.get("patient_id")),
                patient_name=optional_str(context.get("patient_name")),
            )
        )
    return response_contexts
