from __future__ import annotations

import argparse
import asyncio
import importlib
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable, Iterable

import yaml
from sqlalchemy import select

from hans.core.db import SessionLocal
from hans.orders import Order, Specimen, TestRun, Result
from hans.patients import Patient
from hans.tests import TestCatalog

from ..config_reader import InterfaceConfig
from ..server import ListenerSpec, run_listeners
from ..translation import TranslationTable

# Ensure all ORM models are registered in Base.metadata
import hans.specimens
import hans.tests
import hans.orders
import hans.services
import hans.instruments
import hans.patients
import hans.owners


logger = logging.getLogger("hans.dispatcher")


# --- Data Types -------------------------------------------------------

@dataclass(frozen=True)
class QueryContext:
    specimen_id: str
    patient_id: str | None
    patient_name: str | None
    test_codes: list[str]
    test_run_ids: list[int]


@dataclass(frozen=True)
class InterfaceState:
    config: InterfaceConfig
    handler: object
    translation: TranslationTable
    handler_name: str
    config_path: Path


# --- Dispatcher Core --------------------------------------------------

class Dispatcher:
    def __init__(self, base_trace_dir: Path | str = Path("../live/instruments")) -> None:
        self._base_trace_dir = Path(base_trace_dir)
        self._lock = asyncio.Lock()
        self._states: dict[str, InterfaceState] = {}
        self._trace_started: set[str] = set()

    def register_state(self, state: InterfaceState) -> None:
        # Track interface state.
        self._states[state.config.interface_code] = state

    async def log_raw_in(self, interface_code: str, raw: str) -> None:
        # Write raw input trace.
        await self._write_raw(interface_code, "input.trace", raw)

    async def log_raw_out(self, interface_code: str, raw: str) -> None:
        # Write raw output trace.
        await self._write_raw(interface_code, "output.trace", raw)

    async def log_interface(self, interface_code: str, level: str, message: str) -> None:
        # Write interface trace line.
        state = self._state(interface_code)
        date_dir = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"{interface_code}:{date_dir}"
        line = _format_interface_line(level, message)
        path = self._interface_trace_path(interface_code, date_dir)
        async with self._lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            if key not in self._trace_started:
                start = _format_interface_line(
                    "INFO",
                    f"trace.start interface={interface_code} config={state.config_path}",
                )
                with path.open("a", encoding="utf-8", newline="") as handle:
                    handle.write(start)
                    handle.write(line)
                self._trace_started.add(key)
                return
            with path.open("a", encoding="utf-8", newline="") as handle:
                handle.write(line)

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
        # Write dispatcher trace line.
        ts = _format_timestamp()
        barcodes_str = ",".join(barcodes)
        test_runs = ",".join(str(item) for item in test_run_ids)
        parts = [
            f"ts={ts}",
            f"interface={interface_code}",
            f"dir={direction}",
            f"type={message_type}",
            f"stage={stage}",
            f"peer={peer}",
            f"barcodes={barcodes_str}",
            f"test_run_ids={test_runs}",
        ]
        if reason:
            parts.append(f"reason={reason}")
        line = " ".join(parts) + "\n"
        path = self._trace_path()
        async with self._lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="") as handle:
                handle.write(line)

    async def load_query_contexts(
        self, interface_code: str, barcodes: list[str]
    ) -> list[QueryContext]:
        # Load context for barcodes.
        state = self._state(interface_code)
        return await _load_query_contexts(barcodes, state.translation)

    async def store_results(self, interface_code: str, payloads: list) -> list[int]:
        # Store results and update status.
        state = self._state(interface_code)
        return await _store_results(payloads, state.translation)

    async def mark_sent(self, test_run_ids: list[int]) -> None:
        # Update test runs as SENT.
        await _mark_status(test_run_ids, "SENT", skip_if="RECEIVED")

    async def mark_received(self, test_run_ids: list[int]) -> None:
        # Update test runs as RECEIVED.
        await _mark_status(test_run_ids, "RECEIVED")

    async def _write_raw(self, interface_code: str, filename: str, raw: str) -> None:
        path = self._raw_path(interface_code, filename)
        async with self._lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="") as handle:
                handle.write(raw)

    def _raw_path(self, interface_code: str, filename: str) -> Path:
        date_dir = datetime.utcnow().strftime("%Y-%m-%d")
        return self._base_trace_dir / interface_code / date_dir / filename

    def _trace_path(self) -> Path:
        date_dir = datetime.utcnow().strftime("%Y-%m-%d")
        return self._base_trace_dir / "dispatcher" / date_dir / "dispatcher.trace"

    def _interface_trace_path(self, interface_code: str, date_dir: str) -> Path:
        return self._base_trace_dir / interface_code / date_dir / f"{interface_code}.trace"

    def _state(self, interface_code: str) -> InterfaceState:
        if interface_code not in self._states:
            raise KeyError(f"Interface not registered: {interface_code}")
        return self._states[interface_code]


def _format_timestamp() -> str:
    now = datetime.utcnow()
    ms = now.microsecond // 1000
    return now.strftime("%Y-%m-%dT%H:%M:%S") + f".{ms:03d}Z"


def _format_interface_line(level: str, message: str) -> str:
    now = datetime.utcnow()
    ms = now.microsecond // 1000
    ts = now.strftime("%H:%M:%S")
    return f"{ts}.{ms:03d} [{level}] {message}\n"


# --- Config Loading ---------------------------------------------------

def _default_configs_dir() -> Path:
    # Resolve the default interface config directory.
    return Path(__file__).resolve().parents[1] / "configs"


def _load_raw_config(path: Path) -> dict:
    raw_text = path.read_text(encoding="utf-8")
    return yaml.safe_load(raw_text) or {}


def _resolve_handler_name(raw: dict) -> str:
    handler = raw.get("handler")
    if not handler:
        raise ValueError("Config must provide 'handler'.")
    return str(handler).strip()


def _import_handler_module(handler_name: str):
    module_path = handler_name
    if "." not in handler_name:
        module_path = f"hans.interfaces.handlers.{handler_name}"
    return importlib.import_module(module_path)


def _scan_dir(path: Path) -> list[Path]:
    if not path.exists():
        return []
    patterns = ("*.yaml", "*.yml", "*.json")
    results: list[Path] = []
    for pattern in patterns:
        results.extend(sorted(path.glob(pattern)))
    return results


def _collect_configs(paths: Iterable[str], configs_dir: Path | None) -> list[Path]:
    config_paths: list[Path] = []
    for item in paths:
        candidate = Path(item)
        if candidate.is_dir():
            config_paths.extend(_scan_dir(candidate))
        else:
            config_paths.append(candidate)

    if configs_dir:
        config_paths.extend(_scan_dir(configs_dir))

    seen: set[Path] = set()
    unique: list[Path] = []
    for path in config_paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


async def _load_query_contexts(
    barcodes: list[str],
    translation: TranslationTable,
) -> list[QueryContext]:
    # Load context for query barcodes.
    contexts: list[QueryContext] = []
    for barcode in barcodes:
        context = await _load_one_context(barcode, translation)
        if not context:
            return []
        contexts.append(context)
    return contexts


async def _load_one_context(
    barcode: str,
    translation: TranslationTable,
) -> QueryContext | None:
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
        test_run_ids: list[int] = []
        for test_run, test_catalog in runs_result.all():
            lis_code = test_catalog.code
            code = translation.lis_to_instrument.get(lis_code, lis_code)
            test_codes.append(code)
            test_run_ids.append(test_run.id)

        patient_id = str(patient.id) if patient else None
        patient_name = patient.name if patient else None
        return QueryContext(
            specimen_id=specimen.specimen_id,
            patient_id=patient_id,
            patient_name=patient_name,
            test_codes=test_codes,
            test_run_ids=test_run_ids,
        )


async def _store_results(payloads: list, translation: TranslationTable) -> list[int]:
    # Store results and mark received.
    if not payloads:
        return []

    deduped: dict[tuple[str, str], object] = {}
    for payload in payloads:
        deduped[(payload.specimen_id, payload.test_code)] = payload

    payloads = list(deduped.values())
    specimen_ids = {payload.specimen_id for payload in payloads}
    lis_codes = {
        translation.instrument_to_lis.get(payload.test_code, payload.test_code)
        for payload in payloads
    }
    if not specimen_ids or not lis_codes:
        return []

    async with SessionLocal() as session:
        runs_result = await session.execute(
            select(TestRun, TestCatalog)
            .join(TestCatalog, TestCatalog.id == TestRun.test_catalog_id)
            .where(
                TestRun.specimen_id.in_(specimen_ids),
                TestCatalog.code.in_(lis_codes),
            )
        )
        test_runs: dict[tuple[str, str], TestRun] = {}
        test_run_ids: list[int] = []
        for test_run, test_catalog in runs_result.all():
            test_runs[(test_run.specimen_id, test_catalog.code)] = test_run
            test_run_ids.append(test_run.id)

        existing = await _load_existing_results(session, test_run_ids)
        updated_ids = _apply_results(session, payloads, test_runs, existing, translation)

        if updated_ids:
            await session.commit()
        return updated_ids


def _apply_results(
    session,
    payloads: list,
    test_runs: dict[tuple[str, str], TestRun],
    existing: dict[int, Result],
    translation: TranslationTable,
) -> list[int]:
    updated_ids: list[int] = []
    for payload in payloads:
        lis_code = translation.instrument_to_lis.get(payload.test_code, payload.test_code)
        test_run = test_runs.get((payload.specimen_id, lis_code))
        if not test_run:
            continue

        existing_result = existing.get(test_run.id)
        if existing_result:
            existing_result.value = payload.value
            existing_result.units = payload.units
            existing_result.flags = payload.flags
            existing_result.completed_at = payload.completed_at
            existing_result.verified = payload.verified
        else:
            session.add(
                Result(
                    test_run_id=test_run.id,
                    value=payload.value,
                    units=payload.units,
                    flags=payload.flags,
                    completed_at=payload.completed_at,
                    verified=payload.verified,
                )
            )

        if test_run.status != "RECEIVED":
            test_run.status = "RECEIVED"
        updated_ids.append(test_run.id)
    return list({run_id for run_id in updated_ids})


async def _load_existing_results(session, test_run_ids: list[int]) -> dict[int, Result]:
    if not test_run_ids:
        return {}
    existing: dict[int, Result] = {}
    existing_result = await session.execute(
        select(Result)
        .where(Result.test_run_id.in_(test_run_ids))
        .order_by(Result.id.desc())
    )
    for result in existing_result.scalars():
        if result.test_run_id not in existing:
            existing[result.test_run_id] = result
    return existing


async def _mark_status(test_run_ids: list[int], status: str, skip_if: str | None = None) -> None:
    if not test_run_ids:
        return
    unique_ids = list({run_id for run_id in test_run_ids if run_id})
    if not unique_ids:
        return
    async with SessionLocal() as session:
        result = await session.execute(select(TestRun).where(TestRun.id.in_(unique_ids)))
        updated = 0
        for test_run in result.scalars():
            if skip_if and test_run.status == skip_if:
                continue
            if test_run.status != status:
                test_run.status = status
                updated += 1
        if updated:
            await session.commit()


def _make_connection_handler(state: InterfaceState, dispatcher: Dispatcher) -> Callable[..., Awaitable[None]]:
    async def _handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        session = state.handler.AstmSession(reader, writer, state.config, dispatcher)
        await session.run()
    return _handle


# --- CLI Runner -------------------------------------------------------

async def _run_with_configs(config_paths: list[Path]) -> None:
    # Build listeners from resolved config paths and run them.
    dispatcher = Dispatcher()
    # Collect listener specs for each interface.
    listeners = []

    for config_path in config_paths:
        raw = _load_raw_config(config_path)
        handler_name = _resolve_handler_name(raw)
        handler_module = _import_handler_module(handler_name)
        config = InterfaceConfig.load(config_path)
        translation = TranslationTable.from_data(config.translation)

        state = InterfaceState(
            config=config,
            handler=handler_module,
            translation=translation,
            handler_name=handler_name,
            config_path=config_path,
        )
        dispatcher.register_state(state)

        listeners.append(
            ListenerSpec(
                interface_code=config.interface_code,
                host=config.server.host,
                port=config.server.port,
                handler=_make_connection_handler(state, dispatcher),
            )
        )

    await run_listeners(listeners)


async def run_from_configs(
    config_paths: list[str] | None = None,
    configs_dir: str | Path | None = None,
) -> None:
    # Load configs and start listener tasks.
    resolved_dir = Path(configs_dir).resolve() if configs_dir else _default_configs_dir()
    config_paths = _collect_configs(config_paths or [], resolved_dir)
    if not config_paths:
        raise FileNotFoundError("No config files provided or found.")
    await _run_with_configs(config_paths)


async def run_from_args(args: argparse.Namespace) -> None:
    # Run the dispatcher from CLI-provided arguments.
    await run_from_configs(args.config or [], args.configs_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Hans interface dispatcher")
    parser.add_argument(
        "--config",
        action="append",
        default=[],
        help="Config file or directory. Can be provided multiple times.",
    )
    parser.add_argument(
        "--configs-dir",
        default=str(_default_configs_dir()),
        help="Directory containing interface configs.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    asyncio.run(run_from_args(args))


if __name__ == "__main__":
    main()
