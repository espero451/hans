from __future__ import annotations

from datetime import datetime
from typing import Iterable

from .constants import CONTROL_CHARS
from .models import AstmDelimiters, AstmMessage, AstmRecord


# --- Parsing ----------------------------------------------------------

def parse_message(raw: str, record_sep: str = "\r") -> AstmMessage:
    # Parse raw ASTM message.
    return AstmMessage.parse(raw, record_sep=record_sep)


def resolve_delimiters(raw: object) -> AstmDelimiters:
    # Normalize delimiter config.
    if isinstance(raw, AstmDelimiters):
        return raw
    if isinstance(raw, dict):
        return AstmDelimiters(
            field=raw.get("field", "|"),
            component=raw.get("component", "^"),
            repeat=raw.get("repeat", "\\"),
            escape=raw.get("escape", "&"),
            record=raw.get("record", "\r"),
        )
    return AstmDelimiters()


def classify_records(records: list[AstmRecord]) -> str:
    # Classify message records.
    has_q = any(record.record_type == "Q" for record in records)
    has_r = any(record.record_type == "R" for record in records)
    if has_q and has_r:
        return "INVALID"
    if has_r:
        return "RESULT"
    if has_q:
        return "QUERY"
    return "INVALID"


def invalid_reason(records: list[AstmRecord]) -> str:
    # Explain why a message is invalid.
    has_q = any(record.record_type == "Q" for record in records)
    has_r = any(record.record_type == "R" for record in records)
    if has_q and has_r:
        return "has_q_and_r"
    return "no_q_or_r"


# --- Parsing Internals ------------------------------------------------

def _split_records(raw: str, record_sep: str = "\r") -> list[str]:
    if not raw:
        return []
    cleaned = "".join(ch for ch in raw if ch not in CONTROL_CHARS)
    cleaned = cleaned.strip(record_sep + "\n")
    if not cleaned:
        return []
    return [line for line in cleaned.split(record_sep) if line]


def _resolve_delimiters_from_lines(lines: list[str], record_sep: str) -> AstmDelimiters:
    if not lines:
        return AstmDelimiters(record=record_sep)

    field_sep = "|"
    if len(lines[0]) > 1 and lines[0][0] == "H":
        field_sep = lines[0][1]

    header_record = AstmRecord.parse(lines[0], field_sep=field_sep)
    if header_record.record_type == "H" and len(header_record.fields) > 1:
        return AstmDelimiters.from_header_field(
            header_record.fields[1], field=field_sep, record=record_sep
        )

    return AstmDelimiters(field=field_sep, record=record_sep)


def _extract_barcode(
    record: AstmRecord,
    delimiters: AstmDelimiters,
    indexes: Iterable[int],
    allow_component_split: bool,
) -> str:
    for idx in indexes:
        raw = record.get(idx)
        if not raw:
            continue
        if allow_component_split and delimiters.component in raw:
            parts = [part for part in raw.split(delimiters.component) if part]
            raw = parts[-1] if parts else raw
        raw = raw.strip()
        if raw:
            return raw
    return ""


def _first_nonempty(record: AstmRecord, indexes: Iterable[int]) -> str:
    for idx in indexes:
        value = record.get(idx).strip()
        if value:
            return value
    return ""


def _parse_result_datetime(raw: str) -> datetime | None:
    raw = raw.strip()
    if not raw:
        return None
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) >= 14:
        digits = digits[:14]
        fmt = "%Y%m%d%H%M%S"
    elif len(digits) >= 12:
        digits = digits[:12]
        fmt = "%Y%m%d%H%M"
    elif len(digits) >= 8:
        digits = digits[:8]
        fmt = "%Y%m%d"
    else:
        return None
    try:
        return datetime.strptime(digits, fmt)
    except ValueError:
        return None
