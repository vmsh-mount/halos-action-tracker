# Standup action tracker

Halos engineering assignment. Reads daily standup transcripts and keeps a running list of action items that
the lead reviews and approves after each standup.

Status: in progress. See [PLAN.md](PLAN.md) for scope, requirements and milestones.

## How to run

Python 3.11 or later.

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/pip install -e .
```

Start the review page, then open http://127.0.0.1:8000:

```bash
.venv/bin/python -m standup_tracker serve
```

**With no API key** the app replays saved model answers, so it works offline for the five standups in
`transcripts/`: paste Monday's file with the date 2025-10-13, review, approve, then Tuesday, and so on. A
transcript it has no saved answer for is refused with a message saying a key is needed.

**With a key** it reads any transcript with a live model:

```bash
cp .env.example .env
```

then set `LLM_API_KEY` in `.env`. `LLM_BASE_URL` and `LLM_MODEL` are already filled in for OpenRouter and
`openai/gpt-5-mini`; any chat-completions endpoint and model can be named instead. `.env` is git-ignored.

The same steps from the command line:

```bash
.venv/bin/python -m standup_tracker run-week transcripts
```

Other commands: `process <file> --date YYYY-MM-DD`, `approve`, `discard`, `show`, `reset`. State is kept in
`data/state.json`; `reset` deletes it.

## How to run the tests

After the install steps above:

```bash
.venv/bin/python -m pytest
```

No API key and no network are needed. Tests that involve a model use saved answers, recorded once from
`openai/gpt-5-mini`; three properties that recorded run got wrong are marked as expected failures and are
printed with `-rx`. Results against a live model are still to come (M5).

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
