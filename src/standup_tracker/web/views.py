"""Turns stored records into what the page shows. Reads only; changes nothing."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field

from .. import vocab
from ..items import labels_for
from ..models import DayRecord, Diff, Item, Quote

_DATED_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})")


def date_in_name(filename: str) -> str:
    """The date in a file name like 2025-10-13.txt, or an empty string."""
    found = _DATED_NAME.search(filename or "")
    return found.group(1) if found else ""


FIELD_NAMES = {
    "title": "Title", "owner": "Owner", "due": "Due", "due_phrase": "Said as", "status": "Status",
    "ticket": "Ticket", "parent": "Part of", "note": "Note", "removed_on": "Removed",
}
STATUS_LABELS = {status.key: status.label for status in vocab.STATUSES}


def show_value(name: str, value) -> str:
    if value in (None, "", []):
        return "none"
    if name == "status":
        return STATUS_LABELS.get(value, str(value))
    if name in ("due", "removed_on"):
        return show_date(value)
    return str(value)


def show_date(value) -> str:
    if not value:
        return "none"
    day = dt.date.fromisoformat(value) if isinstance(value, str) else value
    return f"{day.strftime('%a')} {day.day} {day.strftime('%b')}"


@dataclass
class Step:
    name: str
    before: str
    after: str


@dataclass
class Row:
    item: Item
    labels: list[str] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    quotes: list[Quote] = field(default_factory=list)
    lead_steps: list[Step] = field(default_factory=list)
    overdue: bool = False
    changed: bool = False
    support: list[Quote] = field(default_factory=list)  # the words the item rests on
    support_date: dt.date | None = None


_STEP_ORDER = ["status", "owner", "due", "due_phrase", "title", "ticket", "parent", "note", "removed_on"]


def _steps(diffs: list[Diff]) -> list[Step]:
    """What changed, most important first. The phrase is left out when the date itself is shown changing."""
    fields = {d.field for d in diffs}
    shown = [d for d in diffs if d.field in FIELD_NAMES and not (d.field == "due_phrase" and "due" in fields)]
    shown.sort(key=lambda d: _STEP_ORDER.index(d.field))
    return [Step(FIELD_NAMES[d.field], show_value(d.field, d.before), show_value(d.field, d.after)) for d in shown]


def is_overdue(item: Item, shown: dt.date) -> bool:
    return bool(item.due and item.due < shown and not vocab.is_closed(item.status))


def supporting_words(item: Item) -> tuple[list[Quote], dt.date | None]:
    """The quotes from the item's most recent history entry that has any. A lead edit has none and hides nothing."""
    for entry in reversed(item.history):
        if entry.quotes:
            return entry.quotes, entry.date
    return [], None


def _row(item: Item, shown: dt.date | None) -> Row:
    support, said_on = supporting_words(item)
    return Row(item=item, overdue=bool(shown and is_overdue(item, shown)), support=support, support_date=said_on)


def net_diffs(item: Item, day: dt.date) -> list[Diff]:
    """Per field, the value before anything happened on this day and the value now. Unchanged fields are left out."""
    first: dict[str, object] = {}
    last: dict[str, object] = {}
    for entry in item.history:
        if entry.date != day:
            continue
        for diff in entry.diffs:
            first.setdefault(diff.field, diff.before)
            last[diff.field] = diff.after
    return [Diff(field=name, before=first[name], after=last[name]) for name in first if first[name] != last[name]]


def rows_for(day: DayRecord) -> tuple[list[Row], list[Row]]:
    """(changed today, the whole list). One row per item, however many changes touched it."""
    shown = day.standup.date
    rows = {item.id: _row(item, shown) for item in day.items_after}
    for change in day.checked_changes:
        if change.outcome != "applied" or change.item_id not in rows:
            continue
        row = rows[change.item_id]
        row.changed = True
        row.steps += _steps(change.diffs) if "added" not in change.change_labels else []
        row.quotes += [q for q in change.quotes if q.text not in {seen.text for seen in row.quotes}]
    for row in rows.values():
        for entry in row.item.history:
            if entry.by == "lead" and entry.date == shown and entry.action in ("edit", "remove"):
                row.lead_steps += _steps(entry.diffs)
                row.changed = True
        if row.changed:
            # Labels describe where the item ends up today, the model's changes and the lead's taken together.
            # A date the model cleared and the lead then set reads "Rescheduled", not "Date cleared, Scheduled".
            added = row.item.created_on == shown
            row.labels = labels_for(net_diffs(row.item, shown), added=added)
            if added and row.item.removed_on:
                row.labels.append("removed")
    listed = [row for row in rows.values() if not row.item.removed_on]
    changed = [row for row in rows.values() if row.changed]
    changed.sort(key=lambda row: (not row.item.review_reasons, int(row.item.id[1:]) if row.item.id[1:].isdigit() else 0))
    return changed, listed


def rows_for_list(items: list[Item], shown: dt.date | None) -> list[Row]:
    return [_row(i, shown) for i in items if not i.removed_on]


def known_people(day: DayRecord | None, items: list[Item], team) -> list[str]:
    names = [person.name for person in team.people]
    names += [t.speaker for t in (day.standup.turns if day else []) if t.speaker]
    names += [i.owner for i in items if i.owner]
    return list(dict.fromkeys(names))


# ---------------------------------------------------------------------------------------------------------
# Wording. The stored labels, reasons and notes are the engine's; these turn them into what a person reads.

LABEL_TEXT = {
    "added": "New", "updated": "Updated", "closed": "Completed", "dropped": "Dropped", "reopened": "Reopened",
    "blocked": "Blocked", "unblocked": "Unblocked", "picked up": "Picked up", "reassigned": "Reassigned",
    "unassigned": "Unassigned", "dated": "Scheduled", "re-dated": "Rescheduled", "date cleared": "Date cleared",
    "removed": "Removed",
}
FIELD_NAMES.update({"due": "Due date", "due_phrase": "Said as", "parent": "Part of"})

_REASONS = [
    (re.compile(r"^hedged: '(.+)'$"), "The date sounded uncertain (“{0}”), so no due date was set."),
    (re.compile(r"^conditional: '(.+)'$"), "The date depends on something else (“{0}”), so no due date was set."),
    (re.compile(r"^two days named$"), "Two different days were mentioned, so no due date was set."),
    (re.compile(r"^date no longer pinned: '(.+)'$"), "The timing changed to “{0}”, which isn’t a specific day. The due date was cleared."),
    (re.compile(r"^timing mentioned, date unchanged: '(.+)'$"), "Timing came up (“{0}”) but no specific day. The due date was left as it was."),
    (re.compile(r"^date phrase not in the quoted words$"), "A due date was proposed without supporting words, so it was not applied."),
    (re.compile(r"^owner '(.+)' is not a known person$"), "“{0}” isn’t in team settings. Check the owner."),
    (re.compile(r"^possible duplicate of (\S+)$"), "This may duplicate {0}: both mention the same ticket."),
    (re.compile(r"^parent link dropped: (.+)$"), "A link to a parent item was not applied: {0}."),
    (re.compile(r"^more than one owner named: (.+)$"), "More than one owner was named ({0}). Choose one."),
    (re.compile(r"^status (.+) ignored: not a known status$"), "The proposed status {0} isn’t recognised, so the status was left as it was."),
    (re.compile(r"^(\w+) ignored: not text$"), "The proposed {0} could not be read and was skipped."),
    (re.compile(r"^empty title ignored$"), "An empty title was proposed and skipped."),
]


def label_text(label: str) -> str:
    return LABEL_TEXT.get(label, label.capitalize())


def friendly_reason(reason: str) -> str:
    for pattern, text in _REASONS:
        found = pattern.match(reason)
        if found:
            return text.format(*found.groups())
    return reason  # the model's own words


def friendly_note(note: str) -> str:
    found = re.match(r"^Saved answer, recorded (\S+) from (.+)\.$", note)
    if found:
        return f"Replay mode: this result is a saved model response ({found.group(2)}, recorded {show_date(found.group(1))})."
    if note.startswith("This saved answer was recorded against a different list"):
        return "The saved response was recorded against a different list, so some proposed changes may not fit."
    return note


@dataclass
class Overview:
    active: int = 0
    blocked: int = 0
    overdue: int = 0
    unassigned: int = 0
    closed: int = 0


def overview(rows: list[Row]) -> Overview:
    out = Overview()
    for row in rows:
        if vocab.is_closed(row.item.status):
            out.closed += 1
            continue
        out.active += 1
        out.blocked += row.item.status == "blocked"
        out.overdue += row.overdue
        out.unassigned += row.item.owner is None
    return out


def split_changed(changed: list[Row]) -> tuple[list[Row], list[Row], list[Row]]:
    """(needs attention, new, changed). An item appears once, under the first heading that fits.

    Items the lead removed are in none of the three; the page lists them under their own heading.
    """
    kept = [row for row in changed if not row.item.removed_on]
    attention = [row for row in kept if row.item.review_reasons]
    rest = [row for row in kept if row not in attention]
    return attention, [r for r in rest if "added" in r.labels], [r for r in rest if "added" not in r.labels]


def mentions_without_change(day: DayRecord) -> list[tuple[Item, list[Quote]]]:
    """Items that came up and stayed as they were: the model proposed an update that changed nothing."""
    items = {item.id: item for item in day.items_after}
    return [
        (items[change.item_id], change.quotes)
        for change in day.checked_changes
        if change.outcome == "discarded" and change.item_id in items
    ]


def status_group(item: Item) -> str:
    return "closed" if vocab.is_closed(item.status) else "active"
