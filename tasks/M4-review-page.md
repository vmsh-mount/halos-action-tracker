# M4 — Review page

Budget: 55 min. Plan: [PLAN.md](../PLAN.md) section 3.

The page the lead checks after each standup. It reads day records and calls the existing service and review
functions. It changes nothing about what the model is shown: the prompt, the item lines and the engine are
frozen (see `progress/M3-reading-transcripts.md`).

References: **flow** = `docs/components-and-data-flow.md` §4.2, §6; **impl** = `docs/implementation-details.md` §2, §4.

| # | Item | Done |
|---|---|---|
| 1 | `web/views.py`: turn a day record into what the page shows. One row per changed item with its labels, old → new, quotes with speakers, review reasons and the lead's own edits; flagged rows first | [x] |
| 2 | `web/app.py`: `GET /`, `POST /standup`, `POST /items/{id}/edit`, `POST /items/{id}/remove`, `POST /approve`, `POST /discard`, `GET /items/{id}` | [x] |
| 3 | Templates: the draft under review; the approved list with the submit form; one item's history | [x] |
| 4 | Draft page sections in order: notes, changed today, could not verify, heard but not tracked, the whole list (untouched dimmed, overdue marked) | [x] |
| 5 | Edit form per item: owner (suggests known people, takes free text), date, status; only values that differ count | [x] |
| 6 | A failed run shows what failed and keeps the transcript in the form; a re-run asks for confirmation | [x] |
| 7 | A cleared date is visible when the lead reopens an item closed on an earlier day (carried from M2) | [x] |
| 8 | `python -m standup_tracker serve` starts the page | [x] |
| 9 | Tests through the app with saved answers: submit, edit, remove, approve, discard, failure, re-run | [x] |
| 10 | Looked at in a browser: Monday's draft and Thursday's draft | [x] |

## Done when

- With no key, a reviewer can start the page, paste Monday's transcript, see what changed, fix an owner and a
  date, remove an item, approve, and carry on to Tuesday.
- `pytest` passes with no key and no network.

## Not in this milestone

- Editing title, note or parent. Undo after approval. Any styling beyond clear and readable.
