# Implementation details — contracts, transitions and edge cases

Status: **proposal for review** (second revision: contradictions and open questions now decided). No code
exists yet.

This document turns the five approved design documents into contracts an engineer can code against. Writing
it exposed 16 places where those documents disagreed and 12 where they were silent. Each is listed with the
decision taken, in section 10 (**[X n]**) and section 11 (**[O n]**), and the source documents have been
corrected to match. The references are kept in the text so a reader can see which contracts came from a
decision made here.

Abbreviations: **rules** = `action-item-rules.md`, **models** = `data-models.md`, **flow** =
`components-and-data-flow.md`, **gen** = `generalisation-beyond-the-five-standups.md`, **key** =
`answer-key-five-standups.md`.

## 0. Terms that look alike and are not

| Term | Means | Not to be confused with |
|---|---|---|
| **Dropped** | A status. The team cancelled real work. Item stays visible, can be reopened | **Removed**: a lead-only act meaning "never an item". Item hidden, `removed_on` set, never re-added. **Discarded** (change): an update that altered nothing. **Discarded** (draft): the lead threw the whole day away |
| **Closed** | `done` or `dropped` | **Done**: one of the two closed statuses |
| **Reopened** | Closed → active | **Unblocked**: `blocked` → another active status. No date effect |
| **Not tracked** | Something heard that is deliberately not an item | **Could not verify**: a proposed change the checks refused |
| **Flag** | A record on one checked change that a check or date step fired | **Review reason**: text on the item, accumulated from flags and the model, cleared at approval. **Failure**: why a change was not applied. **Note**: a day-level remark from the LLM layer |
| **Change label** | What a change did, derived from its diffs | **Status**: a stored field |
| **Hedged** (D2) | The speaker was unsure; an existing date is cleared | **Unpinned** (D4): no computable day; an existing date is cleared. **Phrase error** (D1): the model's mistake; an existing date is kept |
| **Retry** | A second model call inside one run | **Re-run**: the lead resubmits a date still in draft. **Replay**: an LLM implementation that returns saved answers |
| **Lookup key** | Names a saved answer: date + hash of parsed turns | **Fingerprint**: hash of the full request; detects that the list or prompt changed |
| **Known person** (C3) | In team settings, or speaks today, or already owns an item | **New speaker**: a speaker not in team settings who has not spoken on any approved day [O 2] |
| **Draft id** | Provisional: a re-run may give the same number to a different item | **Approved id**: permanent, never reused |
| **Firm / soft** | Whether tests may assert a rule's outcome | Whether code enforces it (section 5) |

## 1. State transitions

### 1.1 Day record

| From | Event | To | Effect on saved state |
|---|---|---|---|
| none | Submit succeeds | draft | `draft` set; `days`, counter untouched |
| none | Submit fails (any step before save) | none | Only `last_failed_run` written |
| draft (date D) | Submit date D again, confirmed, succeeds | draft | `draft` replaced; lead edits on the old draft are gone [X 2] |
| draft (date D) | Submit date D again, fails | draft | Old draft kept; `last_failed_run` written |
| draft (date D) | Submit any other date | draft | Rejected before the model is called |
| draft | Lead edit / remove | draft | Draft items and histories change |
| draft | Approve | approved | Appended to `days`; `draft` emptied; counter advanced past the highest id in the draft |
| draft | Discard | none | `draft` emptied; nothing else changes [X 2] |
| approved | anything | approved | Immutable. No edit, no re-run, no un-approve |

### 1.2 Item existence

| Stage | Where it lives | Id |
|---|---|---|
| Proposed | Only in `draft.items_after` | Provisional |
| Approved | `items_after` of an approved day and every later day | Permanent |
| Removed | Same, with `removed_on` set. Hidden on the page, listed to the model as removed | Permanent; not reused |

There is no un-remove. Before approval the only way back is discard or re-run.

### 1.3 Status

The status set and the closed flag come from `vocab`. Any status may move to any other. The label depends
only on the closed/active class of the two ends, except where stated.

| From | To | Label | Side effect |
|---|---|---|---|
| (no item) | any | added | Status defaults to `open` when the add gives none |
| active | `done` | closed | None |
| active | `dropped` | dropped | None |
| `done` | `dropped` | dropped | None |
| `dropped` | `done` | closed | None |
| closed | active | reopened | Due date cleared unless this same change sets one through D3. It has to be a real reopen of an item closed on an earlier day, not the undoing of a close made today by the model or by the lead. The baseline is the status before the lead's own first status edit in this review if there is one, otherwise the status when the day began; the date is cleared only if that baseline is closed. So the lead setting back an item the model wrongly closed today keeps its date. The reopen rule wins over D1: a reopen whose phrase is not in the quotes still clears the date [X 5] |
| `open` ↔ `in_progress` | | updated | None |
| `open` / `in_progress` | `blocked` | blocked [O 1] | None |
| `blocked` | `open` / `in_progress` | unblocked [O 1] | None. The model is told to use `in_progress` for work that is unblocked and unfinished [X 9] |
| any | same | (no diff) | |

The same table applies whether the model or the lead makes the change; both go through `items`.

### 1.4 Owner

Owner names are canonicalised before comparison: matched case-insensitively against each person's `name`
and `also`, and replaced by `name`. An unmatched name is kept as given.

| From | To | Label | Check |
|---|---|---|---|
| none | B | picked up [O 1] | C3 on B |
| A | B | reassigned | C3 on B |
| A | none | unassigned [O 1] | None |
| A | A (after canonicalising) | (no diff) | |

### 1.5 Due date and phrase

The model never sets `due`. It sets `due_phrase`, and code derives both fields. For a change, exactly one
row below applies.

| The change's `due_phrase` is | Item had no date | Item had a date |
|---|---|---|
| Left out | Nothing | Nothing |
| Explicitly empty (update only) | `due_phrase` cleared | `due` and `due_phrase` cleared. No review reason |
| Present, **D1**: not inside any quote of this change | Nothing stored. Review reason "date phrase not in the quoted words" | Same; **existing date kept** |
| Present, **D2**: hedge or condition word in the sentence, or two different days in the phrase | `due_phrase` := phrase. Review reason | `due` cleared, `due_phrase` := phrase. Review reason |
| Present, **D3**: one computable day, no day-shifting word | `due` := date, `due_phrase` := phrase | `due` := date, `due_phrase` := phrase. If the date equals the one already held, neither `due` nor `due_phrase` changes [X 4] |
| Present, **D4** with a day or a day-shifting word in the phrase ("next Friday", "next week", "after this") | `due_phrase` := phrase. No review reason | `due` cleared, `due_phrase` := phrase. Review reason "date no longer pinned" |
| Present, **D4** with neither ("soon", "at some point", but also "in two days", "end of month") | `due_phrase` := phrase. No review reason | `due` and `due_phrase` kept. Review reason "timing mentioned, date unchanged", because code cannot tell vague talk from a real re-date it does not understand |

Labels: none → date = dated; date → different date = re-dated (earlier or later alike); date → none = date
cleared [O 1] [X 3].

Order inside D1–D4 is fixed: first match wins. Definitions the steps need:

| Term | Definition |
|---|---|
| Sentence | In the turn where the quote was found, the span containing the phrase's first occurrence inside that quote, bounded by `.`, `?`, `!` or the turn's ends |
| Word match | Case-insensitive, whole words. "worst case" is matched as two adjacent words |
| D2 words | Scanned over the **sentence**: maybe, probably, perhaps, possibly, might, hopefully, worst case, if, once, unless |
| Two days | The **phrase** (not the sentence) contains two day expressions that resolve to different dates |
| Stand-alone forms | Checked **first**, on the whole phrase: "this morning", "this afternoon", "this evening", "end of day" resolve to the standup date |
| Time-of-day words | Then removed from the phrase: morning, afternoon, evening, after lunch. So "tomorrow morning" becomes "tomorrow" |
| Day-shifting words | Scanned over the **phrase** after time-of-day removal: next, last, previous, after, following, before, week, or |
| Computable day | today, tonight → standup date. tomorrow → standup date + 1. A weekday name → the first such day strictly after the standup date ("Friday" said on a Friday is 7 days on). A written date: a day number with a month name in either order ("17 October", "Oct 17"), with or without a year, or `YYYY-MM-DD`. With no year it is the first such date on or after the standup date. Numeric forms like 10/11 are not computable [O 5] |
| Arithmetic | Calendar days. Weekends are not skipped: "tomorrow" on a Friday is Saturday [O 5] |

### 1.6 Other fields

| Field | Change | Label |
|---|---|---|
| `title`, `note`, `ticket`, `parent`, `due_phrase` alone | any diff | updated |
| `review_reasons` | reason appended | none; shown as a badge (section 2) |
| `review_reasons` | emptied at approval | none; history entry `by: lead, action: approve` |
| `removed_on` | set by lead | removed |
| `parent` | cleared because the parent was removed | updated; history entry on the child with `by: lead, action: remove` [O 9] |

### 1.7 One change, several effects

A checked change carries the list of every label its diffs produce. Tuesday's update to the auth item sets
ticket, date and status: `[dated, updated]`. An update that reopens and re-dates: `[reopened, re-dated]`.
The page shows one row per item with the union of labels from all of that item's applied changes today.

Within one change, fields are applied in this order, because later steps read earlier results:
owner → ticket → due (D1–D4) → status (reopen rule reads the due result) → title, note → parent.

## 2. Flags and badges

| Badge | On | Stored or derived | Appears when | Goes away when |
|---|---|---|---|---|
| Change labels (§1) | Item row, today | Stored in the checked change; recomputable from diffs | A change is applied | The day is no longer the one shown |
| Needs review + reasons | Item | Stored: `review_reasons` | Any flag below fires on an applied change, or the model supplies `review_reason` | Approval, and only approval. Fixing the field a reason is about does not clear it [O 3] |
| Overdue | Item | Derived | `due` strictly earlier than the standup date of the day shown, and status active. The clock is not used [O 10] | Never stored |
| Blocked | Item | Derived from status | Status is `blocked` | Status changes |
| Possible duplicate of *id* | Item | A review reason (C4) | An add's ticket matches another item's, and that item is not the add's parent [O 6] | Approval |
| Could not verify | Proposed change | Stored: `outcome`, `failure` | C1 or C2 fails | Permanent on that day record |
| New speaker | Day | Stored: `new_speakers` | A speaker is not in team settings and has not spoken on any approved day [O 2] | Permanent on that day record |
| Saved answer | Day | Derived from `model_run.provider` | Provider is Replay | |
| Recorded against a different list | Day | Stored: LLM response `notes` | Replay hit, fingerprint differs | Permanent on that day record |
| Draft / Approved | Day | Stored: `state` | | |

Flags that create review reasons, and their source:

| Source | Reason text (fixed prefix) | Raised by |
|---|---|---|
| C3 | owner '*name*' is not a known person | Code |
| C4 | possible duplicate of *id* | Code |
| C5 | parent link dropped: *why* | Code |
| D1 | date phrase not in the quoted words | Code |
| D2 | hedged: '*word*' / conditional: '*word*' / two days named | Code |
| D4 with prior date | date no longer pinned: '*phrase*', or timing mentioned, date unchanged: '*phrase*' | Code |
| Model | free text from `review_reason` | Model |

Rules U3 (undecided), U20 (conditional, apart from the date) and "two owners named" [X 11] have no code check.
Their review reason exists only if the model supplies one.

## 3. Validation and failure handling

Three tiers. A failure in one tier never reaches the next.

### 3.1 Request tier — before the model is called

| Condition | Result |
|---|---|
| Date missing or not `YYYY-MM-DD` | Rejected with a message |
| Date not later than the last approved day | Rejected |
| A draft exists for a different date | Rejected: approve or discard it first |
| A draft exists for the same date | Needs confirmation; then proceeds as a re-run |
| Text empty, or no line starts a speaker turn | Rejected; nothing sent |
| Provider is the chat API and `LLM_API_KEY`, `LLM_BASE_URL` or `LLM_MODEL` is empty | Rejected with a message naming the setting |
| Provider is Replay and no saved answer has this lookup key | Rejected: "No saved answer for this transcript…" |

The date is not compared with the clock. A 2025 transcript is accepted in 2026.

### 3.2 Answer tier — the whole answer

A whole-answer failure costs the lead the entire run, so it is kept for answers that cannot be read at all.
A slip inside one change is handled in §3.3 and costs only that change or that field.

| Condition | Result |
|---|---|
| Timeout (180 s) or HTTP 5xx | One retry, same request |
| HTTP 429 | One retry after a pause: the `Retry-After` value if the provider gives one, capped at 30 seconds; otherwise 5 seconds |
| HTTP 200 with an empty body, or a body that carries an error instead of an answer | Treated as a provider error: one retry, same request |
| Other HTTP error (401, 402, other 4xx) | Fails at once, no retry |
| After stripping a surrounding code fence, and trying the text between the outer braces if the whole is not JSON: still not JSON, not an object, or no `changes` list | One retry, with the validation error appended to the request |
| Second attempt fails for any reason | Run fails. No draft. `last_failed_run` holds the error and the raw text of both attempts [O 8] |

Tolerated without failing: keys the shape does not name (ignored), a missing `not_tracked` (treated as
empty), a missing `ref` on an add (§8.1).

### 3.3 Change tier — each proposed change

Processing is two passes. **Pass 1**, over all changes in answer order: C1, then C2, then an id for each add
that passed [X 6]. **Pass 2**, in answer order: the field steps of §1.7, then the no-op test.

| Condition | Class | Result |
|---|---|---|
| A quote is not found inside one turn | Rejected | `could_not_verify`, C1 |
| No quote meets the length rule | Rejected | `could_not_verify`, C1 |
| Zero quotes | Rejected | `could_not_verify`, C1 |
| More than three quotes | Accepted | All are checked; the limit is guidance to the model [O 11] |
| `update` names an id that does not exist | Rejected | `could_not_verify`, C2 |
| `update` names a removed item | Moved | Outcome `not_tracked`, reason "removed by lead"; listed with the day's not-tracked entries [X 1] |
| A change that is not well formed: not an object at all, `kind` not `add` / `update`, an update with no `item_id`, an add with no title, `fields` not an object, `quotes` not a list of text | Rejected | `could_not_verify`, reason "malformed change" |
| `status` not in the vocabulary, or explicitly empty in an update | Corrected | That field is ignored; the rest of the change applies; marked for the lead [O 11] |
| `title` explicitly empty in an update | Corrected | Field ignored; marked for the lead [O 11] |
| A field whose value is not text (a list, a number, an object) | Corrected | Field ignored; marked for the lead. Never stored as text. Two exceptions: a one-name list for `owner` is read as that name, and a number for `ticket` as its digits. A list of several owners gives the reason "more than one owner named" and no owner [X 11] |
| `not_tracked` is not a list | Corrected | Treated as empty |
| Owner not a known person | Flagged | Applied as given |
| Owner is another name of a known person | Corrected | Canonical name stored; no flag |
| Add's ticket matches another item's (approved, or added earlier in this answer) | Flagged | Applied; "possible duplicate of *id*". **Not** flagged when that item is the add's own parent [O 6] |
| Add's ticket matches a removed item's | Moved | Outcome `not_tracked`, reason "removed by lead" [O 6] |
| An update sets a ticket another item holds | Accepted | No check; C4 covers adds only [O 6] |
| Ticket is a bare number | Corrected | Replaced by the one existing ticket ending in that number, if exactly one; otherwise kept as given [O 6] |
| `parent` is itself, unknown, removed, or a `ref` whose add was not applied | Flagged | Applied without the link |
| Due phrase cases | See §1.5 | |
| After all steps, no stored field differs | Discarded | `discarded`; not shown; no history entry [X 4] |
| A `not_tracked` entry's quote is not found in the transcript | Flagged | Still listed, marked "quote not found" [O 7] |

Quote matching (C1): both sides are lower-cased, runs of whitespace collapsed, and curly quotes and
apostrophes straightened; nothing else is normalised. The quote must then appear in one turn's words as whole words: it
cannot start or end in the middle of a word. A possessive counts as a word end, so "Wednesday" is found in
"Wednesday's fine". The same matching is used to find a due phrase inside its quote. An ellipsis in
a quote therefore fails. A quote is "four words or longer" by whitespace count after normalising; it is "a
whole turn" if it equals the turn's words ignoring leading and trailing punctuation, and that turn has two
words or more. If a quote occurs in several turns, the first turn is taken for speaker and turn number.

A quote may support more than one change (the key does this on Wednesday and Friday). A turn with no
speaker, text before the first speaker line, is a valid place for a quote; its speaker is empty.

## 4. Input handling

| Topic | Case | Behaviour |
|---|---|---|
| Ordering | Standup dates | Strictly increasing across approved days. Gaps are allowed. No backfill |
| Ordering | Changes in an answer | Applied in the order given. Two updates to one item both apply; on a conflicting field the later wins. Each writes its own history entry |
| Ordering | Ids for adds | Counter order, in answer order, for adds that pass pass 1 |
| Ordering | Parent links | Resolved after all ids exist, so a child may precede its parent in the answer |
| Retries | Model call | §3.2. Never more than two attempts |
| Retries | After a failed run | The lead resubmits. Nothing was saved except `last_failed_run`, so it is a fresh run |
| Duplicates | Same date and transcript resubmitted while in draft | A re-run. With Replay the result is identical; live, it may differ |
| Duplicates | Same transcript submitted under a later date after approval | Accepted as a new day. Not detected |
| Duplicates | Double submit of Approve | The second finds no draft: message, no change |
| Duplicates | Two adds for the same work in one answer | Detected only if both carry the same ticket: the second is flagged [O 6] |
| Duplicates | An add for work already on the list | Detected only by ticket (C4). Otherwise the model's responsibility (section 9) |
| Invalid | Edit or remove with no draft, or on an id not in the draft, or on a removed item | Rejected with a message |
| Invalid | Edit with a status not in the vocabulary, or a date not `YYYY-MM-DD` | Rejected |
| Invalid | Edit with an owner name | Any text is accepted. The input offers the known people (an HTML datalist) and takes free text. A typed name is canonicalised if it matches a known person and is never flagged: the lead is the authority [O 4] |
| Conflicts | Lead edit after the model's change, same field, same draft | The lead's value stands. One lead history entry per field per review; its `from` is the value the system proposed |
| Conflicts | Lead sets a date on an item that was closed in the approved list, then reopens it | The reopen clears the date. The lead sets it again |
| Conflicts | Lead closes an item by mistake, then sets it back | Nothing is lost: date and phrase stay, and no correction is recorded |
| Conflicts | Lead reopens an item that was closed on an earlier day, through a form that also posts its existing date | The date is cleared: an unchanged date is not "setting a date". The page must show that the date went, so the lead does not assume it was kept (for M4) |
| Conflicts | An edit form posts owner, date and status together | Only the values that differ from the current ones count. An unchanged date keeps its phrase |
| Conflicts | The model contradicts a value the lead set on an earlier day | Applied like any change: it needs a quote from today. No field is locked |
| Conflicts | A saved answer refers to an id the current list lacks | C2, could not verify, plus the "different list" note |
| Conflicts | Two browser tabs | No locking. The last write wins. Stated limit |

## 5. Deterministic logic versus model judgment

| Decision | Decided by | Code's part |
|---|---|---|
| Whether something said is an action | Model | None |
| Which existing item a mention refers to | Model | C2 that the id exists; C4 when a ticket repeats |
| Whether work is new or already on the list | Model | C4 only |
| Who owns it | Model | Canonical name; C3 |
| Which words name the due day | Model | D1 that they are inside a quote |
| What date those words mean | Code | Entirely (§1.5). The model's opinion is never used |
| Whether the date is too unsure to keep | Code, from the sentence | Entirely. The model must still return the phrase |
| Whether a day belongs to this work or to someone else's | Model | None |
| Status | Model | Vocabulary membership; reopen side effect |
| Whether to mark for the lead | Both | Code for C3, C4, C5, D1, D2, D4; model for everything else |
| Which words support the change | Model | C1 entirely: existence, single turn, length |
| Who said them | Code | From the turn |
| Item ids, labels, history, diffs | Code | Entirely |
| Whether a change is a no-op | Code | Entirely |
| Parent link | Model | C5 |
| What is not tracked | Model | Listing only [O 7] |
| Expanding "everything of hers" into items | Model | None. This is the one place the model compares dates: it picks the person's active items due before the new date. Code cannot tell a group roll-over from an ordinary re-date, so it does not second-guess [X 8] |

## 6. Persistence and lifecycle

| Thing | Stored or derived | Where / from what |
|---|---|---|
| Item fields | Stored | `items_after` of each day |
| Item history | Stored | On the item. Fields must equal history replayed |
| Current list | Derived | `items_after` of the last approved day; empty before the first |
| Closed / active, needs review, overdue | Derived | Status + `vocab`; `review_reasons`; `due` + shown day's date |
| Change labels | Stored, recomputable | Checked change |
| Supporting words for an item | Derived | Most recent history entry that has quotes [X 7] |
| Proposed changes, raw answer | Stored verbatim | Day record |
| Id counter | Stored | Advanced only on approval |
| Lead correction counts | Derived | History entries with `by: lead` |
| Team settings, prompt template, vocabularies | Not in state | Repo files |
| Anchors, homes | Not in the product | Tests only |

What each event writes:

| Event | Writes |
|---|---|
| Submit, success | `draft` |
| Submit, failure | `last_failed_run` |
| Lead edit / remove | `draft` |
| Approve | `days`, `draft`, `next_item_number` |
| Discard | `draft` |
| `reset` (command line only) | Deletes the file |

Every write replaces the whole file through a temporary file and a rename.

Reprocessing:

| Case | Behaviour |
|---|---|
| Re-run a draft day | New model call (or replay). Starts again from the last approved list. Draft ids are reissued from the same counter value and may land on different items. Lead edits are lost [X 2] |
| Re-run an approved day | Not possible |
| Start the week again | `reset`, then submit from the first day |
| Replay after the lead edited an earlier day | Same lookup key, so the saved answer is returned; fingerprint differs, so the note is shown; any id the answer names that no longer fits fails C2 |

## 7. Business rules — conditions and edge cases

Rules U1–U21 in the rules document stand as written. This section adds the conditions and edge cases that
decide what code does.

| # | Condition | Behaviour |
|---|---|---|
| B1 | An add gives no status | `open` |
| B2 | An add gives a closed status | Applied. Code does not enforce U10 ("already done is not an item"); that is the model's rule [O 12] |
| B3 | An update changes only `note` or only `status` | A real change: applied, labelled, shown. "No change" in the answer key means no date change [X 10] |
| B4 | A closed item receives a due phrase without a status change | Date steps run as normal. A closed item may hold a date; it is never overdue |
| B5 | A reopen whose due phrase resolves by D3 | Reopened with the new date |
| B6 | A reopen whose due phrase hits D2 or D4 | Reopened, no date |
| B7 | A reopen whose due phrase hits D1 | Reopened, old date cleared, and the D1 review reason added. The reopen rule wins [X 5] |
| B8 | A reopen with no due phrase | Reopened, old date cleared, old phrase cleared with it |
| B9 | `done` → `dropped`, or the reverse | Not a reopen; date kept |
| B10 | The lead removes an item that other items name as parent | Each child keeps everything except the link |
| B11 | The lead removes an item added in this same draft | It stays in the draft with `removed_on`; its id is consumed at approval |
| B12 | The model adds an item the lead removed earlier, with no ticket | Applied as a new item. Nothing in code can tell (section 9) |
| B13 | The model adds an item whose ticket matches a removed item's | Not applied; listed under not tracked as "removed by lead" [O 6] |
| B14 | An owner is named who is not known | Stored as given, marked for the lead. From then on that name is an existing owner, so it is known |
| B15 | The lead sets a date different from the current one | `due_phrase` cleared. No review reason. A past date is accepted and shows as overdue |
| B16 | Approval | Clears every `review_reasons` list; writes a history entry only on items that had reasons. Could-not-verify changes stay on the day record and are not carried forward |
| B17 | Approval of a draft with no applied changes | Valid. The day is recorded; the list is unchanged |
| B18 | A speaker absent from team settings speaks on several days | Listed as a new speaker on the first day only. From the second day the name is found among the speakers of approved days [O 2] |
| B19 | Phrase "this Friday" | "this" is not a day-shifting word: treated as "Friday" |
| B20 | Phrase "Friday" said on a Friday | Seven days on, by U6. "today" is the way to say the standup date |
| B21 | A weekday phrase in a re-date resolves to a date earlier than the item's current date | Applied. A date may move earlier |
| B22 | A group statement ("everything of hers rolls to Monday") | The model emits one update per item. Code treats each independently and discards any that change nothing |

## 8. Model structure

### 8.1 The answer

```json
{
  "changes": [
    {
      "kind": "add",
      "ref": "new1",
      "fields": {
        "title": "…", "owner": "…", "due_phrase": "…", "status": "open",
        "ticket": "…", "parent": "A2 or new2", "note": "…"
      },
      "quotes": ["…", "…"],
      "review_reason": "…"
    },
    {
      "kind": "update",
      "item_id": "A5",
      "fields": { "due_phrase": "Wednesday" },
      "quotes": ["…"]
    }
  ],
  "not_tracked": [ { "quote": "…", "reason": "…" } ]
}
```

| Field | Add | Update |
|---|---|---|
| `kind` | Required | Required |
| `ref` | Optional. Needed only if another add names this one as its parent. If two adds share a `ref`, a parent naming it is treated as unknown (C5) | Ignored |
| `item_id` | Ignored | Required |
| `fields.title` | Required, not empty | Optional |
| `fields.*` other | Optional; left out and empty mean the same | Optional; left out = unchanged, `null` or an empty string = clear, value = set |
| `quotes` | Required | Required |
| `review_reason` | Optional | Optional |

`changes` is required and may be an empty list; `not_tracked` may be left out. An answer with no changes is
valid and produces a draft with no changes. Keys not named here are ignored wherever they appear.

### 8.2 What the model can and cannot set

| The model sets | The model never sets |
|---|---|
| `title`, `owner`, `status`, `ticket`, `note` | `id` |
| `due_phrase` | `due` |
| `parent` (an id or a `ref`) | `history`, `created_on`, `removed_on` |
| One `review_reason` per change | `review_reasons` as a list; it cannot clear them |
| Quote text | Speaker, turn number |
| | Change labels, flags, outcomes |

The model cannot remove an item, and cannot target a `ref` with an update.

### 8.3 Fixed before the model is called

| Input | Rule |
|---|---|
| The list shown | `items_after` of the last approved day. Never the draft, even on a re-run |
| Per item | id, title, owner, status, due, due phrase, ticket, parent, note. No history, no review reasons |
| Removed items | A separate list: id and title only |
| Closed items | Included, all of them, indefinitely |
| Turns | Numbered from 1, with speaker |
| Date | The standup date and its weekday |
| Team facts | People with other names and roles, glossary, ticket prefixes |
| Instructions | The template with team facts filled in. Identical for every day |
| Temperature | Not sent, unless `LLM_TEMPERATURE` is set |
| Lookup key | Standup date + short hash of the turns (speaker and words, whitespace collapsed) |
| Fingerprint | Hash of the instructions, the input text and the answer shape, as first sent. Not the model name, so switching models does not raise the "different list" note [O 8] |

## 9. Known limitations — what code cannot validate, and how it is tested instead

"Practice" = per-case properties on the five days, on saved answers and on repeated live runs. "Held-out" =
the set run once after the freeze (gen §6). "None" = stated in the README only.

| Cannot be validated mechanically | Consequence if the model errs | Tested by |
|---|---|---|
| That a quote supports the change it is attached to. C1 proves the words were said, not that they mean this | A real quote under a wrong change passes every check | Practice: owner, date and status of each anchored item |
| That an item was not skipped | Nothing appears; no signal at all | Practice: every piece of work in the key has exactly one item at home |
| That an add is not a duplicate, when no ticket is involved | Two items for one piece of work | Practice: the home-uniqueness check; the Wednesday "Atlas export" turn |
| That the owner is the right known person | Wrong name, no flag | Practice: owner of the auth, onboarding, PR-review items |
| That a day belongs to this work (U12) | A real date on the wrong item | Practice: the Tuesday cert line |
| That the phrase is complete ("Friday" for "next Friday", one day of two) | A wrong date, no flag | Code tests cover the whole phrase; the shortened one is held-out only |
| That an undecided or conditional item gets marked (U3, U20) | Item present, not marked | Practice: flaky test item marked. Held-out: conditional |
| That a group statement reached the right items (U17) | Wrong items moved, or none | Practice: Friday roll-over |
| That something already done or a scheduled meeting is not added (U10, U11) | Extra items | Practice: no item found by those turns |
| That a removed item with no ticket is not re-added | It returns as new | None |
| Status accuracy between `open` and `in_progress` | Soft; either is accepted | Not tested |
| Hedges outside the word list, or not in English | Date set from an unsure sentence | None |
| A mis-split line treated as a speaker ("Note:") | A bogus known person | Code test for the splitter; the new-speaker badge for the rest |
| Model behaviour on a list of dozens of items | Unknown | None |

## 10. Contradictions found between the existing documents, and the decision on each

| # | Where | Disagreement | Decision |
|---|---|---|---|
| X 1 | Rules C2 vs rules §6 and models §9 | An update aimed at a removed item: "could not verify" in one place, "not tracked, removed by lead" in two | Not tracked. Checked changes gain a fourth outcome, `not_tracked` |
| X 2 | Rules §6, PLAN R20 vs flow §4.2 | "Everything the lead does is recorded" against edits being lost on discard and re-run | The promise covers approved days. Edits on a draft that is discarded or re-run are gone |
| X 3 | Models §6 example | A first date labelled `re-dated` | A first date is `dated` |
| X 4 | Rules §4 vs the key | "Still Monday" resolves to the date already held but changes the stored phrase, so it was not a no-op | When D3 yields the date already held, neither field changes |
| X 5 | Rules §4 reopen rule vs D1 | A reopen whose phrase fails D1: keep the date, or clear it | The reopen rule wins: cleared |
| X 6 | Models §6 vs rules C5 | Whether a refused add consumes an id | Ids only for adds that pass C1 |
| X 7 | Rules §2 vs models §8 | Supporting words from "the most recent change" or "the most recent entry that has quotes" | The most recent entry that has quotes |
| X 8 | Rules U17 vs "the model does no date arithmetic" | U17 has the model pick items due before the new date | U17 stands. It is the one place the model compares dates |
| X 9 | Gen G25 vs rules | "Unblocked goes back to in progress" cited rules that did not say it | Added to rules U18 |
| X 10 | Key, Tuesday and Wednesday, vs rules | "A5: nothing" read as if a note or status update were wrong | Key reworded: no date change |
| X 11 | Gen G4 vs rules §2 | Two owners named: the rules did not say what the owner field holds | No owner, marked for the lead |
| X 12 | Models §12 vs §11 | "Replay matching: by date" | Row corrected: date plus a hash of the turns |
| X 13 | Rules §8 | Settled rows cited an earlier check numbering | Rows corrected |
| X 14 | Gen §5 vs models §10 | "The list never loses an item except by removal" | Reworded: an approved id never disappears |
| X 15 | PLAN layout vs models §3 | No `config/` folder in the layout | Added |
| X 16 | Rules U20 vs rules §3 | U20 said the model returns the date expression "condition included"; §3 says conditions need not be in the phrase | U20 corrected to match §3 |

## 11. Questions the documents did not answer, and the decision on each

| # | Question | Decision |
|---|---|---|
| O 1 | Change labels beyond those in the documents | All used: added, updated, closed, dropped, reopened, picked up, reassigned, unassigned, dated, re-dated, date cleared, blocked, unblocked, removed |
| O 2 | Is a speaker outside team settings "new" every day | First day only |
| O 3 | Does fixing a field clear the review reason about it | No. Only approval clears |
| O 4 | Owner edit on the page | One input: suggests known people, accepts free text. Never flagged |
| O 5 | Written dates and weekends | Day number with month name in either order, optional year, or `YYYY-MM-DD`. No year: first such date on or after the standup. Numeric forms give no date. Calendar days; weekends not skipped |
| O 6 | Ticket matching | No flag when the matching item is the add's parent. A match with a removed item moves the add to not tracked. Adds only. Compared against approved items and earlier adds in the same answer. A bare number with no match is stored as given |
| O 7 | Is a `not_tracked` quote checked | Yes. An unfound one is still listed, marked "quote not found" |
| O 8 | Retried calls, fingerprint, failed runs, file version | Both attempts kept in `model_run.attempts`. Fingerprint covers instructions, input and answer shape, not the model name. `last_failed_run` is cleared by the next successful submit. A state file whose `version` is not 1 is refused with a message |
| O 9 | History entry on a child when its parent is removed | `by: lead, action: remove`, with a diff on `parent` |
| O 10 | "Overdue" relative to what | The standup date of the day shown. Equal is not overdue |
| O 11 | An update with an empty or unknown `status`, or an empty `title`; more than three quotes | Field ignored, rest of the change applies, marked for the lead. All quotes are checked |
| O 12 | Should code refuse an add that arrives already closed | No |
