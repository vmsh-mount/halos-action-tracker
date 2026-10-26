# M2 — List engine (no AI)

Budget: 40 min.

Everything that turns proposed changes into a reviewed list, with no model and no web page. Input is
hand-written proposed changes; output is checked changes, the draft, and the saved state.

References: **impl** = `docs/implementation-details.md`, **models** = `docs/data-models.md`, **flow** =
`docs/components-and-data-flow.md`, **eval** = `docs/evaluation-checks.md`.

## Work items, in build order

Code under `src/standup_tracker/`, tests under `tests/`.

| # | Item | Implements | Done |
|---|---|---|---|
| 1 | Project setup: virtual environment, `requirements.txt` (Pydantic, pytest; pinned), test config so `pytest` finds `src/` | flow §8 | [x] |
| 2 | `config/team.json`: the four people with other names and roles, glossary, ticket prefixes | models §3 | [x] |
| 3 | `vocab`: statuses with closed flag and start status; hedge, condition, time-of-day, stand-alone and day-shifting words | models §4, impl §1.5 | [x] |
| 4 | `models`: item, history entry, proposed change, checked change, day record, state | models §5–10, impl §8.1 | [x] |
| 5 | `transcript`: split into turns; stop when none; find a quote in a turn; the length rule | models §2, impl §3.3 | [x] |
| 6 | `dates`: steps D1–D4 with the definitions table | impl §1.5 | [x] |
| 7 | `items`: the one place a field changes; diff, history entry, reopen clears the date | impl §1.3–1.6, flow §2 | [x] |
| 8 | `apply`: two passes; checks C1–C5; outcomes applied / could not verify / discarded / not tracked; labels; review reasons | impl §1.7, §3.3 | [x] |
| 9 | `review`: edit owner, date, status; remove; approve; discard | impl §1.1, §4 | [x] |
| 10 | `store`: load and save `data/state.json`; whole-file replace; version check | models §10, impl §6 | [x] |

## Tests, in the cut order from eval §3

| Priority | Test | Done |
|---|---|---|
| Protected | Date steps: one case per cell of the D1–D4 table; every due phrase in the answer key; the untested cases listed in eval §3 | [x] |
| Protected | Quote matching: case, spacing, curly quotes, ellipsis, two turns, the four-word floor, a short whole turn, "Sure." alone | [x] |
| Protected | The key through the code: the answer key as five days of proposed changes, each day approved; the final list equals `action-item-rules.md` section 7 | [x] |
| Protected | History invariant: each item's fields equal its history replayed, checked at the end of the key run | [x] |
| Next | Applying changes: one case per row of the change-tier table | [x] |
| Next | Lead actions and lifecycle: edit, remove, approve, discard; same field twice; ids repeat on a re-run; date order | [x] |
| Next | Turn splitting: wrapped lines, "Rohan's benefit:", CRLF, no speaker turn | [x] |
| First to go | One test per row of the transition tables; storage round trip | [x] |

The key-through-the-code fixture lives at `tests/fixtures/answer_key_changes/`, one file per day. It is test
data for the practice week, so it may name the week's people and tickets; nothing under `src/` may.

## Done when

- `pytest` passes with no key and no network.
- The four protected tests exist and pass.
- The final list from the key run matches the reference week on every field, including the soft items,
  since the fixture is the answer key and not model output.
- Anything dropped under the cut order is named in `progress/M2-list-engine.md`.

## Not in this milestone

- The prompt, the LLM interface, `extract` and `service` (M3).
- The web page and the command line (M3, M4).
- Saved model answers and the per-day properties on them (M3, M5).
- The word test on the prompt template: there is no template yet. The `src/` half of it can be added here
  if time allows.
