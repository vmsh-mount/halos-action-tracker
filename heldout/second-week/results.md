# Second week: results

Run on 2026-10-11 at 17:00 with `heldout/run_second_week.py --runs 3`. Model `openai/gpt-5-mini` through
OpenRouter. Code and prompt at commit `315d91a`, unchanged before, between and after the runs. Raw runs and a
text report for each are in `runs/2026-10-11-1700/`.

Each run started from the list a correct practice week ends with, and each day was approved with no edits.

**Judged by hand** against `expected-results.md`, by the assistant that wrote the prompt, the code and the
expectations. The expectations were fixed, and reviewed by the owner, before the runs. The judging was done
from a day-by-day table of every item in each run; a second reader could reach a different verdict on the
lines marked ‡.

## Score

| | Run 1 | Run 2 | Run 3 | All |
|---|---|---|---|---|
| Monday (9) | 6 | 6 | 6 | 18 of 27 |
| Tuesday (10) | 8 | 7 | 8 | 23 of 30 |
| Wednesday (7) | 5 | 6 | 6 | 17 of 21 |
| Thursday (6) | 4 | 4 | 4 | 12 of 18 |
| Friday (10) | 7 | 7 | 9 | 23 of 30 |
| **Firm checks (42)** | **30** | **30** | **33** | **93 of 126 (74%)** |
| Changes proposed | 33 | 34 | 37 | 104 |
| Changes refused for an unfound quote | 0 | 0 | 0 | 0 |
| Extra items (not in the expectations at all) | 0 | 0 | 0 | 0 |
| Items at the end of the week | 19 | 21 | 23 | |

## Every firm check

| # | Check | Passed | What happened when it failed |
|---|---|---|---|
| M1 | Android check captured, owner Dev, due 21 or 22 Oct | 3 of 3 | All three reopened A2 for it (the accepted alternative), none made a separate item |
| M2 | New item for the rollback fix, Dev, due 20 Oct | 1 of 3 ‡ | Runs 1 and 3 put it on A13, the schema review item, with the right owner and date |
| M3 | Retry bug not done on Monday | 3 of 3 | |
| M4 | Retry bug no longer due 20 Oct | 2 of 3 | Run 2: the model's phrase was not in its quotes, so the old date stood; it was marked for the lead |
| M5 | Onboarding draft check due 21 Oct | 3 of 3 | |
| M6 | Export has no date and is marked | **0 of 3** | The model quoted "If memory usage is okay, we can still target Wednesday" and returned no date phrase, so 22 Oct stayed |
| M7 | No item for the storage alert on Monday | **0 of 3** | All three added one, with no owner, marked for the lead to decide |
| M8 | No item from the dashboard remark | 3 of 3 | |
| M9 | A4, A10, A12 unchanged | 3 of 3 | |
| T1 | Retry bug done | 3 of 3 | |
| T2 | Rollback fix done | 1 of 3 ‡ | Follows from M2: in runs 1 and 3 the work sat on A13, which stayed open |
| T3 | Onboarding draft check done | 2 of 3 | Run 2 left it open until Thursday |
| T4 | Onboarding doc still active | 3 of 3 | |
| T5 | Active review item, Dev, due 21 Oct | 2 of 3 | Run 2 had closed A13 on Monday and made no new one |
| T6 | Export active with no date | **0 of 3** | Follows from M6: still 22 Oct |
| T7 | A2 not reopened by Tuesday | 3 of 3 ‡ | It was already open from Monday in every run |
| T8 | Android work still active, Dev | 3 of 3 | |
| T9 | Storage investigation, Sana, due 22 Oct | 3 of 3 | |
| T10 | No item for the slow local start | 3 of 3 | |
| W1 | Expired-cookie fix, Dev, due 23 Oct, separate from A2 | 3 of 3 | |
| W2 | A2 still done | **0 of 3** | A2 was reopened on Monday and never closed again |
| W3 | Export active | 3 of 3 | |
| W4 | Sana's storage item due 23 Oct | 3 of 3 | |
| W5 | Onboarding doc still active | 3 of 3 | |
| W6 | Final migration review, Priya, due 22 Oct | 2 of 3 | Run 1 noted it on A13 and made no item for Priya |
| W7 | No item for the team lunch | 3 of 3 | |
| H1 | Expired-cookie fix not done | 3 of 3 | |
| H2 | Export due 24 Oct and active | 1 of 3 | Run 2: no date. Run 3: closed on "Export cancellation is fixed", a day early |
| H3 | Sana's storage work still active | 3 of 3 | |
| H4 | Migration monitoring alerts, Sana, due 27 Oct | 1 of 3 | Runs 1 and 2 made no item for it |
| H5 | Final migration review done | 1 of 3 | Run 1 had no such item. Run 3 closed A13 and left Priya's review open |
| H6 | Run the Falcon migration, due 27 Oct, separate | 3 of 3 | |
| F1 | Export done | 3 of 3 | |
| F2 | Onboarding doc done | 3 of 3 | |
| F3 | Monitoring alerts done | 1 of 3 | Follows from H4 |
| F4 | Expired-cookie fix still not done | 3 of 3 | |
| F5 | Production cleanup, Sana, blocked | 2 of 3 | Run 2 left the storage item in progress |
| F6 | Rollback test on a production-sized snapshot, Dev, due 24 Oct | 2 of 3 | Run 1 skipped it |
| F7 | No item for the laptop | 3 of 3 | |
| F8 | A4, A10, A12 as they started | 3 of 3 | |
| F9 | A2 done, never reopened from Tuesday | **0 of 3** | Same as W2 |
| F10 | Migration item still active and separate | 3 of 3 | |

25 checks passed in all three runs, 5 in none, 12 in one or two.

## The mistakes behind the failures

Several checks fail for the same reason. Counted as distinct mistakes:

| Mistake | Runs | Checks it costs |
|---|---|---|
| **A2 reopened on Monday and left open all week.** Reopening was an accepted reading on Monday. On Wednesday the team agreed to track the new problem separately, and all three runs did add that separate item, but none closed A2 again. It ends the week in progress and overdue | 3 of 3 | W2, F9 |
| **The export kept its Wednesday date** after "If memory usage is okay…" and "Let's not promise Wednesday". The model was told to return a day whenever one is said, however unsure. It quoted the sentence and returned no day, so code never saw it | 3 of 3 | M6, T6 |
| **A storage-alert item on Monday**, when the lead said not to make one. Each run left it unowned and marked it for the lead | 3 of 3 | M7 |
| **Work put on the wrong existing item.** The rollback fix went onto A13 (the schema review) | 2 of 3 | M2, T2 |
| **A skipped item**: the monitoring alerts (2 runs), Priya's final review (1), the rollback snapshot test (1) | 3 of 3 | H4, F3, W6, H5, F6 |
| **Closed too early**: the export on Thursday, on "cancellation is fixed" | 1 of 3 | H2 |
| **A status missed**: production cleanup not marked blocked | 1 of 3 | F5 |
| **A wrong owner** on a soft item: run 3 moved the cleanup-query review from Priya to Sana on Friday | 1 of 3 | not scored |

What did not go wrong in any run: no quote was invented (0 of 104 changes refused), no item was added that
the expectations do not name, nothing was made of the lunch, the laptop, the slow start or the dashboard
remark, the three items nobody mentioned all week were left exactly alone, the expired-cookie fix was kept
separate from PAY-231 and never closed early, and the retry bug was not closed while it was only on staging.

## The predictions

| Prediction, written before the runs | Outcome |
|---|---|
| 1. "assuming the staging metrics stay clean" is not a condition word, so the code will set 21 Oct | Right in runs 1 and 3. In run 2 the date stood for another reason (M4) |
| 2. "I'll try" will not stop Thursday being set | Right: all three set 23 Oct. But in runs 2 and 3 the model itself marked the item, quoting "I'll try" |
| 3. On Wednesday the hedge about Friday may be missed, giving 24 Oct | Right in runs 1 and 3. Run 2 quoted the "if" sentence and the code cleared the date |
| 4. Unknown what happens with Priya's "schema review is done" | Run 2 closed A13. Runs 1 and 3 kept it and used it for the rollback work |
| 5. A day attached to the wrong work | Not seen this week |
| 6. The migration would sometimes be left out as a scheduled event | **Wrong.** All three made the item, with no single owner, marked for the lead |

## Cost

54,638 tokens in and 81,490 out across the fifteen calls: about **$0.18** at $0.25 and $2.00 per million.

## How far to trust this

- Three runs of one week. A check at "0 of 3" is a pattern; "1 of 3" and "2 of 3" are not rates.
- The transcripts were not seen while the prompt and code were written, and nothing was changed after seeing
  these results. But the expectations and the judging are by the same hand as the prompt.
- The week is for the same team, with the same names and systems. It says nothing about a different team.
- The starting list was the correct one, not the output of a live practice week. In real use the mistakes of
  one week would carry into the next.
- 74% is a count of checks, and several checks follow from one mistake. Read the mistakes table, not the
  percentage.
