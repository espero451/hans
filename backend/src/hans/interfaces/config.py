from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import yaml

from .model import AstmDelimiters


@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int


@dataclass(frozen=True)
class FrameConfig:
    size: int = 240
    validate_checksum: bool = False


@dataclass(frozen=True)
class QueryConfig:
    barcode_field_indexes: List[int] = field(default_factory=lambda: [2, 3])
    allow_component_split: bool = True


@dataclass(frozen=True)
class ResponseConfig:
    include_patient: bool = True
    send_empty_on_missing: bool = True


@dataclass(frozen=True)
class InterfaceConfig:
    interface_name: str
    mode: str
    server: ServerConfig
    frame: FrameConfig
    delimiters: AstmDelimiters
    query: QueryConfig
    response: ResponseConfig
    translation: Dict
    trace_dir: Path

    @classmethod
    def load(cls, path: Path) -> "InterfaceConfig":
        raw = _load_data(path)
        server = ServerConfig(**raw.get("server", {}))
        frame = FrameConfig(**raw.get("frame", {}))

        delims = raw.get("delimiters", {})
        delimiters = AstmDelimiters(
            field=delims.get("field", "|"),
            component=delims.get("component", "^"),
            repeat=delims.get("repeat", "\\"),
            escape=delims.get("escape", "&"),
            record=delims.get("record", "\r"),
        )

        query = QueryConfig(
            barcode_field_indexes=raw.get("query", {}).get("barcode_field_indexes", [2, 3]),
            allow_component_split=raw.get("query", {}).get("allow_component_split", True),
        )
        response = ResponseConfig(
            include_patient=raw.get("response", {}).get("include_patient", True),
            send_empty_on_missing=raw.get("response", {}).get("send_empty_on_missing", True),
        )

        translation = raw.get("translation") or {}
        mode = raw.get("mode", "query")
        interface_name = raw.get("interface_name") or path.stem
        trace_dir = _resolve_trace_dir(raw.get("trace_dir"), default=Path.cwd() / "trace")

        return cls(
            interface_name=interface_name,
            mode=mode,
            server=server,
            frame=frame,
            delimiters=delimiters,
            query=query,
            response=response,
            translation=translation,
            trace_dir=trace_dir,
        )


def _resolve_trace_dir(value: str | None, default: Path) -> Path:
    if not value:
        return default.resolve()
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return (Path.cwd() / candidate).resolve()


def _load_data(path: Path) -> dict:
    suffix = path.suffix.lower()
    raw_text = path.read_text(encoding="utf-8")
    if suffix in {".yaml", ".yml"}:
        return yaml.safe_load(raw_text) or {}
    if suffix == ".json":
        return yaml.safe_load(raw_text) or {}
    return yaml.safe_load(raw_text) or {}
