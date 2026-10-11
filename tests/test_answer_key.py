"""The answer key, written as five days of proposed changes, run through the real code. Protected.

No model is involved. If the model returned exactly these changes, this is the week the code would produce.
The expected list is the table in docs/action-item-rules.md section 7.
"""

import datetime as dt

import pytest

from conftest import WEEK, by_id, key_answer, run_week, submit
from standup_tracker import items as items_mod
from standup_tracker.models import State


def d(day):
    return dt.date(2025, 10, day)


# id: (owner, due, status, parent, ticket)
REFERENCE_WEEK = {
    "A1": ("Arjun", None, "done", None, None),
    "A2": ("Dev", None, "done", None, "PAY-231"),
    "A3": ("Sana", None, "done", None, None),
    "A4": (None, None, "open", None, None),
    "A5": ("Priya", d(22), "in_progress", None, None),
    "A6": ("Rohan", None, "in_progress", None, None),
    "A7": ("Dev", None, "done", None, None),
    "A8": ("Priya", None, "done", "A2", None),
    "A9": ("Dev", d(15), "done", "A1", None),
    "A10": ("Arjun", d(15), "open", None, None),
    "A11": ("Sana", d(20), "open", None, "APP-402"),
    "A12": (None, None, "open", "A2", None),
    "A13": ("Dev", d(17), "open", None, None),
    "A14": ("Priya", None, "open", "A6", None),
}


@pytest.fixture(scope="module")
def week(team):
    return run_week(team)


def test_final_list_equals_the_reference_week(week):
    final = by_id(week.days[-1].items_after)
    got = {i: (x.owner, x.due, x.status, x.parent, x.ticket) for i, x in final.items()}
    assert got == REFERENCE_WEEK


def test_item_count_after_each_day(week):
    assert [len(day.items_after) for day in week.days] == [6, 8, 10, 11, 14]


def test_no_change_in_the_key_is_refused(week):
    refused = [(day.standup.date, c.failure) for day in week.days for c in day.checked_changes if c.failure]
    assert refused == []


def test_history_replays_to_the_current_fields_on_every_day(week):
    for day in week.days:
        for item in day.items_after:
            assert items_mod.replay(item) == items_mod.current(item), (day.standup.date, item.id)


def test_review_reasons_are_cleared_by_approval(week):
    assert all(not item.review_reasons for day in week.days for item in day.items_after)


def test_monday_draft_marks_the_hedged_date_and_the_undecided_item(team):
    state = State()
    draft = submit(state, team, WEEK[0], key_answer(WEEK[0]))
    items = by_id(draft.items_after)
    assert items["A1"].due is None and items["A1"].review_reasons == ["hedged: 'maybe'"]
    assert items["A4"].owner is None and items["A4"].review_reasons == ["Raised, deferred, no decision"]
    assert items["A5"].due == d(20) and not items["A5"].review_reasons
    assert items["A6"].due is None and items["A6"].due_phrase == "at some point" and not items["A6"].review_reasons
    assert [n.quote_found for n in draft.not_tracked] == [True, True]
    assert draft.new_speakers == []


def changes_for(week, day_index, item_id):
    return [c for c in week.days[day_index].checked_changes if c.item_id == item_id]


def test_restating_the_same_date_is_discarded(week):
    assert [c.outcome for c in changes_for(week, 1, "A5")] == ["discarded"]  # "Still Monday"
    assert [c.outcome for c in changes_for(week, 2, "A5")] == ["discarded"]  # "still on for Monday"


def test_tuesday_auth_update_carries_several_labels(week):
    (change,) = changes_for(week, 1, "A2")
    assert change.change_labels == ["updated", "dated"]
    assert by_id(week.days[1].items_after)["A2"].due == d(14)


def test_reopening_clears_the_old_date(week):
    (change,) = changes_for(week, 3, "A2")
    assert change.change_labels == ["reopened", "updated"]
    thursday = by_id(week.days[3].items_after)["A2"]
    assert (thursday.status, thursday.due, thursday.due_phrase) == ("in_progress", None, None)
    assert [c.change_labels for c in changes_for(week, 4, "A2")] == [["closed"]]


def test_labels_through_the_week(week):
    assert changes_for(week, 2, "A3")[0].change_labels == ["closed"]  # blocked straight to done
    assert changes_for(week, 3, "A5")[0].change_labels == ["re-dated"]
    assert changes_for(week, 3, "A6")[0].change_labels == ["picked up"]
    assert changes_for(week, 4, "A11")[0].change_labels == ["re-dated"]


def test_a_speaker_outside_the_team_settings_is_new_on_the_first_day_only(week):
    assert [day.new_speakers for day in week.days] == [[], [], [], ["Rohan"], []]


def test_quotes_carry_the_turn_and_speaker(week):
    (change,) = changes_for(week, 3, "A5")
    assert [(q.turn, q.speaker) for q in change.quotes] == [(6, "Priya"), (6, "Priya"), (7, "Arjun")]


def test_ids_advance_only_on_approval(week):
    assert week.next_item_number == 15
