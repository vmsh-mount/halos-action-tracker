"""What the lead does to a draft: edit, remove, approve, discard. No files."""

from __future__ import annotations

import datetime as dt
from typing import Any

from . import vocab
from .items import set_fields
from .models import DayRecord, Item, State, Team

UNSET: Any = object()


class ReviewError(ValueError):
    pass


def _draft(state: State) -> DayRecord:
    if state.draft is None:
        raise ReviewError("There is no draft to review.")
    return state.draft


def _item(draft: DayRecord, item_id: str) -> Item:
    item = next((i for i in draft.items_after if i.id == item_id), None)
    if item is None:
        raise ReviewError(f"No item {item_id} in this draft.")
    if item.removed_on:
        raise ReviewError(f"{item_id} was removed.")
    return item


def edit_item(
    state: State, item_id: str, team: Team, *, owner: Any = UNSET, due: Any = UNSET, status: Any = UNSET
) -> None:
    draft = _draft(state)
    item = _item(draft, item_id)
    changes: dict[str, Any] = {}
    if owner is not UNSET:
        name = (owner or "").strip()
        changes["owner"] = team.canonical_names().get(name.lower(), name) or None
    if status is not UNSET:
        if status not in vocab.STATUS_KEYS:
            raise ReviewError(f"{status!r} is not a status.")
        changes["status"] = status
    if due is not UNSET:
        if due is not None and not isinstance(due, dt.date):
            raise ReviewError("The date must be a calendar date.")
        if due != item.due:
            changes["due"] = due
            changes["due_phrase"] = None  # a date the lead typed has no phrase behind it
    changed = set_fields(item, changes, on=draft.standup.date, by="lead", action="edit", merge=True)
    if changed:
        _resolve(item, draft)


def _resolve(item: Item, draft: DayRecord) -> None:
    """The lead has dealt with this item, so it no longer needs their attention."""
    if item.review_reasons:
        set_fields(item, {"review_reasons": []}, on=draft.standup.date, by="lead", action="reviewed")


def mark_reviewed(state: State, item_id: str) -> None:
    """The lead looked at a flagged item and is keeping it as proposed."""
    draft = _draft(state)
    _resolve(_item(draft, item_id), draft)


def remove_item(state: State, item_id: str) -> None:
    draft = _draft(state)
    item = _item(draft, item_id)
    on = draft.standup.date
    set_fields(item, {"removed_on": on}, on=on, by="lead", action="remove")
    for child in draft.items_after:
        if child.parent == item.id:
            set_fields(child, {"parent": None}, on=on, by="lead", action="remove")


def approve(state: State, *, now: dt.datetime | None = None) -> DayRecord:
    draft = _draft(state)
    on = draft.standup.date
    for item in draft.items_after:
        if item.review_reasons:
            set_fields(item, {"review_reasons": []}, on=on, by="lead", action="approve")
    draft.state = "approved"
    draft.approved_at = now or dt.datetime.now()
    numbers = [int(i.id[1:]) for i in draft.items_after if i.id[1:].isdigit()]
    state.next_item_number = max([state.next_item_number, *(n + 1 for n in numbers)])
    state.days.append(draft)
    state.draft = None
    return draft


def discard(state: State) -> None:
    _draft(state)
    state.draft = None
