"""Saved answers: Replay returns them, the Recorder makes them."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .base import LLMClient, LLMRequest, LLMResponse, LLMUnavailable, fingerprint

NO_SAVED_ANSWER = "No saved answer for this transcript. Set LLM_API_KEY to use a live model."
DIFFERENT_REQUEST = "This saved answer was recorded against a different list or prompt."


def _path(folder: Path, lookup_key: str) -> Path:
    return folder / f"{lookup_key}.json"


class ReplayClient:
    """Answers only the question it was recorded for. No key, no network."""

    def __init__(self, folder: str | Path):
        self.folder = Path(folder)

    def complete(self, request: LLMRequest) -> LLMResponse:
        path = _path(self.folder, request.lookup_key)
        if not path.exists():
            raise LLMUnavailable(NO_SAVED_ANSWER)
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            answer = saved["answer"]
            if not isinstance(answer, str):
                raise TypeError("answer is not text")
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            raise LLMUnavailable(f"The saved answer {path.name} cannot be read: {error}") from error
        notes = [f"Saved answer, recorded {saved.get('recorded_at', '?')[:10]} from {saved.get('model', '?')}."]
        if saved.get("request_fingerprint") != fingerprint(request):
            notes.append(DIFFERENT_REQUEST)
        return LLMResponse(text=answer, provider="replay", model=str(saved.get("model", "")), notes=notes)


class RecordingClient:
    """Wraps another client and saves each answer under its lookup key."""

    def __init__(self, inner: LLMClient, folder: str | Path):
        self.inner = inner
        self.folder = Path(folder)

    def complete(self, request: LLMRequest) -> LLMResponse:
        response = self.inner.complete(request)
        self.folder.mkdir(parents=True, exist_ok=True)
        saved = {
            "lookup_key": request.lookup_key,
            "request_fingerprint": fingerprint(request),
            "provider": response.provider,
            "model": response.model,
            "recorded_at": dt.datetime.now().isoformat(timespec="seconds"),
            "answer": response.text,
        }
        _path(self.folder, request.lookup_key).write_text(json.dumps(saved, indent=2), encoding="utf-8")
        return response
