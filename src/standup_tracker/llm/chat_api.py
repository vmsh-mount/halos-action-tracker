"""A client for any chat-completions endpoint. Nothing in it is specific to one provider."""

from __future__ import annotations

import httpx

from .base import LLMFatal, LLMRequest, LLMResponse, LLMRetryable

TIMEOUT_SECONDS = 180.0  # a reasoning model reading a long prompt can take well over a minute
DEFAULT_RATE_LIMIT_PAUSE = 5.0
MAX_RATE_LIMIT_PAUSE = 30.0  # never wait longer than this, whatever the provider asks


class ChatAPIClient:
    def __init__(self, base_url: str, api_key: str, model: str, *, http: httpx.Client | None = None):
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.api_key = api_key
        self.model = model
        self.http = http or httpx.Client(timeout=TIMEOUT_SECONDS)

    def complete(self, request: LLMRequest) -> LLMResponse:
        body: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.instructions},
                {"role": "user", "content": request.input},
            ],
            "response_format": {"type": "json_object"},
        }
        if request.temperature is not None:
            body["temperature"] = request.temperature
        try:
            reply = self.http.post(self.url, json=body, headers={"Authorization": f"Bearer {self.api_key}"})
        except httpx.TimeoutException as error:
            raise LLMRetryable(f"The model did not answer within {TIMEOUT_SECONDS:.0f} seconds.") from error
        except httpx.HTTPError as error:
            raise LLMRetryable(f"Could not reach the model: {error}") from error

        if reply.status_code == 429:
            raise LLMRetryable("The provider is rate limiting (429).", pause=_retry_after(reply))
        if reply.status_code >= 500:
            raise LLMRetryable(f"The provider had an error ({reply.status_code}).")
        if reply.status_code >= 400:
            raise LLMFatal(f"The provider refused the request ({reply.status_code}): {_error_text(reply)}")

        try:
            data = reply.json()
        except ValueError as error:
            raise LLMRetryable("The provider's reply was not JSON.") from error
        if not isinstance(data, dict) or data.get("error"):
            raise LLMRetryable(f"The provider returned an error in place of an answer: {_error_text(reply)}")
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            text = None
        if not isinstance(text, str) or not text.strip():
            raise LLMRetryable("The provider returned an empty answer.")
        return LLMResponse(text=text, provider="api", model=str(data.get("model") or self.model), usage=data.get("usage") or {})


def _retry_after(reply: httpx.Response) -> float:
    try:
        asked = float(reply.headers.get("retry-after", ""))
    except ValueError:
        return DEFAULT_RATE_LIMIT_PAUSE
    return min(max(0.0, asked), MAX_RATE_LIMIT_PAUSE)


def _error_text(reply: httpx.Response) -> str:
    try:
        error = reply.json().get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error)[:300]
        if error:
            return str(error)[:300]
    except (ValueError, AttributeError):
        pass
    return reply.text[:300]
