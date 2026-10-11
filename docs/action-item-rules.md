# Action item rules — what an item is and how a standup changes the list

Status: **approved**, with corrections from `implementation-details.md` sections 10 and 11 applied. No code exists yet.

This document says what an action item is, what the model is asked to produce, how that output is checked,
and what the system does when the conversation is unclear. Components, storage and the LLM interface are in
`components-and-data-flow.md`; the checks we automate are in `evaluation-checks.md`.

## 1. The idea

The model does not write the list. It reads today's transcript and the current list, and proposes
**changes**: "add this item", "update item A5". Every change carries the exact words from the transcript
that justify it. Ordinary code checks each change and applies it to a **draft**. The lead reviews the draft,
corrects it, and approves. The approved list is what the model sees tomorrow.

Example, Thursday. Proposed change: *update A5 (Export feature): due phrase "Wednesday"*, supported by two
quotes:

- Priya: "export is going to slip"
- Priya: "Say Wednesday?"

Code works out that "Wednesday", said on Thursday 16 October, is 22 October. The page shows "A5 re-dated:
Mon 20 Oct → Wed 22 Oct" with those words under it.

Why this shape:

- A repeat mention has to point at an existing item, so it is harder for it to become a duplicate.
- "What changed today" is exactly the list of changes; nothing has to be compared afterwards.
- Each change is small enough to check with code and to test.

## 2. An action item

| Field | Meaning | Example |
|---|---|---|
| `id` | Short, permanent, given by code (never by the model) | `A5` |
| `title` | What it is, a few words | Export feature |
| `owner` | One person, or empty | Priya |
| `due` | A calendar date, or empty | 2025-10-22 |
| `due_phrase` | How the date was said | "Wednesday" |
| `status` | `open`, `in_progress`, `blocked`, `done` or `dropped` | in_progress |
| `ticket` | Ticket id if one was said | PAY-231 |
| `parent` | The item this one is a part of, or empty | A8 (review Dev's PR) → `A2` (the auth bug) |
| `note` | One line on where it stands | "Waiting on infra for the cert" |
| `review_reasons` | Why a human should look; a list, and "needs review" means it is not empty | "Raised, deferred, no decision" |
| `history` | Every change: date, what changed, the quotes, who made it (model or lead) | |

Choices:

- **Five statuses, and room for more.** `open` = taken on or raised, no work reported yet. `in_progress` =
  the owner says they are working on it. `blocked` = waiting on something. `done` = finished. `dropped` = the
  team cancelled the work. `done` and `dropped` are the two **closed** statuses; the rest are **active**.
  The set of statuses, and which of them count as closed, is defined in one place as data, and any status
  may move to any other; nothing in the code assumes a fixed number or order. Adding `in_review` later means
  adding one entry, not hunting through conditions.
- **Dropped is not removed.** Dropped means the work was real and the team decided not to do it; the item
  stays on the list with its history. Removed is something only the lead does, and means it was never an
  item (section 6).
- **Parent link.** A review, a check or a retro belongs to another item. The link lets the page show them
  together. It carries no behaviour: closing a parent does not close its parts, and the other way round.
- **One owner.** If two people are named and neither is clearly the one, the owner is left empty and the
  item is flagged for the lead to pick. A second person's part
  (a review, a check) is its own item — see U14.
- **Supporting words** shown for an item are the quotes from its most recent history entry that has any (a
  lead edit has none, and does not hide them), with the full history one click away.

## 3. What the model returns

Two kinds of change, plus a list of things it chose not to track.

| Kind | Contains |
|---|---|
| `add` | optionally a `ref` naming it within this response only (`new1`, `new2`), title, and any of owner / due phrase / status / ticket / parent / note; quotes; optional needs-review reason |
| `update` | the item's `id`, the fields that change; quotes; optional needs-review reason |
| `not_tracked` | one quote and a short reason ("already done", "meeting, not an action", "small talk") |

**Quotes.** A change carries one to three quotes. Each quote is a run of words copied exactly from inside a
single speaker turn: no joining two turns, no "…" to skip words. At least one of them must be four words or
longer, or be a whole turn of two words or more ("APP-402 merged."). A shorter one ("Sure.") may sit beside
it but cannot justify a change alone. The speaker is not supplied by the model; code reads it from the turn
the quote was found in.

**Due dates: the model returns the phrase, code works out the date.** The model gives only `due_phrase`,
and it must appear inside one of the change's quotes. Three rules for what goes in it:

- **Always return it when a day is said for this work**, however unsure or conditional it sounds. A change
  with no phrase leaves an existing date alone, so a withheld hedge would silently keep the old date.
- **Keep it short: the day word, plus any word attached to it that shifts the day.** "Wednesday", "tonight",
  "next Friday", "Thursday or Friday", "end of week". Not the rest of the sentence.
- **Hedges and conditions need not be in it.** Code reads the whole sentence the phrase sits in (step D2),
  so "probably" or "if the cert lands" is seen either way.

The model never returns a calendar date.

**Fields in an update** have three states: a value (set it), explicitly empty (clear it), or left out
(unchanged).

**Parent** is either the id of an existing item, or the `ref` of another `add` in the same response. The
second form covers "I'll fix X" and "I'll review it" said in one standup, where the parent has no id yet.

There is no separate "close", "reassign" or "re-date" kind. The page works those labels out from which field
changed and how: *closed*, *dropped*, *reopened*, *blocked*, *unblocked* for status; *picked up* (no owner →
someone), *reassigned*, *unassigned* for owner; *dated* (first date), *re-dated*, *date cleared* for the due
date; *updated* for anything else. The full table is in `implementation-details.md` section 1.

## 4. What code does with each change

**Checks on the change as a whole**

| # | Check | If it fails |
|---|---|---|
| C1 | Every quote is found word for word inside one turn of today's transcript (ignoring case, spacing and quote-mark style), and at least one meets the length rule in section 3 | Change not applied; shown under "could not verify" |
| C2 | An `update` points at an item that exists | Not applied; shown under "could not verify". If the item exists but the lead removed it, the change is not applied and is listed under "not tracked" as "removed by lead" |
| C3 | The owner is a known person (team list, anyone who speaks today, any existing owner) | Applied, flagged needs review |
| C4 | An `add` names a ticket another item already has (an approved item, or an add earlier in this response). Ticket ids are normalised first, so "231" matches PAY-231 when only one ticket has that number | Applied, flagged "possible duplicate of A2". Not flagged when that item is the add's own parent: a review of PAY-231's fix may carry the ticket too. If the matching item was removed by the lead, the add is not applied and is listed under "not tracked" |
| C5 | `parent` names a different item that exists and was not removed, or an `add` in this response that was itself applied | Applied without the link, flagged needs review |

**Working out the date.** These steps run only when the change carries a `due_phrase`. A change with no
phrase leaves the item's date alone. The first step that matches decides.

| # | Case | Date | Phrase | Flag |
|---|---|---|---|---|
| D1 | The phrase is not inside any of the quotes (a model error) | Existing date untouched | Not stored | Needs review |
| D2 | Hedged or conditional: the sentence holding the phrase has a hedge word (maybe, probably, perhaps, possibly, might, hopefully, worst case) or a condition word (if, once, unless), or the phrase itself names two different days | Cleared, including any existing date | Stored | Needs review |
| D3 | The phrase holds one day code can work out, and no day-shifting word. Checked in this order: the stand-alone forms "this morning / afternoon / evening" and "end of day" mean today; then times of day are set aside (morning, afternoon, evening, after lunch); then the day: today, tonight, tomorrow, a weekday name (the next one after the standup date), a written date (day number with month name, with or without a year, or `YYYY-MM-DD`; with no year, the first such date on or after the standup). Other leftover words are ignored, so "Still Monday" and "Should be done tomorrow" work. Calendar days: weekends are not skipped | Set. If it equals the date the item already has, nothing changes | Stored, unless the date is unchanged | — |
| D4 | The phrase has a day-shifting word (next, after, following, before, week, or), or no day code knows: "next Friday", "next week", "after this", "end of sprint" | Empty. If the item had a date, it is cleared | Stored | Only if a date was cleared |

D1 and D2 look alike on the page but are different events. D1 is the model's mistake, so nothing it said
about the date is trusted and the old date stands. D2 is the speaker being unsure, so the old date is gone.

**Applied by code, not left to the model**

- **Reopening clears the date.** When a closed item (`done` or `dropped`) moves to an active status and the
  change sets no new date, the old date is cleared (it stays in history). Otherwise the item would return
  already overdue. This wins over D1: a reopen whose phrase is not in the quotes still clears the date.
- **Updates that change nothing are discarded.** "Still Monday" about an item already due Monday is not a
  change and is not shown as one.
- **Removing a parent** leaves its parts on the list with the link cleared. The cleared link is recorded in
  their history.

Nothing else is discarded silently: a failed change is still visible to the lead, with the reason.

**What this does not cover**

- A date is only ever set from words code understands, so "the 22nd" or "end of sprint" give no date and the
  lead fills it in.
- The hedge list is short and English only. It will sometimes clear a date that was firm, which is the safe
  direction.
- A day-shifting word the model leaves off. It is told to keep such words in the phrase, but if it returns
  "Friday" for "next Friday", code sets this coming Friday.
- The day-shifting list, like the hedge list, is short and English only.
- "Thursday or Friday" is caught only if the model returns both days in the phrase. If it returns just
  "Thursday", code sets Thursday. Scanning the whole sentence for a second day is not an option: Monday's
  export sentence names Friday, "this morning" and Monday, and is not a hedge.
- **A real day attached to the wrong thing.** Code checks that a phrase is a day, not whose day it is. On
  Tuesday infra's cert "will be done tomorrow morning"; if the model returns that as the deploy's due phrase,
  code sets 15 Oct, against U12. Only the model can avoid it.
- **Duplicates without a ticket id rest on the model alone.** Nothing in code notices if "Atlas export" is
  added as a new item beside "Export feature". This is the mistake the brief names, so it is the first thing
  `evaluation-checks.md` measures, and the lead's remove button is the only correction for it in this
  version.

## 5. When the conversation is unclear

The principle: **when the system cannot conclude, it leaves the field empty, keeps the words that were said,
and hands the decision to the lead.** It does not pick the likeliest answer. Trust in the system's own
judgment is something to build up over time from how often the lead has to correct it (section 6), not
something to assume on day one.

**Firm** rules are ones the tests will assert. **Soft** rules are judgment calls where either outcome is
acceptable; the lead settles them on the page.

| # | Situation | Rule | Example | Firm / Soft |
|---|---|---|---|---|
| U1 | Ownership moves during the conversation | Owner is the last person who accepts it or is assigned it. An offer that is handed on does not count | Dev: "I'll take it." and Arjun: "Cool, Dev on auth then." → Dev, although Priya offered first | Firm |
| U2 | Nobody takes it | Item with empty owner. Never guess | "Someone should fix that at some point" → onboarding doc, no owner | Firm |
| U3 | Raised but not decided | Item, no owner, needs review | Flaky CI test: "Let's talk about it after, not now." | Firm |
| U4 | Same thing, different words | Update the existing item | "the auth bug", "PAY-231", "231", "auth"; "export feature", "Atlas export" | Firm |
| U5 | A done or dropped item comes back | Reopen the same item, keep its history. Its old due date is cleared unless a new one is given | "231 is back. Different cause this time" | Firm |
| U6 | Bare weekday | The next such day after the standup date (worked out by code) | "Monday" said on Mon 13 Oct → 20 Oct | Firm |
| U7 | Date moves | Update the date; the old one stays in history | Export: Mon 20 → Wed 22 Oct | Firm |
| U8 | Hedged date: two days named, or "maybe" / "probably" / "worst case" | No date, and any existing date is cleared. Keep the words, flag needs review. A plain estimate ("should be done tomorrow", "going out today") is not a hedge and does set a date | "today, maybe tomorrow worst case" and "Tomorrow, probably." → empty | Firm |
| U9 | No day that can be pinned down | No date; keep the words | "next week", "at some point", "after this" | Firm |
| U10 | Already done when first mentioned | Not an item; listed under "not tracked" | "I replied last night, that's done." | Firm |
| U11 | Small talk, scheduled meetings, staffing | Not an item. A meeting with a time already set is an event; one that still has to be arranged is an action | Not items: 10:15 call, Falcon kickoff "Thursday, two pm", "Don't deploy on Friday", who is on Falcon. Item: "We should do a retro on that one next week" | Firm |
| U12 | Someone else's work blocks ours | Our item, status `blocked`, the dependency in `note`. No item for the other team, and their estimate is not our due date | Hermes staging deploy: blocked, "cert with infra, expected tomorrow morning" | Firm |
| U13 | A short promise | It is an item, with its own owner. If it is a step in an item the same person already owns, it is an update to that item | New item: "I'll send something tonight." → Arjun, due 15 Oct. Update: Rohan's "I've got a draft, I'll send it to Priya to check" → note on his onboarding doc item | Firm |
| U14 | A review or check owed by a second person | Its own item once that person agrees, with `parent` set to the item it belongs to | Priya: "I'll look at Dev's PR after this." Also Friday: Rohan will send the draft to Priya, Priya: "Sure." | Soft |
| U15 | Closing | Only on words that say it shipped or finished ("done", "deployed", "merged", "went out"). Silence never closes, and a passed due date never closes | Arjun's Falcon doc is never mentioned again → stays open | Firm |
| U16 | Finished but being watched | `done`, with the caveat in `note` | "Search is merged, I'm watching the numbers" | Soft |
| U17 | A statement about several items at once | One update per affected item, each quoting the same sentence. Affects that person's active items (not done, not dropped) that are due before the new date. This is the one place the model compares dates | "anything of hers rolls to Monday" → APP-402 to 20 Oct | Firm |
| U18 | `open` or `in_progress` | `in_progress` only when the owner reports working on it; otherwise `open`. Work that was blocked and is now unblocked but unfinished is `in_progress` | "Search, still on it." → in_progress; "I'm picking up the Hermes retry bug" → either | Soft |
| U19 | The team cancels work | `dropped`, only on words that say so. The item stays on the list | No case in the five days. Invented: "Let's not do the export after all, sales don't need it" | Firm |
| U20 | A promise that depends on something else happening | Item, with the condition in `note`, no date, needs review. The model returns the day as it would for any date; date step D2 sees the condition word in the sentence and gives it no date | No case in the five days. Invented: "If the cert lands, I'll deploy tomorrow" | Firm |
| U21 | A speaker corrects themselves | The corrected value is the one used, for an owner, a date or a status. For a date the model returns the corrected expression; if it returns both, date step D2 clears the date and asks the lead | No case in the five days. Invented: "Tuesday. Sorry, not Tuesday, Thursday" | Firm |

## 6. What the lead does

- **Edit owner, date or status.** Applied on top of the draft. The lead can set any status directly, so
  finishing or cancelling an item is a status change (`done`, `dropped`) and never has to go through Remove.
  The model sees the corrected value tomorrow as the truth, and can only change it again on the strength of
  new words in a new transcript.
- **Remove.** Means "this was never an action item". The item leaves the list, and the model is told not to
  add it again. If it comes up later it appears under "not tracked" with the reason "removed by lead".
- **Approve.** The draft becomes that day's approved list, and every needs-review flag on it is cleared: the
  lead has seen it. The next day cannot be processed until this happens.
- **Run the same day again** before approving replaces the draft, including any edits made to it; the page
  warns first.

Overdue items (due date earlier than the standup date of the day shown, still active) are marked on the page.
This is display only; nothing changes.

**Everything the lead does on a day that ends up approved is recorded.** Edits on a draft that is discarded
or run again are lost with it. Each edit, removal and approval is kept with the standup date, the
item, the field, the value the system had proposed and the value the lead chose. A removed item is hidden
from the list, not deleted: it is kept whole, with its quotes, its history and any edits the lead made to
it before removing it. Nothing uses this record yet. It is the raw material for later measuring where the
system can be trusted to decide alone.

## 7. What a correct week looks like

The list after Friday is approved, if every rule above is followed and the lead changes nothing. This is the
reference the tests are built from.

† marks something that depends on a soft rule: the item existing at all (U14), `done` on a watched item
(U16), or a parent link that is a matter of opinion. Tests may not assert these. `open` and `in_progress` are interchangeable everywhere (U18). The item
count is not a target.

| Id | Item | Part of | Owner | Due | Status | Through the week |
|---|---|---|---|---|---|---|
| A1 | Fix search latency | — | Arjun | — | done † | Mon hedged, no date, flagged → Tue hedged, flagged → Wed in review → Thu merged |
| A2 | Auth bug (PAY-231) | — | Dev | — | done | Mon Dev takes it → Tue due 14 → Wed done → Thu reopened, date cleared → Fri done |
| A3 | Hermes staging deploy | — | Sana | — | done | Mon blocked on infra cert → Wed done |
| A4 | Flaky CI test | — | — | — | open | Mon raised, deferred, flagged; flag cleared when Monday is approved |
| A5 | Export feature | — | Priya | 22 Oct | in_progress | Mon due 20 → Thu due 22. Tue and Wed "still Monday" are discarded as no change |
| A6 | Fix onboarding doc | — | Rohan | — | in_progress | Mon no owner → Thu Rohan → Fri draft ready |
| A7 | Atlas login slow | — | Dev | — | done | Tue raised → Wed fixed |
| A8 † | Review Dev's PAY-231 PR | A2 | Priya | — | done | Tue promised ("after this", no date) → Wed "Priya looked at it" |
| A9 † | Review Arjun's search PR | A1 | Dev | 15 Oct | done | Wed promised "today" → Thu reviewed |
| A10 | Send Falcon doc | — | Arjun | 15 Oct | open, overdue | Wed promised "tonight", never confirmed |
| A11 | Hermes retry bug (APP-402) | — | Sana | 20 Oct | open | Thu due 17 → Fri rolled to 20 |
| A12 | Retro on PAY-231 | A2 † | — | — ("next week") | open | Fri proposed |
| A13 † | Review Falcon schema draft | — | Dev | 17 Oct | open | Fri promised "today, after lunch" |
| A14 † | Check onboarding doc draft | A6 | Priya | — | open | Fri Priya agrees |

Not tracked: the CSV customer reply (already done), the 10:15 call, Rohan's introduction, the Falcon kickoff
meeting, who is staffed on Falcon, "Don't deploy on Friday".

## 8. Settled in review

| Question | Decision |
|---|---|
| Which statuses | Five: `open`, `in_progress`, `blocked`, `done`, `dropped`. Statuses and transitions stay open to extension |
| Dropped versus removed | Different things. Dropped: the team cancelled the work (a status). Removed: the lead says it was never an item. The lead can set any status directly |
| Link from a part to its parent item | Yes, `parent` field, display only |
| Recording what the lead does | Every edit, removal and approval is kept, including edits to items later removed |
| Name of the field holding how a date was said | `due_phrase` |
| Second independent review, 9 points | Eight taken up: hedge versus model error on dates (D1, D2), date steps run only when a phrase is given (section 4), quote floor allows a short whole turn (section 3), parent may name a same-day item and survives parent removal (section 3, C5), "discarded" for no-op updates, the two-days gap stated, grammar, and the model returning only the phrase. One needed no change: PLAN.md already listed status as editable |
| Short promises as their own items (U13, U14) | Yes |
| Hedged dates (U8) | Date left empty and handed to the lead. General principle stated at the top of section 5 |
| Independent review, 12 points | All taken up: quote shape (section 3, C1, now D1), flags after approval (section 7), missing Friday item (A14, U13), date cleared on reopen (U5), "not done" in U17, clearing and no-op updates (sections 3, 4), hedge check in code (now D2), "after this" gives no date (now D4, U9, A8), meeting versus action (U11), soft markers (section 7), ticket normalising and the duplicate gap stated (now C4, section 4), ordering and column header |
