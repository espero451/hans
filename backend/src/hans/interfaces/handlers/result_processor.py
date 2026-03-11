from __future__ import annotations

from types import SimpleNamespace
from typing import Protocol

from ..config_reader import InterfaceConfig
from ..dom import ResultsReceived


# --- Result Processor -------------------------------------------------

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

    async def store_results(self, interface_code: str, payloads: list[object]) -> list[int]:
        ...


class ResultProcessor:
    def __init__(self, dispatcher: DispatcherLike, config: InterfaceConfig) -> None:
        self._dispatcher = dispatcher
        self._config = config

    async def process(self, message: ResultsReceived) -> None:
        # Convert plain domain dicts to attribute objects expected by dispatcher storage.
        payloads = [SimpleNamespace(**payload) for payload in message.results]
        barcodes = [payload.specimen_id for payload in payloads]
        await self._dispatcher.log_event(
            interface_code=self._config.interface_code,
            peer=message.peer,
            direction="IN",
            message_type="RESULT",
            stage="DISPATCHED",
            barcodes=barcodes,
            test_run_ids=[],
        )
        await self._dispatcher.log_interface(
            self._config.interface_code,
            "INFO",
            (
                "results.parsed "
                f"barcodes={_format_csv(barcodes)} "
                f"results={len(payloads)}"
            ),
        )
        if not payloads:
            await self._dispatcher.log_event(
                interface_code=self._config.interface_code,
                peer=message.peer,
                direction="IN",
                message_type="RESULT",
                stage="PARSED",
                barcodes=barcodes,
                test_run_ids=[],
            )
            await self._dispatcher.log_event(
                interface_code=self._config.interface_code,
                peer=message.peer,
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
            peer=message.peer,
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


# --- Helpers ----------------------------------------------------------

def _format_csv(items: list[object]) -> str:
    # Join list values for compact trace logging.
    return ",".join(str(item) for item in items if item)
