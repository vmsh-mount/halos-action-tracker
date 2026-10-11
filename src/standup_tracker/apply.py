"""Proposed changes in, checked changes and the new list out. No files, no model."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import vocab
from .dates import resolve_due
from .items import labels_for, set_fields
from .models import CheckedChange, Flag, Item, NotTracked, ProposedChange, Quote, Standup, Team, Turn
from .transcript import find_quote, meets_length_rule

REMOVED_BY_LEAD = "removed by lead"
TEXT_FIELDS = ("title", "owner", "due_phrase", "status", "ticket", "parent", "note")


@dataclass
class ApplyResult:
    checked: list[CheckedChange]
    items: list[Item]
    not_tracked: list[NotTracked]
    new_speakers: list[str]


@dataclass
class _Work:
    change: ProposedChange
    found: list[tuple[str, Turn]] = field(default_factory=list)
    item: Item | None = None
    result: CheckedChange | None = None  # set in pass 1 when the change goes no further


def _empty(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def proposed_from_raw(raw) -> ProposedChange:
    """Anything the model put in the changes list. A thing that is not an object is kept and refused later."""
    if isinstance(raw, dict):
        return ProposedChange.model_validate(raw)
    return ProposedChange(unparsed=raw)


def _shape_problem(change: ProposedChange) -> str | None:
    if change.unparsed is not None:
        return "not an object"
    if change.kind not in ("add", "update"):
        return f"kind is {change.kind!r}"
    if change.fields is not None and not isinstance(change.fields, dict):
        return "fields is not an object"
    if not isinstance(change.quotes, list) or not all(isinstance(q, str) for q in change.quotes):
        return "quotes is not a list of text"
    fields = change.fields or {}
    if change.kind == "update" and (not isinstance(change.item_id, str) or not change.item_id.strip()):
        return "update with no item_id"
    if change.kind == "add" and (not isinstance(fields.get("title"), str) or not fields["title"].strip()):
        return "add with no title"
    return None


def normalise_ticket(raw, items: list[Item]) -> str:
    """Upper-case; a bare number becomes the one existing ticket that ends in it, if exactly one does."""
    ticket = str(raw).strip().upper()
    if ticket.isdigit():
        matches = {i.ticket for i in items if i.ticket and i.ticket.rsplit("-", 1)[-1] == ticket}
        if len(matches) == 1:
            return matches.pop()
    return ticket


def apply_changes(
    *,
    items: list[Item],
    standup: Standup,
    changes: list[ProposedChange],
    not_tracked: list | None,
    team: Team,
    next_number: int,
    prior_speakers: frozenset[str] = frozenset(),
) -> ApplyResult:
    items = [item.model_copy(deep=True) for item in items]
    by_id = {item.id: item for item in items}
    turns = standup.turns
    names = team.canonical_names()
    known = set(names) | {t.speaker.lower() for t in turns if t.speaker} | {i.owner.lower() for i in items if i.owner}

    extra_not_tracked: list[NotTracked] = []
    ref_ids: dict[str, str] = {}
    ref_clash: set[str] = set()

    def refuse(work: _Work, rule: str, reason: str) -> None:
        work.result = CheckedChange(
            proposed=work.change, outcome="could_not_verify", quotes=_quotes(work), failure=Flag(rule=rule, reason=reason)
        )

    def move_to_not_tracked(work: _Work, item_id: str | None) -> None:
        work.result = CheckedChange(proposed=work.change, outcome="not_tracked", item_id=item_id, quotes=_quotes(work))
        extra_not_tracked.append(
            NotTracked(quote=work.found[0][0], reason=REMOVED_BY_LEAD, quote_found=True, source="code")
        )

    # Pass 1: shape, quotes (C1), target (C2), and an id for every add that gets this far.
    work_list = [_Work(change) for change in changes]
    for work in work_list:
        change = work.change
        problem = _shape_problem(change)
        if problem:
            refuse(work, "shape", f"malformed change: {problem}")
            continue
        if not change.quotes:
            refuse(work, "C1", "no quotes")
            continue
        missing = None
        for quote in change.quotes:
            turn = find_quote(turns, quote)
            if turn is None:
                missing = quote
                break
            work.found.append((quote, turn))
        if missing is not None:
            work.found = []
            refuse(work, "C1", f"quote not found in one turn of the transcript: {missing!r}")
            continue
        if not any(meets_length_rule(q, t) for q, t in work.found):
            refuse(work, "C1", "no quote of four words or more, or a whole turn")
            continue

        fields = change.fields or {}
        if change.kind == "update":
            target = by_id.get(change.item_id.strip())
            if target is None:
                refuse(work, "C2", f"no item {change.item_id!r}")
            elif target.removed_on:
                move_to_not_tracked(work, target.id)
            else:
                work.item = target
            continue

        if not _empty(fields.get("ticket")):
            ticket = normalise_ticket(fields["ticket"], items)
            removed = next((i for i in items if i.removed_on and i.ticket == ticket), None)
            if removed:
                move_to_not_tracked(work, removed.id)
                continue
        new = Item(id=f"A{next_number}", created_on=standup.date)
        next_number += 1
        items.append(new)
        by_id[new.id] = new
        work.item = new
        if isinstance(change.ref, str) and change.ref.strip():
            ref = change.ref.strip()
            if ref in ref_ids or ref in ref_clash:
                ref_ids.pop(ref, None)
                ref_clash.add(ref)
            else:
                ref_ids[ref] = new.id

    # Pass 2: the fields, in an order where later steps can read earlier results.
    for work in work_list:
        if work.result is not None:
            continue
        change, item = work.change, work.item
        added = change.kind == "add"
        new_values: dict = {}
        flags: list[Flag] = []

        # A field that is not text is ignored and handed to the lead; it is never stored as stringified junk.
        fields = {}
        for name, value in (change.fields or {}).items():
            if value is None or isinstance(value, str):
                fields[name] = value
            elif name == "ticket" and isinstance(value, int) and not isinstance(value, bool):
                fields[name] = str(value)
            elif name == "owner" and isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
                fields[name] = value[0]
            elif name == "owner" and isinstance(value, list) and len(value) > 1:
                flags.append(Flag(rule="shape", reason="more than one owner named: " + ", ".join(map(str, value))))
            elif name in TEXT_FIELDS:
                flags.append(Flag(rule="shape", reason=f"{name} ignored: not text"))

        parent_id = None
        if "parent" in fields and not _empty(fields["parent"]):
            wanted = str(fields["parent"]).strip()
            target = by_id.get(ref_ids.get(wanted, wanted))
            if wanted in ref_clash:
                flags.append(Flag(rule="C5", reason=f"parent link dropped: more than one new item is called {wanted!r}"))
            elif target is None:
                flags.append(Flag(rule="C5", reason=f"parent link dropped: no item or new item called {wanted!r}"))
            elif target.id == item.id:
                flags.append(Flag(rule="C5", reason="parent link dropped: an item cannot be part of itself"))
            elif target.removed_on:
                flags.append(Flag(rule="C5", reason=f"parent link dropped: {target.id} was removed by the lead"))
            else:
                parent_id = target.id

        if "owner" in fields:
            if _empty(fields["owner"]):
                new_values["owner"] = None
            else:
                owner = str(fields["owner"]).strip()
                owner = names.get(owner.lower(), owner)
                if owner.lower() not in known:
                    flags.append(Flag(rule="C3", reason=f"owner '{owner}' is not a known person"))
                    known.add(owner.lower())
                new_values["owner"] = owner

        if "ticket" in fields:
            if _empty(fields["ticket"]):
                new_values["ticket"] = None
            else:
                ticket = normalise_ticket(fields["ticket"], items)
                new_values["ticket"] = ticket
                if added:
                    twin = next((i for i in items if i.id != item.id and i.ticket == ticket and not i.removed_on), None)
                    if twin and twin.id != parent_id:
                        flags.append(Flag(rule="C4", reason=f"possible duplicate of {twin.id}"))

        if "due_phrase" in fields:
            if _empty(fields["due_phrase"]):
                new_values["due"] = None
                new_values["due_phrase"] = None
            else:
                phrase = str(fields["due_phrase"]).strip()
                result = resolve_due(phrase, work.found, standup.date)
                if result.step == "D1":
                    flags.append(Flag(rule="D1", reason=result.reason))
                elif result.step == "D2":
                    new_values["due"] = None
                    new_values["due_phrase"] = phrase
                    flags.append(Flag(rule="D2", reason=result.reason))
                elif result.step == "D3":
                    new_values["due"] = result.date
                    if result.date != item.due:
                        new_values["due_phrase"] = phrase
                elif item.due is not None and result.vague:
                    # "soon" does not say the date moved, but "in two days" lands here too: keep the date and
                    # let the lead see that timing came up.
                    flags.append(Flag(rule="D4", reason=f"timing mentioned, date unchanged: '{phrase}'"))
                else:
                    if item.due is not None:
                        flags.append(Flag(rule="D4", reason=f"date no longer pinned: '{phrase}'"))
                    new_values["due"] = None
                    new_values["due_phrase"] = phrase

        if added:
            new_values["status"] = vocab.START_STATUS
        if "status" in fields:
            if fields["status"] in vocab.STATUS_KEYS:
                new_values["status"] = fields["status"]
            elif not (added and _empty(fields["status"])):
                flags.append(Flag(rule="shape", reason=f"status {fields['status']!r} ignored: not a known status"))

        if "title" in fields:
            if _empty(fields["title"]):
                flags.append(Flag(rule="shape", reason="empty title ignored"))
            else:
                new_values["title"] = str(fields["title"]).strip()
        if "note" in fields:
            new_values["note"] = None if _empty(fields["note"]) else str(fields["note"]).strip()

        if "parent" in fields:
            if _empty(fields["parent"]):
                new_values["parent"] = None
            elif parent_id:
                new_values["parent"] = parent_id

        reasons = [flag.reason for flag in flags]
        if isinstance(change.review_reason, str) and change.review_reason.strip():
            reasons.append(change.review_reason.strip())
        if reasons:
            new_values["review_reasons"] = list(dict.fromkeys([*item.review_reasons, *reasons]))

        quotes = _quotes(work)
        diffs = set_fields(item, new_values, on=standup.date, by="model", quotes=quotes, flags=flags)
        if not diffs and not added:
            work.result = CheckedChange(proposed=change, outcome="discarded", item_id=item.id, quotes=quotes)
            continue
        work.result = CheckedChange(
            proposed=change,
            outcome="applied",
            item_id=item.id,
            quotes=quotes,
            diffs=diffs,
            change_labels=labels_for(diffs, added=added),
            flags=flags,
        )

    listed: list[NotTracked] = []
    for entry in not_tracked if isinstance(not_tracked, list) else []:
        if not isinstance(entry, dict):
            continue
        quote, reason = str(entry.get("quote") or "").strip(), str(entry.get("reason") or "").strip()
        if quote or reason:
            listed.append(NotTracked(quote=quote, reason=reason, quote_found=find_quote(turns, quote) is not None))

    seen = {name.lower() for name in prior_speakers} | set(names)
    new_speakers = list(dict.fromkeys(t.speaker for t in turns if t.speaker and t.speaker.lower() not in seen))

    return ApplyResult(
        checked=[w.result for w in work_list],
        items=items,
        not_tracked=listed + extra_not_tracked,
        new_speakers=new_speakers,
    )


def _quotes(work: _Work) -> list[Quote]:
    return [Quote(text=q, turn=t.n, speaker=t.speaker) for q, t in work.found]
