from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Protocol

from ...config_reader import InterfaceConfig
from ...dom import QueryRequested, QueryResponsePrepared, ResultsReceived
from .codec import classify_records, invalid_reason, parse_message, resolve_delimiters
from .constants import ACK, CR, ENQ, EOT, ETB, ETX, LF, NAK, STX
from .framing import calc_checksum, frame_message
from .mapping import astm_mapping
from .models import AstmDelimiters, AstmMessage
from .query import build_query_response, extract_query_barcodes, query_response_contexts
from .results import parse_results, result_payload_as_dom
from .utils import format_csv, format_peer


# --- Protocols --------------------------------------------------------

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


class DomainMessageRouter(Protocol):
    async def handle_query(
        self, message: QueryRequested
    ) -> QueryResponsePrepared | None:
        ...

    async def handle_results(self, message: ResultsReceived) -> None:
        ...

    async def handle_query_sent(self, message: QueryResponsePrepared) -> None:
        ...


# --- Message Handling -------------------------------------------------

@dataclass(frozen=True)
class HandleResult:
    response: AstmMessage | None = None
    barcodes: list[str] | None = None
    test_run_ids: list[int] | None = None
    peer: str = ""
    query_response: QueryResponsePrepared | None = None


async def handle_astm_message(
    raw: str,
    peer: str,
    config: InterfaceConfig,
    router: DomainMessageRouter,
    dispatcher: AstmDispatcher,
    delimiters: AstmDelimiters,
) -> HandleResult:
    message = parse_message(raw, record_sep=delimiters.record)
    message_type = classify_records(message.records)

    await dispatcher.log_interface(
        config.interface_code,
        "INFO",
        f"message.parsed type={message_type}",
    )

    # Resolve mapping overrides for message parsing.
    mapping = astm_mapping(config)
    query_mapping = mapping.query
    barcode_index = query_mapping.barcode_field
    if barcode_index < 0:
        raise ValueError("Config must define astm_mapping.query.barcode_field.")
    barcode_indexes = [barcode_index]
    component_last = query_mapping.component_last

    order_in = mapping.order_in
    specimen_index = order_in.specimen_field
    if specimen_index < 0:
        raise ValueError("Config must define astm_mapping.order_in.specimen_field.")
    specimen_indexes = [specimen_index]
    specimen_component_last = (
        component_last if order_in.component_last is None else order_in.component_last
    )
    result_fields = mapping.result

    if message_type == "INVALID":
        reason = invalid_reason(message.records)
        await dispatcher.log_event(
            interface_code=config.interface_code,
            peer=peer,
            direction="IN",
            message_type="INVALID",
            stage="DISPATCHED",
            barcodes=[],
            test_run_ids=[],
        )
        await dispatcher.log_event(
            interface_code=config.interface_code,
            peer=peer,
            direction="IN",
            message_type="INVALID",
            stage="PARSED",
            barcodes=[],
            test_run_ids=[],
        )
        await dispatcher.log_event(
            interface_code=config.interface_code,
            peer=peer,
            direction="IN",
            message_type="INVALID",
            stage="REJECTED",
            barcodes=[],
            test_run_ids=[],
            reason=reason,
        )
        await dispatcher.log_interface(
            config.interface_code,
            "INFO",
            f"message.rejected reason={reason}",
        )
        return HandleResult()

    if message_type == "QUERY":
        queries = [record for record in message.records if record.record_type == "Q"]
        barcodes = extract_query_barcodes(
            queries,
            message.delimiters,
            barcode_indexes,
            component_last,
        )
        query_message = QueryRequested(peer=peer, barcodes=barcodes)

        # Trace query_message
        await dispatcher.log_interface(
            config.interface_code,
            "INFO",
            "dom.query_requested payload="
            + json.dumps(
                {
                    "peer": query_message.peer,
                    "barcodes": query_message.barcodes,
                },
                ensure_ascii=False,
                default=str,
            ),
        )

        response_message = await router.handle_query(query_message)
        if not response_message:
            return HandleResult()

        response_contexts = query_response_contexts(response_message.contexts)
        response = build_query_response(
            response_contexts,
            message.delimiters,
            config.response.include_patient,
            mapping=mapping,
        )
        return HandleResult(
            response=response,
            barcodes=response_message.barcodes,
            test_run_ids=response_message.test_run_ids,
            peer=response_message.peer,
            query_response=response_message,
        )

    payloads = parse_results(
        message.records,
        message.delimiters,
        specimen_indexes,
        specimen_component_last,
        result_fields=result_fields,
    )
    results_message = ResultsReceived(
        peer,
        [result_payload_as_dom(payload) for payload in payloads],
    )
    # Trace results_message DOM
    await dispatcher.log_interface(
        config.interface_code,
        "INFO",
        "dom.results_received payload="
        + json.dumps(
            {
                "peer": results_message.peer,
                "results": results_message.results,
            },
            ensure_ascii=False,
            default=str,  # importand for datetime in completed_at
        ),
    )

    await router.handle_results(results_message)
    return HandleResult()


# --- Session ----------------------------------------------------------

class AstmSession:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        config: InterfaceConfig,
        dispatcher: AstmDispatcher,
        message_router: DomainMessageRouter,
    ) -> None:
        self._reader = reader
        self._writer = writer
        self._config = config
        self._dispatcher = dispatcher
        self._message_router = message_router
        self._delimiters = resolve_delimiters(config.delimiters)

        self._state = "idle"
        self._frame_data = bytearray()
        self._checksum_bytes = bytearray()
        self._end_char: int | None = None
        self._chunks = []
        self._raw_buffer = bytearray()

    async def run(self) -> None:
        # Handle one TCP session.
        peer = self._writer.get_extra_info("peername")
        await self._dispatcher.log_interface(
            self._config.interface_code,
            "INFO",
            f"connection.open peer={format_peer(peer)}",
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
                f"connection.close peer={format_peer(peer)}",
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

    def _collect_raw(self) -> bytes:
        raw = b""
        if self._chunks:
            raw = b"".join(self._chunks)
        elif self._raw_buffer:
            raw = bytes(self._raw_buffer)

        self._chunks.clear()
        self._raw_buffer.clear()
        self._state = "idle"
        return raw

    async def _finish_message(self) -> None:
        raw = self._collect_raw()
        if not raw:
            return

        text = raw.decode("ascii", errors="ignore")
        await self._dispatcher.log_raw_in(self._config.interface_code, text)

        peer = format_peer(self._writer.get_extra_info("peername"))
        await self._dispatcher.log_interface(
            self._config.interface_code,
            "INFO",
            f"message.received peer={peer} bytes={len(raw)}",
        )
        handled = await handle_astm_message(
            text,
            peer,
            self._config,
            self._message_router,
            self._dispatcher,
            self._delimiters,
        )
        if not handled.response:
            return

        was_sent = await self._send_message(
            handled.response,
            handled.barcodes or [],
            handled.test_run_ids or [],
            handled.peer,
        )
        if was_sent and handled.query_response is not None:
            await self._message_router.handle_query_sent(handled.query_response)

    async def _send_message(
        self,
        message: AstmMessage,
        barcodes: list[str],
        test_run_ids: list[int],
        peer: str,
    ) -> bool:
        frames = frame_message(message, self._config.frame.size)
        if not frames:
            return False

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
            return False

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
                return False

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
                f"barcodes={format_csv(barcodes)} "
                f"test_run_ids={format_csv(test_run_ids)}"
            ),
        )
        return True

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
