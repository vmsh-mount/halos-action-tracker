# M5 — Live repeats of the practice week: progress

Date: 2026-10-11. Tasks: [tasks/M5-live-repeats.md](../tasks/M5-live-repeats.md).

## What was run

`tests/live_check.py --runs 3`: the five practice days, from an empty list, three times against
`openai/gpt-5-mini` through OpenRouter, each day approved with no edits. Fifteen model calls, all answered
on the first attempt, the three runs side by side in 2 min 7 s. Each run is saved in full under
`tests/live_runs/2026-10-11-1639/` (state, drafts, raw answers, token counts).

The prompt and the engine were the committed ones (`d2137fd`); nothing was changed before, between or after
the runs.

## Results

38 properties were put to each run. **26 passed in all three runs. 12 passed in one or two. None failed in
all three.**

| Group | Property | Passed |
|---|---|---|
| Always true | Every quote sits in one turn; every date has its phrase in a quote; owners known or marked; history replays; closing needs a quote | 3 of 3 each |
| H1 made up | No change refused for an unfound quote (0 of 79 proposed changes) | 3 of 3 |
| H2 duplicates | No piece of work has two items: Mon, Tue, Wed | 3 of 3 each |
| H2 duplicates | No piece of work has two items: Thu, Fri | **1 of 3** each |
| H2 duplicates | The auth bug is one item under every name | 2 of 3 |
| H3 owners | Auth bug owned by the one who took it; onboarding doc unowned until picked up; undecided item unowned and marked | 3 of 3 each |
| H4 skipped | Search fix, staging deploy, flaky test, onboarding doc, slow login, doc to send, retry bug, retro | 3 of 3 each |
| H4 skipped | Auth bug, export (exactly one item each) | 2 of 3 each |
| H5 made up | No item outside the answer key; none resting only on a not-tracked turn | 2 of 3 each |
| H6 dates | Hedged search fix undated and marked; retry bug rolls 17 → 20 Oct; small promises get their day | 3 of 3 each |
| H6 dates | Export 20 → 22 Oct | 2 of 3 |
| H6 dates | The search fix never gets a date | **1 of 3** |
| H6 dates | Another team's estimate is not our due date | **1 of 3** |
| Status | Statuses through the week; reopening kept the item and cleared the date | 2 of 3 each |
| Other | Item count within 10 to 14; the other item on the same system not reopened; new speaker listed once | 3 of 3 each |

Several rows fail together because they see the same mistake from different sides. Counted as mistakes, not
as rows:

| Run | Items | What the model got wrong |
|---|---|---|
| 1 | 13 | **An extra item**: "Falcon payments DB migration", from the staffing remark on Thursday. Infra's estimate taken as the staging deploy's date. The search fix was never closed (soft) |
| 2 | 11 | The reviewer's "today" put on the search fix. Nothing else |
| 3 | 13 | **A duplicate**: on Thursday "231 is back" was added as a new item, "Investigate 231 session cookie issue", and the original auth item stayed done. **An extra item** for work already finished ("Falcon schema draft is up"). Infra's estimate taken as a date. The reviewer's "today" on the search fix |

Across the four runs so far (the one recording and these three):

| Mistake | Runs it appeared in |
|---|---|
| Infra's estimate taken as our due date | 3 of 4 |
| The reviewer's "today" put on the search fix | 3 of 4 |
| An item added for something that is not an action | 2 of 4 |
| A returning item added as new (the duplicate the brief names) | 1 of 4 |
| A skipped item (the retro) | 1 of 4 |
| A quote that was not said | 0 of 4 |
| A wrong owner | 0 of 4 |

## Item-level summary

Against the answer key, at the end of the week, over the three live runs. Only the ten firm pieces of work
are scored; the four soft items are not counted either way.

| Measure | Result |
|---|---|
| Work captured: each firm piece of work has an item | 30 of 30 |
| Items fully right: one item, right owner, due date and done / not done | 25 of 30 (83%) |
| Owner right | 30 of 30 |
| Done / not done right | 30 of 30 |
| Due date right | 25 of 30 |
| Items produced that were wanted | 34 of 37 (92%) |
| Proposed changes backed by words that were said | 79 of 79 |

Per run, items fully right: 9, 9 and 7 of 10. With the earlier recorded run included: 39 of 40 captured,
32 of 40 fully right (80%).

A script's strict count gives 24 of 30, because it charges run 1's extra item to the export as a second
item. The export item itself was right and the extra item is already counted as unwanted, so 25 is used.
These are end-of-week states: an item wrong mid-week and right by Friday counts as right. The per-day
properties above are stricter: 98 of 114 checks passed (86%), with some mistakes counted more than once.

"Right" means agreeing with an answer key written by the same hand that wrote the rules.

## Cost

| Run | Tokens in | Tokens out | Estimated cost |
|---|---|---|---|
| 1 | 14,385 | 20,676 | $0.045 |
| 2 | 14,249 | 19,891 | $0.043 |
| 3 | 14,327 | 20,536 | $0.045 |

$0.13 for the fifteen calls, from the token counts the provider reported, at $0.25 and $2.00 per million. The
estimate before the run was $0.30. Output tokens include the model's reasoning, which is why they outnumber
the input.

## What this does and does not show

- **Three runs is a small sample.** "1 of 3" and "2 of 3" say a mistake happens; they do not give a rate.
- **Two dates go wrong more often than not.** Both are the same kind of mistake: a real day attached to the
  wrong work. Code cannot see it, and the prompt already states the rule.
- **The duplicate was not caught by code.** The model wrote "231" in the new item's title but did not fill in
  the ticket field, so the ticket check had nothing to compare. The design documents said duplicates without
  a ticket rest on the model alone; this is that case happening.
- **One check mislabelled a mistake.** Run 1's extra "Falcon migration" item quoted a sentence from the turn
  where the export slips, so the checks counted it as a second export item. The run did fail, and should
  have, but the reason was an extra item, not a duplicate. The cause is an anchor that treats that whole
  turn as being about the export.
- **Nothing here is about unseen transcripts.** These are the five days the prompt was written beside.

## Not done

- The prompt was not changed for any of these. A change would need a general reason and repeats showing it
  helped.
- **A possible code change, not made:** flag a new item as a possible duplicate when its quotes or title
  mention the number of a ticket an existing item already carries. It is general, it would have flagged run
  3's duplicate for the lead, and it does not touch what the model is shown. It is a change to the engine
  made after seeing practice results, so it is left as a proposal.
- The held-out run (M6) has not been done.
