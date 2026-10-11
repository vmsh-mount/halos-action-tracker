"""Settings come from the environment and a git-ignored .env file, never from code."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    state_file: Path
    team_file: Path
    saved_answers: Path
    env: dict[str, str]

    @property
    def temperature(self) -> float | None:
        raw = (self.env.get("LLM_TEMPERATURE") or "").strip()
        return float(raw) if raw else None


def load_settings() -> Settings:
    load_dotenv()  # values may reference the shell, e.g. LLM_API_KEY=${SOME_KEY_ALREADY_EXPORTED}
    env = dict(os.environ)
    return Settings(
        state_file=Path(env.get("STATE_FILE") or "data/state.json"),
        team_file=Path(env.get("TEAM_FILE") or "config/team.json"),
        saved_answers=Path(env.get("SAVED_ANSWERS_DIR") or "tests/saved_answers"),
        env=env,
    )
