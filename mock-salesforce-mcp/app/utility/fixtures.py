from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(base_dir: Path, filename: str) -> list[dict[str, Any]]:
    path = base_dir / filename
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

