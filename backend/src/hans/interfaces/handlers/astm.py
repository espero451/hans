from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, List

from sqlalchemy import select

from hans.core.db import SessionLocal
from hans.orders import Order, Specimen, TestRun
from hans.patients import Patient
from hans.tests import TestCatalog

from ..config_reader import InterfaceConfig
from ..translation import TranslationTable


STX = 0x02
ETX = 0x03
EOT = 0x04
ENQ = 0x05
ACK = 0x06
NAK = 0x15
ETB = 0x17
CR = 0x0D
LF = 0x0A


logger = logging.getLogger("hans.astm")
trace_logger = logging.getLogger("hans.astm.trace")
_TRACE_CONFIGURED: set[str] = set()


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


def _ensure_trace_logger(config: InterfaceConfig, config_path: Path | None = None) -> None:
    key = f"{config.interface_name}:{config.server.host}:{config.server.port}"
    if key in _TRACE_CONFIGURED:
        return

    today = datetime.utcnow().strftime("%Y-%m-%d")
    trace_base = config.trace_dir / config.interface_name / today
    trace_base.mkdir(parents=True, exist_ok=True)
    trace_path = trace_base / f"{config.interface_name}.trace"

    handler = logging.FileHandler(trace_path)
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    trace_logger.handlers.clear()
    trace_logger.addHandler(handler)
    trace_logger.propagate = False

    trace_logger.info(
        "trace.start interface=%s config=%s",
        config.interface_name,
        config_path or config.interface_name,
    )
    _TRACE_CONFIGURED.add(key)


def _resolve_delimiters(raw: object) -> AstmDelimiters:
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

def calc_checksum(payload: bytes) -> str:
    total = sum(payload) % 256
    return f"{total:02X}"


def frame_message(message: AstmMessage, frame_size: int) -> list[bytes]:
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


@dataclass
class QueryContext:
    specimen_id: str
    order_id: int
    patient: Patient | None
    test_codes: list[str]


class AstmQueryHandler:
    def __init__(
        self,
        config: InterfaceConfig,
        translation: TranslationTable,
        delimiters: AstmDelimiters,
    ) -> None:
        self._config = config
        self._translation = translation
        self._delimiters = delimiters

    async def handle(self, message: AstmMessage) -> Optional[AstmMessage]:
        queries = [record for record in message.records if record.record_type == "Q"]
        if not queries:
            logger.info("No Q record in message; ignoring.")
            trace_logger.info("message.ignored reason=no_q_record")
            return None

        contexts: List[QueryContext] = []
        for query in queries:
            barcode = _extract_barcode(
                query,
                message.delimiters,
                self._config.query.barcode_field_indexes,
                self._config.query.allow_component_split,
            )
            if not barcode:
                logger.warning("Query received without barcode.")
                trace_logger.info("message.rejected reason=missing_barcode")
                return None

            trace_logger.info("query.received barcode=%s", barcode)
            context = await self._load_context(barcode)
            if not context:
                logger.info("Specimen not found for barcode=%s", barcode)
                trace_logger.info("query.not_found barcode=%s", barcode)
                return None

            trace_logger.info(
                "query.mapped barcode=%s tests=%s",
                context.specimen_id,
                ",".join(context.test_codes),
            )
            contexts.append(context)

        if not contexts:
            return None

        return _build_query_response(
            contexts=contexts,
            delimiters=message.delimiters or self._delimiters,
            include_patient=self._config.response.include_patient,
        )

    async def _load_context(self, barcode: str) -> Optional[QueryContext]:
        async with SessionLocal() as session:
            result = await session.execute(
                select(Order, Specimen, Patient)
                .join(Specimen, Specimen.order_id == Order.id)
                .join(Patient, Patient.id == Order.patient_id, isouter=True)
                .where(Specimen.specimen_id == barcode)
            )
            row = result.first()
            if not row:
                return None
            order, specimen, patient = row

            runs_result = await session.execute(
                select(TestRun, TestCatalog)
                .join(TestCatalog, TestCatalog.id == TestRun.test_catalog_id)
                .where(TestRun.specimen_id == barcode)
                .order_by(TestRun.id)
            )
            test_codes: list[str] = []
            for test_run, test_catalog in runs_result.all():
                lis_code = test_catalog.code
                code = self._translation.lis_to_instrument.get(lis_code, lis_code)
                test_codes.append(code)

            return QueryContext(
                specimen_id=specimen.specimen_id,
                order_id=order.id,
                patient=patient,
                test_codes=test_codes,
            )


class AstmSession:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        config: InterfaceConfig,
        handler: AstmQueryHandler,
        delimiters: AstmDelimiters,
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._config = config
        self._handler = handler
        self._delimiters = delimiters

        self._state = "idle"
        self._frame_data = bytearray()
        self._checksum_bytes = bytearray()
        self._end_char: int | None = None
        self._chunks: list[bytes] = []
        self._raw_buffer = bytearray()

    async def run(self) -> None:
        addr = self._writer.get_extra_info("peername")
        logger.info("Client connected: %s", addr)
        trace_logger.info("connection.open peer=%s", addr)
        try:
            while True:
                data = await self._reader.read(1024)
                if not data:
                    break
                trace_logger.info("recv.bytes size=%d", len(data))
                for byte in data:
                    await self._handle_byte(byte)
        finally:
            logger.info("Client disconnected: %s", addr)
            trace_logger.info("connection.close peer=%s", addr)
            self._writer.close()
            await self._writer.wait_closed()

    async def _handle_byte(self, byte: int) -> None:
        if byte == ENQ:
            await self._send_byte(ACK)
            trace_logger.info("protocol.enq_ack")
            return

        if byte == EOT:
            trace_logger.info("protocol.eot")
            await self._finish_message()
            return

        if self._state == "idle":
            if byte == STX:
                self._frame_data = bytearray()
                self._checksum_bytes = bytearray()
                self._end_char = None
                self._state = "frame"
                trace_logger.info("frame.start")
            else:
                self._raw_buffer.append(byte)
            return

        if self._state == "frame":
            if byte in (ETX, ETB):
                self._end_char = byte
                self._state = "checksum"
                trace_logger.info("frame.end end_char=%s", "ETX" if byte == ETX else "ETB")
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
                trace_logger.info(
                    "frame.checksum expected=%s computed=%s valid=%s",
                    expected,
                    computed,
                    is_valid,
                )
            if is_valid:
                self._chunks.append(frame_payload)
                await self._send_byte(ACK)
                trace_logger.info("frame.ack")
            else:
                await self._send_byte(NAK)
                trace_logger.info("frame.nak")

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

        try:
            text = raw.decode("ascii", errors="ignore")
        except UnicodeDecodeError:
            logger.warning("Failed to decode ASTM message.")
            trace_logger.info("message.decode_failed")
            return

        trace_logger.info("message.raw %s", text.replace("\r", "\\r"))
        message = AstmMessage.parse(text, record_sep=self._delimiters.record)
        trace_logger.info("message.parsed records=%d", len(message.records))
        response = await self._handler.handle(message)
        if response:
            trace_logger.info("message.responding")
            await self._send_message(response)

    async def _send_message(self, message: AstmMessage) -> None:
        frames = frame_message(message, self._config.frame.size)
        if not frames:
            return

        raw = message.serialize(include_trailing_record_sep=True)
        trace_logger.info("response.raw %s", raw.replace("\r", "\\r"))
        trace_logger.info("response.frames size=%d", len(frames))

        trace_logger.info("send.enq")
        await self._send_byte(ENQ)
        if not await self._expect_ack():
            logger.warning("Analyzer did not ACK ENQ; aborting response.")
            trace_logger.info("send.enq_failed")
            return

        trace_logger.info("send.frames count=%d", len(frames))
        for frame in frames:
            await self._send_bytes(frame)
            if not await self._expect_ack():
                logger.warning("Analyzer did not ACK frame; aborting response.")
                trace_logger.info("send.frame_failed")
                return

        trace_logger.info("send.eot")
        await self._send_byte(EOT)

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


def _build_query_response(
    contexts: List[QueryContext],
    delimiters: AstmDelimiters,
    include_patient: bool,
) -> AstmMessage:
    trace_logger.info("response.build.start include_patient=%s count=%d", include_patient, len(contexts))
    message = AstmMessage(delimiters=delimiters)
    message.add(AstmRecord("H", ["H", delimiters.header_field(), "", "", "", "", "", "", "", "P", "1"]))

    if include_patient and contexts and contexts[0].patient:
        patient = contexts[0].patient
        message.add(AstmRecord("P", ["P", "1", "", str(patient.id), "", patient.name]))

    for idx, context in enumerate(contexts, start=1):
        test_list = delimiters.repeat.join(context.test_codes)
        order_record = AstmRecord("O", ["O", str(idx), context.specimen_id, "", test_list])
        message.add(order_record)
        trace_logger.info(
            "response.build.o_record index=%d barcode=%s tests=%s",
            idx,
            context.specimen_id,
            test_list,
        )

    message.add(AstmRecord("L", ["L", "1", "N"]))
    trace_logger.info("response.build.done records=%d", len(message.records))
    return message


async def handle_connection(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    *,
    config: InterfaceConfig,
    raw_config: dict | None = None,
    config_path: Path | None = None,
) -> None:
    _ensure_trace_logger(config, config_path)
    delimiters = _resolve_delimiters(config.delimiters)
    translation = TranslationTable.from_data(config.translation)
    handler = AstmQueryHandler(config, translation, delimiters)
    session = AstmSession(reader, writer, config, handler, delimiters)
    await session.run()
