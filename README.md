# Standup action tracker

Halos engineering assignment. Reads daily standup transcripts and keeps a running list of action items that
the lead reviews and approves after each standup.

Status: in progress. See [PLAN.md](PLAN.md) for scope, requirements and milestones.

## How to run

_To be written (M2–M4)._

Model access goes through OpenRouter. Copy `.env.example` to `.env` and set `OPENROUTER_API_KEY` and
`LLM_MODEL`. Tests and the replay demo need no key.

## How to run the tests

_To be written (M5)._

## Important choices and why

_To be written (M1, M6). Details in `docs/`._

## What was verified

_To be written (M6): what was run, the results, what used saved model responses, what was sent to a live
model, and what could not be verified._

## Left out or unfinished

_To be written (M6)._

## With one more day

_To be written (M6)._

## Time spent

_To be written (M6). Per-milestone times are in `progress/`._

## Repository layout

| Path | Contents |
|---|---|
| `Halos Assignment.pdf` | The assignment brief |
| `PLAN.md` | Scope, requirements, milestones, setup |
| `docs/` | Design, architecture and testing documents |
| `tasks/` | One file per milestone: work items and what counts as done |
| `progress/` | One note per milestone: what was done, evidence, time spent |
| `transcripts/` | The five standups, one file per day, named by date |
| `src/` | Application code |
| `tests/` | Tests and saved model responses |
