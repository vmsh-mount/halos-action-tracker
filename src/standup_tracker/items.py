"""The one place a field on an item changes. Both the model's changes and the lead's edits come through here."""

from __future__ import annotations

import datetime as dt
from typing import Any

from . import vocab
from .models import Diff, Flag, HistoryEntry, Item, Quote

# Order matters only for stable output.
TRACKED_FIELDS = (
    "title", "owner", "due", "due_phrase", "status", "ticket", "parent", "note", "review_reasons", "removed_on",
)
_DEFAULTS: dict[str, Any] = {name: None for name in TRACKED_FIELDS} | {"title": "", "status": "", "review_reasons": []}


def jsonable(value: Any) -> Any:
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, list):
        return list(value)
    return value


def set_fields(
    item: Item,
    changes: dict[str, Any],
    *,
    on: dt.date,
    by: str,
    action: str | None = None,
    quotes: list[Quote] | None = None,
    flags: list[Flag] | None = None,
    merge: bool = False,
) -> list[Diff]:
    """Apply the changes, record them in the item's history, and return what actually changed.

    merge=True is for the lead's edits: a second edit to the same field on the same day updates the first
    entry, so its "from" stays the value the system proposed.
    """
    changes = dict(changes)
    if "status" in changes and vocab.is_closed(item.status) and not vocab.is_closed(changes["status"]):
        # Reopening: the old date does not come back with the item unless this change sets one. It has to be
        # a real reopen of an item closed on an earlier day, not the undoing of a close made today, whether
        # the model or the lead made it. The baseline is the status before the lead's own first status edit
        # in this review if there is one, and otherwise the status when the day began.
        earlier = _earlier_lead_diff(item, on, action, "status") if merge else None
        was = earlier.before if earlier else status_at_start_of(item, on)
        if vocab.is_closed(was) and changes.get("due") is None:
            changes["due"] = None
            changes.setdefault("due_phrase", None)

    diffs: list[Diff] = []
    for name in TRACKED_FIELDS:
        if name not in changes:
            continue
        old, new = getattr(item, name), changes[name]
        if jsonable(old) != jsonable(new):
            setattr(item, name, list(new) if isinstance(new, list) else new)
            diffs.append(Diff(field=name, before=jsonable(old), after=jsonable(new)))
    if not diffs:
        return []

    fresh = diffs
    if merge:
        fresh = []
        for diff in diffs:
            earlier = _earlier_lead_diff(item, on, action, diff.field)
            if earlier is None:
                fresh.append(diff)
            else:
                earlier.after = diff.after
        for entry in item.history:
            if entry.date == on and entry.by == "lead" and entry.action == action:
                entry.diffs = [d for d in entry.diffs if d.before != d.after]
        item.history = [e for e in item.history if e.diffs or e.by != "lead" or e.action != action]
    if fresh:
        item.history.append(
            HistoryEntry(date=on, by=by, action=action, diffs=fresh, quotes=quotes or [], flags=flags or [])
        )
    return diffs


def status_at_start_of(item: Item, day: dt.date) -> str:
    """The item's status before anything changed it on this day."""
    for entry in item.history:
        if entry.date == day:
            for diff in entry.diffs:
                if diff.field == "status":
                    return diff.before
    return item.status


def _earlier_lead_diff(item: Item, on: dt.date, action: str | None, name: str) -> Diff | None:
    for entry in item.history:
        if entry.date == on and entry.by == "lead" and entry.action == action:
            for diff in entry.diffs:
                if diff.field == name:
                    return diff
    return None


def replay(item: Item) -> dict[str, Any]:
    """The item's fields as its history says they should be."""
    state = {name: jsonable(value) for name, value in _DEFAULTS.items()}
    for entry in item.history:
        for diff in entry.diffs:
            state[diff.field] = diff.after
    return state


def current(item: Item) -> dict[str, Any]:
    return {name: jsonable(getattr(item, name)) for name in TRACKED_FIELDS}


def labels_for(diffs: list[Diff], *, added: bool = False) -> list[str]:
    """What a change did, worked out from its diffs."""
    if added:
        return ["added"]
    labels: list[str] = []
    by_field = {d.field: d for d in diffs}

    status = by_field.get("status")
    reopened = False
    if status:
        was_closed, now_closed = vocab.is_closed(status.before), vocab.is_closed(status.after)
        if was_closed and not now_closed:
            labels.append("reopened")
            reopened = True
        elif status.after == "done":
            labels.append("closed")
        elif status.after == "dropped":
            labels.append("dropped")
        elif status.after == "blocked":
            labels.append("blocked")
        elif status.before == "blocked":
            labels.append("unblocked")
        else:
            labels.append("updated")

    owner = by_field.get("owner")
    if owner:
        labels.append("picked up" if owner.before is None else "unassigned" if owner.after is None else "reassigned")

    due = by_field.get("due")
    if due:
        if due.before is None:
            labels.append("dated")
        elif due.after is None:
            if not reopened:
                labels.append("date cleared")
        else:
            labels.append("re-dated")

    if "removed_on" in by_field:
        labels.append("removed")
    other = {"title", "note", "ticket", "parent"} | ({"due_phrase"} if not due else set())
    if other & by_field.keys():
        labels.append("updated")
    return list(dict.fromkeys(labels))
