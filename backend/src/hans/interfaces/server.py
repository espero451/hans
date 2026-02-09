from __future__ import annotations

# poetry run python -m hans.interfaces.server --config src/hans/interfaces/configs/astm_base.yaml
# poetry run python -m hans.interfaces.server

import argparse
import asyncio
import importlib
import inspect
import logging
from pathlib import Path
from typing import Callable, Awaitable, Iterable

import yaml

from .config_reader import InterfaceConfig


logger = logging.getLogger("hans.interfaces")


def _load_raw_config(path: Path) -> dict:
    raw_text = path.read_text(encoding="utf-8")
    return yaml.safe_load(raw_text) or {}


def _resolve_handler_name(raw: dict) -> str:
    handler = raw.get("handler")

    if not handler:
        raise ValueError("Config must provide 'handler', 'route', or 'protocol'.")

    return str(handler).strip()


def _import_handler_module(handler_name: str):
    module_path = handler_name
    if "." not in handler_name:
        module_path = f"hans.interfaces.handlers.{handler_name}"
    return importlib.import_module(module_path)


def _resolve_handler_func(module) -> Callable[..., Awaitable[None]]:
    for candidate in ("handle_connection", "handle_stream", "handle"):
        func = getattr(module, candidate, None)
        if callable(func):
            return func
    raise AttributeError(
        f"Handler module {module.__name__} must define async function "
        f"'handle_connection', 'handle_stream', or 'handle'."
    )


async def _run_one(config_path: Path) -> None:
    raw = _load_raw_config(config_path)
    handler_name = _resolve_handler_name(raw)
    module = _import_handler_module(handler_name)
    handler_func = _resolve_handler_func(module)

    config = InterfaceConfig.load(config_path)

    logger.info(
        "Starting interface=%s handler=%s host=%s port=%s",
        config.interface_name,
        handler_name,
        config.server.host,
        config.server.port,
    )

    async def _handle_connection(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        addr = writer.get_extra_info("peername")
        logger.info("Client connected interface=%s peer=%s", config.interface_name, addr)
        try:
            sig = inspect.signature(handler_func)
            kwargs = {}
            if "config" in sig.parameters:
                kwargs["config"] = config
            if "raw_config" in sig.parameters:
                kwargs["raw_config"] = raw
            if "config_path" in sig.parameters:
                kwargs["config_path"] = config_path
            await handler_func(reader, writer, **kwargs)
        except Exception:
            logger.exception(
                "Handler error interface=%s handler=%s peer=%s",
                config.interface_name,
                handler_name,
                addr,
            )
        finally:
            if not writer.is_closing():
                writer.close()
                await writer.wait_closed()
            logger.info("Client disconnected interface=%s peer=%s", config.interface_name, addr)

    server = await asyncio.start_server(
        _handle_connection,
        host=config.server.host,
        port=config.server.port,
    )
    addr = ", ".join(str(sock.getsockname()) for sock in (server.sockets or []))
    logger.info("Listening interface=%s addr=%s", config.interface_name, addr)
    async with server:
        await server.serve_forever()


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

    # De-duplicate while preserving order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in config_paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def _scan_dir(path: Path) -> list[Path]:
    if not path.exists():
        return []
    patterns = ("*.yaml", "*.yml", "*.json")
    results: list[Path] = []
    for pattern in patterns:
        results.extend(sorted(path.glob(pattern)))
    return results


async def run_from_args(args: argparse.Namespace) -> None:
    configs_dir = Path(args.configs_dir).resolve() if args.configs_dir else None
    config_paths = _collect_configs(args.config or [], configs_dir)
    if not config_paths:
        raise FileNotFoundError("No config files provided or found.")

    await asyncio.gather(*(_run_one(path) for path in config_paths))


def main() -> None:
    parser = argparse.ArgumentParser(description="Hans interface server (multi-protocol)")
    parser.add_argument(
        "--config",
        action="append",
        default=[],
        help="Config file or directory. Can be provided multiple times.",
    )
    parser.add_argument(
        "--configs-dir",
        default=str(Path(__file__).with_name("configs")),
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
