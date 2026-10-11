"""Runs each use case end to end. Holds no rules of its own; it sequences the other parts.

The model call is added around build_draft in the next milestone.
"""

from __future__ import annotations

import datetime as dt

from .apply import apply_changes
from .models import DayRecord, Item, ModelRun, ProposedChange, Standup, State, Team
from .transcript import split_turns


class SubmitError(ValueError):
    pass


class RerunNeedsConfirmation(SubmitError):
    pass


def current_items(state: State) -> list[Item]:
    """The approved list: what the model is shown. Never the draft."""
    return state.days[-1].items_after if state.days else []


def prior_speakers(state: State) -> frozenset[str]:
    return frozenset(t.speaker for day in state.days for t in day.standup.turns if t.speaker)


def check_can_submit(state: State, date: dt.date, *, confirm_rerun: bool = False) -> None:
    if state.days and date <= state.days[-1].standup.date:
        raise SubmitError(f"{date} is not later than the last approved day, {state.days[-1].standup.date}.")
    if state.draft is not None:
        if state.draft.standup.date != date:
            raise SubmitError(f"{state.draft.standup.date} is waiting for approval. Approve or discard it first.")
        if not confirm_rerun:
            raise RerunNeedsConfirmation(f"{date} already has a draft. Running it again replaces the draft and its edits.")


def make_standup(date: dt.date, text: str) -> Standup:
    return Standup(date=date, text=text, turns=split_turns(text))


def build_draft(
    state: State,
    standup: Standup,
    changes: list[ProposedChange],
    not_tracked: list | None,
    team: Team,
    *,
    model_run: ModelRun | None = None,
) -> DayRecord:
    """Check and apply the proposed changes to a copy of the approved list, and make that the draft."""
    result = apply_changes(
        items=current_items(state),
        standup=standup,
        changes=changes,
        not_tracked=not_tracked,
        team=team,
        next_number=state.next_item_number,
        prior_speakers=prior_speakers(state),
    )
    state.draft = DayRecord(
        standup=standup,
        model_run=model_run,
        checked_changes=result.checked,
        not_tracked=result.not_tracked,
        new_speakers=result.new_speakers,
        items_after=result.items,
    )
    state.last_failed_run = None
    return state.draft
