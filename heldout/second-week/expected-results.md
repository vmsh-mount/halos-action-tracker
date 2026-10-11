# Second week: what a correct run should produce

Status: **reviewed by the owner on 2026-10-11, before anything was run against these transcripts.** The
owner's four rulings are recorded at the end.

Written by the assistant that built the prompt and the code, after reading the five transcripts and before
seeing any model output for them. It applies `docs/action-item-rules.md` as it stands. Where the rules do not
settle something, the line is marked **soft** and either outcome counts as right.

## How it will be used

- Each run starts from the list a correct practice week ends with (the 14 items in
  `docs/action-item-rules.md` section 7, ids A1 to A14), not from a live practice run.
- Each day is approved with no edits.
- The checks below are judged by hand against each run's output and reported as "N of 3".
- **Firm** checks are the score. **Soft** lines are recorded but not scored.
- New items are identified by what they are about, never by id.

## The starting list

| Id | Item | Owner | Due | Status |
|---|---|---|---|---|
| A1 | Fix search latency | Arjun | — | done |
| A2 | Auth bug (PAY-231) | Dev | — | done |
| A3 | Hermes staging deploy | Sana | — | done |
| A4 | Flaky CI test | — | — | open |
| A5 | Export feature | Priya | Wed 22 Oct | in progress |
| A6 | Fix onboarding doc | Rohan | — | in progress |
| A7 | Atlas login slow | Dev | — | done |
| A8 | Review Dev's PAY-231 PR (part of A2) | Priya | — | done |
| A9 | Review Arjun's search PR (part of A1) | Dev | 15 Oct | done |
| A10 | Send Falcon doc | Arjun | 15 Oct | open |
| A11 | Hermes retry bug (APP-402) | Sana | Mon 20 Oct | open |
| A12 | Retro on PAY-231 (part of A2) | — | — | open |
| A13 | Review Falcon schema draft | Dev | 17 Oct | open |
| A14 | Check onboarding doc draft (part of A6) | Priya | — | open |

## Monday 20 October

| # | Expected | | Trap |
|---|---|---|---|
| M1 | The check of the older Android clients is captured with owner **Dev**, due 21 or 22 Oct: as a new item (the cleaner reading), or by reopening A2 for it (accepted) | Firm | Skipped, because 231 "looks clean" |
| M2 | A new item for fixing the rollback path in the migration script, owner **Dev**, due **20 Oct** | Firm | Skipped as a small promise ("I'll fix the rollback today") |
| M3 | A11 (retry bug) is **not done**: it is on staging, not in production | Firm | Closed on "Hermes retry bug is fixed" |
| M4 | A11's due date is no longer 20 Oct: either 21 Oct, or cleared and marked for the lead | Firm | Left at 20 Oct |
| M5 | A14 (check onboarding draft) is due **21 Oct** | Firm | A second "review the onboarding doc" item for Priya |
| M6 | A5 (export) has **no due date** and is marked for the lead | Firm | Wednesday kept, although it now depends on a test and the lead says not to promise it |
| M7 | No item for the storage alert | Firm | An item from "Keep an eye on it", when the lead said not to make a ticket |
| M8 | No item from the search dashboard remark or the joke | Firm | |
| M9 | A4, A10, A12 unchanged | Firm | Closing the overdue Falcon doc or the retro because nobody mentions them |
| — | A13: Priya says the "schema review is done from my side", but the list has Dev owning that review. Closed or left open | Soft | The transcript and the list disagree about who was reviewing |
| — | M1's item is linked to A2 | Soft | |

## Tuesday 21 October

| # | Expected | | Trap |
|---|---|---|---|
| T1 | A11 (retry bug) is **done** | Firm | |
| T2 | The rollback fix (M2) is **done** | Firm | |
| T3 | A14 (check onboarding draft) is **done**: Rohan reports that Priya reviewed it | Firm | Left open because Priya did not say so herself |
| T4 | A6 (onboarding doc) is still active | Firm | Closed on "Priya reviewed the onboarding doc" |
| T5 | An active review item owned by **Dev**, due **21 Oct**: A13 updated, or a new one | Firm | Given to Priya, who was the reviewer a moment earlier; the lead asks Dev and Dev says "Yep" |
| T6 | A5 (export) is active with **no due date** | Firm | 22 Oct from "I should know by tomorrow", which is when she will know, not when it ships |
| T7 | A2 is **not reopened** by Tuesday's standup | Firm | Reopened on "still sending a few refresh errors"; the lead says not to |
| T8 | The Android item (M1) is still active, owner Dev | Firm | Closed, or merged into A2 |
| T9 | A new item for investigating the staging database storage, owner **Sana**, due **22 Oct** | Firm | Skipped because Monday said no ticket |
| T10 | No item for the slow local start | Firm | The lead says to keep it off the list |
| — | A6 due 23 Oct, or no date and marked ("I'll try") | Soft | |

## Wednesday 22 October

| # | Expected | | Trap |
|---|---|---|---|
| W1 | An active item for the expired-cookie fix, owner **Dev**, due **23 Oct**, that is **not A2** | Firm | A2 reopened; Dev and the lead agree to track it separately |
| W2 | A2 is still done | Firm | |
| W3 | A5 (export) is active | Firm | |
| W4 | Sana has an active storage item due **23 Oct** (the investigation re-dated, or a new one for the retention policy) | Firm | Two unconnected items for the same storage problem |
| W5 | A6 (onboarding doc) is still active | Firm | Closed on "The onboarding links are fixed"; the lead says keep it open |
| W6 | An item for the final Falcon migration review, owner **Priya**, due **22 Oct** | Firm | Given to Dev, who asks for it |
| W7 | No item for the team lunch | Firm | |
| — | A5 has no due date and is marked (Friday is "probably" and "if"), or is due 24 Oct | Soft | |
| — | The regression test is noted on the fix item, or is its own item | Soft | |
| — | A separate item for Priya testing the setup steps on a clean machine | Soft | |
| — | The Android check (M1) is closed, or has become the fix item | Soft | |

## Thursday 23 October

| # | Expected | | Trap |
|---|---|---|---|
| H1 | The expired-cookie fix is **not done** | Firm | Closed on "The expired-cookie patch is ready" |
| H2 | A5 (export) is due **24 Oct** and still active | Firm | Closed on "Export cancellation is fixed" |
| H3 | Sana's storage work is still active | Firm | Closed on "I checked the retention policy" |
| H4 | A new item for the migration monitoring alerts, owner **Sana**, due **27 Oct** | Firm | Folded into a "run the migration" item |
| H5 | The final migration review (W6) is **done** | Firm | Left open; it is Dev who reports it complete |
| H6 | A new item for running the Falcon migration, due **27 Oct**, separate from the monitoring item (H4) | Firm | Treated as a scheduled event and not tracked; or merged with its preparation tasks |
| — | H6's owner: none and marked for the lead (two people are named), or one of Priya and Dev | Soft | |
| — | An item for reviewing the cleanup query, owner Priya, due 24 Oct | Soft | |
| — | A6 done on Rohan's "Done.", or active and due 23 Oct | Soft | "Done." may mean "will do" |
| — | The troubleshooting section not tracked, or kept with no owner and marked | Soft | |

## Friday 24 October

| # | Expected | | Trap |
|---|---|---|---|
| F1 | A5 (export) is **done** | Firm | |
| F2 | A6 (onboarding doc) is **done** | Firm | Kept open for "I'll incorporate those next week"; the lead says close it |
| F3 | The migration monitoring item (H4) is **done** | Firm | |
| F4 | The expired-cookie fix is still **not done** | Firm | Closed on "went to staging yesterday" |
| F5 | An item for the production cleanup, owner **Sana**, status **blocked** | Firm | Closed on "cleaned up in staging"; or left active, when the lead says leave it blocked |
| F6 | A new item for testing the rollback against a production-sized snapshot, owner **Dev**, due **24 Oct** | Firm | Owner Priya, who raises it |
| F7 | No item for the laptop start time | Firm | |
| F8 | A4, A10 and A12 are exactly as they were on the starting list | Firm | A week of silence closes nothing |
| F9 | A2 is done, and was never reopened from Tuesday onward | Firm | |
| F10 | The migration item (H6) is still active, and separate from the rollback test (F6) and the monitoring item | Firm | Closed or merged because Friday restates the plan |
| — | The expired-cookie fix due 27 Oct, or no date | Soft | "Review the numbers Monday" is not a deploy date |

## Every day

The always-true properties from `docs/evaluation-checks.md`: every quote sits in one turn of that day; no
change refused for an unfound quote; every date has its phrase in a quote; history replays to the fields.

## Scoring

42 firm checks: 9 on Monday, 10 on Tuesday, 7 on Wednesday, 6 on Thursday, 10 on Friday, plus the count of
refused changes and extra items per run. An **extra item** is any item that is not on the starting list and
is not named in a firm or soft line above.

## Predictions, written before running

Places where I expect the system to fall short of the rules, so they cannot be explained away afterwards:

1. **Monday, the retry bug (M4).** "Let's get that into production tomorrow, assuming the staging metrics
   stay clean" is a promise with a condition. The rules say no date and a mark for the lead. The code's list
   of condition words is "if, once, unless"; "assuming" is not in it, so the code will set 21 Oct.
2. **Tuesday, the onboarding doc.** "Can you send the updated doc by Thursday?" answered with "I'll try".
   "I'll try" is not in the hedge list, and it sits in a different turn from the day word.
3. **Wednesday, the export.** "By Friday?" answered with "Probably… If that works the way I expect, Friday
   is realistic". If the model quotes the lead's question, the hedge is in another turn and the code sets
   24 Oct.
4. **Role mismatch on Monday.** The list has Dev reviewing the schema draft; the transcript has Priya saying
   her review is done. I do not know what the model will do, and the rules do not say.
6. **The migration item (H6).** The prompt tells the model that an event with its time already set is not
   an action item. The owner has ruled the migration is one. I expect the model to leave it out at least
   some of the time.
5. **A real day on the wrong work**, as in the practice week: "I should know by tomorrow" (Tuesday) and
   "report back tomorrow" are the likeliest places.

## The owner's rulings

| Question | Ruling |
|---|---|
| The Android check on Monday | Both readings are valid. A separate item is the cleaner one; reopening A2 is the softer alternative (M1) |
| The storage alert | No item on Monday, where it is dismissed as transient. An item on Tuesday, when it repeats, lasts longer and storage is at 86% (M7, T9) |
| The Falcon migration on Monday 27 October | An action item, not only a scheduled event. It is kept distinct from its preparation tasks (H6, F10) |
| Priya's "schema review is done" against Dev owning that item | Soft. The transcript does not transfer the item, so no reassignment is forced |

The third ruling goes further than the prompt, which says an event with its time set is not an action item.
The prompt is not changed for it; prediction 6 records what I expect.
