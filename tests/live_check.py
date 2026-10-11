"""Runs the practice week against the live model several times and reports each property as "passed N of M".

    .venv/bin/python tests/live_check.py --runs 3

Needs LLM_API_KEY, LLM_BASE_URL and LLM_MODEL (from .env). It costs money: five model calls per run.
Each run starts from an empty list and approves every day with no edits. Every run is saved in full under
tests/live_runs/, then the property tests in test_practice_saved_answers.py are put to each saved run.

With --evaluate-only <folder> nothing is called; the saved runs in that folder are evaluated again.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from standup_tracker import review, service, store  # noqa: E402
from standup_tracker.llm import make_client  # noqa: E402
from standup_tracker.models import State  # noqa: E402
from standup_tracker.settings import load_settings  # noqa: E402

WEEK = ["2025-10-13", "2025-10-14", "2025-10-15", "2025-10-16", "2025-10-17"]
# US dollars per million tokens, from the provider's public list on 2026-10-11. Used only for the estimate.
PRICES = {"openai/gpt-5-mini": (0.25, 2.00)}


def run_week(number: int, settings, team, folder: Path) -> Path:
    client = make_client(settings.env | {"LLM_PROVIDER": "api"}, settings.saved_answers)
    state, drafts = State(), []
    for day in WEEK:
        text = (ROOT / "transcripts" / f"{day}.txt").read_text(encoding="utf-8")
        draft = service.submit_standup(
            state, dt.date.fromisoformat(day), text, team, client, temperature=settings.temperature
        )
        drafts.append(draft.model_dump(mode="json", by_alias=True))
        review.approve(state)
        print(f"  run {number}: {day} done", flush=True)
    path = folder / f"run-{number}.json"
    path.write_text(json.dumps({"state": state.model_dump(mode="json", by_alias=True), "drafts": drafts}, indent=1))
    return path


def evaluate(path: Path) -> dict[str, str]:
    """Property name -> passed / failed / skipped, by running the property tests on one saved run."""
    report = path.with_suffix(".junit.xml")
    env = os.environ | {"PRACTICE_RUN_FILE": str(path)}
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_practice_saved_answers.py", f"--junitxml={report}", "-p", "no:cacheprovider"],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    outcomes = {}
    for case in ET.parse(report).getroot().iter("testcase"):
        if case.find("skipped") is not None:
            continue
        failed = case.find("failure") is not None or case.find("error") is not None
        outcomes[case.get("name")] = "failed" if failed else "passed"
    report.unlink()
    return outcomes


def usage_of(path: Path) -> tuple[int, int, int, int]:
    state = json.loads(path.read_text())["state"]
    days = state["days"]
    used = [day["model_run"]["usage"] for day in days]
    refused = sum(1 for day in days for c in day["checked_changes"] if (c.get("failure") or {}).get("rule") == "C1")
    proposed = sum(len(day["checked_changes"]) for day in days)
    return sum(u.get("prompt_tokens", 0) for u in used), sum(u.get("completion_tokens", 0) for u in used), refused, proposed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--evaluate-only", metavar="FOLDER")
    args = parser.parse_args()

    settings = load_settings()
    model = settings.env.get("LLM_MODEL", "?")
    if args.evaluate_only:
        folder = Path(args.evaluate_only)
        paths = sorted(folder.glob("run-*.json"))
    else:
        team = store.load_team(ROOT / "config" / "team.json")
        folder = ROOT / "tests" / "live_runs" / dt.datetime.now().strftime("%Y-%m-%d-%H%M")
        folder.mkdir(parents=True, exist_ok=True)
        print(f"Running the practice week {args.runs} times on {model} ({args.runs * len(WEEK)} model calls)…", flush=True)
        with ThreadPoolExecutor(max_workers=args.runs) as pool:
            paths = sorted(pool.map(lambda n: run_week(n, settings, team, folder), range(1, args.runs + 1)))
        (folder / "about.json").write_text(json.dumps({"model": model, "runs": args.runs, "at": dt.datetime.now().isoformat(timespec="seconds")}, indent=1))

    results: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        for name, outcome in evaluate(path).items():
            results[name].append(outcome)

    total = len(paths)
    print(f"\n{'Property':92} passed")
    for name, outcomes in results.items():
        passed = outcomes.count("passed")
        note = "" if passed in (0, total) else "   unstable"
        print(f"{name[:90]:92} {passed} of {total}{note}")
    stable = sum(1 for o in results.values() if o.count("passed") == total)
    never = sum(1 for o in results.values() if o.count("passed") == 0)
    print(f"\n{len(results)} properties: {stable} passed every run, {never} passed in none, {len(results) - stable - never} unstable.")

    price_in, price_out = PRICES.get(model, (None, None))
    print(f"\n{'Run':8} {'changes':>8} {'refused (C1)':>13} {'tokens in':>10} {'tokens out':>11} {'est. cost':>10}")
    spent = 0.0
    for path in paths:
        tokens_in, tokens_out, refused, proposed = usage_of(path)
        cost = (tokens_in * price_in + tokens_out * price_out) / 1e6 if price_in else None
        spent += cost or 0
        print(f"{path.stem:8} {proposed:>8} {refused:>13} {tokens_in:>10} {tokens_out:>11} {('$%.3f' % cost) if cost is not None else 'n/a':>10}")
    if price_in:
        print(f"Estimated total: ${spent:.2f} (tokens as the provider reported them, at ${price_in}/${price_out} per million).")
    print(f"\nRuns saved in {folder.relative_to(ROOT) if folder.is_relative_to(ROOT) else folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
