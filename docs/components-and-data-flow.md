# Components and data flow — the parts of the program and how a standup moves through them

Status: **approved**, with corrections from `implementation-details.md` sections 10 and 11 applied. No code exists yet.

What the program is made of, what each part is allowed to know, and the path from "transcript submitted" to
"list approved". The shapes passed around are in `data-models.md`; the rules applied are in
`action-item-rules.md`.

## 1. The shape in one picture

```
   Review page (browser)        Command line
            │                        │
            └──────────┬─────────────┘
                       ▼
                    Service            the only thing the page and the command line call
        ┌──────────────┼───────────────────────────┐
        ▼              ▼                           ▼
   Reading the      Core rules                   Store
   transcript       (no model, no files)         data/state.json
        │           turns · dates · checks
        ▼           apply · lead actions
   LLM interface
   ├─ OpenRouter
   ├─ Replay (saved answers)
   └─ Recorder (wraps another, saves what it returns)
```

Two ideas hold it together:

- **The core is plain code with no model and no files.** Given a list, a standup and a set of proposed
  changes, it returns the checked changes and the new list. Same input, same output. This is what M2 builds
  and tests before any model is involved.
- **The model is behind one narrow door.** Everything about providers lives on the far side of it.

## 2. The parts

All under `src/standup_tracker/`.

| Part | Does | Must not |
|---|---|---|
| `vocab` | Holds the fixed lists as data: statuses, hedge and condition words, day words, day-shifting words | Contain anything about a particular team |
| `models` | The data shapes from `data-models.md` | Contain behaviour |
| `transcript` | Splits text into speaker turns; finds which turn a quote sits in | Call the model |
| `dates` | Date steps D1–D4: phrase + sentence + standup date → date, or no date and why | Know about items |
| `items` | The one place a field on an item is changed: writes the diff and the history entry, and clears the date when a closed item becomes active | Know who is asking, the model or the lead |
| `apply` | Checks C1–C5, the date steps, discarding no-ops, parent links. Proposed changes → checked changes + new list. Changes fields only through `items` | Read or write files; call the model |
| `review` | The lead's actions on a draft: edit, remove, approve, discard. Changes fields only through `items` | Read or write files |
| `prompt` | Builds the text sent to the model from the template, team settings, current list and turns | Name a provider |
| `llm/` | The interface and its three implementations (section 3) | Know what a standup or an item is |
| `extract` | Sends the prompt through the interface; turns the answer into proposed changes; rejects an answer in the wrong shape | Apply anything to the list |
| `store` | Loads and saves `data/state.json` | Decide anything |
| `service` | Runs each use case end to end (section 4) | Contain rules; it only sequences the parts above |
| `web/` | The review page: routes and templates | Do anything except call `service` |
| `cli` | The command line: same use cases | Do anything except call `service` |

The prompt template is a text file, `src/standup_tracker/prompts/propose_changes.md`, with slots for team
facts, the list and the transcript. It is the file the word test scans.

Because `apply` and `review` both go through `items`, the lead reopening an item by setting its status
clears the old date exactly as a model-made reopen does. The rule exists once.

## 3. The LLM interface

One operation: **text in, text out**.

| | Fields |
|---|---|
| Request | Instructions, input text, the answer shape wanted (a JSON schema), temperature, and a **lookup key**: an opaque string the caller chooses |
| Response | The answer text, provider name, model name, token counts if the provider reports them, and **notes**: plain-text remarks for the caller to show ("saved answer, recorded against a different list") |

The lookup key means nothing to the interface. `service` builds it from the standup date and a short hash
of the **parsed turns** (each turn's speaker and words, with runs of whitespace collapsed), not of the text
as typed. Pasting a transcript into the page changes its line endings, and copying from the PDF changes its
line wrapping; the turns come out the same, so the key does too. OpenRouter ignores it; Replay and the Recorder use it as the name of the saved
answer. So `llm/` still knows nothing about standups.

Three implementations:

| Implementation | Behaviour |
|---|---|
| OpenRouter | Sends the request to OpenRouter's chat endpoint with the model named in `LLM_MODEL` and the key in `OPENROUTER_API_KEY` |
| Replay | Returns the saved answer stored under the lookup key. No key, no network |
| Recorder | Wraps another implementation and saves each answer under `tests/saved_answers/`, named by lookup key. Switched on with `--record` |

**Which one is used** (decided in one small factory function, from the environment):

1. `LLM_PROVIDER`, if set, decides.
2. Otherwise, if `OPENROUTER_API_KEY` is set, OpenRouter. A reviewer who sets a key gets the live model
   without a second setting. "Set" means not empty: `.env.example` ships the name with no value, and a
   reviewer who copies it unchanged must get the demo, not a call with a blank key.
3. Otherwise Replay.

**Tests never go through that choice.** They build Replay directly, and the test setup also forces
`LLM_PROVIDER=replay`. A key sitting in `.env` must not make a test run call the live model, cost money and
give varying results. Only the separate live-check script uses OpenRouter.

**Replay answers only the question it was recorded for.**

| Situation | Result |
|---|---|
| Same transcript and date, same list | The saved answer |
| Same transcript and date, the list differs (the lead edited an earlier day) | The saved answer, with a note shown on the page |
| A transcript it has no saved answer for (the reviewer pastes their own) | Stops: "No saved answer for this transcript. Set `OPENROUTER_API_KEY` to use a live model." |

Rules:

- Nothing outside `llm/` imports a network library, names a provider, or reads a key.
- Adding a provider is one new file implementing the one operation.
- **The answer is always checked by our own code**, whatever the provider promises. We ask for JSON in a
  given shape; `extract` strips any code fence around it (many models add one) and validates it. Only an
  answer that cannot be read at all (not JSON, or no `changes` list) is refused as a whole. A slip inside
  one change, such as an unknown status or a missing field, costs that change or that field, never the run.
  Unknown keys are ignored. That keeps us independent of any one provider's structured-output feature.
- **One retry, never more than two attempts in all.** Retried: a timeout, a server error (5xx), a rate limit
  (429, after the pause the provider asks for, or 5 seconds), a 200 whose body is empty or carries an error
  instead of an answer, and an answer that cannot be read. Other errors (a bad key, no credit) fail at once. A wrong-shape retry sends the validation error back
  to the model with the request: at temperature 0 the same request tends to return the same wrong answer.
  If the second attempt fails, the run fails as described in `data-models.md` section 9. Both attempts are
  kept. The fingerprint saved with an answer is always that of the **original** request, even when the
  answer came from the retry; otherwise every later replay of that day would show the "different list"
  note for no reason.
- An explicit timeout of 60 seconds on the network call. The library's default is 5, shorter than many
  model calls.
- Temperature 0. It does not make answers identical between runs, but it narrows the spread.

## 4. What happens, step by step

### 4.1 A standup is submitted

| # | Step | Part | Stops if |
|---|---|---|---|
| 1 | Receive date and text | `web` or `cli` | |
| 2 | Check the date is later than the last approved day, and that no other day is waiting for approval | `service` | Either fails: message, nothing changes |
| 3 | Split into turns; note speakers not in the team settings | `transcript` | No speaker turns found |
| 4 | Build the prompt: rules, team facts, current list, lead-removed list, numbered turns | `prompt` | |
| 5 | Send it; get the answer | `llm` | Network or provider error |
| 6 | Turn the answer into proposed changes | `extract` | Wrong shape twice |
| 7 | Check and apply to a copy of the list | `apply` | Never: a failed change is recorded, not fatal |
| 8 | Save as the draft day record | `store` | |
| 9 | Show the review page | `web` | |

If a draft for the **same** date already exists, step 2 asks for confirmation and step 8 replaces it. If the
re-run fails at any step before 8, the existing draft is left as it was.

### 4.2 The lead reviews

The page shows, top to bottom:

1. Notes, if any: new speakers, or a saved answer recorded against a different list.
2. **Changed today**: one row per item, however many things changed on it. The row carries its labels
   (added, re-dated, closed …), each change as old → new, who said it and the words, and any review reasons.
   **Rows with review reasons come first.** The lead reads each item once.
3. **Could not verify**: changes the checks refused, with why.
4. **Heard but not tracked**: the model's list.
5. **The whole list**, with the untouched items dimmed and overdue items (date passed, still active) marked.

On any item in the draft the lead can change owner, date or status, or remove it. The owner input suggests
the known people and also takes free text. Each is one small form;
the page reloads with the change in place and recorded (`review`, then `store`). Nothing here calls the
model.

**Edit and remove work only on a draft.** When no draft is waiting, the page shows the approved list
read-only. Changing it would rewrite a day the lead already approved; a correction waits for the next
standup's review.

**Discard.** The lead can throw the draft away: the list goes back to the last approved day, as if the
standup had never been submitted. This is the way out of a wrong date or a pasted-in wrong transcript.
Edits made to the discarded draft are lost with it.

### 4.3 The lead approves

`review` clears the review reasons and marks the day approved; `store` moves it from `draft` to `days` and
advances the id counter. The page then shows the current list and the form for the next standup.

### 4.4 Something fails

No draft is made and the list is untouched. The page shows what failed in plain words (no key set, provider
error, answer not understood) and the transcript stays in the form so it can be resubmitted.

## 5. What the model is given, and what it is not

| Given | Why |
|---|---|
| The rules, as general behaviours | `generalisation-beyond-the-five-standups.md` section 2 |
| Team facts: people and other names, glossary, ticket prefixes | From `config/team.json` |
| Standup date and weekday | Context only; it does not compute dates |
| Each active or closed item: id, title, owner, status, due date and phrase, ticket, parent, note | To point updates at the right item |
| Items the lead removed: id and title | So they are not added again |
| The turns, numbered, with speakers | The thing to read |

Not given: item histories, earlier transcripts, anything about what the lead corrected. This keeps the
prompt small and the same size from day to day. The cost is that the model matches "the auth one" to an
item using only its title, note and ticket. If duplicates turn out to be common in practice runs, sending
each item's most recent quote is the first thing to try.

## 6. The page and the command line

| Page | Purpose |
|---|---|
| `GET /` | The draft under review if there is one; otherwise the current list and the submit form |
| `POST /standup` | Submit date and text (4.1) |
| `POST /items/{id}/edit` | Change owner, date or status (draft only) |
| `POST /items/{id}/remove` | Remove (draft only) |
| `POST /approve` | Approve the draft |
| `POST /discard` | Throw the draft away |
| `GET /items/{id}` | One item with its full history |

Server-rendered pages with ordinary forms. No front-end framework and no build step.

| Command | Purpose |
|---|---|
| `process <file> --date D` | Submit a standup from a file; prints the proposed changes |
| `approve` | Approve the draft as it stands |
| `discard` | Throw the draft away |
| `show` | Print the current list |
| `run-week <folder>` | Process every dated file in order, approving each. Used for the live check and to record answers (`--record`) |
| `reset` | Delete the saved state |

## 7. Settings

All from the environment (a git-ignored `.env`), never from code.

| Name | Meaning | Default |
|---|---|---|
| `LLM_PROVIDER` | `openrouter` or `replay` | Not set: OpenRouter if a key is set, otherwise Replay |
| `LLM_MODEL` | Model name as the provider knows it | None in code. `.env.example` ships with the model chosen in M3 filled in; OpenRouter without it is a clear error |
| `OPENROUTER_API_KEY` | Key | none; required for `openrouter` |
| `STATE_FILE` | Where the state is saved | `data/state.json` |
| `TEAM_FILE` | Team settings | `config/team.json` |

With no key, the app runs on Replay: a reviewer gets a working demo of the five days, and the page says
plainly that the answers are saved ones. With a key in `.env`, it uses the live model.

## 8. Built with

Python 3.11+, FastAPI and Jinja templates for the page, `python-multipart` (FastAPI needs it to read form
posts), `httpx` for the one network call, Pydantic for the data shapes and for validating the model's
answer, `python-dotenv` to load `.env`, pytest for the tests. Installed with `pip` from a `requirements.txt`
into a virtual environment, with versions pinned; development is on Python 3.14, so Pydantic is pinned to
a release that supports it.

One detail the data shapes depend on: an update's fields have three states (a value, explicitly empty, left
out). A plain optional field cannot tell the last two apart, so `extract` reads which fields the model
actually sent (Pydantic's `model_fields_set`) and not just their values.

One process, one user. The state file is written to a temporary file and renamed, so a crash cannot leave
it half-written. There is no locking: two browser tabs approving at once is not handled.

## 9. Settled in review

| Question | Decision |
|---|---|
| Default provider | Replay when no key is set; a set key selects OpenRouter by itself; `LLM_PROVIDER` overrides both |
| Retry | One, for a timeout, a 5xx or a wrong shape; a wrong-shape retry sends the validation error back |
| History sent to the model | No, as a starting point |
| Second independent review | All taken up: lookup key hashed from parsed turns; "set" means not empty; tests build Replay directly; the saved fingerprint is the original request's |
| Independent review | All taken up: replay looks up by an opaque key built from date and transcript, and stops on a miss (section 3); discard a draft (4.2, section 6); one row per item with flagged rows first (4.2); explicit timeout; edit and remove on a draft only; a failed re-run leaves the draft; overdue marker; notes on the response; dependencies and pinning; three-state fields; one place for field changes (`items`) |
