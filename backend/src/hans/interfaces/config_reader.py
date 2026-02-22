from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import yaml


@dataclass(frozen=True)
class ServerConfig:
    host: str
    port: int


@dataclass(frozen=True)
class FrameConfig:
    size: int
    validate_checksum: bool = True


@dataclass(frozen=True)
class ResponseConfig:
    include_patient: bool = True
    send_empty_on_missing: bool = False


@dataclass(frozen=True)
class InterfaceConfig:
    interface_code: str
    server: ServerConfig
    frame: FrameConfig
    delimiters: Dict
    response: ResponseConfig
    translation: Dict

    @classmethod
    def load(cls, path: Path) -> "InterfaceConfig":
        # Parse raw config data from disk.
        raw = _load_data(path)
        server = ServerConfig(**raw.get("server", {}))
        frame = FrameConfig(**raw.get("frame", {}))

        delimiters = raw.get("delimiters") or {}

        response = ResponseConfig(
            include_patient=raw.get("response", {}).get("include_patient", True),
            send_empty_on_missing=raw.get("response", {}).get("send_empty_on_missing", True),
        )

        translation = raw.get("translation") or {}
        # Attach ASTM mapping to translation payload for handler access.
        if not isinstance(translation, dict):
            translation = {}
        astm_mapping = raw.get("astm_mapping")
        if isinstance(astm_mapping, dict):
            translation = dict(translation)
            translation["_astm_mapping"] = astm_mapping
        # Use explicit interface_code or fall back to the filename stem.
        interface_code = raw.get("interface_code") or path.stem

        return cls(
            interface_code=interface_code,
            server=server,
            frame=frame,
            delimiters=delimiters,
            response=response,
            translation=translation,
        )


def _load_data(path: Path) -> dict:
    # Load YAML configuration into a plain dict.
    raw_text = path.read_text(encoding="utf-8")
    return yaml.safe_load(raw_text) or {}
