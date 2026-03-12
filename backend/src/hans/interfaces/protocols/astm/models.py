from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


# --- Data Models ------------------------------------------------------

@dataclass
class AstmDelimiters:
    field: str = "|"
    component: str = "^"
    repeat: str = "\\"
    escape: str = "&"
    record: str = "\r"

    def header_field(self) -> str:
        return f"{self.repeat}{self.component}{self.escape}"

    @classmethod
    def from_header_field(
        cls,
        header_field: str,
        field: str = "|",
        record: str = "\r",
    ) -> "AstmDelimiters":
        repeat = header_field[0] if len(header_field) > 0 else "\\"
        component = header_field[1] if len(header_field) > 1 else "^"
        escape = header_field[2] if len(header_field) > 2 else "&"
        return cls(field=field, component=component, repeat=repeat, escape=escape, record=record)


@dataclass
class AstmRecord:
    record_type: str
    fields: list[str]

    @classmethod
    def parse(cls, line: str, field_sep: str = "|") -> "AstmRecord":
        fields = line.split(field_sep)
        record_type = fields[0] if fields else ""
        return cls(record_type=record_type, fields=fields)

    def serialize(self, field_sep: str = "|") -> str:
        return field_sep.join(self.fields)

    def get(self, index: int, default: str = "") -> str:
        if 0 <= index < len(self.fields):
            return self.fields[index]
        return default

    def set(self, index: int, value: str) -> None:
        if index < 0:
            return
        if index >= len(self.fields):
            self.fields.extend([""] * (index + 1 - len(self.fields)))
        self.fields[index] = value
        if index == 0:
            # Keep record type aligned with field 0 updates.
            self.record_type = value


@dataclass
class AstmMessage:
    records: list[AstmRecord] = field(default_factory=list)
    delimiters: AstmDelimiters = field(default_factory=AstmDelimiters)

    def add(self, record: AstmRecord) -> None:
        self.records.append(record)

    def serialize(self, include_trailing_record_sep: bool = True) -> str:
        body = self.delimiters.record.join(
            record.serialize(self.delimiters.field) for record in self.records
        )
        if include_trailing_record_sep and body:
            return body + self.delimiters.record
        return body

    @classmethod
    def parse(cls, raw: str, record_sep: str = "\r") -> "AstmMessage":
        # Keep class API stable while parser internals live in codec.
        from .codec import _resolve_delimiters_from_lines, _split_records

        lines = _split_records(raw, record_sep=record_sep)
        if not lines:
            return cls()
        delimiters = _resolve_delimiters_from_lines(lines, record_sep)
        records = [AstmRecord.parse(line, field_sep=delimiters.field) for line in lines]
        return cls(records=records, delimiters=delimiters)


@dataclass(frozen=True)
class QueryResponseContext:
    specimen_id: str
    test_codes: list[str]
    patient_id: str | None = None
    patient_name: str | None = None


@dataclass(frozen=True)
class ResultPayload:
    specimen_id: str
    test_code: str
    value: str | None
    units: str | None
    flags: str | None
    completed_at: datetime | None
    verified: bool
