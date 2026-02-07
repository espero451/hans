from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


CONTROL_CHARS = {"\x02", "\x03", "\x04", "\x17"}  # STX, ETX, EOT, ETB


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
    def from_header_field(cls, header_field: str, field: str = "|", record: str = "\r") -> "AstmDelimiters":
        repeat = header_field[0] if len(header_field) > 0 else "\\"
        component = header_field[1] if len(header_field) > 1 else "^"
        escape = header_field[2] if len(header_field) > 2 else "&"
        return cls(field=field, component=component, repeat=repeat, escape=escape, record=record)


@dataclass
class AstmRecord:
    record_type: str
    fields: List[str]

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
            self.record_type = value


@dataclass
class AstmMessage:
    records: List[AstmRecord] = field(default_factory=list)
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
        lines = _split_records(raw, record_sep=record_sep)
        if not lines:
            return cls()

        field_sep = "|"
        if len(lines[0]) > 1 and lines[0][0] == "H":
            field_sep = lines[0][1]

        records = [AstmRecord.parse(line, field_sep=field_sep) for line in lines]
        delimiters = AstmDelimiters(field=field_sep, record=record_sep)

        if records and records[0].record_type == "H" and len(records[0].fields) > 1:
            delimiters = AstmDelimiters.from_header_field(
                records[0].fields[1], field=field_sep, record=record_sep
            )

        return cls(records=records, delimiters=delimiters)


def _split_records(raw: str, record_sep: str = "\r") -> List[str]:
    if not raw:
        return []
    cleaned = "".join(ch for ch in raw if ch not in CONTROL_CHARS)
    cleaned = cleaned.strip(record_sep + "\n")
    if not cleaned:
        return []
    return [line for line in cleaned.split(record_sep) if line]
