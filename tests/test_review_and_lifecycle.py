"""Lead actions and the day lifecycle (implementation-details sections 1.1, 4 and 6)."""

import datetime as dt

import pytest

from conftest import WEEK, by_id, key_answer, run_week, submit
from standup_tracker import items as items_mod
from standup_tracker import review, service, store
from standup_tracker.models import State

MON, TUE = WEEK[0], WEEK[1]


@pytest.fixture
def monday(team):
    state = State()
    submit(state, team, MON, key_answer(MON))
    return state


def lead_entries(item):
    return [(e.action, [(d.field, d.before, d.after) for d in e.diffs]) for e in item.history if e.by == "lead"]


def test_edit_owner_date_and_status(monday, team):
    review.edit_item(monday, "A6", team, owner="devansh", due=dt.date(2025, 10, 24), status="in_progress")
    item = by_id(monday.draft.items_after)["A6"]
    assert (item.owner, item.due, item.due_phrase, item.status) == ("Dev", dt.date(2025, 10, 24), None, "in_progress")
    assert items_mod.replay(item) == items_mod.current(item)


def test_editing_the_same_field_twice_keeps_one_entry_with_the_system_value(monday, team):
    review.edit_item(monday, "A2", team, owner="Priya")
    review.edit_item(monday, "A2", team, owner="Sana")
    item = by_id(monday.draft.items_after)["A2"]
    assert lead_entries(item) == [("edit", [("owner", "Dev", "Sana")])]
    review.edit_item(monday, "A2", team, owner="Dev")  # back to what the system had: no correction left
    assert lead_entries(item) == [] and items_mod.replay(item) == items_mod.current(item)


def test_a_typed_owner_outside_the_team_is_accepted_without_a_flag(monday, team):
    review.edit_item(monday, "A4", team, owner="Meera")
    item = by_id(monday.draft.items_after)["A4"]
    assert item.owner == "Meera" and item.review_reasons == ["Raised, deferred, no decision"]


def test_invalid_edits_are_refused(monday, team):
    with pytest.raises(review.ReviewError):
        review.edit_item(monday, "A2", team, status="finished")
    with pytest.raises(review.ReviewError):
        review.edit_item(monday, "A99", team, owner="Priya")
    review.remove_item(monday, "A4")
    with pytest.raises(review.ReviewError):
        review.edit_item(monday, "A4", team, owner="Priya")


def test_no_edit_remove_approve_or_discard_without_a_draft(monday, team):
    review.approve(monday)
    for act in (lambda: review.edit_item(monday, "A2", team, owner="Priya"), lambda: review.remove_item(monday, "A2"),
                lambda: review.approve(monday), lambda: review.discard(monday)):
        with pytest.raises(review.ReviewError):
            act()


def test_lead_reopening_clears_the_date_like_a_model_reopen(team):
    state = run_week(team, WEEK[:3])  # after Wednesday the auth item is done with its date still on it
    assert by_id(state.days[-1].items_after)["A2"].due == dt.date(2025, 10, 14)
    submit(state, team, WEEK[3], {"changes": []})
    review.edit_item(state, "A2", team, status="open")
    item = by_id(state.draft.items_after)["A2"]
    assert (item.status, item.due) == ("open", None)
    assert items_mod.replay(item) == items_mod.current(item)


def test_done_to_dropped_is_not_a_reopen(team):
    state = run_week(team, WEEK[:3])
    submit(state, team, WEEK[3], {"changes": []})
    review.edit_item(state, "A2", team, status="dropped")
    assert by_id(state.draft.items_after)["A2"].due == dt.date(2025, 10, 14)


def test_removing_a_parent_unlinks_its_parts_and_is_recorded(team):
    state = run_week(team, WEEK[:2])
    submit(state, team, WEEK[2], {"changes": []})
    review.remove_item(state, "A2")
    items = by_id(state.draft.items_after)
    assert items["A2"].removed_on == dt.date(2025, 10, 15) and items["A8"].parent is None
    assert lead_entries(items["A8"]) == [("remove", [("parent", "A2", None)])]


def test_a_lead_correction_survives_the_next_day_and_a_removed_item_stays_out(team):
    def edit(day, state):
        if day == MON:
            review.edit_item(state, "A2", team, owner="Priya")
            review.remove_item(state, "A6")

    state = run_week(team, after_draft=edit)
    items = by_id(state.days[-1].items_after)
    assert (items["A2"].owner, items["A2"].ticket, items["A2"].status) == ("Priya", "PAY-231", "done")
    assert items["A6"].removed_on == dt.date(2025, 10, 13) and items["A6"].owner is None
    for index in (3, 4):  # Thursday and Friday both come back to the removed item
        day = state.days[index]
        assert [c.outcome for c in day.checked_changes if c.item_id == "A6"] == ["not_tracked"]
        assert ("removed by lead", "code") in [(n.reason, n.source) for n in day.not_tracked]
    assert items["A14"].parent is None and "removed by the lead" in state.days[4].checked_changes[-1].flags[0].reason


def test_dates_must_increase_and_a_waiting_draft_blocks_other_days(monday, team):
    with pytest.raises(service.SubmitError):
        submit(monday, team, TUE, key_answer(TUE))  # Monday is still waiting
    review.approve(monday)
    with pytest.raises(service.SubmitError):
        submit(monday, team, MON, key_answer(MON))  # not later than the last approved day


def test_rerun_needs_confirmation_replaces_the_draft_and_reissues_the_same_ids(monday, team):
    review.edit_item(monday, "A2", team, owner="Priya")
    with pytest.raises(service.RerunNeedsConfirmation):
        submit(monday, team, MON, key_answer(MON))
    draft = submit(monday, team, MON, key_answer(MON), confirm_rerun=True)
    assert [i.id for i in draft.items_after] == ["A1", "A2", "A3", "A4", "A5", "A6"]
    assert by_id(draft.items_after)["A2"].owner == "Dev" and monday.next_item_number == 1


def test_discard_goes_back_to_the_approved_list(monday, team):
    review.discard(monday)
    assert monday.draft is None and service.current_items(monday) == [] and monday.next_item_number == 1


def test_a_draft_with_no_changes_can_be_approved(monday, team):
    review.approve(monday)
    submit(monday, team, TUE, {"changes": []})
    review.approve(monday)
    assert len(monday.days) == 2 and len(monday.days[1].items_after) == 6


def test_state_round_trips_through_the_file(team, tmp_path):
    state = run_week(team)
    path = tmp_path / "data" / "state.json"
    store.save_state(path, state)
    again = store.load_state(path)
    assert again.model_dump(mode="json") == state.model_dump(mode="json")
    for item in again.days[-1].items_after:
        assert items_mod.replay(item) == items_mod.current(item)
    assert '"from"' in path.read_text()


def test_missing_file_is_an_empty_state_and_another_version_is_refused(tmp_path):
    assert store.load_state(tmp_path / "none.json").days == []
    (tmp_path / "old.json").write_text('{"version": 2}')
    with pytest.raises(store.StoreError):
        store.load_state(tmp_path / "old.json")


def test_closing_by_mistake_and_undoing_it_keeps_the_date(monday, team):
    before = by_id(monday.draft.items_after)["A5"]
    kept = (before.status, before.due, before.due_phrase)
    review.edit_item(monday, "A5", team, status="done")
    review.edit_item(monday, "A5", team, status="in_progress")
    item = by_id(monday.draft.items_after)["A5"]
    assert (item.status, item.due, item.due_phrase) == kept == ("in_progress", dt.date(2025, 10, 20), "Monday")
    assert lead_entries(item) == []


def test_an_edit_with_the_date_unchanged_keeps_the_phrase_and_records_nothing(monday, team):
    item = by_id(monday.draft.items_after)["A5"]
    review.edit_item(monday, "A5", team, owner="Priya", due=item.due, status=item.status)
    assert item.due_phrase == "Monday" and lead_entries(item) == []
    review.edit_item(monday, "A5", team, owner="Sana", due=item.due, status=item.status)
    assert item.due_phrase == "Monday" and lead_entries(item) == [("edit", [("owner", "Priya", "Sana")])]


def test_undo_keeps_a_date_the_lead_set_on_an_item_the_model_reopened(team):
    state = run_week(team, WEEK[:3])
    submit(state, team, WEEK[3], key_answer(WEEK[3]))  # Thursday: the model reopens the auth item, date cleared
    friday = dt.date(2025, 10, 17)
    review.edit_item(state, "A2", team, due=friday)
    review.edit_item(state, "A2", team, status="done")  # by mistake
    review.edit_item(state, "A2", team, status="in_progress")  # undone
    item = by_id(state.draft.items_after)["A2"]
    assert (item.status, item.due) == ("in_progress", friday)
    assert lead_entries(item) == [("edit", [("due", None, "2025-10-17")])]
    assert items_mod.replay(item) == items_mod.current(item)


def test_lead_reopen_of_an_item_closed_earlier_clears_the_date_even_via_another_closed_status(team):
    state = run_week(team, WEEK[:3])
    submit(state, team, WEEK[3], {"changes": []})
    review.edit_item(state, "A2", team, status="dropped")
    review.edit_item(state, "A2", team, status="open")
    assert by_id(state.draft.items_after)["A2"].due is None


def test_the_confirming_line_alone_can_carry_the_new_date(team):
    state = run_week(team, WEEK[:3])
    change = {"kind": "update", "item_id": "A5", "fields": {"due_phrase": "Wednesday"},
              "quotes": ["export is going to slip.", "Wednesday's fine."]}
    item = by_id(submit(state, team, WEEK[3], {"changes": [change]}).items_after)["A5"]
    assert (item.due, item.review_reasons) == (dt.date(2025, 10, 22), [])


def test_the_lead_undoing_a_close_the_model_made_today_keeps_the_date(team):
    state = run_week(team, WEEK[:2])
    submit(state, team, WEEK[2], key_answer(WEEK[2]))  # Wednesday: the model closes the auth item
    review.edit_item(state, "A2", team, status="in_progress")
    auth = by_id(state.draft.items_after)["A2"]
    assert (auth.status, auth.due, auth.due_phrase) == ("in_progress", dt.date(2025, 10, 14), "today")
    review.approve(state)

    submit(state, team, WEEK[3], key_answer(WEEK[3]))  # Thursday: the model closes the search PR review
    review.edit_item(state, "A9", team, status="open")
    assert by_id(state.draft.items_after)["A9"].due == dt.date(2025, 10, 15)
