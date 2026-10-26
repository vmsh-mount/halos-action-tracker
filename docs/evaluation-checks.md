# Evaluation checks — which tests we run and what each one shows

Status: **proposal for review** (second revision, after review). No code exists yet.

The goal is a few meaningful tests aimed at what a model gets wrong, and for honesty about which
results came from saved model answers and which from a live model. This document names the tests, says what
each demonstrates, and says what a pass does and does not mean. The method (properties, anchors, homes, the
held-out protocol) is in `generalisation-beyond-the-five-standups.md` sections 5 and 6 and is not repeated.

## 1. Four kinds of evidence

| Kind | Model involved | Shows | Does not show |
|---|---|---|---|
| **Code tests** | None | Our checks and date logic do what the documents say, on inputs we construct | Anything about the model |
| **Practice, saved answers** | One recorded answer per day, replayed | The whole pipeline works end to end on the five days; lead edits carry forward | That the model is reliable. A saved answer passes every time by construction |
| **Practice, live** | Live, the week run 3 times | How often the model gets each property right on the five days | Behaviour on unseen transcripts. The prompt was written with these days in view |
| **Held-out, live** | Live, 3 runs, once, after the freeze | Behaviour on transcripts that shaped nothing | Much: four short transcripts |

The first two run with `pytest`, need no key and cost nothing. The last two need a key and are run by hand.

## 2. The headline checks

These are the core tests. Each maps to a known model mistake.

| # | Check | The mistake it targets | What a pass demonstrates | Runs as |
|---|---|---|---|---|
| H1 | As a code test: a change carrying an invented quote is refused. On every model run: **the number of changes refused by check C1 is reported** | Making things up | The code test: an invented item cannot reach the list even when the model produces one. The count: zero refusals is what shows this run invented nothing. "Every applied quote is in the transcript" is true of every run by construction and shows nothing about the model | Code test; a reported number on practice and held-out runs |
| H2 | Every piece of work in the answer key has **exactly one** item at home on it, at the end of each day | Treating a repeat mention as new | The auth bug stayed one item under four names and two closures; "Atlas export" on Wednesday did not become a second item | Practice, saved and live |
| H3 | Owner of the auth item is Dev after Monday. The onboarding item has no owner until Thursday, then Rohan | Giving an item to the wrong person | The model tells offering, raising and noticing apart from owning, and accepts a person not in the team settings | Practice, saved and live |
| H4 | Each of the ten firm pieces of work has an item by the day it first comes up, including the four-word promise on Wednesday | Skipping things | Nothing in the key was missed, down to the smallest commitment | Practice, saved and live |
| H5 | No item is found only by a not-tracked turn; and no item is homeless (belongs to no piece of work in the key) | Making up items from talk that is not an action | The customer reply, the kickoff, the staffing note and the sign-off did not become items | Practice, saved and live |
| H6 | Export: due 20 Oct after Monday, still 20 Oct after Wednesday, 22 Oct after Thursday. Search: no date after Monday or Tuesday. Retry bug: 17 Oct after Thursday, 20 Oct after Friday | Wrong or stale dates | Phrase extraction by the model plus date arithmetic and hedge handling by code | Practice, saved and live; date logic also as code tests |
| H7 | Two runs from Monday's draft. (a) The lead changes the auth item's owner and approves; Tuesday's update to that item changes its ticket and date and leaves the lead's owner in place. (b) The lead removes the onboarding doc item and approves; Thursday's and Friday's updates to it land under not tracked as "removed by lead", and it is not on the list on Friday | Edits not carrying forward | "The reviewed list should carry forward into the next day", on items the later standups do come back to. Removing an item nobody mentions again would pass trivially | Practice, saved only |
| H8 | The prompt template and `src/` contain no word from the practice week | Fitting to the examples | Nothing is wired to this team or these five days | Code test |

## 3. Code tests

Table-driven where the documents give a table. References are to `implementation-details.md`.

| Area | What is tested | Source |
|---|---|---|
| Turn splitting | `Name:` lines, wrapped lines continue a turn, "Rohan's benefit:" is not a speaker, CRLF input, text with no speaker turn stops | models §2 |
| Quote matching | Case, spacing, curly quotes; an ellipsis fails; a quote across two turns fails; the four-word floor; a short whole turn passes; "Sure." alone fails | §3.3 |
| Date steps | One case per cell of the D1–D4 table, with and without an existing date. Every due phrase in the answer key. The untested cases: "next Friday", "Thursday or Friday", "the 24th", "30 October", "end of week", "this afternoon", "tomorrow morning", a weekday said on that weekday, a hedge on a dated item, a condition word | §1.5 |
| Applying changes | Each row of the change-tier table: refused, moved, corrected, flagged, discarded. Unknown status ignored without losing the change. Two updates to one item. A child before its parent. A parent that is itself. Ticket "231" finding PAY-231; no flag against the add's own parent | §3.3 |
| Transitions | Each row of the status, owner and due tables gives the stated label and side effect. Reopen clears the date, and still does when the phrase fails D1 | §1.3–1.5 |
| Lead actions | Edit, remove, approve, discard. Same field edited twice keeps one entry. Reopen by the lead clears the date. Removing a parent unlinks its children. Edit with no draft is refused | §4 |
| Lifecycle | Ids repeat on a re-run and advance only on approval. A failed run leaves the draft. Date order enforced. A second approve is a no-op | §1.1, §6 |
| History | After any sequence of the above, each item's fields equal its history replayed | models §8 |
| Storage | Save and load round trip; a file with another `version` is refused | models §10 |
| LLM layer | Provider choice from the environment, including an empty key. Replay: hit, miss, fingerprint mismatch. With a fake transport: timeout, 5xx, 429, error body, unreadable answer each retried once; 401 not retried; code fence stripped | flow §3 |
| **The key through the code** | The answer key written out as five days of proposed changes and run through the real checks, approving each day. The final list must equal `action-item-rules.md` section 7 field for field | key; gen §6 |

The last row is the strongest code test: it proves that if the model returns the right changes, the code
produces the right week. It also produces the starting list for the held-out standup.

**Cut order.** This table is close to exhaustive and the time for tests is not. If time runs short, tests
are dropped from the bottom of this list, and what was dropped is named in the README.

| Priority | Tests |
|---|---|
| Protected | Date steps; quote matching; the key through the code; the history invariant |
| Next | Applying changes (the change-tier table); lead actions; lifecycle; turn splitting |
| First to go | The LLM transport cases (timeout, 5xx, 429, error body); one test per row of the transition tables; storage |

## 4. The practice week: pieces of work and their anchors

`day.turn`. An asterisk means the anchor is part of the turn, because the turn covers more than one thing.
† = the item's existence depends on a soft rule: it is checked only if present.

| # | Piece of work | Anchor turns |
|---|---|---|
| W1 | Search latency fix | Mon 1*, Tue 1, Wed 1*, Thu 4* |
| W2 | Auth bug, PAY-231 | Mon 2, Mon 3, Mon 4*, Tue 2*, Wed 2*, Thu 3*, Fri 2 |
| W3 | Hermes staging deploy | Mon 5, Mon 6, Tue 4, Wed 4 |
| W4 | Flaky CI test | Mon 7*, Mon 8* |
| W5 | Export | Mon 9, Mon 10*, Tue 5*, Wed 8, Thu 6, Thu 7 |
| W6 | Onboarding doc | Mon 12, Mon 13*, Thu 9, Thu 10*, Fri 6* |
| W7 | Atlas login slow | Tue 2*, Wed 2* |
| W8 † | Review of the PAY-231 PR | Tue 2*, Tue 5*, Wed 2* |
| W9 † | Review of the search PR | Wed 1*, Wed 2*, Thu 3* |
| W10 | Falcon doc to send | Wed 6, Wed 7 |
| W11 | Hermes retry bug, APP-402 | Thu 8, Fri 1* |
| W12 | Retro on PAY-231 | Fri 3 |
| W13 † | Review of the Falcon schema draft | Fri 4*, Fri 5 |
| W14 † | Check of the onboarding draft | Fri 6*, Fri 7 |
| — | Not tracked | Mon 1* (the call), Mon 11, Wed 5, Thu 1, Thu 2, Thu 4* (staffing), Fri 4* (draft is up), Fri 8 |

The exact words for each starred anchor, and which are core and which shared, live in the test file.

Five turns are in no row: Tue 3, Tue 6, Wed 3, Wed 9 and Thu 5. Each is an acknowledgement of a word or two
("Okay.", "Nice.", "Yeah."). An item found only by one of them fails H5 like any not-tracked turn. Every
other turn of the week is in the table; a script checked this against the transcript files.

## 5. Per-day properties

Checked after each day is approved with no edits. Only firm outcomes; `open` and `in_progress` are never
told apart.

| After | Property |
|---|---|
| Mon | W1–W6 each have one home item. W2 owner Dev. W4 and W6 have no owner. W5 due 20 Oct. W1 has no date. W3 is blocked. In the draft, W1 and W4 are marked for the lead |
| Tue | W2 carries PAY-231 and is due 14 Oct. W1 has no date. W3 is still blocked and has **no date**. W5 is due 20 Oct. W7 exists, owner Dev, no date |
| Wed | W2, W3, W7 are done. W1 is still active. W10 exists, owner Arjun, due 15 Oct. W5 is due 20 Oct and still has one home item |
| Thu | W2 is active again, the same item, with no date. W5 is due 22 Oct. W11 exists, owner Sana, APP-402, due 17 Oct. W3 is still done. W6 owner Rohan |
| Fri | W11 is due 20 Oct. W2 is done. W12 exists with no owner and no date. W6 is active, owner Rohan. W10 is still active. W3 and W4 are unchanged from Thursday. Between 10 and 14 items; none homeless |

Always-true properties (gen §5) are checked after every day as well.

## 6. Saved answers and live runs

**How saved answers are made.** Once the prompt is settled, the five days are run live **once** with the
Recorder and the answers committed under `tests/saved_answers/`. They are not edited by hand and not
recorded again in search of a better run; that would be choosing the sample. If the prompt changes
afterwards they are recorded again, once. The test run prints how many saved answers were recorded against
a different prompt or list, so stale ones are visible.

**What is asserted on saved answers.** Two classes, kept apart:

| Class | Checks | If the recording misses one |
|---|---|---|
| Hard | The always-true properties; the pipeline (each day produces a draft, approves, carries over); H7; the key through the code | The test fails. These do not depend on the model being right |
| Model quality | H2 to H6 and the per-day properties of section 5 | The property is marked as an **expected failure** with its reason (for example "recorded run set 15 Oct on the staging deploy from infra's estimate"). `pytest` stays green, the miss is printed, and it is listed in the README |

So a reviewer running `pytest` sees a passing suite and an honest list of what the one recorded run got
wrong. The deterministic all-pass run of the week is the key-through-the-code test, which needs no model.

**What passing on saved answers means.** That the code handles one real answer per day correctly. It says
nothing about how often the model produces such an answer. If the prompt was adjusted until the recorded
run passed, a pass here is partly by construction, and the README will say so.

**Live runs.** A separate script processes the week from an empty state three times and prints, for every
property in sections 2 and 5, how many of the three runs passed, and the number of C1 refusals in each run.
A property at 1 or 2 of 3 is reported as unstable. Three is the smallest number that can show that.

**Extra items.** H5 is strict: any item outside the fourteen pieces of work fails the run, and the report
shows the item with its quotes so a reader can judge it. There is no list of tolerated extras; such a list
could only be written after seeing runs, which would be fitting the check to the output.

**Cost.** Every live run is preceded by a stated estimate and your go-ahead. One pass of the week is five
model calls on about 900 words of transcript plus the prompt and list; three passes is fifteen calls, the
held-out session twelve more.

**What the README will report.**

| Set | Reported as |
|---|---|
| Code tests | Passed / total, and any dropped under the cut order |
| Practice, saved | Hard checks passed / total; model-quality properties passed / total with each expected failure named; the model and date of the recording |
| Practice, live | Each property as N of 3, with model name and date; unstable properties named; C1 refusals per run |
| Held-out, live | Each property as N of 3, as it came out, with any change made afterwards disclosed |
| Not tested | The list in `implementation-details.md` section 9 |

## 7. Commands

| Command | Needs a key | Runs |
|---|---|---|
| `pytest` | No | Code tests and practice on saved answers |
| `python tests/live_check.py --runs 3` | Yes | Practice, live. It sits under `tests/` because it needs the practice week's anchors, which are test data |
| (not built) | Yes | Held-out, after the freeze |

## 8. Settled in review

| Question | Decision |
|---|---|
| Live repeats | Three. No separate "run twice" step: 1 or 2 of 3 already shows instability |
| "No homeless item" | Strict, with the item shown in the report. No tolerated-extras list |
| H7 | Saved answers only |
| Review | Taken up: H1 reports C1 refusals instead of claiming a by-construction pass; saved-answer checks split into hard asserts and expected failures; H7 removes an item that later standups return to; a cut order for the code tests |
