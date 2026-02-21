from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable


logger = logging.getLogger("hans.interfaces")


@dataclass(frozen=True)
class ListenerSpec:
    interface_code: str
    host: str
    port: int
    handler: Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]]


async def _serve_one(spec: ListenerSpec) -> None:
    # Serve one interface.
    async def _handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        logger.info("Client connected interface=%s peer=%s", spec.interface_code, addr)
        try:
            await spec.handler(reader, writer)
        except Exception:
            logger.exception(
                "Handler error interface=%s peer=%s",
                spec.interface_code,
                addr,
            )
        finally:
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
            logger.info("Client disconnected interface=%s peer=%s", spec.interface_code, addr)

    server = await asyncio.start_server(_handle, host=spec.host, port=spec.port)
    addr = ", ".join(str(sock.getsockname()) for sock in (server.sockets or []))
    logger.info("Listening interface=%s addr=%s", spec.interface_code, addr)
    try:
        async with server:
            await server.serve_forever()
    except asyncio.CancelledError:
        # Allow graceful shutdown on cancellation.
        logger.info("Listener cancelled interface=%s", spec.interface_code)
        raise


async def run_listeners(listeners: Iterable[ListenerSpec]) -> None:
    # Start all listeners.
    await asyncio.gather(*(_serve_one(spec) for spec in listeners))
