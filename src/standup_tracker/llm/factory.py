from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .base import LLMClient, LLMUnavailable
from .chat_api import ChatAPIClient
from .replay import RecordingClient, ReplayClient


def make_client(settings: Mapping[str, str], saved_answers: str | Path, *, record: bool = False) -> LLMClient:
    """LLM_PROVIDER decides if set. Otherwise a key that is not empty means the chat API, and no key means Replay."""

    def get(name: str) -> str:
        return (settings.get(name) or "").strip()

    provider = get("LLM_PROVIDER").lower() or ("api" if get("LLM_API_KEY") else "replay")
    if provider == "replay":
        return ReplayClient(saved_answers)
    if provider != "api":
        raise LLMUnavailable(f"LLM_PROVIDER is {provider!r}; it must be 'api' or 'replay'.")
    for name in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
        if not get(name):
            raise LLMUnavailable(f"{name} is not set. Set it in .env, or leave LLM_API_KEY empty to use saved answers.")
    client: LLMClient = ChatAPIClient(get("LLM_BASE_URL"), get("LLM_API_KEY"), get("LLM_MODEL"))
    return RecordingClient(client, saved_answers) if record else client
