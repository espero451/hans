from __future__ import annotations

from ..dom import QueryRequested, QueryResponsePrepared, ResultsReceived
from .query_processor import QueryProcessor
from .result_processor import ResultProcessor


# --- Message Router ---------------------------------------------------

class MessageRouter:
    def __init__(
        self,
        query_processor: QueryProcessor,
        result_processor: ResultProcessor,
    ) -> None:
        self._query_processor = query_processor
        self._result_processor = result_processor

    async def handle_query(
        self, message: QueryRequested
    ) -> QueryResponsePrepared | None:
        # Route query domain messages to query business logic.
        return await self._query_processor.process(message)

    async def handle_results(self, message: ResultsReceived) -> None:
        # Route result domain messages to result business logic.
        await self._result_processor.process(message)

    async def handle_query_sent(self, message: QueryResponsePrepared) -> None:
        # Finalize query lifecycle after outbound ASTM response succeeds.
        await self._query_processor.mark_sent(message)
