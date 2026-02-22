from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Protocol

from ..config_reader import InterfaceConfig


# --- Constants --------------------------------------------------------

logger = logging.getLogger("hans.astm")


STX = 0x02
ETX = 0x03
EOT = 0x04
ENQ = 0x05
ACK = 0x06
NAK = 0x15
ETB = 0x17
CR = 0x0D
LF = 0x0A


CONTROL_CHARS = {chr(STX), chr(ETX), chr(EOT), chr(ETB)}

R_TEST_CODE_FIELD = 2
R_VALUE_FIELD = 3
R_UNITS_FIELD = 4
R_FLAGS_FIELD = 6
R_STATUS_FIELD = 8
R_COMPLETED_FIELDS = (9, 10, 12)
# Key used to store mapping in config translation.
ASTM_MAPPING_KEY = "_astm_mapping"


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
            # Keep record_type in sync when updating field 0.
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


# --- Protocols --------------------------------------------------------

class QueryContextLike(Protocol):
    specimen_id: str
    patient_id: str | None
    patient_name: str | None
    test_codes: list[str]
    test_run_ids: list[int]


class AstmDispatcher(Protocol):
    async def log_raw_in(self, interface_code: str, raw: str) -> None:
        ...

    async def log_raw_out(self, interface_code: str, raw: str) -> None:
        ...

    async def log_interface(self, interface_code: str, level: str, message: str) -> None:
        ...

    async def log_event(
        self,
        interface_code: str,
        peer: str,
        direction: str,
        message_type: str,
        stage: str,
        barcodes: list[str],
        test_run_ids: list[int],
        reason: str | None = None,
    ) -> None:
        ...

    async def load_query_contexts(
        self, interface_code: str, barcodes: list[str]
    ) -> list[QueryContextLike]:
        ...

    async def store_results(
        self, interface_code: str, payloads: list[ResultPayload]
    ) -> list[int]:
        ...

    async def mark_sent(self, test_run_ids: list[int]) -> None:
        ...


# --- Parsing & Builders -----------------------------------------------

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


def _astm_mapping(config: InterfaceConfig) -> dict:
    # Read ASTM mapping from translation payload.
    translation = config.translation
    if not isinstance(translation, dict):
        return {}
    mapping = translation.get(ASTM_MAPPING_KEY)
    if isinstance(mapping, dict):
        return mapping
    return {}


def _mapping_section(mapping: dict, name: str) -> dict:
    # Return a mapping section as a dict.
    section = mapping.get(name)
    return section if isinstance(section, dict) else {}


def _mapping_bool(section: dict, key: str, default: bool) -> bool:
    # Resolve a boolean flag from mapping.
    value = section.get(key)
    if value is None:
        return default
    return bool(value)


def _mapping_index(section: dict, key: str, default: int) -> int:
    # Resolve a single index from mapping.
    value = section.get(key, default)
    if isinstance(value, list):
        value = value[0] if value else default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _mapping_indexes(section: dict, key: str, default: Iterable[int]) -> list[int]:
    # Resolve a list of indices from mapping.
    value = section.get(key)
    if value is None:
        return [int(item) for item in default]
    if isinstance(value, list):
        indexes = []
        for item in value:
            try:
                indexes.append(int(item))
            except (TypeError, ValueError):
                return [int(item) for item in default]
        return indexes
    try:
        return [int(value)]
    except (TypeError, ValueError):
        return [int(item) for item in default]


def _resolve_join_separator(delimiters: AstmDelimiters, rule: str | None) -> str:
    # Resolve join separator by name.
    if rule == "component":
        return delimiters.component
    if rule == "field":
        return delimiters.field
    if rule == "record":
        return delimiters.record
    return delimiters.repeat


def _split_patient_name(name: str | None, component_sep: str) -> tuple[str, str]:
    # Split patient name into first/last when provided as components.
    if not name:
        return "", ""
    if component_sep and component_sep in name:
        parts = [part for part in name.split(component_sep) if part]
        if len(parts) >= 2:
            return parts[1], parts[0]
        return "", parts[0] if parts else ""
    return "", name


def _build_patient_record(
    patient_id: str,
    patient_name: str,
    patient_out: dict,
    delimiters: AstmDelimiters,
) -> AstmRecord:
    # Build a P record using mapping fields.
    record = AstmRecord("P", ["P"])
    record.set(1, "1")

    patient_id_field = _mapping_index(patient_out, "patient_id_field", 3)
    if patient_id_field >= 0:
        record.set(patient_id_field, str(patient_id))

    first_name, last_name = _split_patient_name(patient_name, delimiters.component)
    first_name_field = _mapping_index(patient_out, "first_name_field", 6)
    last_name_field = _mapping_index(patient_out, "last_name_field", 5)
    if last_name_field >= 0:
        record.set(last_name_field, last_name)
    if first_name_field >= 0:
        record.set(first_name_field, first_name)

    dob_field = _mapping_index(patient_out, "dob_field", -1)
    if dob_field >= 0:
        record.set(dob_field, "")

    return record


def extract_query_barcodes(
    queries: list[AstmRecord],
    delimiters: AstmDelimiters,
    indexes: Iterable[int],
    allow_component_split: bool,
) -> list[str]:
    # Extract barcodes from Q records.
    barcodes: list[str] = []
    for query in queries:
        barcode = _extract_barcode(query, delimiters, indexes, allow_component_split)
        if not barcode:
            return []
        barcodes.append(barcode)
    return barcodes


def parse_results(
    records: list[AstmRecord],
    delimiters: AstmDelimiters,
    barcode_indexes: Iterable[int],
    allow_component_split: bool,
    result_fields: dict | None = None,
) -> list[ResultPayload]:
    # Parse O/R records into payloads.
    # Apply mapping overrides for result fields.
    fields = result_fields or {}
    test_code_field = _mapping_index(fields, "test_code_field", R_TEST_CODE_FIELD)
    test_code_component_last = _mapping_bool(fields, "component_last", True)
    value_field = _mapping_index(fields, "value_field", R_VALUE_FIELD)
    units_field = _mapping_index(fields, "units_field", R_UNITS_FIELD)
    flags_field = _mapping_index(fields, "flags_fields", R_FLAGS_FIELD)
    status_field = _mapping_index(fields, "status_fields", R_STATUS_FIELD)

    current_specimen = ""
    parsed: dict[tuple[str, str], ResultPayload] = {}

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


def build_query_response(
    contexts: list[QueryResponseContext],
    delimiters: AstmDelimiters,
    include_patient: bool,
    mapping: dict | None = None,
) -> AstmMessage:
    # Build ASTM query response message.
    # Resolve mapping overrides for response fields.
    mapping = mapping or {}
    order_out = _mapping_section(mapping, "order_out")
    patient_out = _mapping_section(mapping, "patient_out")
    tests_field = _mapping_index(order_out, "tests_field", 4)
    specimen_field = _mapping_index(order_out, "specimen_field", 2)
    join_rule = order_out.get("join") or order_out.get("split")
    join_sep = _resolve_join_separator(delimiters, join_rule)

    message = AstmMessage(delimiters=delimiters)
    message.add(AstmRecord("H", ["H", delimiters.header_field(), "", "", "", "", "", "", "", "P", "1"]))

    if include_patient and contexts and contexts[0].patient_id:
        context = contexts[0]
        patient_id = context.patient_id or ""
        patient_name = context.patient_name or ""
        if patient_out:
            message.add(
                _build_patient_record(patient_id, patient_name, patient_out, delimiters)
            )
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
    # Explain invalid message.
    has_q = any(record.record_type == "Q" for record in records)
    has_r = any(record.record_type == "R" for record in records)
    if has_q and has_r:
        return "has_q_and_r"
    return "no_q_or_r"


# --- Session ----------------------------------------------------------

class AstmSession:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        config: InterfaceConfig,
        dispatcher: AstmDispatcher,
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._config = config
        self._dispatcher = dispatcher
        self._delimiters = resolve_delimiters(config.delimiters)

        self._state = "idle"
        self._frame_data = bytearray()
        self._checksum_bytes = bytearray()
        self._end_char: int | None = None
        self._chunks: list[bytes] = []
        self._raw_buffer = bytearray()

    async def run(self) -> None:
        # Handle one TCP session.
        peer = self._writer.get_extra_info("peername")
        await self._dispatcher.log_interface(
            self._config.interface_code,
            "INFO",
            f"connection.open peer={_format_peer(peer)}",
        )
        try:
            while True:
                data = await self._reader.read(1024)
                if not data:
                    break
                for byte in data:
                    await self._handle_byte(byte)
        finally:
            await self._dispatcher.log_interface(
                self._config.interface_code,
                "INFO",
                f"connection.close peer={_format_peer(peer)}",
            )
            self._writer.close()
            await self._writer.wait_closed()

    async def _handle_byte(self, byte: int) -> None:
        if byte == ENQ:
            await self._send_byte(ACK)
            return

        if byte == EOT:
            await self._finish_message()
            return

        if self._state == "idle":
            if byte == STX:
                self._frame_data = bytearray()
                self._checksum_bytes = bytearray()
                self._end_char = None
                self._state = "frame"
            else:
                self._raw_buffer.append(byte)
            return

        if self._state == "frame":
            if byte in (ETX, ETB):
                self._end_char = byte
                self._state = "checksum"
            else:
                self._frame_data.append(byte)
            return

        if self._state == "checksum":
            self._checksum_bytes.append(byte)
            if len(self._checksum_bytes) >= 2:
                self._state = "post_cr"
            return

        if self._state == "post_cr":
            if byte == CR:
                self._state = "post_lf"
                return
            await self._finalize_frame()
            self._state = "idle"
            await self._handle_byte(byte)
            return

        if self._state == "post_lf":
            if byte == LF:
                await self._finalize_frame()
                self._state = "idle"
                return
            await self._finalize_frame()
            self._state = "idle"
            await self._handle_byte(byte)

    async def _finalize_frame(self) -> None:
        payload = bytes(self._frame_data)
        if payload:
            frame_payload = payload[1:] if len(payload) > 1 else b""
            is_valid = True
            if self._config.frame.validate_checksum and self._end_char is not None:
                expected = self._checksum_bytes.decode("ascii", errors="ignore").upper()
                computed = calc_checksum(payload + bytes([self._end_char]))
                is_valid = expected == computed
            if is_valid:
                self._chunks.append(frame_payload)
                await self._send_byte(ACK)
            else:
                await self._send_byte(NAK)

    async def _finish_message(self) -> None:
        raw = b""
        if self._chunks:
            raw = b"".join(self._chunks)
        elif self._raw_buffer:
            raw = bytes(self._raw_buffer)

        self._chunks.clear()
        self._raw_buffer.clear()
        self._state = "idle"

        if not raw:
            return

        text = raw.decode("ascii", errors="ignore")
        await self._dispatcher.log_raw_in(self._config.interface_code, text)

        peer = _format_peer(self._writer.get_extra_info("peername"))
        await self._dispatcher.log_interface(
            self._config.interface_code,
            "INFO",
            f"message.received peer={peer} bytes={len(raw)}",
        )
        message = parse_message(text, record_sep=self._delimiters.record)
        message_type = classify_records(message.records)
        await self._dispatcher.log_interface(
            self._config.interface_code,
            "INFO",
            f"message.parsed type={message_type}",
        )

        # Resolve mapping overrides for message parsing.
        mapping = _astm_mapping(self._config)
        query_mapping = _mapping_section(mapping, "query")
        barcode_index = _mapping_index(query_mapping, "barcode_field", -1)
        if barcode_index < 0:
            raise ValueError("Config must define astm_mapping.query.barcode_field.")
        barcode_indexes = [barcode_index]
        component_last = _mapping_bool(query_mapping, "component_last", True)

        order_in = _mapping_section(mapping, "order_in")
        specimen_index = _mapping_index(order_in, "specimen_field", -1)
        if specimen_index < 0:
            raise ValueError("Config must define astm_mapping.order_in.specimen_field.")
        specimen_indexes = [specimen_index]
        specimen_component_last = _mapping_bool(order_in, "component_last", component_last)
        result_fields = _mapping_section(mapping, "result")

        if message_type == "INVALID":
            reason = invalid_reason(message.records)
            await self._dispatcher.log_event(
                interface_code=self._config.interface_code,
                peer=peer,
                direction="IN",
                message_type="INVALID",
                stage="DISPATCHED",
                barcodes=[],
                test_run_ids=[],
            )
            await self._dispatcher.log_event(
                interface_code=self._config.interface_code,
                peer=peer,
                direction="IN",
                message_type="INVALID",
                stage="PARSED",
                barcodes=[],
                test_run_ids=[],
            )
            await self._dispatcher.log_event(
                interface_code=self._config.interface_code,
                peer=peer,
                direction="IN",
                message_type="INVALID",
                stage="REJECTED",
                barcodes=[],
                test_run_ids=[],
                reason=reason,
            )
            await self._dispatcher.log_interface(
                self._config.interface_code,
                "INFO",
                f"message.rejected reason={reason}",
            )
            return

        if message_type == "QUERY":
            queries = [record for record in message.records if record.record_type == "Q"]
            barcodes = extract_query_barcodes(
                queries,
                message.delimiters,
                barcode_indexes,
                component_last,
            )
            await self._dispatcher.log_event(
                interface_code=self._config.interface_code,
                peer=peer,
                direction="IN",
                message_type="QUERY",
                stage="DISPATCHED",
                barcodes=barcodes,
                test_run_ids=[],
            )
            await self._dispatcher.log_interface(
                self._config.interface_code,
                "INFO",
                f"query.received barcodes={_format_csv(barcodes)}",
            )
            if not barcodes:
                await self._dispatcher.log_event(
                    interface_code=self._config.interface_code,
                    peer=peer,
                    direction="IN",
                    message_type="QUERY",
                    stage="PARSED",
                    barcodes=[],
                    test_run_ids=[],
                )
                await self._dispatcher.log_event(
                    interface_code=self._config.interface_code,
                    peer=peer,
                    direction="IN",
                    message_type="QUERY",
                    stage="REJECTED",
                    barcodes=[],
                    test_run_ids=[],
                    reason="missing_barcode",
                )
                await self._dispatcher.log_interface(
                    self._config.interface_code,
                    "INFO",
                    "query.rejected reason=missing_barcode",
                )
                return

            contexts = await self._dispatcher.load_query_contexts(
                self._config.interface_code, barcodes
            )
            test_run_ids = [
                run_id for context in contexts for run_id in context.test_run_ids if run_id
            ]
            tests_count = _count_tests(contexts)
            await self._dispatcher.log_event(
                interface_code=self._config.interface_code,
                peer=peer,
                direction="IN",
                message_type="QUERY",
                stage="PARSED",
                barcodes=barcodes,
                test_run_ids=test_run_ids,
            )
            await self._dispatcher.log_interface(
                self._config.interface_code,
                "INFO",
                (
                    "query.context_loaded "
                    f"barcodes={_format_csv(barcodes)} "
                    f"test_run_ids={_format_csv(test_run_ids)} "
                    f"tests={tests_count}"
                ),
            )
            if not contexts:
                await self._dispatcher.log_event(
                    interface_code=self._config.interface_code,
                    peer=peer,
                    direction="IN",
                    message_type="QUERY",
                    stage="REJECTED",
                    barcodes=barcodes,
                    test_run_ids=[],
                    reason="specimen_not_found",
                )
                await self._dispatcher.log_interface(
                    self._config.interface_code,
                    "INFO",
                    "query.rejected reason=specimen_not_found",
                )
                return

            response_contexts = [
                QueryResponseContext(
                    specimen_id=context.specimen_id,
                    test_codes=context.test_codes,
                    patient_id=context.patient_id,
                    patient_name=context.patient_name,
                )
                for context in contexts
            ]
            response = build_query_response(
                response_contexts,
                message.delimiters,
                self._config.response.include_patient,
                mapping=mapping,
            )
            await self._dispatcher.log_interface(
                self._config.interface_code,
                "INFO",
                (
                    "response.built "
                    f"barcodes={_format_csv(barcodes)} "
                    f"test_run_ids={_format_csv(test_run_ids)} "
                    f"tests={tests_count}"
                ),
            )
            await self._send_message(response, barcodes, test_run_ids, peer)
            return

        payloads = parse_results(
            message.records,
            message.delimiters,
            specimen_indexes,
            specimen_component_last,
            result_fields=result_fields,
        )
        barcodes = [payload.specimen_id for payload in payloads]
        await self._dispatcher.log_event(
            interface_code=self._config.interface_code,
            peer=peer,
            direction="IN",
            message_type="RESULT",
            stage="DISPATCHED",
            barcodes=barcodes,
            test_run_ids=[],
        )
        await self._dispatcher.log_interface(
            self._config.interface_code,
            "INFO",
            f"results.parsed barcodes={_format_csv(barcodes)} results={len(payloads)}",
        )
        if not payloads:
            await self._dispatcher.log_event(
                interface_code=self._config.interface_code,
                peer=peer,
                direction="IN",
                message_type="RESULT",
                stage="PARSED",
                barcodes=barcodes,
                test_run_ids=[],
            )
            await self._dispatcher.log_event(
                interface_code=self._config.interface_code,
                peer=peer,
                direction="IN",
                message_type="RESULT",
                stage="REJECTED",
                barcodes=barcodes,
                test_run_ids=[],
                reason="no_results",
            )
            await self._dispatcher.log_interface(
                self._config.interface_code,
                "INFO",
                "results.rejected reason=no_results",
            )
            return

        test_run_ids = await self._dispatcher.store_results(
            self._config.interface_code, payloads
        )
        await self._dispatcher.log_event(
            interface_code=self._config.interface_code,
            peer=peer,
            direction="IN",
            message_type="RESULT",
            stage="PARSED",
            barcodes=barcodes,
            test_run_ids=test_run_ids,
        )
        await self._dispatcher.log_interface(
            self._config.interface_code,
            "INFO",
            (
                "results.stored "
                f"test_run_ids={_format_csv(test_run_ids)} "
                f"results={len(payloads)}"
            ),
        )
        await self._dispatcher.log_interface(
            self._config.interface_code,
            "INFO",
            f"status.received test_run_ids={_format_csv(test_run_ids)}",
        )

    async def _send_message(
        self,
        message: AstmMessage,
        barcodes: list[str],
        test_run_ids: list[int],
        peer: str,
    ) -> None:
        frames = frame_message(message, self._config.frame.size)
        if not frames:
            return

        raw = message.serialize(include_trailing_record_sep=True)
        await self._dispatcher.log_raw_out(self._config.interface_code, raw)
        await self._dispatcher.log_event(
            interface_code=self._config.interface_code,
            peer=peer,
            direction="OUT",
            message_type="ORDER",
            stage="DISPATCHED",
            barcodes=barcodes,
            test_run_ids=test_run_ids,
        )

        await self._send_byte(ENQ)
        if not await self._expect_ack():
            await self._dispatcher.log_event(
                interface_code=self._config.interface_code,
                peer=peer,
                direction="OUT",
                message_type="ORDER",
                stage="FAILED",
                barcodes=barcodes,
                test_run_ids=test_run_ids,
                reason="enq_failed",
            )
            await self._dispatcher.log_interface(
                self._config.interface_code,
                "INFO",
                "response.failed reason=enq_failed",
            )
            return

        for frame in frames:
            await self._send_bytes(frame)
            if not await self._expect_ack():
                await self._dispatcher.log_event(
                    interface_code=self._config.interface_code,
                    peer=peer,
                    direction="OUT",
                    message_type="ORDER",
                    stage="FAILED",
                    barcodes=barcodes,
                    test_run_ids=test_run_ids,
                    reason="frame_failed",
                )
                await self._dispatcher.log_interface(
                    self._config.interface_code,
                    "INFO",
                    "response.failed reason=frame_failed",
                )
                return

        await self._send_byte(EOT)
        await self._dispatcher.log_event(
            interface_code=self._config.interface_code,
            peer=peer,
            direction="OUT",
            message_type="ORDER",
            stage="SENT",
            barcodes=barcodes,
            test_run_ids=test_run_ids,
        )
        await self._dispatcher.log_interface(
            self._config.interface_code,
            "INFO",
            (
                "response.sent "
                f"barcodes={_format_csv(barcodes)} "
                f"test_run_ids={_format_csv(test_run_ids)}"
            ),
        )
        await self._dispatcher.mark_sent(test_run_ids)
        await self._dispatcher.log_interface(
            self._config.interface_code,
            "INFO",
            f"status.sent test_run_ids={_format_csv(test_run_ids)}",
        )

    async def _expect_ack(self, timeout: float = 5.0) -> bool:
        try:
            while True:
                data = await asyncio.wait_for(self._reader.read(1), timeout=timeout)
                if not data:
                    return False
                byte = data[0]
                if byte == ACK:
                    return True
                if byte == NAK:
                    return False
                if byte == ENQ:
                    await self._send_byte(ACK)
        except asyncio.TimeoutError:
            return False

    async def _send_byte(self, byte: int) -> None:
        self._writer.write(bytes([byte]))
        await self._writer.drain()

    async def _send_bytes(self, data: bytes) -> None:
        self._writer.write(data)
        await self._writer.drain()


# --- Framing ----------------------------------------------------------

def calc_checksum(payload: bytes) -> str:
    # Calculate ASTM checksum.
    total = sum(payload) % 256
    return f"{total:02X}"


def frame_message(message: AstmMessage, frame_size: int) -> list[bytes]:
    # Frame ASTM message for transport.
    payload = message.serialize(include_trailing_record_sep=True).encode("ascii", errors="ignore")
    if not payload:
        return []

    chunks = [payload[i:i + frame_size] for i in range(0, len(payload), frame_size)]
    frames: list[bytes] = []
    frame_no = 1
    for idx, chunk in enumerate(chunks):
        end_char = ETB if idx < len(chunks) - 1 else ETX
        frame_id = ord(str(frame_no))
        body = bytes([frame_id]) + chunk
        checksum = calc_checksum(body + bytes([end_char]))
        frame = b"".join(
            [
                bytes([STX]),
                body,
                bytes([end_char]),
                checksum.encode("ascii"),
                bytes([CR, LF]),
            ]
        )
        frames.append(frame)
        frame_no = 1 if frame_no >= 7 else frame_no + 1
    return frames


# --- Utilities --------------------------------------------------------

def _format_peer(peer) -> str:
    if isinstance(peer, tuple):
        return f"{peer[0]}:{peer[1]}"
    return str(peer)


def _format_csv(items: Iterable[object]) -> str:
    # Join items for logs.
    return ",".join(str(item) for item in items if item)


def _count_tests(contexts: Iterable[QueryContextLike]) -> int:
    # Count tests across contexts.
    return sum(len(context.test_codes) for context in contexts)


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
