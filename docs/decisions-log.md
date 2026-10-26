# Decisions log

The decisions that shaped the system, in the order they were made, with the ones that were later reversed
marked. Each links to where the detail lives. Built in one session on 2026-10-11 by the project owner working
with a coding agent; "review" means an independent review the owner brought in at that step.

## Approach

| # | Decision | Why |
|---|---|---|
| 1 | The model proposes changes ("add", "update A5") with exact quotes; code checks and applies them | A repeat mention must point at an existing item; the day's diff comes for free; each change is small enough to check. [Rules §1](action-item-rules.md) |
| 2 | Design against all five given standups; get the unseen test from new transcripts | Friday holds cases nothing else covers, and one short held-out day proves little |
| 3 | The model returns the phrase for a date ("Monday"); code works out the date | Date arithmetic is a known weak spot for models and trivial for code. [Rules §3](action-item-rules.md) |
| 4 | When the conversation does not settle something, leave the field empty, keep the words, flag it | The owner's ruling: hand control to the lead; trust is built over time, not assumed |
| 5 | Short promises ("I'll send something tonight") are items | They are what gets forgotten |
| 6 | Statuses are data, not code. Five: open, in progress, blocked, done, dropped | The owner asked for room to add states |
| 7 | Dropped (team cancelled it) is separate from removed (lead says it was never an item) | The owner's distinction; the lead can set any status, so cancelling never needs Remove |
| 8 | Items can link to a parent; the link is display only | A review belongs to the work it reviews |
| 9 | Every lead action is recorded in the item's history | So corrections can later show where the system can be trusted |
| 10 | Firm rules are asserted by tests; soft rules are judgment calls and are not | Some outcomes are right either way |

## Generalising

| # | Decision | Why |
|---|---|---|
| 11 | The five standups are a practice set; nothing in the prompt or code may name them | New transcripts have to work. A test fails if a practice word appears in the prompt or source. [Generalisation](generalisation-beyond-the-five-standups.md) |
| 12 | Checks are properties found through transcript turns, never through model-written titles | A title match is a wording check in disguise. [Generalisation §5](generalisation-beyond-the-five-standups.md) |
| 13 | Saved answers are recorded once and not edited; misses are marked as expected failures | Re-recording until it passes would be choosing the sample |
| 14 | Expectations for unseen transcripts are written, and reviewed, before running | So the output cannot steer the judging |

## Build

| # | Decision | Why |
|---|---|---|
| 15 | A core with no model and no files, built and tested first | The answer key run through real code proves the engine before any model is involved |
| 16 | One generic model interface; settings are `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` | The owner's requirement: no coupling to a provider or model |
| 17 | Model: `openai/gpt-5-mini` | The owner's choice. The agent had proposed a mid-tier model for the judgment calls; cost did not separate them at this size |
| 18 | No key means replay of saved answers; a key selects the live model | A reviewer can try it with nothing set up |
| 19 | Our code validates the answer; only an unreadable answer fails the run | Independent of any provider's structured-output feature; one bad change must not cost the whole day |
| 20 | Server-rendered pages, plain HTML, CSS and JavaScript | No build step; one command to run |

## Flags, badges and citations

How free text becomes structured state, and how each piece of state stays tied to the words behind it.

### From free text to state

The model reads free text; everything it returns is either a pick from a fixed set, or text that code then
interprets. Nothing on the page is a free-text guess at a state.

| What is shown | Where it comes from | Who decides |
|---|---|---|
| Status | One of five fixed values the model picks. Anything else is ignored and the item is flagged | Model picks; code enforces the set |
| Due date | The model returns the words ("Monday"); code turns them into a date, or into no date, by fixed steps D1 to D4 | Code |
| Owner | A name the model returns, matched against the team's names and nicknames | Model picks; code makes it canonical and flags unknown names |
| Change labels (New, Completed, Reopened, Rescheduled, Picked up…) | Worked out from before and after values of each field. Never from the text, and never from the model | Code |
| Overdue, Blocked, Needs attention | Derived from the due date, the status and the list of review reasons | Code |
| Ticket | Text the model returns, normalised; a bare number is matched to the one existing ticket ending in it | Code |

So the only judgment in the mapping is the model's choice of status, owner and which words name the date.
Labels and badges are arithmetic on the result. [Implementation details §1 and §2](implementation-details.md)

### Flags are general

A flag says "a person should look at this". Every flag is raised by a rule that knows nothing about any
particular transcript:

| Flag | Raised when |
|---|---|
| Hedged, conditional, two days | The sentence holding the date has a hedge or condition word, or the phrase names two days |
| Date no longer pinned; timing mentioned | A dated item gets a phrase that is not a specific day |
| Date phrase not in the quoted words | The model's date phrase does not appear in its own quotes |
| Unknown person | The owner is not in team settings, did not speak today and owns nothing already |
| Possible duplicate | A new item carries a ticket another item already has |
| Parent link dropped | The parent named does not exist, was removed, or is the item itself |
| Field ignored | A status outside the fixed set, an empty title, a value that is not text |
| The model's own reason | The model says in free text that something was left undecided |

The first seven come from code and have fixed wording, which the page turns into plain sentences by pattern.
The last is the model's words, shown as written. Word lists (hedges, conditions, day words) and statuses are
plain data in one module, so extending them does not touch logic. The practice week is not in any of them: a
test fails if a practice name or ticket appears in the source.

Known limit: the word lists are short and English only. "assuming" and "I'll try" were predicted to get
through, and did.

### Citations

Every change carries the words that justify it, and code will not apply a change whose words were not said.

| Rule | Why |
|---|---|
| One to three quotes per change, each copied from inside one speaker turn | A quote stitched across turns, or with words skipped, can be made to say anything |
| Whole words only; case, spacing and curly quotes are ignored, nothing else | Tolerant of copy-paste, intolerant of rewording |
| At least one quote of four words, or a short whole turn | "Sure." cannot justify a change alone |
| The date phrase must sit inside one of the quotes | What set a date is always on show |
| The speaker and turn are read from the transcript by code, not supplied by the model | The model cannot misattribute |
| A change with an unfound quote is not applied and is shown under "Not applied" | Nothing is dropped silently |

Quotes are stored on the change and on the item's history. The page shows them directly under the change
they support; on the list, each item shows the quotes from its most recent change that had any, so a lead
edit never hides the evidence.

What a citation proves: the words were said. It does not prove they mean what the change claims. A real
quote attached to the wrong item passes, which is why owners, dates and duplicates are tested separately.
[Rules §3 and §4](action-item-rules.md)

## Reversed or corrected

| # | First decision | What changed it | Now |
|---|---|---|---|
| R1 | Three statuses | Owner review | Five (see 6, 7) |
| R2 | A hedged date takes the latest day named | Owner review | No date; flagged for the lead |
| R3 | The model returns words and a date; code compares them | Review: code is already the authority | The model returns only the phrase |
| R4 | The model returns the date expression in full, and any leftover word means no date | Review: this broke "Still Monday" and "Say Wednesday?" | A short phrase; leftover words ignored unless one shifts the day ("next", "last") |
| R5 | Replay stops if the request differs at all from the recording | Review: the demo would stop the moment a reviewer fixed an owner | Looked up by date and a hash of the turns; a changed list shows a note |
| R6 | A separate list of lead actions | Review: a second copy of the same facts | Lead actions live in item history |
| R7 | Every request sent at temperature 0 | The provider's model list: the chosen model accepts no temperature | Optional setting, off by default; results are reported as N of 3 |
| R8 | Prompt examples that mirrored practice-week traps | Review | Five examples of behaviours the practice week never shows. Cost: those are the behaviours the unseen set tests, so it measures unseen wording, not unseen behaviour |
| R9 | Reopening always clears the old date | Three reviews of the code | Only for an item closed on an earlier day; undoing a close made today loses nothing |
| R10 | Only approval clears a review flag | The owner, using the page: an item stayed under "Needs attention" after its date was set | An edit that changes the item settles it, as does "Keep as proposed" |
| R11 | A plain form-and-table page | The owner, on seeing it | Redesigned: one vocabulary, overview, review sections, evidence beside each change |

## Contradictions found in the design

Writing [implementation-details.md](implementation-details.md) surfaced 16 places where the earlier documents
disagreed and 12 they left open. Each is listed there with its decision (sections 10 and 11).

## Left as they are, knowingly

| What | Why it was not changed |
|---|---|
| The mistakes seen in live runs (a reopened item left open, a date kept against the lead's word, an item added for a dismissed alert, another team's estimate taken as a due date) | A prompt change after seeing results needs a general reason and fresh transcripts to measure on. Both weeks are now seen |
| A duplicate with no ticket number is not caught by code | A general fix is proposed in the README; it would be an engine change made after practice results |
| Word lists for hedges and conditions are short and English only | "assuming" and "I'll try" got through, as predicted before the run |

## Process slips

- The design phase took 1 h 50 min against a 30-minute plan.
- One commit was made without the owner's go-ahead for it. It was reported at once, undone at the owner's
  request, and committed again after review.
- Several elapsed-time figures given during the session were overstated by 10 to 15 minutes.
