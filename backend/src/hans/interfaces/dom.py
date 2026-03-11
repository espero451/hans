from __future__ import annotations


# --- Domain Messages --------------------------------------------------

class QueryRequested:
    def __init__(self, peer: str, barcodes: list[str]) -> None:
        # Keep raw query input normalized for downstream handlers.
        self.peer = peer
        self.barcodes = barcodes


class ResultsReceived:
    def __init__(self, peer: str, results: list[dict[str, object]]) -> None:
        # Carry parsed result values independent from ASTM record internals.
        self.peer = peer
        self.results = results


class QueryResponsePrepared:
    def __init__(
        self,
        peer: str,
        barcodes: list[str],
        test_run_ids: list[int],
        contexts: list[dict[str, object]],
    ) -> None:
        # Keep response payload as pure domain data until protocol rendering.
        self.peer = peer
        self.barcodes = barcodes
        self.test_run_ids = test_run_ids
        self.contexts = contexts
