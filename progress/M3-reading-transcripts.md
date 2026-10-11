# M3 — Reading transcripts: progress

Date: 2026-10-11. Tasks: [tasks/M3-reading-transcripts.md](../tasks/M3-reading-transcripts.md).

## Part A (offline) — done

- **Settings** are provider-neutral, at the owner's direction: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.
  No setting or code names a provider. `.env` may reference a key already exported in the shell
  (`LLM_API_KEY=${OPENROUTER_API_KEY}`) so the secret is not copied into the project.
- **`llm/`**: request and response, a chat-completions client, Replay, Recorder, and the function that
  picks one (a non-empty key selects the API; no key selects Replay; `LLM_PROVIDER` overrides).
- **Prompt template** `src/standup_tracker/prompts/propose_changes.md`: about 1,600 words. It states the
  behaviours in general terms and uses five invented examples about an events team.
- **`extract`**: strips a code fence, reads the answer, at most two attempts in all, validation error fed
  back on a retry.
- **`service.submit_standup`** and the **command line** (`python -m standup_tracker …`).

## Evidence

- `pytest`: **217 passed**, 0.3 s, no key, no network. 73 of them are new in this part.
- With no key and no saved answers, the command line stops with "No saved answer for this transcript. Set
  LLM_API_KEY to use a live model." and records the failed run. Forced to the API with no key, it names the
  missing setting.
- The whole week run through `submit_standup` with a stand-in model that returns the answer key gives the
  same final list as the engine alone.
- The practice-word test fails when a practice word is planted in the template (checked, then reverted).
- A failed run leaves an existing draft, and the lead's edits on it, untouched (tested for a fatal error, a
  missing saved answer, and an unreadable answer twice).

## Changed after review

- **Prompt examples replaced.** The first four each had the shape of a practice-week trap (a hand-off, a bare
  ticket number, two days with a hedge, an appointment and a scheduled event), though no wording was shared.
  They are now five examples of behaviours the practice week never shows: cancelled work, a reassignment, a
  conditional promise, a removed item coming up again, and "didn't get to it".
  **Cost of that swap:** all five are behaviours the held-out set is required to include, so the held-out run
  will measure unseen wording and an unseen team, not unseen behaviours. The examples stay, since they are
  general rules and not practice lines; this goes in the README beside the held-out results.
- **The package installs.** `pyproject.toml` has a project section and the README adds `pip install -e .`,
  so `python -m standup_tracker` runs from the repository root. Before, it needed `PYTHONPATH=src`.
- **Timeout raised to 180 s** for the reasoning model; the rate-limit pause is capped at 30 s.
- **A sentence around the JSON** no longer costs the retry.
- **Vague timing no longer wipes a firm date**: "soon" about an item that has a date leaves it alone, and
  marks the item "timing mentioned, date unchanged", since "in two days" is treated the same way.
- **The command line has tests** and reports a missing file as a message.
- **A corrupt saved answer** is reported as a failed run, not an unhandled error.

## What this does not show

**No model has been called.** The prompt has never been read by a model. Every test here uses a stand-in
that returns the hand-written answer key, or a scripted reply. Whether the prompt produces good changes is
entirely untested until Part B.

## Decisions made while building

- **Temperature is optional**, sent only when `LLM_TEMPERATURE` is set. The provider's model list shows the
  chosen model does not accept one. The components and implementation documents are corrected.
- **Model**: `openai/gpt-5-mini`, chosen by the owner over my proposal of a mid-tier model; may change.
- **The retry lives in `extract`, not in the client.** The client makes one attempt and says whether the
  failure is worth another. That keeps "never more than two attempts" true across transport failures and
  unreadable answers together.
- **The Recorder saves every answer it sees**, including an unreadable first attempt, which the retry then
  overwrites under the same key. If both attempts fail, an unreadable answer is left on disk; replaying it
  fails the same way.
- **JSON mode, not strict schema**: the client asks for a JSON object and the instructions describe the
  shape. An endpoint that rejects `response_format` would fail with a clear error; not handled further.

## Open

- Part B needs a go-ahead with a cost figure before the first live call.
- Not committed.
