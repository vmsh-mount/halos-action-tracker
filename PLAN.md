# PLAN — Standup action tracker

Status: **draft for review**. Nothing is built yet.

This document covers scope, requirements and project setup only. How the system works (data shapes, prompt,
handling of unclear conversation, page layout, choice of tests) is decided in separate design documents,
listed in section 6.

Source of truth for requirements: `Halos Assignment.pdf`.

## 1. Goal

A small local app where the lead submits a standup transcript and its date, and gets back proposed changes to
a running action-item list. The lead corrects and approves; the approved list is the starting point for the
next day.

Done means a reviewer can, on their own machine with their own API key:

1. Run the five given standups in order and end the week with a sensible list.
2. Submit a transcript we have never seen and get a reasonable result.
3. See what changed each day, fix an owner or date, remove an item, approve.
4. Run the tests, and read in the README which results came from saved model responses and which from a live model.

Time budget: 3–5 hours, hard stop at 5.

## 2. Requirements

### From the assignment

| # | Requirement |
|---|---|
| R1 | Accept transcript text and its date (text box, file or command line) |
| R2 | Keep one running list across days; a standup can add, update, close, reassign or re-date items |
| R3 | Each item shows: what it is, owner if known, due date if given, current status, supporting transcript words |
| R4 | Handle uncertain and incomplete conversation deliberately, and explain the important choices |
| R5 | Work on a new transcript beyond the five examples |
| R6 | Review page shows what changed today |
| R7 | Lead can fix an owner or date, remove an item, and approve the result |
| R8 | The reviewed list carries forward into the next day |
| R9 | A few meaningful tests aimed at model mistakes (skipped, invented, wrong owner, repeat treated as new) |
| R10 | State where tests or demo use saved model responses, and separately what was tested against a live model |
| R11 | App and tests run locally; API key supplied by the reviewer, never in the repo or agent transcript |
| R12 | Commit at meaningful points; history not squashed or rewritten |
| R13 | README: how to run, important choices, what was verified and results, what's unfinished, one more day, time spent |
| R14 | Agent conversation transcript exported for this assignment only |

### Our own

| # | Requirement |
|---|---|
| R15 | All model calls go through one generic LLM interface. No code outside that interface knows which provider or model is in use |
| R16 | Provider, model name and API key come from configuration (environment variables), not from code |
| R17 | Default provider is OpenRouter, key read from `OPENROUTER_API_KEY` |
| R18 | The interface has a replay implementation that returns saved responses, so tests and the demo run with no key and no spend |
| R19 | The lead can also set an item's status directly, including finishing or cancelling it |
| R20 | Everything the lead does (edits, removals, approvals) is recorded; a removed item is hidden, not deleted |

## 3. Milestones

Each milestone ends with something you can look at, then stops for your go-ahead before committing.

| # | Milestone | Output | Budget |
|---|---|---|---|
| M0 | Setup | Repo skeleton, the five transcripts as dated text files, README stub, `.env.example`, `.gitignore`, confirm the agent transcript can be exported | 15 min |
| M1 | Design docs | The documents in section 6, reviewed and approved | 30 min |
| M2 | List engine (no AI) | Running list, applying changes, day-to-day carry-over, local file storage, unit tests | 40 min |
| M3 | Reading transcripts | Generic LLM interface with OpenRouter and replay implementations; Mon–Fri run live from the command line; responses saved | 55 min |
| M4 | Review page | Submit transcript + date, see today's changes with supporting words, edit owner/date, remove, approve | 55 min |
| M5 | Tests | The agreed checks, one command, on saved responses; separate script for a live run | 40 min |
| M6 | Write-up | README complete; final live run on an unseen sixth transcript | 25 min |

Total 4 h 20 min, leaving 40 min of slack. If M4 runs long, M5 is protected and the page loses polish first.

## 4. Out of scope

- Login, multiple users, multiple teams.
- A database, deployment, hosting.
- Real Linear / Jira / Slack integration.
- Audio or speech-to-text; input is text only.
- Editing fields other than owner, date and status (title, note, parent only if time is left).
- Undo after approval, or re-processing an earlier day.
- Splitting or merging items by hand.
- Notifications, reminders, overdue alerts.
- Streaming responses, cost tracking, automatic fallback between models.
- Comparing or benchmarking several models; one is picked and named in the README.
- Visual polish beyond clear and readable; no mobile layout.
- A large evaluation set; the five transcripts plus one unseen one are the test data.

## 5. Setup

Proposed, to confirm before M0.

| Area | Choice |
|---|---|
| Language | Python 3.11+ |
| App | One local web server, started with a single command; a command-line entry for processing a transcript without the page |
| State | Local JSON file under `data/`, git-ignored |
| Model access | OpenRouter through the generic interface (R15–R17); model name set by `LLM_MODEL` |
| Secrets | `.env` file, git-ignored; `.env.example` committed with empty values |
| Tests | One command, no key needed (uses saved responses) |
| Live check | Separate script, needs a key, prints what it spent where the provider reports it |

Repo layout:

```
halos-assignment/
  Halos Assignment.pdf
  PLAN.md
  README.md
  .env.example
  docs/            design documents (section 6)
  tasks/           one file per milestone: the work items and what counts as done
  progress/        one dated note per milestone: what was done, evidence, time spent, what's open
  transcripts/     2025-10-13.txt … 2025-10-17.txt, plus one unseen
  src/             application code
  tests/           tests and saved model responses
  data/            local state (git-ignored)
```

## 6. Design documents to follow

Written and approved in M1, before any implementation.

| Document | Answers |
|---|---|
| `docs/action-item-rules.md` | What an item and a change look like; how the model's output is checked and applied; how unclear ownership, vague dates, reopened items and non-items are treated |
| `docs/data-models.md` | Every stored shape besides the item: standup, team settings, proposed and checked changes, history, day record, the saved file, saved model answers |
| `docs/components-and-data-flow.md` | Components and how they connect, the LLM interface, storage, the review flow from draft to approved |
| `docs/evaluation-checks.md` | Which checks, what each one demonstrates, saved versus live |

## 7. Risks

- **Time.** The review page is where hours go; it has a fixed budget.
- **Model output varies between runs.** Live results are reported as "passed N of M runs", not a single pass.
- **Model choice is open.** The model has to return structured output reliably through OpenRouter; confirmed with a small live check at the start of M3, before building on it.
