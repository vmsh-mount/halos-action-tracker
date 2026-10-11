"""The command line, run in-process on saved answers made from the answer key. No network."""

import datetime as dt
import json

import pytest

from conftest import ROOT, WEEK, key_answer, transcript
from standup_tracker import cli, service, store
from standup_tracker.llm import LLMResponse
from standup_tracker.llm.replay import RecordingClient
from standup_tracker.models import State
from standup_tracker import review


class KeyModel:
    def complete(self, request):
        return LLMResponse(text=json.dumps(key_answer(request.lookup_key[:10])), provider="api", model="stand-in")


@pytest.fixture
def workspace(tmp_path, monkeypatch, team):
    """A state file and a folder of saved answers recorded from the stand-in, as the Recorder would make them."""
    saved = tmp_path / "saved"
    recorder, state = RecordingClient(KeyModel(), saved), State()
    for day in WEEK:
        service.submit_standup(state, dt.date.fromisoformat(day), transcript(day), team, recorder)
        review.approve(state)
    monkeypatch.chdir(ROOT)
    monkeypatch.setenv("STATE_FILE", str(tmp_path / "state.json"))
    monkeypatch.setenv("SAVED_ANSWERS_DIR", str(saved))
    monkeypatch.setenv("TEAM_FILE", str(ROOT / "config" / "team.json"))
    return tmp_path


def run(*argv):
    return cli.main(list(argv))


def test_run_week_replays_the_five_days(workspace, capsys):
    assert run("run-week", "transcripts") == 0
    out = capsys.readouterr().out
    state = store.load_state(workspace / "state.json")
    assert len(state.days) == 5 and state.draft is None and len(state.days[-1].items_after) == 14
    assert "The list (14 items)" in out and "Saved answer, recorded" in out and "new speakers: Rohan" in out


def test_process_show_approve_and_discard(workspace, capsys):
    assert run("process", "transcripts/2025-10-13.txt") == 0
    assert "needs review: hedged: 'maybe'" in capsys.readouterr().out
    assert run("process", "transcripts/2025-10-13.txt") == 1  # a draft exists; needs --rerun
    assert "already has a draft" in capsys.readouterr().err
    assert run("process", "transcripts/2025-10-13.txt", "--rerun") == 0
    assert run("show") == 0 and "A6" in capsys.readouterr().out
    assert run("discard") == 0 and store.load_state(workspace / "state.json").draft is None
    assert run("process", "transcripts/2025-10-13.txt") == 0 and run("approve") == 0
    assert len(store.load_state(workspace / "state.json").days) == 1
    assert run("approve") == 1 and "no draft" in capsys.readouterr().err


def test_errors_are_messages_not_tracebacks(workspace, capsys, tmp_path):
    assert run("process", "transcripts/no-such-file.txt", "--date", "2025-10-13") == 1
    assert "Error:" in capsys.readouterr().err
    other = tmp_path / "notes.txt"
    other.write_text("Ana: Something nobody recorded an answer for.")
    assert run("process", str(other)) == 1 and "Give --date" in capsys.readouterr().err
    assert run("process", str(other), "--date", "2025-10-13") == 1
    assert "No saved answer for this transcript" in capsys.readouterr().err
    assert store.load_state(workspace / "state.json").last_failed_run["date"] == "2025-10-13"


def test_reset_deletes_the_state(workspace):
    run("process", "transcripts/2025-10-13.txt")
    assert (workspace / "state.json").exists()
    assert run("reset") == 0 and not (workspace / "state.json").exists()
