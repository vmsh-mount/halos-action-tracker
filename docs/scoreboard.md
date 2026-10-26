# Scoreboard — the bars for quality, cost and speed

The agent is "good" only if it meets all of these together. A cheaper or faster configuration that drops
below the quality bars is not an improvement. This page lists each bar, how it is measured, where the current
configuration stands, and a target.

**The targets are proposals for the owner to set. None has been agreed.**

Current configuration: `openai/gpt-5-mini` through OpenRouter, default reasoning effort, prompt at commit
`17bda57`. Every figure is from three live runs of a five-day week (15 model calls), on 2026-10-11.

## Quality

| Bar | How it is measured | Practice week | Second week (unseen) | Proposed target |
|---|---|---|---|---|
| Invented quotes | Changes refused because their words are not in the transcript | 0 of 79 | 0 of 104 | 0. Code enforces that none is ever applied |
| Firm checks passed | Expected results written before the run, judged by hand | not scored this way | **93 of 126 (74%)** | ≥ 90% on transcripts not seen before |
| Work captured | Each piece of work in the answer key has an item | 30 of 30 | not scored this way | ≥ 95% |
| Items fully right at week's end | One item, right owner, due date, done or not | 25 of 30 (83%) | not scored this way | ≥ 90% |
| Unwanted items | Items for things that are not actions, and duplicates | 3 of 37 (8%) | 0 | ≤ 5% |
| Stability | Checks that pass in some runs and fail in others | 12 of 38 | 12 of 42 | ≤ 10% of checks |

## Cost

| Bar | How it is measured | Practice week | Second week | Proposed target |
|---|---|---|---|---|
| Billed per update | The provider's own cost figure, per model call | $0.0084 | $0.0113 | ≤ $0.01 |
| Billed per week | Five updates | $0.042 | $0.057 | ≤ $0.05 |
| Tokens in, mean | Provider's count | 2,864 | 3,643 | No target; watch the trend as the list grows |
| Tokens out, mean | Provider's count | 4,074 | 5,433 | No target; this is what drives the bill |

Where the money goes: output tokens are about 95% of the bill, and **about 85% of the output is the model's
own reasoning**, not the answer. Input is cheap here because 56 to 71% of it (the fixed instructions) is
served from the provider's cache.

## Speed and reliability

| Bar | How it is measured | Practice week | Second week | Proposed target |
|---|---|---|---|---|
| Seconds per update, median | Time for the model to answer | 23.6 | 33.6 | ≤ 15 |
| Seconds per update, slowest | | 29.7 | 40.8 | ≤ 30 |
| Calls needing a retry | Timeout, provider error or unreadable answer | 0 of 15 | 0 of 15 | ≤ 2% |
| Runs that failed outright | No draft produced | 0 | 0 | 0 |

The times for these runs were worked out afterwards from the gaps between calls (12 of the 15 calls in each
set), with three runs going at once. From now on each call's time is recorded with the run.

## Not measured yet

| Bar | Why it matters | What it needs |
|---|---|---|
| Lead's corrections per update | The real cost of a mistake is the lead's time | Reviewed days from real use. The owner's three test days show 6 corrections on 13 changes, which is an anecdote |
| Items needing attention per update | Too many flags and the lead stops reading them | The same |
| Time for a lead to review a day | The lead has to be able to check quickly | Watching someone do it |
| A different team | Nothing so far shows the prompt is not fitted to this one | A second team's transcripts and settings |

## The levers, most promising first

None of these has been tried. Each is a guess about cost and speed, with an unknown effect on quality, which
is why every bar above has to be re-measured for each.

| Lever | Expected effect | Risk |
|---|---|---|
| Lower the model's reasoning effort | Reasoning is ~85% of output, and output is ~95% of cost and most of the wait. The largest lever on both | The judgment calls (which item, whose date) are where the mistakes already are |
| A different model tier | A stronger model may fix the three mistakes seen in every second-week run; a smaller one is cheaper | Cost or quality, in opposite directions |
| Stop sending long-closed items | Input grows with the list for ever | A returning item would no longer be recognised |
| Ask for shorter notes | A small cut in output | Less context on the page |
| Shorten the instructions | Little: most of the input is cached | Rules dropped |

## How to compare configurations

1. One configuration is a model, a reasoning setting and a prompt version. Change one at a time.
2. Same transcripts, same starting list, at least three runs each.
3. Report every bar on this page for each configuration, side by side. Never one bar alone.
4. Quality bars first. Among the configurations that meet them, take the cheapest, then the fastest.
5. Use transcripts that have not been seen. Both weeks here are now seen, so a comparison made on them picks
   the configuration that fits these ten days.

The cost and speed figures are reproduced with:

```bash
.venv/bin/python tests/efficiency_report.py tests/live_runs/2026-10-11-1639 heldout/second-week/runs/2026-10-11-1700
```

Quality figures come from [progress/M5-live-repeats.md](../progress/M5-live-repeats.md) and
[heldout/second-week/results.md](../heldout/second-week/results.md).

| Configuration | Firm checks, unseen | Billed per update | Seconds, median | Retries |
|---|---|---|---|---|
| gpt-5-mini, default reasoning | 74% | $0.0113 | 33.6 | 0 of 15 |
