from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class TranslationTable:
    lis_to_instrument: dict[str, str]
    instrument_to_lis: dict[str, str]

    @classmethod
    def load(cls, path: Path) -> "TranslationTable":
        raw = _load_data(path)
        return cls.from_data(raw)

    @classmethod
    def from_data(cls, raw: dict) -> "TranslationTable":
        lis_to_instrument: dict[str, str] = {}
        instrument_to_lis: dict[str, str] = {}

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
    raw_text = path.read_text(encoding="utf-8")
    return yaml.safe_load(raw_text) or {}
