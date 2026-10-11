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

## Part B (live) — done

Six calls to `openai/gpt-5-mini` through OpenRouter on 2026-10-11, as approved: one on Monday to confirm the
endpoint, then the five days once with the Recorder. All six answered on the first attempt, in 19 to 39
seconds each. The key was read from the shell profile at run time and was not printed or written to disk.

The five answers are committed under `tests/saved_answers/`, unedited. They were recorded once; the Monday
confirmation call was a separate run and is not the saved one.

### What the one recorded run got right

Checked by `tests/test_practice_saved_answers.py` (39 checks pass, 3 are expected failures):

- **No change was refused** for an unfound quote: zero C1 refusals across 26 proposed changes.
- **No duplicates.** The auth bug stayed one item under "the auth bug", "PAY-231", "231" and "Auth", was
  closed, reopened and closed again. The export stayed one item; "Atlas export" on Wednesday did not add a
  second.
- **Owners.** The auth bug went to the person who took it, not the one who offered. The onboarding doc had no
  owner until Thursday, then the intern, who is not in the team settings.
- **Dates.** Export 20 Oct, then 22 Oct. The hedged search fix had no date on Monday or Tuesday and was
  marked. The retry bug moved from 17 to 20 Oct on "anything of hers rolls to Monday".
- **Nothing made up.** No item from the customer reply, the kickoff meeting, the introduction, the staffing
  note or the sign-off. Every item belongs to a piece of work in the answer key. 11 items, inside the 10 to
  14 the soft rules allow.
- **The lead's review carries forward** (two of the 39, replaying with an edit made on Monday): a corrected
  owner survives Tuesday's update to the same item, and a removed item stays out when Thursday and Friday
  return to it.

### What it got wrong

Four misses. The first three are each marked as an expected failure with its reason, so `pytest` is green
and the miss is printed. The fourth is on a soft outcome and has no check:

| Miss | Day | What happened |
|---|---|---|
| Another team's estimate taken as our date | Tue | "They say the cert will be done tomorrow morning" set 15 Oct on the staging deploy. Predicted in the rules document as something only the model can avoid |
| A day attached to the wrong work | Wed | The reviewer's "I'll review the search PR today" set 15 Oct on the search fix itself. The separate review item (soft) was not created |
| A skipped item | Fri | "We should do a retro on that one next week" produced nothing |
| A wrong parent link | Fri | The review of the Falcon schema draft was linked as a part of "send the Falcon kickoff doc". They share a project name and nothing else. Parent links are soft, so no check fails, but the link is wrong and will show on the review page |

The search-fix check was added after seeing this run. It is taken from the reference week, which gives that
item no date, and it counts against the run, not for it.

### What this does and does not show

- It is **one run**. Nothing here says how often the model gets each property right; that is the three
  repeats in M5. The Monday confirmation call differed from the recorded Monday in wording, statuses and
  item order, so run-to-run variation is real.
- The prompt was **not changed** after seeing these results. The saved answers match the committed prompt:
  a test fails if they drift.
- **Cost was not measured.** These six calls did not record token counts. The estimate before the run was
  about $0.10; the provider's dashboard has the real figure. Token counts are stored with each run from now
  on (`model_run.usage`), so later live runs can report their own.

`pytest`: **256 passed, 3 expected failures**, 0.6 s, no key, no network.
`python -m standup_tracker run-week transcripts` with no key replays the five days from the saved answers.

## Open

- **Decided: the misses are left as they are.** The prompt is not changed for them. It already states the
  rule for another team's estimate and for small promises, so more wording would be wording for one practice
  line. One run says nothing about how often they happen; the three repeats in M5 will.
- **Frozen from here**, because the saved answers are tied to them: the prompt template, the format of the
  item lines in `prompt.py`, and what the engine produces for an earlier day. Changing any of them turns
  `test_saved_answers_match_the_current_prompt_and_list` red, and the only fix is to record again, which
  costs calls and gives a new single sample with different misses.
- Not committed.
