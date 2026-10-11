"""The change tier: what is refused, moved, corrected, flagged or discarded (implementation-details 3.3)."""

import datetime as dt

from conftest import by_id, submit
from standup_tracker import review
from standup_tracker.models import State

DAY1, DAY2 = "2025-10-13", "2025-10-14"
TEXT1 = """Ana: I'll take the login bug, PAY-231. Should be done tomorrow.
Ben: The export feature is mine, due Friday.
Ana: Sure."""
TEXT2 = """Ana: The login bug is fixed and deployed, 231 is closed.
Ben: I'll review Ana's fix for PAY-231 after lunch.
Ana: Meera will take the dashboard cleanup.
Ben: Export is still Friday."""

ADD_LOGIN = {"kind": "add", "ref": "n1", "fields": {"title": "Login bug", "owner": "Ana", "ticket": "PAY-231", "due_phrase": "tomorrow"},
             "quotes": ["I'll take the login bug, PAY-231."]}
ADD_LOGIN["quotes"].append("Should be done tomorrow.")
ADD_EXPORT = {"kind": "add", "ref": "n2", "fields": {"title": "Export", "owner": "Ben", "due_phrase": "Friday"},
              "quotes": ["The export feature is mine, due Friday."]}


def day1(team, *more):
    state = State()
    draft = submit(state, team, DAY1, {"changes": [ADD_LOGIN, ADD_EXPORT, *more]}, text=TEXT1)
    return state, draft


def outcomes(draft):
    return [(c.outcome, c.failure.rule if c.failure else None) for c in draft.checked_changes]


def day2(team, *changes, not_tracked=None, before_approve=None):
    state, _ = day1(team)
    if before_approve:
        before_approve(state)
    review.approve(state)
    return state, submit(state, team, DAY2, {"changes": list(changes), "not_tracked": not_tracked or []}, text=TEXT2)


def test_adds_are_applied_and_dated(team):
    _, draft = day1(team)
    items = by_id(draft.items_after)
    assert outcomes(draft) == [("applied", None), ("applied", None)]
    assert (items["A1"].due, items["A2"].due) == (dt.date(2025, 10, 14), dt.date(2025, 10, 17))


def test_refused_changes(team):
    bad = [
        {"kind": "add", "fields": {"title": "Invented"}, "quotes": ["We must rewrite the billing engine."]},
        {"kind": "add", "fields": {"title": "Too short"}, "quotes": ["Sure."]},
        {"kind": "add", "fields": {"title": "No quotes"}, "quotes": []},
        {"kind": "add", "fields": {"title": "Stitched"}, "quotes": ["Should be done tomorrow. The export feature is mine"]},
        {"kind": "update", "item_id": "A99", "fields": {"note": "x"}, "quotes": ["The export feature is mine, due Friday."]},
        {"kind": "rename", "fields": {"title": "x"}, "quotes": ["The export feature is mine, due Friday."]},
        {"kind": "add", "fields": {}, "quotes": ["The export feature is mine, due Friday."]},
        {"kind": "update", "fields": {"note": "x"}, "quotes": ["The export feature is mine, due Friday."]},
    ]
    _, draft = day1(team, *bad)
    assert outcomes(draft)[2:] == [("could_not_verify", r) for r in ("C1", "C1", "C1", "C1", "C2", "shape", "shape", "shape")]
    assert len(draft.items_after) == 2  # a refused add consumes no id


def test_an_unknown_status_costs_the_field_not_the_change(team):
    _, draft = day2(team, {"kind": "update", "item_id": "A1", "fields": {"status": "finished", "note": "Fixed and deployed"},
                           "quotes": ["The login bug is fixed and deployed, 231 is closed."]})
    (change,) = draft.checked_changes
    item = by_id(draft.items_after)["A1"]
    assert change.outcome == "applied" and item.note == "Fixed and deployed" and item.status == "open"
    assert item.review_reasons == ["status 'finished' ignored: not a known status"]


def test_bare_ticket_number_finds_the_ticket_and_does_not_duplicate(team):
    _, draft = day2(team, {"kind": "update", "item_id": "A1", "fields": {"ticket": "231", "status": "done"},
                           "quotes": ["The login bug is fixed and deployed, 231 is closed."]})
    assert by_id(draft.items_after)["A1"].ticket == "PAY-231"
    assert draft.checked_changes[0].change_labels == ["closed"]


def test_add_with_an_existing_ticket_is_flagged_unless_it_is_a_part_of_that_item(team):
    quote = ["I'll review Ana's fix for PAY-231 after lunch."]
    _, draft = day2(team,
                    {"kind": "add", "fields": {"title": "Login bug again", "ticket": "231"}, "quotes": quote},
                    {"kind": "add", "fields": {"title": "Review the fix", "owner": "Ben", "ticket": "PAY-231", "parent": "A1"}, "quotes": quote})
    items = by_id(draft.items_after)
    assert items["A3"].review_reasons == ["possible duplicate of A1"]
    assert items["A4"].review_reasons == [] and items["A4"].parent == "A1"


def test_unknown_owner_is_applied_and_flagged_and_another_name_is_made_canonical(team):
    quote = ["Meera will take the dashboard cleanup."]
    _, draft = day2(team,
                    {"kind": "add", "fields": {"title": "Dashboard cleanup", "owner": "Meera"}, "quotes": quote},
                    {"kind": "add", "fields": {"title": "Other", "owner": "devansh"}, "quotes": quote})
    items = by_id(draft.items_after)
    assert (items["A3"].owner, items["A3"].review_reasons) == ("Meera", ["owner 'Meera' is not a known person"])
    assert (items["A4"].owner, items["A4"].review_reasons) == ("Dev", [])


def test_parent_by_ref_in_either_order_and_bad_parents(team):
    quote = ["Meera will take the dashboard cleanup."]
    _, draft = day2(team,
                    {"kind": "add", "ref": "child", "fields": {"title": "Check the cleanup", "parent": "work"}, "quotes": quote},
                    {"kind": "add", "ref": "work", "fields": {"title": "Dashboard cleanup"}, "quotes": quote},
                    {"kind": "add", "ref": "self", "fields": {"title": "Loop", "parent": "self"}, "quotes": quote},
                    {"kind": "add", "fields": {"title": "Orphan", "parent": "A77"}, "quotes": quote})
    items = by_id(draft.items_after)
    assert items["A3"].parent == "A4"
    assert items["A5"].parent is None and "itself" in items["A5"].review_reasons[0]
    assert items["A6"].parent is None and "A77" in items["A6"].review_reasons[0]


def test_changes_aimed_at_a_removed_item_go_to_not_tracked(team):
    quote = ["The login bug is fixed and deployed, 231 is closed."]
    _, draft = day2(team,
                    {"kind": "update", "item_id": "A1", "fields": {"status": "done"}, "quotes": quote},
                    {"kind": "add", "fields": {"title": "Login bug", "ticket": "PAY-231"}, "quotes": quote},
                    before_approve=lambda state: review.remove_item(state, "A1"))
    assert [c.outcome for c in draft.checked_changes] == ["not_tracked", "not_tracked"]
    assert [(n.reason, n.source) for n in draft.not_tracked] == [("removed by lead", "code")] * 2
    assert len([i for i in draft.items_after if not i.removed_on]) == 1


def test_no_op_update_is_discarded_and_a_note_only_update_is_not(team):
    quote = ["Export is still Friday."]
    _, draft = day2(team,
                    {"kind": "update", "item_id": "A2", "fields": {"due_phrase": "still Friday", "owner": "Ben"}, "quotes": quote},
                    {"kind": "update", "item_id": "A2", "fields": {"note": "On track"}, "quotes": quote})
    assert [(c.outcome, c.change_labels) for c in draft.checked_changes] == [("discarded", []), ("applied", ["updated"])]


def test_date_phrase_outcomes_on_an_item_that_has_a_date(team):
    quote = ["Export is still Friday."]

    def run(phrase):
        state, _ = day1(team)
        review.approve(state)
        change = {"kind": "update", "item_id": "A2", "fields": {"due_phrase": phrase}, "quotes": quote}
        item = by_id(submit(state, team, DAY2, {"changes": [change]}, text=TEXT2).items_after)["A2"]
        return item.due, item.due_phrase, item.review_reasons

    friday = dt.date(2025, 10, 17)
    assert run("Thursday") == (friday, "Friday", ["date phrase not in the quoted words"])  # D1 keeps the date
    assert run("Friday") == (friday, "Friday", [])  # same date: nothing changes
    assert run(None) == (None, None, [])  # explicitly empty clears both, no reason


def test_hedge_and_unpinned_phrase_clear_an_existing_date(team):
    def run(text, quote, phrase):
        state, _ = day1(team)
        review.approve(state)
        change = {"kind": "update", "item_id": "A2", "fields": {"due_phrase": phrase}, "quotes": [quote]}
        item = by_id(submit(state, team, DAY2, {"changes": [change]}, text=text).items_after)["A2"]
        return item.due, item.due_phrase, item.review_reasons

    assert run("Ben: Export is probably Monday now.", "Export is probably Monday now.", "Monday") == (
        None, "Monday", ["hedged: 'probably'"])
    assert run("Ben: Export moves to next week sometime.", "Export moves to next week sometime.", "next week") == (
        None, "next week", ["date no longer pinned: 'next week'"])


def test_two_updates_to_one_item_apply_in_order(team):
    quote = ["The login bug is fixed and deployed, 231 is closed."]
    _, draft = day2(team,
                    {"kind": "update", "item_id": "A1", "fields": {"owner": "Ben"}, "quotes": quote},
                    {"kind": "update", "item_id": "A1", "fields": {"owner": "Ana", "status": "done"}, "quotes": quote})
    item = by_id(draft.items_after)["A1"]
    assert (item.owner, item.status) == ("Ana", "done")
    assert [c.change_labels for c in draft.checked_changes] == [["reassigned"], ["closed", "reassigned"]]


def test_not_tracked_quote_is_checked_but_kept(team):
    _, draft = day2(team, not_tracked=[{"quote": "Export is still Friday.", "reason": "no change"},
                                       {"quote": "Never said this", "reason": "small talk"}])
    assert [n.quote_found for n in draft.not_tracked] == [True, False]


def test_a_quote_may_support_more_than_one_change(team):
    quote = ["The login bug is fixed and deployed, 231 is closed."]
    _, draft = day2(team,
                    {"kind": "update", "item_id": "A1", "fields": {"status": "done"}, "quotes": quote},
                    {"kind": "update", "item_id": "A2", "fields": {"note": "Unblocked by the login fix"}, "quotes": quote})
    assert [c.outcome for c in draft.checked_changes] == ["applied", "applied"]


def test_more_than_three_quotes_are_all_checked_and_an_empty_title_is_ignored(team):
    four = ["Ana: nothing", "Export is still Friday."]
    real = ["Export is still Friday.", "Meera will take the dashboard cleanup.", "The login bug is fixed and deployed, 231 is closed.",
            "I'll review Ana's fix for PAY-231 after lunch."]
    _, draft = day2(team,
                    {"kind": "update", "item_id": "A2", "fields": {"title": "", "note": "On track"}, "quotes": real},
                    {"kind": "update", "item_id": "A2", "fields": {"note": "x"}, "quotes": four})
    first, second = draft.checked_changes
    item = by_id(draft.items_after)["A2"]
    assert first.outcome == "applied" and len(first.quotes) == 4
    assert (item.title, item.note, item.review_reasons) == ("Export", "On track", ["empty title ignored"])
    assert (second.outcome, second.failure.rule) == ("could_not_verify", "C1")


def test_fields_that_are_not_text_are_ignored_and_marked_never_stored_as_junk(team):
    quote = ["Meera will take the dashboard cleanup."]
    _, draft = day2(team,
                    {"kind": "add", "fields": {"title": "Cleanup", "owner": ["Ana", "Ben"], "note": {"a": 1}}, "quotes": quote},
                    {"kind": "add", "fields": {"title": "Other", "owner": ["Ben"], "ticket": 231}, "quotes": quote})
    items = by_id(draft.items_after)
    assert (items["A3"].owner, items["A3"].note) == (None, None)
    assert items["A3"].review_reasons == ["more than one owner named: Ana, Ben", "note ignored: not text"]
    assert (items["A4"].owner, items["A4"].ticket) == ("Ben", "PAY-231")


def test_malformed_shapes_are_refused_not_crashed_on(team):
    state, _ = day1(team)
    review.approve(state)
    answer = {"changes": ["just text", 7, None, ["a"]], "not_tracked": "nothing"}
    draft = submit(state, team, DAY2, answer, text=TEXT2)
    assert outcomes(draft) == [("could_not_verify", "shape")] * 4
    assert draft.not_tracked == []


def test_a_quote_cannot_start_or_end_inside_a_word(team):
    _, draft = day2(team,
                    {"kind": "add", "fields": {"title": "Sliced"}, "quotes": ["he login bug is fixed and deploye"]},
                    {"kind": "add", "fields": {"title": "Whole"}, "quotes": ["the login bug is fixed and deployed"]})
    assert outcomes(draft) == [("could_not_verify", "C1"), ("applied", None)]
