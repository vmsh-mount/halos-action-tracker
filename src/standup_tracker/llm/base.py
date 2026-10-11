from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class LLMRequest:
    instructions: str
    input: str
    answer_shape: dict
    lookup_key: str  # opaque to this package; the caller chooses it
    temperature: float | None = None  # sent only when set; many models do not accept one
    original_fingerprint: str | None = None  # set on a retry, so the retry is filed under the first request


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    usage: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


class LLMError(Exception):
    """Something went wrong reaching or reading the model."""


class LLMUnavailable(LLMError):
    """Nothing was sent: a setting is missing, or there is no saved answer."""


class LLMRetryable(LLMError):
    """Worth one more attempt. pause is how long to wait first, in seconds."""

    def __init__(self, message: str, pause: float = 0.0):
        super().__init__(message)
        self.pause = pause


class LLMFatal(LLMError):
    """Not worth another attempt: a bad key, no credit, a refused request."""


class LLMClient(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse: ...


def fingerprint(request: LLMRequest) -> str:
    """A short hash of what was asked: instructions, input and answer shape. Not the model name."""
    if request.original_fingerprint:
        return request.original_fingerprint
    body = json.dumps([request.instructions, request.input, request.answer_shape], sort_keys=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
