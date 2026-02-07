from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import yaml


@dataclass(frozen=True)
class TranslationTable:
    test_id_to_code: Dict[int, str]
    code_to_test_id: Dict[str, int]

    @classmethod
    def load(cls, path: Path) -> "TranslationTable":
        raw = _load_data(path)
        return cls.from_data(raw)

    @classmethod
    def from_data(cls, raw: dict) -> "TranslationTable":
        test_id_to_code: Dict[int, str] = {}
        code_to_test_id: Dict[str, int] = {}

        for entry in raw.get("tests", []):
            raw_id = entry.get("test_catalog_id", entry.get("test_id"))
            if raw_id is None:
                continue
            test_id = int(raw_id)
            code = str(entry["code"])
            test_id_to_code[test_id] = code
            code_to_test_id[code] = test_id

        return cls(test_id_to_code=test_id_to_code, code_to_test_id=code_to_test_id)


def _load_data(path: Path) -> dict:
    suffix = path.suffix.lower()
    raw_text = path.read_text(encoding="utf-8")
    if suffix in {".yaml", ".yml"}:
        return yaml.safe_load(raw_text) or {}
    if suffix == ".json":
        return yaml.safe_load(raw_text) or {}
    return yaml.safe_load(raw_text) or {}
