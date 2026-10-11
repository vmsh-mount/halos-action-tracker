"""One case per row of the status, owner and due tables (implementation-details sections 1.3 to 1.6)."""

import datetime as dt

import pytest

from standup_tracker.items import current, labels_for, replay, set_fields
from standup_tracker.models import Item

DAY = dt.date(2025, 10, 16)
OLD = dt.date(2025, 10, 14)
NEW = dt.date(2025, 10, 22)


def change(before: dict, changes: dict):
    item = Item(id="A1", created_on=DAY, title="Thing", status="open")
    for name, value in before.items():
        setattr(item, name, value)
    diffs = set_fields(item, changes, on=DAY, by="model")
    return item, labels_for(diffs)


# status before, status after, label, whether the date survives
STATUS_ROWS = [
    ("open", "done", "closed", True),
    ("blocked", "done", "closed", True),
    ("in_progress", "dropped", "dropped", True),
    ("done", "dropped", "dropped", True),
    ("dropped", "done", "closed", True),
    ("done", "open", "reopened", False),
    ("done", "blocked", "reopened", False),
    ("dropped", "in_progress", "reopened", False),
    ("open", "in_progress", "updated", True),
    ("in_progress", "open", "updated", True),
    ("open", "blocked", "blocked", True),
    ("in_progress", "blocked", "blocked", True),
    ("blocked", "in_progress", "unblocked", True),
    ("blocked", "open", "unblocked", True),
]


@pytest.mark.parametrize("before,after,label,date_kept", STATUS_ROWS)
def test_status_rows(before, after, label, date_kept):
    item, labels = change({"status": before, "due": OLD, "due_phrase": "today"}, {"status": after})
    assert labels == [label]
    assert (item.due, item.due_phrase) == ((OLD, "today") if date_kept else (None, None))


def test_same_status_is_no_change():
    item, labels = change({"status": "open"}, {"status": "open"})
    assert labels == [] and item.history == []


def test_reopen_that_sets_a_date_keeps_it():
    item, labels = change({"status": "done", "due": OLD}, {"status": "in_progress", "due": NEW, "due_phrase": "Wednesday"})
    assert labels == ["reopened", "re-dated"] and item.due == NEW


@pytest.mark.parametrize("before,after,label", [
    (None, "Bea", "picked up"), ("Ada", "Bea", "reassigned"), ("Ada", None, "unassigned"),
])
def test_owner_rows(before, after, label):
    assert change({"owner": before}, {"owner": after})[1] == [label]


@pytest.mark.parametrize("before,after,label", [(None, NEW, "dated"), (OLD, NEW, "re-dated"), (NEW, OLD, "re-dated"), (OLD, None, "date cleared")])
def test_due_rows(before, after, label):
    assert change({"due": before}, {"due": after, "due_phrase": "x"})[1] == [label]


@pytest.mark.parametrize("name", ["title", "note", "ticket", "parent", "due_phrase"])
def test_other_fields_are_updated(name):
    assert change({}, {name: "something else"})[1] == ["updated"]


def test_review_reasons_alone_carry_no_label_but_are_recorded():
    item, labels = change({}, {"review_reasons": ["look at this"]})
    assert labels == [] and len(item.history) == 1 and replay(item) | {"title": "Thing", "status": "open"} == current(item)
