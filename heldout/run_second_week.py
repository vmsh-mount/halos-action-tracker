"""Runs the second week (20 to 24 October 2025) against the live model, several times.

    .venv/bin/python heldout/run_second_week.py --runs 3

Every run starts from the list a correct practice week ends with: the answer key run through the real code.
Each day is approved with no edits. Runs are saved in full under heldout/second-week/runs/, with a text
report per run for judging by hand against expected-results.md. Costs money: five model calls per run.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from conftest import run_week as practice_week_from_the_answer_key  # noqa: E402
from standup_tracker import cli, review, service, store  # noqa: E402
from standup_tracker.llm import make_client  # noqa: E402
from standup_tracker.settings import load_settings  # noqa: E402

WEEK = ["2025-10-20", "2025-10-21", "2025-10-22", "2025-10-23", "2025-10-24"]
FOLDER = ROOT / "heldout" / "second-week"


def run(number: int, settings, team, out: Path) -> None:
    client = make_client(settings.env | {"LLM_PROVIDER": "api"}, settings.saved_answers)
    state = practice_week_from_the_answer_key(team)
    report, drafts = io.StringIO(), []
    for day in WEEK:
        text = (FOLDER / f"{day}.txt").read_text(encoding="utf-8")
        draft = service.submit_standup(state, dt.date.fromisoformat(day), text, team, client, temperature=settings.temperature)
        drafts.append(draft.model_dump(mode="json", by_alias=True))
        with contextlib.redirect_stdout(report):
            cli.print_day(draft)
            cli.print_list(draft.items_after)
        review.approve(state)
        print(f"  run {number}: {day} done", flush=True)
    (out / f"run-{number}.json").write_text(json.dumps({"state": state.model_dump(mode="json", by_alias=True), "drafts": drafts}, indent=1))
    (out / f"run-{number}.txt").write_text(report.getvalue())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    settings = load_settings()
    team = store.load_team(ROOT / "config" / "team.json")
    out = FOLDER / "runs" / dt.datetime.now().strftime("%Y-%m-%d-%H%M")
    out.mkdir(parents=True, exist_ok=True)
    model = settings.env.get("LLM_MODEL", "?")
    print(f"Running the second week {args.runs} times on {model} ({args.runs * len(WEEK)} model calls)…", flush=True)
    with ThreadPoolExecutor(max_workers=args.runs) as pool:
        list(pool.map(lambda n: run(n, settings, team, out), range(1, args.runs + 1)))
    (out / "about.json").write_text(json.dumps({"model": model, "runs": args.runs, "at": dt.datetime.now().isoformat(timespec="seconds")}, indent=1))
    for path in sorted(out.glob("run-*.json")):
        days = json.loads(path.read_text())["state"]["days"][-len(WEEK):]
        used = [d["model_run"]["usage"] for d in days]
        refused = sum(1 for d in days for c in d["checked_changes"] if c.get("failure"))
        print(f"{path.stem}: {sum(len(d['checked_changes']) for d in days)} changes, {refused} refused, "
              f"{sum(u.get('prompt_tokens', 0) for u in used)} tokens in, {sum(u.get('completion_tokens', 0) for u in used)} out, "
              f"{len([i for i in days[-1]['items_after'] if not i.get('removed_on')])} items at the end")
    print(f"Saved in {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
