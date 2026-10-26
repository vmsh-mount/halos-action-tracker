# M4 — Review page: progress

Date: 2026-10-11. Tasks: [tasks/M4-review-page.md](../tasks/M4-review-page.md).

## Done

All ten items. `src/standup_tracker/web/`: `views.py` (day record → rows), `app.py` (seven routes),
four templates. `python -m standup_tracker serve` starts it. The README now has the run steps.

The page for a draft shows, in order: notes (saved answer, new speakers), **changed today** with one card
per item, could not verify, heard but not tracked, the whole list, and a way to run the day again. Each card
has the item's labels, what changed as old → new, the words with who said them, any reason it needs the
lead's decision, the lead's own edits, and an edit form (owner with suggestions, date, status) plus Remove.
Cards with a review reason come first. When no draft is waiting, the page shows the approved list read-only
and the form for the next standup.

## Evidence

- `pytest`: **284 passed, 3 expected failures**, 1.2 s, no key, no network. 21 of them drive the page
  through the app on the saved answers: submit, fix an owner and a date, approve, carry forward to Tuesday,
  an unchanged form recording nothing, remove, discard, a failed run keeping the transcript, bad input,
  re-run confirmation, item history, the overdue marker, and a lead reopen showing on the card.
- **Looked at in a browser** on saved answers, Monday's and Thursday's drafts:
  - Monday: six cards, the three needing a decision first (hedged date, two with no owner), each with its
    quotes and speakers; the customer reply under "heard but not tracked".
  - Thursday: the "new speaker: Rohan" notice; the auth item as *reopened* with "Due: Tue 14 Oct → none";
    the onboarding doc as *picked up*, "Owner: none → Rohan"; an edit I made shown under "Your edits"; the
    Falcon doc marked *overdue* in the list.
- Nothing the model is shown was changed: the saved-answer match test still passes.

## Added after the first look and a review

- **File upload**: the form takes a transcript file as well as pasted text; a file named by its date fills
  the date in. Asked for by the owner.
- **A waiting message**, and the submit button is disabled once pressed, so a second click cannot start a
  second model call.
- **Supporting words on every item.** The whole-list table and the approved list now show, under each
  title, the quotes from the item's most recent history entry that has any, with speaker and date. Before,
  items the day did not touch showed none without a click, and the approved list showed none at all, which
  fell short of the goal ("the words in the transcript that support it").
- The note is no longer shown twice on a changed card.
- A state file that cannot be read gives a message with what to do, not a bare server error.
- A local `.env` (git-ignored) holds a reference to the key in the shell, so the page can run live.

## Redesign (asked for by the owner after seeing the first version)

The first version worked but read as a plain form-and-table page. It was rebuilt in the same plain HTML, CSS
and JavaScript, with no new dependency and no change to routes, state transitions or anything the model is
shown. Templates, one stylesheet (`_style.css`) and one script (`_app.js`) under `web/templates/`; wording
helpers in `web/views.py`.

**Terms.** One vocabulary throughout: a *team update* is processed into *proposed changes*, which are
reviewed and approved into *tracked work*. "Standup" no longer appears in the interface. Engine labels and
reasons are translated for display only: `closed` reads "Completed", `re-dated` "Rescheduled",
`hedged: 'maybe'` reads "The date sounded uncertain (“maybe”), so no due date was set."

**Structure.**

- *Workspace*: a header with the mode (Live and model name, or Replay mode); the latest update and whether
  it is approved; four counts that are each actionable (active, blocked, overdue, unassigned); the composer
  for the next update; the tracked-work table.
- *Composer*: date, file attach, transcript box with an example of the expected format, one primary action.
  Client-side check for an empty transcript; a progress line with elapsed seconds and a locked button while
  processing.
- *Tracked work*: item, owner, due, status. Status has a distinct icon shape per state, not colour alone.
  Filters (all, active, blocked, overdue, unassigned, closed), an owner filter, and sorting by column, all
  in the page. Supporting words under each item.
- *Review*: a sticky bar saying "Review pending", the counts, and Approve / Discard. Sections in order:
  needs attention, new, changed, removed by you, mentioned with no change, not applied, mentioned and not
  tracked, then the list as it will be after approval. Each change shows what changed as old → new with the
  transcript words directly under it. Editing is a small popover per item.
- *Item page*: an activity timeline, newest first.

**Interaction.** Discard and Remove ask for confirmation. Every form locks its buttons once submitted.
Visible focus rings; Escape closes an edit popover; only one is open at a time. Narrow screens stack the
table into rows. Motion is limited to a spinner and a progress bar, and is switched off for
reduced-motion settings.

**Checked in a browser** on saved answers at 1280 px and 375 px wide: the empty workspace, the empty-form
validation, Monday's review (three items needing attention), Thursday's review (new, completed, reopened,
picked up), the edit popover, the approved workspace after Friday with its overview counts, and one item's
activity page. Filters, owner filter and column sorting were exercised by script in the page and gave the
expected rows. A horizontal overflow at 375 px (the filter bar) was found and fixed.

**Changed after the owner used it.**

- *A flagged item stayed under "Needs attention" after the owner set the date it asked about.* An earlier
  decision said only approval clears a review reason. That is reversed: an edit that changes a flagged item
  settles it, and a "Keep as proposed" button settles it without an edit. New route
  `POST /items/{id}/reviewed`; history action `reviewed`.
- *Chips contradicted each other* ("Date cleared", "Scheduled") when the model cleared a date and the lead
  then set one. Labels now describe the net change for the day ("Rescheduled").
- *A removed item appeared twice*, under "Removed by you" and under New or Changed, with inflated counts.
  Removed items are now only under their own heading.
- *A new item read "Changed"* in the list after approval; it now reads "New".

**Not checked.** The processing state during a real 20 to 40 second live run. The native confirmation
dialogs (tests check they are wired; I did not click through them). Keyboard-only use beyond Escape and
focus rings. A screen reader. Widths between phone and desktop. There is no dark theme.

## What was not checked

- **No live model through the page by me.** Every run I made used saved answers. The page calls the same
  `submit_standup` the command line used for the live run, but a 20 to 40 second wait in the browser has not
  been seen. The waiting message has been checked only by reading the code, not by watching a live run.
- **Looked at, not user-tested.** I checked that the page renders and reads sensibly at one window size. No
  one timed how quickly a lead can check a day, which is what matters most.
- Friday's draft, the could-not-verify section and the failed-run notice were exercised by tests, not looked
  at in the browser. The recorded week has no refused change, so that section has never been rendered with
  real data.

## Decisions made while building

- The launch helper in the desktop app could not start the server from the virtual environment (a sandbox
  permission on `.venv`), so I started it with a shell command and opened the address in the built-in
  browser. `.claude/launch.json` is left in place but git-ignored.
- Edit forms sit inside a collapsed "Edit" control on every card and list row, so the page reads as a
  report first and a form second.
- The whole list is editable in a draft, not only the changed items: the lead may want to fix something the
  standup did not mention.
- A lead reopen shows on the card as a *reopened* label with the status change under "Your edits". If a date
  was cleared, it appears there as "Due: … → none" (carried over from M2).

## Open

- Not committed.
