# Data models — everything stored besides the action item

Status: **proposal for review** (second revision, after independent review). No code exists yet.

The action item itself is defined in `action-item-rules.md` section 2. This document covers the other shapes
the system reads, produces and saves, and how they fit together in the one local file. How the parts of the
program pass them around is in `components-and-data-flow.md`.

## 1. How they fit together

```
Team settings ─┐
Standup ───────┼─► model ─► Proposed changes ─► code checks ─► Checked changes ─┐
Current list ──┘                                                                ▼
                                                                    Draft (items + checked changes)
                                                                                │  lead edits, removes
                                                                                ▼
                                                                    Approved day ─► becomes Current list
```

One standup produces one **day record**. A day record is a draft until the lead approves it. Only one draft
exists at a time.

## 2. Standup (the input)

| Field | Meaning | Example |
|---|---|---|
| `date` | The day of the standup. Must be later than the last approved day | 2025-10-16 |
| `text` | The transcript exactly as submitted | |
| `turns` | The text split by code into speaker turns: number, speaker, words | `{n: 3, speaker: "Dev", text: "Hey. Okay, so, bad news…"}` |

**Splitting into turns.** A line starts a new turn only if it begins with a speaker name followed by a
colon and a space. A speaker name is one or two words, letters only, each starting with a capital. Every
other line continues the previous turn, so pasted text with wrapped lines still works. "Rohan's benefit:"
at the start of a wrapped line is not a speaker (apostrophe, lower-case word). Text before the first speaker
line is kept as a turn with no speaker.

A stray "Note:" would still pass as a speaker. So any speaker who is not in the team settings is listed on
the review page as "new speaker", where the lead can see a real newcomer (Rohan) or a mis-split.

## 3. Team settings

A file in the repo (`config/team.json`). It holds only what a different team would change.

| Field | Meaning | Example |
|---|---|---|
| `people` | Name, other names they go by, role | `{name: "Dev", also: ["Devansh"], role: "engineer"}` |
| `glossary` | Terms the model should know | `Hermes: the team's notifications service` |
| `ticket_prefixes` | Prefix and what it is for | `PAY: payments`, `APP: main app` |

Rohan is not in this file. He becomes a known person by speaking on Thursday (check C3).

## 4. Fixed vocabularies (in code)

Kept in one code module as plain data, not in the settings file, because the code's behaviour depends on
the specific entries.

| What | Contents |
|---|---|
| Statuses | Key, label, whether it is closed, and which one a new item starts in. `open` (start), `in_progress`, `blocked`, `done` (closed), `dropped` (closed) |
| Hedge words | The list used by date step D2 |
| Day words | What date step D3 understands: today, tonight, tomorrow, weekday names, written dates |

Adding a status is still one entry in one place.

## 5. Proposed change (what the model returns)

The model's whole answer is `{changes: [...], not_tracked: [...]}`.

| Field | In | Meaning | Example |
|---|---|---|---|
| `kind` | every change | `add` or `update` | `update` |
| `ref` | add | A name for this new item within this answer only, so another add can point at it as its parent | `new1` |
| `item_id` | update | Which existing item | `A5` |
| `fields` | every change | Any of `title`, `owner`, `due_phrase`, `status`, `ticket`, `parent`, `note`. In an update: a value sets, an explicit empty clears, left out means unchanged | `{due_phrase: "Wednesday"}` |
| `quotes` | every change | One to three runs of words from the transcript | `["export is going to slip", "Say Wednesday?"]` |
| `review_reason` | optional | Why a human should look | "Raised, deferred, no decision" |

A `not_tracked` entry is `{quote, reason}`.

This is kept exactly as the model returned it, so that a wrong result can be traced to either the model or
our code.

## 6. Checked change (what code makes of it)

One per proposed change, after the checks in `action-item-rules.md` section 4.

| Field | Meaning | Example |
|---|---|---|
| `proposed` | The proposed change, untouched | |
| `outcome` | `applied`, `could_not_verify` or `discarded` (changed nothing) | `applied` |
| `item_id` | The item it landed on; for an add, the id code just gave it | `A14` |
| `quotes` | Each quote with the turn and speaker code found it in | `{text: "Say Wednesday?", turn: 6, speaker: "Priya"}` |
| `diffs` | What actually changed, field by field | `{field: "due", from: "2025-10-20", to: "2025-10-22"}` |
| `change_labels` | What the page calls it. A list, because one change can do several things | Tuesday's auth update: `[re-dated, updated]` |
| `flags` | Checks or date steps that fired, with the reason | `{rule: "D2", reason: "hedged: 'probably'"}` |
| `failure` | Only when not applied: which check, and why | `{rule: "C1", reason: "quote not found in transcript"}` |

Possible change labels: added, updated, closed, dropped, reopened, reassigned, re-dated.

`diffs` can differ from what the model asked for. The model says `due_phrase: "Wednesday"`; the diff records
both the phrase and the date code worked out. Reopening adds a diff clearing the old date.

**Order of work.** Code first gives an id to every `add` in the answer, then resolves `parent` links. An add
can therefore name a parent that comes later in the same answer.

## 7. Review reasons (how a flag reaches the item)

The item's `needs_review` is not a yes/no. The item holds `review_reasons`, a list, and "needs review" means
the list is not empty. When a change is applied, every flag that fired and the model's own `review_reason`
are added to the list. An item can carry several: "owner 'Rohit' is not a known person" and "hedged:
'probably'".

Approving the day empties the list on every item (section 8 records that).

## 8. History entry (on each item)

An item's history is a list of these, oldest first.

| Field | Meaning | Example |
|---|---|---|
| `date` | Standup date | 2025-10-16 |
| `by` | `model` or `lead` | `model` |
| `action` | For a lead entry: `edit`, `remove` or `approve` | `edit` |
| `diffs` | Same shape as in a checked change | |
| `quotes` | With turn and speaker; empty for a lead entry | |
| `flags` | As above | |

Rules:

- The first entry is the item being added.
- **Every stored change to an item writes an entry**, including the two that are easy to forget: removal
  (a diff setting `removed_on`) and approval clearing review reasons (a diff emptying `review_reasons`,
  written only for items that had some). With that, an item's current fields always equal its history
  replayed in order, and a test checks it.
- **Supporting words** shown on the page come from the most recent entry that has quotes. A lead edit does
  not make them disappear.
- **Editing the same field twice in one review** updates the one lead entry: `from` stays the value the
  system proposed, `to` becomes the lead's latest choice. Counting corrections later is then not skewed by
  the lead changing their mind.
- A lead-set date has no phrase behind it; the edit also clears `due_phrase`.

**There is no separate list of lead actions.** Everything the lead does is in these entries (`by: lead`,
with `action`), plus `approved_at` on the day record. "How often did the lead correct an owner" is a filter
over history entries. This removes a second copy of the same facts that would have to be kept in step.

## 9. Day record

| Field | Meaning |
|---|---|
| `standup` | Section 2 |
| `state` | `draft` or `approved` |
| `model_run` | Provider, model name, when, the raw answer, and the request fingerprint (section 11) |
| `checked_changes` | Section 6, in the order the model gave them |
| `not_tracked` | The model's list, plus anything code moved here ("removed by lead") |
| `new_speakers` | Speakers not in the team settings (section 2) |
| `items_after` | The full list as it stands after this day, including the lead's edits |
| `approved_at` | Set on approval |

`items_after` is a full copy per day, not something rebuilt from histories. The lists are tiny, and a copy
makes "what did the list look like on Wednesday" a lookup.

**When the model call fails** (network error, or an answer that is not in the agreed shape), no draft is
created and the list is untouched. The failure is kept in `last_failed_run` (section 10) with the error and
whatever raw text came back, and the page shows it.

## 10. The saved file

One JSON file, `data/state.json`.

| Field | Meaning |
|---|---|
| `version` | Format number, starts at 1 |
| `next_item_number` | Counter for ids. Moves forward only when a day is approved |
| `days` | Approved day records, oldest first |
| `draft` | The one day record still in review, or empty |
| `last_failed_run` | The most recent failed model call, or empty |

There is no separate "current list". It is `items_after` of the last approved day, and that is what the
model is shown for the next standup. A draft never touches it: approving appends the draft to `days`;
running the same day again replaces `draft`.

**Ids stay put when a day is run again.** A draft numbers its new items from `next_item_number` without
moving the counter. Running Monday a second time gives A1, A2, … again, not A7 onward. The counter moves
only on approval, so an approved id is never reused, including for removed items.

Removed items stay in `items_after` with `removed_on` set. They are hidden on the page and shown to the
model in a separate "removed by the lead, do not add again" list.

Two stored fields on the item that the rules document does not list: `created_on` (standup date it was
added) and `removed_on` (empty unless the lead removed it).

## 11. Saved model answer (for running without a key)

| Field | Meaning |
|---|---|
| `date` | The standup date; this is what replay looks an answer up by |
| `request_fingerprint` | A short hash of exactly what was sent to the model when the answer was recorded |
| `provider`, `model`, `recorded_at` | Where the answer came from |
| `answer` | The raw answer |

Stored under `tests/saved_answers/`, one file per date.

Replay returns the saved answer for the date. If the fingerprint of today's request differs from the
recorded one, it still returns the answer and the page shows a warning: "recorded against a different list
or prompt". This matters for the no-key demo: the reviewer fixes an owner on Monday, which changes what
Tuesday sends, and replay must keep working. The usual effect of a mismatch is harmless (the saved answer
refers to the same ids); the warning is there for the case where it is not.

## 12. Settled in review

| Question | Decision |
|---|---|
| Full copy of the list per day | Yes |
| Statuses and hedge words | In code, one data module. `team.json` holds people, glossary, ticket prefixes only |
| Replay matching | By date. Fingerprint kept; a mismatch shows a warning, it does not stop |
| Independent review, 12 points | All taken up: ids stable across re-runs (section 10), every stored change writes history (section 8), supporting words survive a lead edit, `ref` / `change_labels` naming, turn splitting (section 2), review reasons as a list (section 7), turn number in the example, parent order (section 6), date order (section 2), repeat edits (section 8), failed runs (section 9), lead action list replaced by history entries (section 8) |
