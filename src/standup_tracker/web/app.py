"""Routes for the review page. Every route loads the state, calls the service or review functions, saves."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from urllib.parse import quote_plus

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from .. import review, service, store, vocab
from ..llm import LLMError, make_client
from ..settings import Settings, load_settings
from . import views

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
TEMPLATES.env.filters["day"] = views.show_date
TEMPLATES.env.filters["label"] = views.label_text
TEMPLATES.env.filters["reason"] = views.friendly_reason
TEMPLATES.env.filters["run_note"] = views.friendly_note
TEMPLATES.env.globals["status_label"] = lambda key: views.STATUS_LABELS.get(key, key)
TEMPLATES.env.globals["status_group"] = views.status_group
# The stylesheet and script are plain files, put into the page as they are (never read as templates).
TEMPLATES.env.globals["asset"] = lambda name: Markup((Path(__file__).parent / "templates" / name).read_text(encoding="utf-8"))


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="Standup action tracker", docs_url=None, redoc_url=None)

    def load():
        return store.load_state(settings.state_file), store.load_team(settings.team_file)

    @app.exception_handler(store.StoreError)
    def unreadable_state(request: Request, problem: store.StoreError):
        text = f"The saved state cannot be used.\n\n{problem}\n\nMove the file aside, or run: python -m standup_tracker reset"
        return PlainTextResponse(text, status_code=500)

    def mode() -> dict:
        key = (settings.env.get("LLM_API_KEY") or "").strip()
        forced = (settings.env.get("LLM_PROVIDER") or "").strip().lower()
        if forced == "api" or (not forced and key):
            return {"live": True, "label": "Live", "detail": settings.env.get("LLM_MODEL", "")}
        return {"live": False, "label": "Replay mode", "detail": "No API key is set, so only the sample transcripts can be processed."}

    def back(message: str = "", error: str = "") -> RedirectResponse:
        query = f"?message={quote_plus(message)}" if message else f"?error={quote_plus(error)}" if error else ""
        return RedirectResponse(f"/{query}", status_code=303)

    def page(request: Request, state, team, *, message="", error="", form=None, ask_rerun=False, status=200):
        draft = state.draft
        context = {
            "message": message, "error": error, "mode": mode(), "ask_rerun": ask_rerun,
            "statuses": vocab.STATUSES, "failed": state.last_failed_run,
            "form": form or {"date": "", "text": ""},
        }
        if draft:
            changed, listed = views.rows_for(draft)
            attention, new, updated = views.split_changed(changed)
            context |= {
                "draft": draft, "listed": listed, "attention": attention, "new": new, "updated": updated,
                "removed": [row for row in changed if row.item.removed_on],
                "mentions": views.mentions_without_change(draft),
                "refused": [c for c in draft.checked_changes if c.outcome == "could_not_verify"],
                "people": views.known_people(draft, draft.items_after, team),
                "overview": views.overview(listed),
                "n_new": sum("added" in row.labels for row in changed if not row.item.removed_on),
                "n_changed": sum("added" not in row.labels for row in changed if not row.item.removed_on),
            }
            return TEMPLATES.TemplateResponse(request, "draft.html", context, status_code=status)
        last = state.days[-1] if state.days else None
        listed = views.rows_for_list(service.current_items(state), last.standup.date if last else None)
        context |= {"last": last, "days": state.days, "listed": listed, "overview": views.overview(listed)}
        if not context["form"]["date"] and last:
            context["form"] = {"date": (last.standup.date + dt.timedelta(days=1)).isoformat(), "text": ""}
        return TEMPLATES.TemplateResponse(request, "list.html", context, status_code=status)

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, message: str = "", error: str = ""):
        state, team = load()
        return page(request, state, team, message=message, error=error)

    @app.post("/standup")
    def submit(
        request: Request,
        date: str = Form(""),
        text: str = Form(""),
        confirm_rerun: str = Form(""),
        file: UploadFile | None = File(None),
    ):
        state, team = load()
        if file is not None and file.filename:
            # A chosen file wins over the box. Its text goes into the form, so a failed run keeps it.
            try:
                text = file.file.read().decode("utf-8-sig")
            except UnicodeDecodeError:
                form = {"date": date, "text": text}
                problem = f"{file.filename} isn’t a text file. Attach a .txt transcript or paste the text."
                return page(request, state, team, error=problem, form=form, status=400)
            named = views.date_in_name(file.filename)
            date = date or named
        form = {"date": date, "text": text}
        try:
            day = dt.date.fromisoformat(date)
        except ValueError:
            return page(request, state, team, error="Choose the date of this update.", form=form, status=400)
        try:
            client = make_client(settings.env, settings.saved_answers)
            service.submit_standup(
                state, day, text, team, client, confirm_rerun=bool(confirm_rerun), temperature=settings.temperature
            )
        except service.RerunNeedsConfirmation as problem:
            return page(request, state, team, error=str(problem), form=form, ask_rerun=True, status=409)
        except service.SubmitFailed as problem:
            store.save_state(settings.state_file, state)  # keeps the failed run's details
            return page(request, state, team, error=f"This update couldn’t be processed, and nothing was changed. {problem}", form=form, status=502)
        except (service.SubmitError, LLMError) as problem:
            return page(request, state, team, error=str(problem), form=form, status=400)
        store.save_state(settings.state_file, state)
        return back()

    @app.post("/items/{item_id}/edit")
    def edit(item_id: str, owner: str = Form(""), due: str = Form(""), status: str = Form("")):
        state, team = load()
        try:
            when = dt.date.fromisoformat(due) if due.strip() else None
            review.edit_item(state, item_id, team, owner=owner, due=when, status=status)
        except ValueError as problem:  # ReviewError is one
            return back(error=str(problem))
        store.save_state(settings.state_file, state)
        return back(message=f"Saved changes to {item_id}.")

    @app.post("/items/{item_id}/reviewed")
    def reviewed(item_id: str):
        state, _ = load()
        try:
            review.mark_reviewed(state, item_id)
        except review.ReviewError as problem:
            return back(error=str(problem))
        store.save_state(settings.state_file, state)
        return back(message=f"{item_id} kept as proposed.")

    @app.post("/items/{item_id}/remove")
    def remove(item_id: str):
        state, _ = load()
        try:
            review.remove_item(state, item_id)
        except review.ReviewError as problem:
            return back(error=str(problem))
        store.save_state(settings.state_file, state)
        return back(message=f"{item_id} removed. It won’t be added again from future updates.")

    @app.post("/approve")
    def approve():
        state, _ = load()
        try:
            day = review.approve(state)
        except review.ReviewError as problem:
            return back(error=str(problem))
        store.save_state(settings.state_file, state)
        return back(message=f"Update for {views.show_date(day.standup.date)} approved. Tracked work is up to date.")

    @app.post("/discard")
    def discard():
        state, _ = load()
        try:
            review.discard(state)
        except review.ReviewError as problem:
            return back(error=str(problem))
        store.save_state(settings.state_file, state)
        return back(message="Update discarded. Tracked work is unchanged.")

    @app.get("/items/{item_id}", response_class=HTMLResponse)
    def item(request: Request, item_id: str):
        state, _ = load()
        items = state.draft.items_after if state.draft else service.current_items(state)
        found = next((i for i in items if i.id == item_id), None)
        if found is None:
            return back(error=f"No item {item_id}.")
        entries = [
            {"entry": entry, "steps": views._steps(entry.diffs), "labels": views.labels_for(entry.diffs, added=index == 0)}
            for index, entry in enumerate(found.history)
        ]
        row = views._row(found, (state.draft or (state.days[-1] if state.days else None)).standup.date)
        context = {"item": found, "row": row, "entries": entries, "mode": mode(), "pending": state.draft is not None}
        return TEMPLATES.TemplateResponse(request, "item.html", context)

    return app
