"""Loading and saving the one state file. Decides nothing."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import State, Team

VERSION = 1


class StoreError(RuntimeError):
    pass


def load_state(path: str | Path) -> State:
    path = Path(path)
    if not path.exists():
        return State()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("version") != VERSION:
        raise StoreError(f"{path} has format version {raw.get('version')!r}; this program reads version {VERSION}.")
    return State.model_validate(raw)


def save_state(path: str | Path, state: State) -> None:
    """Write the whole file to a temporary name, then rename, so a crash cannot leave it half-written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state.model_dump(mode="json", by_alias=True), indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_team(path: str | Path) -> Team:
    return Team.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))
