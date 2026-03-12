from __future__ import annotations

from typing import Iterable


# --- Utilities --------------------------------------------------------

def format_peer(peer: object) -> str:
    if isinstance(peer, tuple):
        return f"{peer[0]}:{peer[1]}"
    return str(peer)


def format_csv(items: Iterable[object]) -> str:
    # Join items for logs.
    return ",".join(str(item) for item in items if item)


def optional_str(value: object) -> str | None:
    # Normalize optional values to stripped strings or None.
    if value is None:
        return None
    text = str(value).strip()
    return text or None
