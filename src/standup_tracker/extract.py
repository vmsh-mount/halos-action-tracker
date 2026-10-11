"""Sends the request through the LLM interface and turns the answer into proposed changes. Applies nothing."""

from __future__ import annotations

import dataclasses
import json
import re
import time
from dataclasses import dataclass, field

from .apply import proposed_from_raw
from .llm import LLMClient, LLMError, LLMRequest, LLMResponse, LLMRetryable, fingerprint
from .models import ProposedChange

MAX_ATTEMPTS = 2
_FENCE = re.compile(r"^\s*```[a-zA-Z0-9_-]*\s*\n(.*?)\n?\s*```\s*$", re.DOTALL)


class UnreadableAnswer(ValueError):
    pass


class ModelRunFailed(LLMError):
    """The run produced nothing usable. attempts holds whatever raw text came back."""

    def __init__(self, message: str, attempts: list[str]):
        super().__init__(message)
        self.attempts = attempts


@dataclass
class Proposal:
    changes: list[ProposedChange]
    not_tracked: list | None
    response: LLMResponse
    fingerprint: str
    attempts: list[str] = field(default_factory=list)


def parse_answer(text: str) -> tuple[list[ProposedChange], list | None]:
    """Only an answer that cannot be read at all is refused. A slip inside one change is handled later."""
    fenced = _FENCE.match(text)
    if fenced:
        text = fenced.group(1)
    try:
        data = json.loads(text)
    except ValueError as error:
        # A sentence before or after the object is common. Try what lies between the outer braces.
        start, end = text.find("{"), text.rfind("}")
        try:
            data = json.loads(text[start : end + 1]) if 0 <= start < end else None
        except ValueError:
            data = None
        if data is None:
            raise UnreadableAnswer(f"The answer is not JSON: {error}") from error
    if not isinstance(data, dict):
        raise UnreadableAnswer("The answer is not a JSON object.")
    if not isinstance(data.get("changes"), list):
        raise UnreadableAnswer('The answer has no "changes" list.')
    not_tracked = data.get("not_tracked")
    return [proposed_from_raw(raw) for raw in data["changes"]], not_tracked if isinstance(not_tracked, list) else None


def propose(client: LLMClient, request: LLMRequest, *, sleep=time.sleep) -> Proposal:
    """At most two attempts in all, whatever the cause of the first failure."""
    original = fingerprint(request)
    attempts: list[str] = []
    current = request
    problem = "no attempt was made"
    for _ in range(MAX_ATTEMPTS):
        try:
            response = client.complete(current)
        except LLMRetryable as error:
            problem = str(error)
            attempts.append(f"[error] {problem}")
            if error.pause:
                sleep(error.pause)
            continue
        attempts.append(response.text)
        try:
            changes, not_tracked = parse_answer(response.text)
        except UnreadableAnswer as error:
            problem = str(error)
            # The same request tends to get the same wrong answer, so say what was wrong.
            current = dataclasses.replace(
                request,
                input=f"{request.input}\n\nYour previous answer could not be used. {problem} Return only the JSON object.",
                original_fingerprint=original,
            )
            continue
        return Proposal(changes, not_tracked, response, original, attempts)
    raise ModelRunFailed(f"The model's answer could not be used after {MAX_ATTEMPTS} attempts. {problem}", attempts)
