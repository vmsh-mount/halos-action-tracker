"""The command line. Does nothing except call the service and print."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

from . import review, service, store
from .llm import LLMError, make_client
from .models import DayRecord, Item
from .settings import load_settings

_DATED_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.txt$")


def _item_line(item: Item) -> str:
    due = item.due.isoformat() if item.due else "-"
    flag = "  [needs review: " + "; ".join(item.review_reasons) + "]" if item.review_reasons else ""
    return f"  {item.id:4} {item.status:11} {(item.owner or '-'):8} due {due:10} {item.title}{flag}"


def print_day(day: DayRecord) -> None:
    run = day.model_run
    print(f"\n== {day.standup.date} ({day.state}) " + (f"- {run.provider} / {run.model}" if run else ""))
    for note in run.notes if run else []:
        print(f"  note: {note}")
    if day.new_speakers:
        print(f"  new speakers: {', '.join(day.new_speakers)}")
    for change in day.checked_changes:
        words = " / ".join(f'"{q.text}"' for q in change.quotes) or "(no quotes found)"
        if change.outcome == "applied":
            diffs = ", ".join(f"{d.field}: {d.before} -> {d.after}" for d in change.diffs if d.field != "review_reasons")
            print(f"  {change.item_id:4} {' + '.join(change.change_labels) or 'marked':24} {diffs}\n         {words}")
            for flag in change.flags:
                print(f"         flag {flag.rule}: {flag.reason}")
        elif change.outcome == "could_not_verify":
            print(f"  ??   could not verify ({change.failure.rule}): {change.failure.reason}\n         {words}")
        elif change.outcome == "not_tracked":
            print(f"  {change.item_id:4} not applied: removed by lead\n         {words}")
    for entry in day.not_tracked:
        found = "" if entry.quote_found else "  (quote not found)"
        print(f'  not tracked: {entry.reason} - "{entry.quote}"{found}')


def print_list(items: list[Item]) -> None:
    shown = [i for i in items if not i.removed_on]
    print(f"\nThe list ({len(shown)} items):")
    for item in shown:
        print(_item_line(item))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="standup_tracker", description="Standup action tracker")
    commands = parser.add_subparsers(dest="command", required=True)
    process = commands.add_parser("process", help="submit one standup from a file")
    process.add_argument("file")
    process.add_argument("--date", help="YYYY-MM-DD; defaults to the file name")
    process.add_argument("--rerun", action="store_true", help="replace the draft for this date")
    process.add_argument("--record", action="store_true", help="save the model's answer for replay")
    commands.add_parser("approve", help="approve the draft as it stands")
    commands.add_parser("discard", help="throw the draft away")
    commands.add_parser("show", help="print the current list")
    week = commands.add_parser("run-week", help="process every dated file in a folder, approving each")
    week.add_argument("folder")
    week.add_argument("--record", action="store_true", help="save the model's answers for replay")
    commands.add_parser("reset", help="delete the saved state")
    serve = commands.add_parser("serve", help="start the review page")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    settings = load_settings()
    if args.command == "serve":
        import uvicorn

        from .web.app import create_app

        print(f"Review page: http://127.0.0.1:{args.port}")
        uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port, log_level="warning")
        return 0
    if args.command == "reset":
        settings.state_file.unlink(missing_ok=True)
        print(f"Deleted {settings.state_file}.")
        return 0

    try:
        state = store.load_state(settings.state_file)
        team = store.load_team(settings.team_file)

        if args.command == "show":
            if state.draft:
                print_day(state.draft)
                print_list(state.draft.items_after)
            else:
                print_list(service.current_items(state))
            return 0
        if args.command == "approve":
            day = review.approve(state)
            store.save_state(settings.state_file, state)
            print(f"Approved {day.standup.date}.")
            return 0
        if args.command == "discard":
            review.discard(state)
            store.save_state(settings.state_file, state)
            print("Draft discarded.")
            return 0

        client = make_client(settings.env, settings.saved_answers, record=args.record)
        if args.command == "process":
            files = [(Path(args.file), args.date)]
        else:
            files = [(p, None) for p in sorted(Path(args.folder).iterdir()) if _DATED_FILE.match(p.name)]
        for path, given in files:
            named = _DATED_FILE.match(path.name)
            if not (given or named):
                raise service.SubmitError(f"Give --date for {path.name}; its name is not a date.")
            date = dt.date.fromisoformat(given or named.group(1))
            try:
                day = service.submit_standup(
                    state, date, path.read_text(encoding="utf-8"), team, client,
                    confirm_rerun=getattr(args, "rerun", False), temperature=settings.temperature,
                )
            finally:
                store.save_state(settings.state_file, state)  # keeps a failed run's details
            print_day(day)
            if args.command == "run-week":
                review.approve(state)
                store.save_state(settings.state_file, state)
        print_list(state.draft.items_after if state.draft else service.current_items(state))
        return 0
    except (service.SubmitError, review.ReviewError, store.StoreError, LLMError, ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
