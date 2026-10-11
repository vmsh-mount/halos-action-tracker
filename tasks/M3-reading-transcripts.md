# M3 — Reading transcripts

Budget: 55 min. Plan: [PLAN.md](../PLAN.md) section 3.

The model enters here. Everything from "transcript submitted" to "draft saved", run from the command line.

References: **flow** = `docs/components-and-data-flow.md`, **impl** = `docs/implementation-details.md`,
**gen** = `docs/generalisation-beyond-the-five-standups.md`, **eval** = `docs/evaluation-checks.md`.

## Part A — offline (no key, no spend)

| # | Item | Implements | Done |
|---|---|---|---|
| 1 | Settings from the environment and `.env`: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, optional `LLM_PROVIDER`, `LLM_TEMPERATURE`; state, team and saved-answer paths | flow §7 | [x] |
| 2 | `llm/`: the request and response, the chat API client, Replay, Recorder, and the function that picks one | flow §3 | [x] |
| 3 | Prompt template `prompts/propose_changes.md`, stating the behaviours G1–G30 in general terms with invented examples; `prompt` builds the request from it, the team, the list and the turns | gen §2, §3; impl §8.3 | [x] |
| 4 | `extract`: strip a code fence, read the answer, one retry in all (transport or unreadable answer), validation error fed back | flow §3; impl §3.2 | [x] |
| 5 | `service.submit_standup`: the nine steps, failure leaves the draft and records `last_failed_run` | flow §4.1, §4.4 | [x] |
| 6 | Command line: `process`, `approve`, `discard`, `show`, `run-week`, `reset` | flow §6 | [x] |
| 7 | Tests: provider choice incl. an empty key; Replay hit, miss, mismatch; retry cases with a fake transport; code fence; the word test on the template and `src/` | eval §3, H8 | [x] |

## Part B — live (needs a key and a go-ahead with a cost figure)

| # | Item | Done |
|---|---|---|
| 8 | One call on Monday to confirm the endpoint, the model name and that the answer can be read | [x] |
| 9 | The five days once with the Recorder; answers committed under `tests/saved_answers/` | [x] |
| 10 | Per-day properties on the saved answers (hard asserts, and expected failures where the recording misses) | [x] |

Model: `openai/gpt-5-mini`, chosen by the owner; may change later.

## Done when

- `pytest` passes with no key and no network, including the word test.
- `python -m standup_tracker run-week transcripts` replays the five days from saved answers.
- What the recorded run got right and wrong is written in `progress/M3-reading-transcripts.md`.

## Not in this milestone

- The review page (M4).
- Three live repeats and the README numbers (M5).
- The held-out run (M6).
