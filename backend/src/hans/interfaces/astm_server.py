from __future__ import annotations

import argparse
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, List

from sqlalchemy import select

from hans.db import SessionLocal
from hans.orders import Order, Specimen, TestRun
from hans.patients import Patient
from hans.tests import TestCatalog

from .config import InterfaceConfig
from .model import AstmDelimiters, AstmMessage, AstmRecord
from .translation import TranslationTable


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
    def __init__(self, config: InterfaceConfig, translation: TranslationTable) -> None:
        self._config = config
        self._translation = translation

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
            delimiters=message.delimiters or self._config.delimiters,
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
                code = self._translation.test_id_to_code.get(test_catalog.id, test_catalog.code)
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
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._config = config
        self._handler = handler

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
        message = AstmMessage.parse(text, record_sep=self._config.delimiters.record)
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


async def run_server(config: InterfaceConfig) -> None:
    translation = TranslationTable.from_data(config.translation)
    handler = AstmQueryHandler(config, translation)

    server = await asyncio.start_server(
        lambda r, w: AstmSession(r, w, config, handler).run(),
        host=config.server.host,
        port=config.server.port,
    )

    addr = ", ".join(str(sock.getsockname()) for sock in (server.sockets or []))
    logger.info("ASTM server listening on %s", addr)
    trace_logger.info("server.listen addr=%s", addr)

    async with server:
        await server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Hans ASTM TCP server (query mode)")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("configs") / "astm_base.yaml"),
        help="Path to ASTM interface config YAML.",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    if not config_path.exists() and config_path.suffix.lower() == ".json":
        yaml_candidate = config_path.with_suffix(".yaml")
        if yaml_candidate.exists():
            config_path = yaml_candidate
        else:
            yml_candidate = config_path.with_suffix(".yml")
            if yml_candidate.exists():
                config_path = yml_candidate

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config not found: {config_path}. Try the .yaml file in configs/."
        )
    config = InterfaceConfig.load(config_path)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    today = datetime.utcnow().strftime("%Y-%m-%d")
    trace_base = config.trace_dir / config.interface_name / today
    trace_base.mkdir(parents=True, exist_ok=True)
    trace_path = trace_base / f"{config.interface_name}.trace"
    trace_handler = logging.FileHandler(trace_path)
    trace_handler.setLevel(logging.INFO)
    trace_handler.setFormatter(logging.Formatter("%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
    trace_logger.addHandler(trace_handler)
    trace_logger.propagate = False

    trace_logger.info("trace.start interface=%s config=%s", config.interface_name, config_path)

    asyncio.run(run_server(config))


if __name__ == "__main__":
    main()
