from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import yaml


@dataclass(frozen=True)
class TranslationTable:
    lis_to_instrument: Dict[str, str]
    instrument_to_lis: Dict[str, str]

    @classmethod
    def load(cls, path: Path) -> "TranslationTable":
        raw = _load_data(path)
        return cls.from_data(raw)

    @classmethod
    def from_data(cls, raw: dict) -> "TranslationTable":
        lis_to_instrument: Dict[str, str] = {}
        instrument_to_lis: Dict[str, str] = {}

        for entry in raw.get("tests", []):
            if not isinstance(entry, dict):
                continue
            lis_code = entry.get("lis_code")
            instrument_code = entry.get("instrument_code")
            if not lis_code or not instrument_code:
                continue
            lis_code = str(lis_code)
            instrument_code = str(instrument_code)
            lis_to_instrument[lis_code] = instrument_code
            instrument_to_lis[instrument_code] = lis_code

        return cls(
            lis_to_instrument=lis_to_instrument,
            instrument_to_lis=instrument_to_lis,
        )


def _load_data(path: Path) -> dict:
    suffix = path.suffix.lower()
    raw_text = path.read_text(encoding="utf-8")
    if suffix in {".yaml", ".yml"}:
        return yaml.safe_load(raw_text) or {}
    if suffix == ".json":
        return yaml.safe_load(raw_text) or {}
    return yaml.safe_load(raw_text) or {}
