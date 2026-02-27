from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from .engine import run_from_configs


logger = logging.getLogger("hans.dispatcher.service")


# --- Helpers ----------------------------------------------------------

def _format_timestamp(now: datetime) -> str:
    # Format timestamps with millisecond precision.
    ms = now.microsecond // 1000
    return now.strftime("%H:%M:%S") + f".{ms:03d}"


def _utc_now() -> datetime:
    # Return the current UTC timestamp.
    return datetime.utcnow()


# --- Dispatcher Service -----------------------------------------------

class DispatcherService:
    def __init__(self) -> None:
        # Track the background dispatcher task and last error.
        self._task = None
        self._lock = asyncio.Lock()
        self._last_error = None
        # Store lifecycle timestamps for status reporting.
        self._last_started_at = None
        self._last_stopped_at = None
        # Keep dispatcher trace logs in the shared live directory.
        self._trace_dir = Path("../live/instruments")

    async def start(self) -> None:
        # Start dispatcher listeners if not running.
        async with self._lock:
            if self._task and not self._task.done():
                return
            self._last_error = None
            self._last_started_at = _format_timestamp(_utc_now())
            self._task = asyncio.create_task(self._run(), name="dispatcher")
        self._write_trace("dispatcher.start")

    async def stop(self) -> None:
        # Stop dispatcher listeners if running.
        async with self._lock:
            task = self._task
            if not task or task.done():
                return
            task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        self._last_stopped_at = _format_timestamp(_utc_now())
        self._write_trace("dispatcher.stop")

    async def restart(self) -> None:
        # Restart dispatcher listeners.
        await self.stop()
        await self.start()

    def status(self) -> dict:
        # Report dispatcher status for API/UI.
        task = self._task
        running = bool(task and not task.done())
        return {
            "running": running,
            "error": self._last_error,
            "last_started_at": self._last_started_at,
            "last_stopped_at": self._last_stopped_at,
        }

    def trace_path(self) -> Path | None:
        # Resolve the most recent dispatcher trace path, if any.
        base_dir = self._trace_dir / "dispatcher"
        if not base_dir.exists():
            return None
        date_dirs = sorted(
            (path for path in base_dir.iterdir() if path.is_dir()), reverse=True
        )
        for date_dir in date_dirs:
            trace_path = date_dir / "dispatcher.trace"
            if trace_path.exists():
                return trace_path
        return None

    def read_trace(self) -> str:
        # Read the latest dispatcher trace output for the UI.
        trace_path = self.trace_path()
        if not trace_path or not trace_path.exists():
            return "No dispatcher trace available."
        return trace_path.read_text(encoding="utf-8")

    async def _run(self) -> None:
        # Run dispatcher and capture failures for diagnostics.
        try:
            await run_from_configs()
        except asyncio.CancelledError:
            logger.info("Dispatcher task cancelled")
            raise
        except Exception as exc:
            self._last_error = str(exc)
            self._last_stopped_at = _format_timestamp(_utc_now())
            logger.exception("Dispatcher stopped with error")
            self._write_trace("dispatcher.error", f"error={self._last_error}")
            self._write_trace("dispatcher.stop", "reason=error")
            return

    def _write_trace(self, event: str, detail: str | None = None) -> None:
        # Append a dispatcher lifecycle event to the trace file.
        now = _utc_now()
        line_parts = [f"{_format_timestamp(now)}", f"event={event}"]
        if detail:
            line_parts.append(detail)
        line = " ".join(line_parts) + "\n"
        trace_path = self._trace_dir / "dispatcher" / now.strftime("%Y-%m-%d") / "dispatcher.trace"
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        with trace_path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(line)


# Shared dispatcher service instance.
dispatcher_service = DispatcherService()
