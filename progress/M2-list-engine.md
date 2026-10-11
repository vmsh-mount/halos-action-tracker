# M2 — List engine: progress

Date: 2026-10-11. Tasks: [tasks/M2-list-engine.md](../tasks/M2-list-engine.md).

## Done

All ten work items. Code under `src/standup_tracker/`: `vocab`, `models`, `transcript`, `dates`, `items`,
`apply`, `review`, `store`, and the non-model half of `service`. Team settings in `config/team.json`.

All eight test groups, including the two marked "first to go". Nothing was dropped under the cut order.
Not every row of the change-tier table has its own case: an update that sets a ticket another item holds
(accepted, no check) is untested.

## Evidence

- `pytest`: **144 passed**, 0.15 s, no key, no network. Python 3.14.3, Pydantic 2.14.0, pytest 9.1.1.
- **The answer key through the code** (`tests/test_answer_key.py`): the key written as five days of proposed
  changes under `tests/fixtures/answer_key_changes/`, each day approved. The final list equals the reference
  week in `action-item-rules.md` section 7 on owner, due date, status, parent and ticket for all 14 items;
  item counts per day are 6, 8, 10, 11, 14; no change is refused; every item's fields equal its history
  replayed, on every day.
- **Date steps** (`tests/test_dates.py`): 46 tests, 40 of them rows of one table, covering every due phrase in the
  answer key and the untested cases listed in `evaluation-checks.md` section 3.
- **Transitions** (`tests/test_transitions.py`): one case per row of the status, owner and due tables.
- **The tests can fail.** Five deliberate breaks were each caught by at least one test, then reverted:
  removing "probably" from the hedge words; lowering the quote floor to one word; disabling the
  reopen-clears-date rule; storing the phrase when the date is unchanged; skipping the removed-item check.
- **No practice-week word under `src/`**: a search for the people's names, the three system names and the
  two ticket forms found nothing. This is a manual check; the automated word test comes with the prompt
  template in M3.

## Changed after review

An independent review of the code found seven problems; all are fixed, each with a test:

- Closing an item in a review and undoing it no longer wipes its date: the reopen rule now applies only to
  an item that was closed when the day began.
- An edit that posts the date unchanged no longer clears the phrase or records a correction.
- Speaker names may use any alphabet, hyphens and apostrophes, and may sit alone on their line.
- "last" and "previous" are day-shifting words, so "last Friday" gives no date.
- A field that is not text is ignored and marked for the lead; several owners in a list give "more than one
  owner named" and no owner.
- A `not_tracked` that is not a list, and a change that is not an object, are handled instead of crashing.
- A quote cannot start or end in the middle of a word.

A second review found one regression from those fixes and three smaller points; all are fixed with tests:

- The whole-word match stopped finding a due phrase before a possessive ("Wednesday" in "Wednesday's
  fine"). A possessive now counts as a word end.
- Undo no longer wipes a date the lead set on an item the model reopened that day: for a lead edit, the
  reopen rule compares against the status the system proposed.
- Speaker names may include a lower-case particle ("de Souza") or a title ending in a full stop ("Dr. Rao").

A third review found that the lead undoing a close made by the model in the same draft wiped the date. The
reopen rule now uses one baseline for the model and the lead: the status before the lead's own first status
edit in the review if there is one, otherwise the status when the day began. Known limit, not fixed: a
wrapped line starting "Okay. So:" is read as a speaker and shows up as a new speaker on the page.

One point is carried to M4 and not fixed in code: when the lead reopens an item closed on an earlier day,
the date is cleared even if the form posts the old date along with the status. The page has to show that.

The rules, data models and implementation details documents are updated to match.

## What this does not show

- Nothing here involves a model. The fixture is the answer key, written by hand to be right; it says nothing
  about what a model returns.
- The fixture and the reference list were written by the same hand from the same documents, so agreement
  between them shows the code follows the rules, not that the rules are right.

## Decisions made while building

- An update's fields are kept as a plain dictionary, so "left out" and "explicitly empty" are told apart by
  whether the key is present. The components document suggested Pydantic's `model_fields_set`; the effect is
  the same.
- A proposed change is parsed loosely (every field optional, any type) and checked in `apply`, so one
  malformed change is refused without failing the answer.
- `service` exists already with the parts that need no model (date order, the draft, building a day from
  proposed changes). M3 adds the model call around it.

## Time

About 30 min of building (budget 40). Elapsed since the start of the session: about 3 h.

## Open

- Not committed; waiting for go-ahead.
- `requirements.txt` holds only Pydantic and pytest so far. The web and network libraries are added in M3
  and M4.
