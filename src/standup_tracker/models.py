"""Data shapes. No behaviour beyond small lookups."""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class Person(Base):
    name: str
    also: list[str] = []
    role: str = ""


class Team(Base):
    people: list[Person] = []
    glossary: dict[str, str] = {}
    ticket_prefixes: dict[str, str] = {}

    def canonical_names(self) -> dict[str, str]:
        """Every name a person goes by, lower-cased, mapped to their one stored name."""
        out: dict[str, str] = {}
        for person in self.people:
            for name in (person.name, *person.also):
                out[name.lower()] = person.name
        return out


class Turn(Base):
    n: int
    speaker: str | None
    text: str


class Standup(Base):
    date: dt.date
    text: str
    turns: list[Turn]


class Quote(Base):
    text: str
    turn: int | None = None
    speaker: str | None = None


class Diff(Base):
    field: str
    before: Any = Field(default=None, alias="from")
    after: Any = Field(default=None, alias="to")


class Flag(Base):
    rule: str
    reason: str


class HistoryEntry(Base):
    date: dt.date
    by: Literal["model", "lead"]
    action: str | None = None
    diffs: list[Diff] = []
    quotes: list[Quote] = []
    flags: list[Flag] = []


class Item(Base):
    id: str
    title: str = ""
    owner: str | None = None
    due: dt.date | None = None
    due_phrase: str | None = None
    status: str = ""
    ticket: str | None = None
    parent: str | None = None
    note: str | None = None
    review_reasons: list[str] = []
    created_on: dt.date
    removed_on: dt.date | None = None
    history: list[HistoryEntry] = []


class ProposedChange(Base):
    """Kept as the model returned it. Deliberately loose: one bad change must not cost the whole answer."""

    kind: Any = None
    ref: Any = None
    item_id: Any = None
    fields: Any = None
    quotes: Any = None
    review_reason: Any = None
    unparsed: Any = None  # set when the model put something that is not an object in the list


Outcome = Literal["applied", "could_not_verify", "discarded", "not_tracked"]


class CheckedChange(Base):
    proposed: ProposedChange
    outcome: Outcome
    item_id: str | None = None
    quotes: list[Quote] = []
    diffs: list[Diff] = []
    change_labels: list[str] = []
    flags: list[Flag] = []
    failure: Flag | None = None


class NotTracked(Base):
    quote: str
    reason: str
    quote_found: bool = True
    source: Literal["model", "code"] = "model"


class ModelRun(Base):
    provider: str
    model: str
    at: dt.datetime
    fingerprint: str = ""
    notes: list[str] = []
    attempts: list[str] = []
    usage: dict[str, Any] = {}  # token counts as the provider reported them; empty for a replayed answer


class DayRecord(Base):
    standup: Standup
    state: Literal["draft", "approved"] = "draft"
    model_run: ModelRun | None = None
    checked_changes: list[CheckedChange] = []
    not_tracked: list[NotTracked] = []
    new_speakers: list[str] = []
    items_after: list[Item] = []
    approved_at: dt.datetime | None = None


class State(Base):
    version: int = 1
    next_item_number: int = 1
    days: list[DayRecord] = []
    draft: DayRecord | None = None
    last_failed_run: dict[str, Any] | None = None
