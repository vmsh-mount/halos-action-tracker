import datetime as dt
import json
from pathlib import Path

import pytest

from standup_tracker import review, service
from standup_tracker.apply import proposed_from_raw
from standup_tracker.models import State
from standup_tracker.store import load_team

ROOT = Path(__file__).resolve().parent.parent
WEEK = ["2025-10-13", "2025-10-14", "2025-10-15", "2025-10-16", "2025-10-17"]


@pytest.fixture(autouse=True)
def never_a_live_model(monkeypatch):
    """A key in the shell or in .env must not make a test run call a live model."""
    monkeypatch.setenv("LLM_PROVIDER", "replay")
    monkeypatch.delenv("LLM_API_KEY", raising=False)


@pytest.fixture(scope="session")
def team():
    return load_team(ROOT / "config" / "team.json")


def transcript(day: str) -> str:
    return (ROOT / "transcripts" / f"{day}.txt").read_text()


def key_answer(day: str) -> dict:
    return json.loads((ROOT / "tests" / "fixtures" / "answer_key_changes" / f"{day}.json").read_text())


def submit(state: State, team, day: str, answer: dict, *, text: str | None = None, confirm_rerun: bool = False):
    """Submit one day with a hand-written answer in place of the model's."""
    date = dt.date.fromisoformat(day)
    service.check_can_submit(state, date, confirm_rerun=confirm_rerun)
    standup = service.make_standup(date, transcript(day) if text is None else text)
    changes = [proposed_from_raw(c) for c in answer.get("changes", [])]
    return service.build_draft(state, standup, changes, answer.get("not_tracked"), team)


def run_week(team, days=WEEK, *, after_draft=None) -> State:
    """Run the answer key through the real code, approving each day. after_draft(day, state) may edit first."""
    state = State()
    for day in days:
        submit(state, team, day, key_answer(day))
        if after_draft:
            after_draft(day, state)
        review.approve(state)
    return state


def by_id(items):
    return {item.id: item for item in items}
