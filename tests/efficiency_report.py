"""Cost, speed and size of the model calls in saved live runs. Nothing is called; it only reads saved runs.

    .venv/bin/python tests/efficiency_report.py tests/live_runs/2026-10-11-1639 heldout/second-week/runs/2026-10-11-1700

For each folder of runs it prints, per standup processed (one model call): tokens in and out, how much of the
output was the model's reasoning, how much of the input the provider served from its cache, what the provider
billed, how long the call took, and how often a retry was needed.
"""

from __future__ import annotations

import datetime as dt
import json
import statistics
import sys
from pathlib import Path


def calls_in(folder: Path) -> tuple[list[dict], int, str]:
    about = json.loads((folder / "about.json").read_text()) if (folder / "about.json").exists() else {}
    runs = sorted(folder.glob("run-*.json"))
    calls: list[dict] = []
    for path in runs:
        days = [d for d in json.loads(path.read_text())["state"]["days"] if (d.get("model_run") or {}).get("usage")]
        previous = None
        for day in days:
            run, usage = day["model_run"], day["model_run"]["usage"]
            at = dt.datetime.fromisoformat(run["at"])
            # Older runs did not record how long a call took. The gap since the previous call in the same run
            # is the call plus a few milliseconds of our own work; the first call of a run has no such gap.
            seconds = run.get("seconds") or ((at - previous).total_seconds() if previous else None)
            previous = at
            calls.append({
                "in": usage.get("prompt_tokens", 0),
                "out": usage.get("completion_tokens", 0),
                "reasoning": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
                "cached": (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0),
                "billed": usage.get("cost"),
                "seconds": seconds,
                "timed": bool(run.get("seconds")),
                "attempts": len(run.get("attempts") or [1]),
                "changes": len(day["checked_changes"]),
                "refused": sum(1 for c in day["checked_changes"] if c.get("failure")),
            })
    return calls, len(runs), about.get("model", "?")


def report(folder: Path) -> None:
    calls, runs, model = calls_in(folder)
    if not calls:
        print(f"\n{folder}: no live calls found")
        return
    mean = lambda key: statistics.mean(c[key] for c in calls)  # noqa: E731
    seconds = [c["seconds"] for c in calls if c["seconds"] is not None]
    billed = [c["billed"] for c in calls if c["billed"] is not None]
    how_timed = "recorded" if all(c["timed"] for c in calls) else f"from the gaps between calls, {len(seconds)} of {len(calls)} calls"
    print(f"\n{folder}")
    print(f"  model {model} · {runs} runs · {len(calls)} calls · {len(calls) // runs} per run")
    print(f"  tokens in, mean        {mean('in'):>8.0f}   of which served from the provider's cache {100 * mean('cached') / mean('in'):.0f}%")
    print(f"  tokens out, mean       {mean('out'):>8.0f}   of which the model's reasoning {100 * mean('reasoning') / mean('out'):.0f}%")
    if billed:
        print(f"  billed per call, mean  {'$%.4f' % statistics.mean(billed):>8}   per run ${sum(billed) / runs:.3f}   all runs ${sum(billed):.2f}")
    if seconds:
        print(f"  seconds per call       {statistics.median(seconds):>8.1f}   median; mean {statistics.mean(seconds):.1f}, slowest {max(seconds):.1f} ({how_timed})")
    print(f"  calls needing a retry  {sum(c['attempts'] > 1 for c in calls):>8}   of {len(calls)}")
    print(f"  changes proposed       {sum(c['changes'] for c in calls):>8}   refused by a check: {sum(c['refused'] for c in calls)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for name in sys.argv[1:]:
        report(Path(name))
