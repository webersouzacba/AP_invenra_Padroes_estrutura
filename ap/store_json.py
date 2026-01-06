from __future__ import annotations

import json
import os
from typing import Any, Dict


class JsonFileDatabase:

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        if not os.path.exists(filepath):
            self._write({"instances": {}, "events": []})

    def _read(self) -> Dict[str, Any]:
        with open(self.filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: Dict[str, Any]) -> None:
        tmp = self.filepath + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.filepath)

    def read_all(self) -> Dict[str, Any]:
        return self._read()

    def write_all(self, data: Dict[str, Any]) -> None:
        self._write(data)
