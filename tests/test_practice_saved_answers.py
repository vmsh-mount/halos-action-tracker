"""The five practice days replayed from saved model answers (evaluation-checks sections 2, 5 and 6).

The answers under tests/saved_answers were recorded once from a live model and are not edited. Two classes of
check, kept apart:

- Hard: the pipeline and the always-true properties. These do not depend on the model being right.
- Model quality: what a correct run should produce. Where the one recorded run misses, the test is marked
  xfail with the reason, so the suite stays green and the miss stays visible. strict=True means a re-recorded
  answer that fixes a miss will fail the mark and be noticed.
"""

import datetime as dt
import json
import os

import pytest

from conftest import ROOT, WEEK, by_id, transcript
from practice_week import CORE, FIRM, NOT_TRACKED, _overlaps, home, homes, only
from standup_tracker import items as items_mod
from standup_tracker import review, service
from standup_tracker.llm.replay import DIFFERENT_REQUEST, ReplayClient
from standup_tracker.models import DayRecord, State
from standup_tracker.transcript import find_quote, locate

SAVED = ROOT / "tests" / "saved_answers"
pytestmark = pytest.mark.skipif(len(list(SAVED.glob("*.json"))) < 5, reason="no saved answers recorded yet")

# tests/live_check.py points this at one saved live run, to put the same properties to it. The misses marked
# below belong to the one recording, so in that mode the marks are off and every property simply passes or fails.
LIVE_RUN = os.environ.get("PRACTICE_RUN_FILE")
replay_only = pytest.mark.skipif(bool(LIVE_RUN), reason="about the saved answers, not a live run")


def missed_by_the_recording(reason):
    return pytest.mark.xfail(condition=not LIVE_RUN, strict=True, reason=reason)


def d(day):
    return dt.date(2025, 10, day)


@pytest.fixture(scope="module")
def run(team):
    """Replays the week, approving each day with no edits. Keeps each draft as it stood before approval."""
    if LIVE_RUN:
        saved = json.loads(open(LIVE_RUN, encoding="utf-8").read())
        return State.model_validate(saved["state"]), [DayRecord.model_validate(d) for d in saved["drafts"]]
    state, drafts, client = State(), [], ReplayClient(SAVED)
    for day in WEEK:
        draft = service.submit_standup(state, dt.date.fromisoformat(day), transcript(day), team, client)
        drafts.append(draft.model_copy(deep=True))
        review.approve(state)
    return state, drafts


def after(run, index):
    return homes(run[0].days[index].items_after)


def changes(run):
    return [(day, change) for day in run[0].days for change in day.checked_changes]


# ---------------------------------------------------------------- hard: pipeline and always-true properties


@replay_only
def test_every_day_replays_into_an_approved_day(run):
    state, _ = run
    assert [day.state for day in state.days] == ["approved"] * 5 and state.draft is None
    assert all(day.model_run.provider == "replay" for day in state.days)


@replay_only
def test_saved_answers_match_the_current_prompt_and_list(run):
    stale = [str(day.standup.date) for day in run[0].days if DIFFERENT_REQUEST in day.model_run.notes]
    assert stale == [], f"saved answers recorded against a different prompt or list: {stale}. Record them again."


def test_every_quote_on_an_applied_change_sits_inside_one_turn(run):
    for day, change in changes(run):
        if change.outcome == "applied":
            assert change.quotes and all(find_quote(day.standup.turns, q.text) for q in change.quotes)


def test_every_date_the_model_set_has_a_phrase_inside_its_quotes(run):
    for day, change in changes(run):
        dated = [diff for diff in change.diffs if diff.field == "due" and diff.after]
        if dated:
            phrase = change.proposed.fields["due_phrase"]
            assert any(locate(q.text, phrase) >= 0 for q in change.quotes), (day.standup.date, change.item_id)


def test_in_each_draft_an_owner_is_a_known_person_or_the_item_is_marked(run, team):
    known = {name.lower() for name in team.canonical_names().values()}
    for draft in run[1]:
        known |= {t.speaker.lower() for t in draft.standup.turns if t.speaker}
        for item in draft.items_after:
            assert item.owner is None or item.owner.lower() in known or item.review_reasons


def test_history_replays_to_the_fields_and_ids_never_disappear(run):
    seen: set[str] = set()
    for day in run[0].days:
        ids = [item.id for item in day.items_after]
        assert len(ids) == len(set(ids)) and seen <= set(ids)
        seen = set(ids)
        for item in day.items_after:
            assert items_mod.replay(item) == items_mod.current(item)


def test_an_item_is_closed_only_by_a_change_that_has_a_quote(run):
    for _, change in changes(run):
        if {"closed", "dropped"} & set(change.change_labels):
            assert change.quotes


def test_h1_number_of_changes_refused_for_an_unfound_quote(run, record_property):
    refused = [(str(day.standup.date), c.failure.reason) for day, c in changes(run) if c.failure and c.failure.rule == "C1"]
    record_property("c1_refusals", len(refused))
    assert refused == []  # zero is what supports "this recorded run invented nothing"


# ---------------------------------------------------------------- model quality: H2, the duplicate check


@pytest.mark.parametrize("index", range(5), ids=WEEK)
def test_h2_no_piece_of_work_has_two_items(run, index):
    doubled = {work: [i.id for i in found] for work, found in after(run, index).items() if len(found) > 1}
    assert doubled == {}


def test_h2_the_auth_bug_is_one_item_under_every_name_and_carries_the_ticket(run):
    auth = only(after(run, 4)["W2 auth bug"])
    assert auth.ticket == "PAY-231"
    assert {entry.date for entry in auth.history if entry.by == "model"} == {d(13), d(14), d(15), d(16), d(17)}


# ---------------------------------------------------------------- H3, owners


def test_h3_the_auth_bug_is_owned_by_the_one_who_took_it(run):
    assert only(after(run, 0)["W2 auth bug"]).owner == "Dev"


def test_h3_the_onboarding_doc_has_no_owner_until_it_is_picked_up(run):
    assert [only(after(run, i)["W6 onboarding doc"]).owner for i in range(5)] == [None, None, None, "Rohan", "Rohan"]


def test_h3_the_undecided_item_has_no_owner_and_is_marked_in_the_draft(run):
    flaky = only(homes(run[1][0].items_after)["W4 flaky CI test"])
    assert flaky.owner is None and flaky.review_reasons


# ---------------------------------------------------------------- H4, nothing skipped

FIRST_DAY = {"W1": 0, "W2": 0, "W3": 0, "W4": 0, "W5": 0, "W6": 0, "W7": 1, "W10": 2, "W11": 3, "W12": 4}
MISSED_BY_THE_RECORDING = {
    "W12 retro": "the recorded run skipped the retro proposed on Friday ('We should do a retro on that one next week')",
}


@pytest.mark.parametrize("work", FIRM)
def test_h4_each_firm_piece_of_work_has_an_item_from_the_day_it_comes_up(run, work, request):
    if work in MISSED_BY_THE_RECORDING:
        request.applymarker(missed_by_the_recording(MISSED_BY_THE_RECORDING[work]))
    first = FIRST_DAY[work.split()[0]]
    assert all(len(after(run, index)[work]) == 1 for index in range(first, 5))


# ---------------------------------------------------------------- H5, nothing made up


def test_h5_no_item_belongs_to_no_piece_of_work(run):
    final = [item for item in run[0].days[4].items_after if not item.removed_on]
    homeless = [(item.id, item.title) for item in final if home(item) is None]
    assert homeless == []


def test_h5_no_item_rests_only_on_a_not_tracked_turn(run):
    for item in run[0].days[4].items_after:
        quotes = [(entry.date, quote) for entry in item.history for quote in entry.quotes]
        outside = [q for day, q in quotes if not any(_overlaps(anchor, day, q) for anchor in NOT_TRACKED)]
        assert outside, (item.id, item.title)


def test_item_count_is_within_the_spread_the_soft_rules_allow(run):
    assert 10 <= len(run[0].days[4].items_after) <= 14


# ---------------------------------------------------------------- H6, dates


def test_h6_the_export_date_through_the_week(run):
    assert [only(after(run, i)["W5 export"]).due for i in range(5)] == [d(20), d(20), d(20), d(22), d(22)]


def test_h6_the_hedged_search_fix_has_no_date_on_monday_or_tuesday_and_is_marked(run):
    for index in (0, 1):
        search = only(homes(run[1][index].items_after)["W1 search fix"])
        assert search.due is None and any(reason.startswith("hedged") for reason in search.review_reasons)


@missed_by_the_recording("on Wednesday the recorded run put the reviewer's 'today' on the search fix; "
                         "that day belongs to the review of the PR, not to the fix")
def test_h6_the_search_fix_never_gets_a_date(run):
    assert [only(after(run, i)["W1 search fix"]).due for i in range(5)] == [None] * 5


def test_h6_the_retry_bug_date_rolls_with_the_group_statement(run):
    assert [only(after(run, i)["W11 retry bug"]).due for i in (3, 4)] == [d(17), d(20)]


def test_h6_small_promises_get_their_day(run):
    assert only(after(run, 1)["W2 auth bug"]).due == d(14)
    assert only(after(run, 2)["W10 doc to send"]).due == d(15)


@missed_by_the_recording("on Tuesday the recorded run took infra's estimate ('the cert will be done "
                         "tomorrow morning') as the deploy's due date; code cannot catch this")
def test_h6_another_teams_estimate_is_not_our_due_date(run):
    deploy = only(after(run, 1)["W3 staging deploy"])
    assert deploy.status == "blocked" and deploy.due is None


# ---------------------------------------------------------------- status through the week


def test_statuses_through_the_week(run):
    closed = lambda index, work: only(after(run, index)[work]).status == "done"
    assert only(after(run, 0)["W3 staging deploy"]).status == "blocked"
    assert not closed(1, "W2 auth bug") and closed(2, "W2 auth bug") and not closed(3, "W2 auth bug") and closed(4, "W2 auth bug")
    assert closed(2, "W3 staging deploy") and closed(4, "W3 staging deploy") and closed(2, "W7 login slow")
    assert not closed(2, "W1 search fix")  # in review is not done
    assert not closed(4, "W10 doc to send") and not closed(4, "W6 onboarding doc")  # silence, and a draft, close nothing


def test_reopening_cleared_the_date_and_kept_the_item(run):
    assert only(after(run, 3)["W2 auth bug"]).due is None
    assert only(after(run, 3)["W2 auth bug"]).id == only(after(run, 0)["W2 auth bug"]).id


def test_the_other_item_on_the_same_system_was_not_reopened(run):
    assert only(after(run, 4)["W3 staging deploy"]).status == "done"
    assert only(after(run, 3)["W11 retry bug"]).ticket == "APP-402"


def test_a_speaker_outside_the_team_settings_is_listed_once(run):
    assert [draft.new_speakers for draft in run[1]] == [[], [], [], ["Rohan"], []]


# ---------------------------------------------------------------- H7, the lead's review carries forward (hard)


def replay_week_with(team, on_monday):
    state, client = State(), ReplayClient(SAVED)
    for index, day in enumerate(WEEK):
        service.submit_standup(state, dt.date.fromisoformat(day), transcript(day), team, client)
        if index == 0:
            on_monday(state)
        review.approve(state)
    return state


@replay_only
def test_h7_a_corrected_owner_survives_the_days_that_come_back_to_the_item(team):
    def correct(state):
        review.edit_item(state, only(homes(state.draft.items_after)["W2 auth bug"]).id, team, owner="Sana")

    state = replay_week_with(team, correct)
    tuesday = only(homes(state.days[1].items_after)["W2 auth bug"])
    assert (tuesday.owner, tuesday.ticket, tuesday.due) == ("Sana", "PAY-231", d(14))  # Tuesday's update still landed
    assert only(homes(state.days[4].items_after)["W2 auth bug"]).owner == "Sana"
    assert DIFFERENT_REQUEST in state.days[1].model_run.notes  # the saved answer was recorded against another list


@replay_only
def test_h7_a_removed_item_stays_out_when_later_standups_return_to_it(team):
    removed_id = []

    def remove(state):
        removed_id.append(only(homes(state.draft.items_after)["W6 onboarding doc"]).id)
        review.remove_item(state, removed_id[0])

    state = replay_week_with(team, remove)
    for index in (3, 4):  # Thursday and Friday both come back to it
        day = state.days[index]
        assert [c.outcome for c in day.checked_changes if c.item_id == removed_id[0]] == ["not_tracked"]
        assert "removed by lead" in [n.reason for n in day.not_tracked]
    final = by_id(state.days[4].items_after)[removed_id[0]]
    assert final.removed_on == d(13) and final.owner is None and homes(state.days[4].items_after)["W6 onboarding doc"] == []
