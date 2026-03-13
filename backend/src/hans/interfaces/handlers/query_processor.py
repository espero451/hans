from __future__ import annotations

from typing import Protocol

from ..config_reader import InterfaceConfig
from ..dom import QueryRequested, QueryResponsePrepared


# --- Query Processor --------------------------------------------------

class QueryContextLike(Protocol):
    specimen_id: str
    patient_id: str | None
    patient_name: str | None
    test_codes: list[str]
    test_run_ids: list[int]


class QueryLoadResultLike(Protocol):
    contexts: list[QueryContextLike]
    reject_reason: str | None


class DispatcherLike(Protocol):
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
    ) -> QueryLoadResultLike:
        ...

    async def mark_sent(self, test_run_ids: list[int]) -> None:
        ...


class QueryProcessor:
    def __init__(
        self,
        dispatcher: DispatcherLike,
        config: InterfaceConfig,
    ) -> None:
        self._dispatcher = dispatcher
        self._config = config

    async def process(self, message: QueryRequested) -> QueryResponsePrepared | None:
        # Reject empty barcode batches before DB access.
        barcodes = message.barcodes
        await self._dispatcher.log_event(
            interface_code=self._config.interface_code,
            peer=message.peer,
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
                peer=message.peer,
                direction="IN",
                message_type="QUERY",
                stage="PARSED",
                barcodes=[],
                test_run_ids=[],
            )
            await self._dispatcher.log_event(
                interface_code=self._config.interface_code,
                peer=message.peer,
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

        query_load = await self._dispatcher.load_query_contexts(
            self._config.interface_code, barcodes
        )
        contexts = query_load.contexts
        test_run_ids = [
            run_id for context in contexts for run_id in context.test_run_ids if run_id
        ]
        tests_count = _count_tests(contexts)
        await self._dispatcher.log_event(
            interface_code=self._config.interface_code,
            peer=message.peer,
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
            reject_reason = query_load.reject_reason or "specimen_not_found"
            await self._dispatcher.log_event(
                interface_code=self._config.interface_code,
                peer=message.peer,
                direction="IN",
                message_type="QUERY",
                stage="REJECTED",
                barcodes=barcodes,
                test_run_ids=[],
                reason=reject_reason,
            )
            await self._dispatcher.log_interface(
                self._config.interface_code,
                "INFO",
                f"query.rejected reason={reject_reason}",
            )
            if reject_reason == "specimen_not_received":
                await self._dispatcher.log_interface(
                    self._config.interface_code,
                    "INFO",
                    "Specimen status is not RECEIVED",
                )
            return

        response_contexts = []
        for context in contexts:
            response_contexts.append(
                {
                    "specimen_id": context.specimen_id,
                    "test_codes": context.test_codes,
                    "patient_id": context.patient_id,
                    "patient_name": context.patient_name,
                }
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
        return QueryResponsePrepared(
            peer=message.peer,
            barcodes=barcodes,
            test_run_ids=test_run_ids,
            contexts=response_contexts,
        )

    async def mark_sent(self, message: QueryResponsePrepared) -> None:
        # Mark queued runs as SENT only after successful response delivery.
        await self._dispatcher.mark_sent(message.test_run_ids)
        await self._dispatcher.log_interface(
            self._config.interface_code,
            "INFO",
            f"status.sent test_run_ids={_format_csv(message.test_run_ids)}",
        )


# --- Helpers ----------------------------------------------------------

def _format_csv(items: list[object]) -> str:
    # Join list values for compact trace logging.
    return ",".join(str(item) for item in items if item)


def _count_tests(contexts: list[QueryContextLike]) -> int:
    # Count tests loaded for all resolved barcodes.
    return sum(len(context.test_codes) for context in contexts)
