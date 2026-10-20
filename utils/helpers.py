import json
import uuid
from pathlib import Path
from typing import Any

from config.settings import ROOT_DIR


def unique_id(prefix: str = "test") -> str:
    """Valeur unique pour éviter les collisions de données entre tests parallèles."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def load_json(relative_path: str) -> Any:
    return json.loads(Path(ROOT_DIR, relative_path).read_text(encoding="utf-8"))
