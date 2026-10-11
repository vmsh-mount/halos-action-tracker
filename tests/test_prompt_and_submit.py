"""What is sent to the model, the practice-word test (H8), and the submit use case with a stand-in model."""

import datetime as dt
import json
import re
from pathlib import Path

import pytest

from conftest import ROOT, WEEK, by_id, key_answer, run_week, transcript
from standup_tracker import prompt, review, service
from standup_tracker.llm import LLMFatal, LLMResponse, LLMUnavailable
from standup_tracker.models import State

SRC = ROOT / "src" / "standup_tracker"
# Written by hand, not built from the team settings: two of these are not in that file.
PRACTICE_WORDS = ["Arjun", "Priya", "Dev", "Devansh", "Sana", "Rohan", "Hermes", "Atlas", "Falcon"]
PRACTICE_TICKET_FORMS = ["PAY-", "APP-"]


class Answers:
    """Stands in for the model: returns the answer key for whichever date is asked about."""

    def __init__(self, override=None):
        self.requests, self.override = [], override

    def complete(self, request):
        self.requests.append(request)
        if isinstance(self.override, Exception):
            raise self.override
        day = request.lookup_key[:10]
        return LLMResponse(text=self.override or json.dumps(key_answer(day)), provider="api", model="stand-in")


def submit(state, team, day, client, **kwargs):
    return service.submit_standup(state, dt.date.fromisoformat(day), transcript(day), team, client, **kwargs)


# --- H8: nothing is wired to the practice week


@pytest.mark.parametrize("path", sorted(SRC.rglob("*.py")) + sorted(SRC.rglob("*.md")), ids=lambda p: p.name)
def test_no_word_from_the_practice_week_in_the_source_or_the_prompt_template(path):
    text = path.read_text(encoding="utf-8")
    found = [w for w in PRACTICE_WORDS if re.search(rf"(?<![A-Za-z]){w}(?![A-Za-z])", text)]
    found += [form for form in PRACTICE_TICKET_FORMS if form in text]
    assert found == []


def test_the_template_is_scanned_before_team_facts_are_filled_in():
    assert "{{people}}" in prompt.TEMPLATE.read_text() and prompt.TEMPLATE.is_relative_to(SRC)


# --- what the model is given


def test_instructions_are_the_same_every_day_and_carry_the_team(team):
    text = prompt.instructions(team)
    assert "{{" not in text and "also called Devansh" in text and "PAY-: payments" in text
    state = run_week(team, WEEK[:2])
    wednesday = service.make_standup(dt.date(2025, 10, 15), transcript(WEEK[2]))
    assert prompt.build_request(wednesday, service.current_items(state), team).instructions == text


def test_input_holds_the_date_the_list_the_removed_items_and_numbered_turns(team):
    def remove(day, state):
        if day == WEEK[0]:
            review.remove_item(state, "A4")

    state = run_week(team, WEEK[:2], after_draft=remove)
    text = prompt.input_text(service.make_standup(dt.date(2025, 10, 15), transcript(WEEK[2])), service.current_items(state))
    listed, removed = text.split("Removed by the lead")
    assert text.startswith("Standup date: 2025-10-15 (Wednesday)")
    assert 'A5 | Export feature | owner: Priya | status: in_progress | due: 2025-10-20 (said as "Monday")' in listed
    assert "A4 |" not in listed and "A4 | Flaky test in CI" in removed
    assert "[1] Arjun: Morning." in text and "[9] Arjun: Good. That's it." in text
    assert "review" not in listed.split("A5 |")[1].split("\n")[0]  # no history, no review reasons


def test_lookup_key_survives_pasting_and_rewrapping(team):
    text = transcript(WEEK[0])
    date = dt.date(2025, 10, 13)
    key = prompt.lookup_key(service.make_standup(date, text))
    pasted = text.replace("\n", "\r\n") + "\r\n\r\n"
    wrapped = text.replace(". Search latency", ".\nSearch latency").replace(" I thought", "   I thought")
    assert key == prompt.lookup_key(service.make_standup(date, pasted)) == prompt.lookup_key(service.make_standup(date, wrapped))
    assert key.startswith("2025-10-13-") and key != prompt.lookup_key(service.make_standup(date, text + "\nSana: One more thing."))


# --- submitting a standup


def test_submit_builds_a_draft_and_records_the_run(team):
    state, client = State(), Answers()
    draft = submit(state, team, WEEK[0], client)
    assert len(draft.items_after) == 6 and state.draft is draft
    assert (draft.model_run.provider, draft.model_run.model, len(draft.model_run.attempts)) == ("api", "stand-in", 1)
    assert draft.model_run.fingerprint and "Today's standup:" in client.requests[0].input


def test_the_model_is_shown_the_approved_list_never_the_draft(team):
    state, client = State(), Answers()
    submit(state, team, WEEK[0], client)
    submit(state, team, WEEK[0], client, confirm_rerun=True)
    assert "(empty)" in client.requests[1].input and "A1 |" not in client.requests[1].input


def test_requests_refused_before_the_model_is_called(team):
    state, client = State(), Answers()
    for text in ("", "   \n", "pasted notes with no speaker lines"):
        with pytest.raises(service.SubmitError):
            service.submit_standup(state, dt.date(2025, 10, 13), text, team, client)
    submit(state, team, WEEK[0], client)
    with pytest.raises(service.SubmitError):
        submit(state, team, WEEK[1], client)  # Monday still waits for approval
    assert len(client.requests) == 1


@pytest.mark.parametrize("failure", [LLMFatal("bad key"), LLMUnavailable("no saved answer"), "this is not json"])
def test_a_failed_run_makes_no_draft_and_keeps_an_existing_one(team, failure):
    state = State()
    with pytest.raises(service.SubmitFailed):
        submit(state, team, WEEK[0], Answers(failure))
    assert state.draft is None and state.last_failed_run["date"] == WEEK[0]

    first = submit(state, team, WEEK[0], Answers())
    assert state.last_failed_run is None
    review.edit_item(state, "A2", team, owner="Priya")
    with pytest.raises(service.SubmitFailed):
        submit(state, team, WEEK[0], Answers(failure), confirm_rerun=True)
    assert state.draft is first and by_id(state.draft.items_after)["A2"].owner == "Priya"
    if isinstance(failure, str):
        assert state.last_failed_run["attempts"] == [failure, failure]


def test_the_week_through_submit_matches_the_week_through_the_engine(team):
    state, client = State(), Answers()
    for day in WEEK:
        submit(state, team, day, client)
        review.approve(state)
    direct = run_week(team)
    strip = lambda item: item.model_dump(mode="json")
    assert [strip(i) for i in state.days[-1].items_after] == [strip(i) for i in direct.days[-1].items_after]


def test_token_counts_reported_by_the_provider_are_kept_with_the_run(team):
    class Counted(Answers):
        def complete(self, request):
            response = super().complete(request)
            response.usage = {"prompt_tokens": 3100, "completion_tokens": 900}
            return response

    draft = submit(State(), team, WEEK[0], Counted())
    assert draft.model_run.usage == {"prompt_tokens": 3100, "completion_tokens": 900}
