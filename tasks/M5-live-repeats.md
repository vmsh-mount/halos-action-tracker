# M5 — Live repeats of the practice week

Budget: 40 min. Plan: [PLAN.md](../PLAN.md) section 3. Method: `docs/evaluation-checks.md` section 6.

| # | Item | Done |
|---|---|---|
| 1 | `tests/live_check.py`: run the five days from an empty state N times against the live model, approving each day with no edits; save every run in full under `tests/live_runs/` | [x] |
| 2 | Evaluate each saved run with the same property tests used on the saved answers, with the recording's expected-failure marks switched off | [x] |
| 3 | Print each property as "passed N of 3", the number of changes refused for an unfound quote per run, and token counts with an estimated cost | [x] |
| 4 | Three runs on `openai/gpt-5-mini` (fifteen calls, about $0.30, approved) | [x] |
| 5 | Results written to `progress/M5-live-repeats.md` as they came out | [x] |

The script lives under `tests/`, not in the package, because it needs the practice week's anchors, which are
test data. The prompt, the item lines and the engine stay frozen; nothing is changed in response to what
these runs show.

## Done when

- Three complete runs are saved and every property has a count out of three.
- The prompt is unchanged from the commit the saved answers were recorded against.
