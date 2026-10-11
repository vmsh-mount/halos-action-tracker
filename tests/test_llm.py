"""The LLM layer and answer parsing (components-and-data-flow section 3, implementation-details 3.2). No network."""

import json

import httpx
import pytest

from standup_tracker.extract import ModelRunFailed, parse_answer, propose
from standup_tracker.llm import LLMFatal, LLMRequest, LLMResponse, LLMRetryable, LLMUnavailable, fingerprint, make_client
from standup_tracker.llm.chat_api import ChatAPIClient
from standup_tracker.llm.replay import DIFFERENT_REQUEST, RecordingClient, ReplayClient

GOOD = '{"changes": [], "not_tracked": []}'
REQUEST = LLMRequest(instructions="rules", input="today", answer_shape={"type": "object"}, lookup_key="2025-10-13-abc")


def chat(handler):
    return ChatAPIClient("https://example.test/v1/", "k", "some/model", http=httpx.Client(transport=httpx.MockTransport(handler)))


def answer(text, status=200, **extra):
    return httpx.Response(status, json={"model": "some/model-1", "choices": [{"message": {"content": text}}], **extra})


class Scripted:
    """A client that plays back a list of responses or errors, and keeps the requests it was sent."""

    def __init__(self, *script):
        self.script, self.sent = list(script), []

    def complete(self, request):
        self.sent.append(request)
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return LLMResponse(text=step, provider="api", model="m")


# --- which client is used


def test_no_key_or_an_empty_key_means_replay(tmp_path):
    assert isinstance(make_client({}, tmp_path), ReplayClient)
    assert isinstance(make_client({"LLM_API_KEY": "  ", "LLM_MODEL": "m", "LLM_BASE_URL": "u"}, tmp_path), ReplayClient)


def test_a_key_selects_the_chat_api_and_the_provider_setting_overrides(tmp_path):
    live = {"LLM_API_KEY": "k", "LLM_MODEL": "m", "LLM_BASE_URL": "https://example.test/v1"}
    assert isinstance(make_client(live, tmp_path), ChatAPIClient)
    assert isinstance(make_client(live | {"LLM_PROVIDER": "replay"}, tmp_path), ReplayClient)
    assert isinstance(make_client(live, tmp_path, record=True), RecordingClient)


@pytest.mark.parametrize("missing", ["LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL"])
def test_the_chat_api_names_the_setting_that_is_missing(tmp_path, missing):
    env = {"LLM_PROVIDER": "api", "LLM_API_KEY": "k", "LLM_MODEL": "m", "LLM_BASE_URL": "u"} | {missing: ""}
    with pytest.raises(LLMUnavailable, match=missing):
        make_client(env, tmp_path)


# --- the chat API client


def test_request_shape_and_temperature_only_when_set():
    seen = []

    def handler(request):
        seen.append((str(request.url), request.headers["authorization"], json.loads(request.content)))
        return answer(GOOD)

    response = chat(handler).complete(REQUEST)
    chat(handler).complete(LLMRequest("rules", "today", {}, "k", temperature=0))
    url, auth, body = seen[0]
    assert (url, auth) == ("https://example.test/v1/chat/completions", "Bearer k")
    assert [m["role"] for m in body["messages"]] == ["system", "user"] and "temperature" not in body
    assert seen[1][2]["temperature"] == 0
    assert (response.text, response.provider, response.model) == (GOOD, "api", "some/model-1")


def timeout(request):
    raise httpx.ReadTimeout("slow", request=request)


@pytest.mark.parametrize("handler", [
    timeout,
    lambda r: httpx.Response(503, text="down"),
    lambda r: httpx.Response(200, json={"error": {"message": "upstream failed"}}),
    lambda r: answer(""),
    lambda r: httpx.Response(200, json={"choices": []}),
    lambda r: httpx.Response(200, text="not json"),
])
def test_retryable_failures(handler):
    with pytest.raises(LLMRetryable):
        chat(handler).complete(REQUEST)


def test_rate_limit_carries_the_pause():
    with pytest.raises(LLMRetryable) as given:
        chat(lambda r: httpx.Response(429, headers={"retry-after": "2"})).complete(REQUEST)
    with pytest.raises(LLMRetryable) as default:
        chat(lambda r: httpx.Response(429)).complete(REQUEST)
    assert (given.value.pause, default.value.pause) == (2.0, 5.0)


@pytest.mark.parametrize("status", [400, 401, 402, 404])
def test_other_client_errors_are_not_retried(status):
    with pytest.raises(LLMFatal, match=str(status)):
        chat(lambda r: httpx.Response(status, json={"error": {"message": "no"}})).complete(REQUEST)


# --- reading the answer, and the one retry


def test_code_fence_is_stripped_and_extra_keys_ignored():
    changes, not_tracked = parse_answer('```json\n{"changes": [{"kind": "add", "surprise": 1}], "extra": true}\n```')
    assert changes[0].kind == "add" and not_tracked is None


@pytest.mark.parametrize("text", ["sorry, I cannot", "[1, 2]", '{"not_tracked": []}', '{"changes": "none"}'])
def test_unreadable_answers(text):
    with pytest.raises(ValueError):
        parse_answer(text)


def test_things_that_are_not_objects_in_the_list_are_kept_for_refusal():
    changes, _ = parse_answer('{"changes": ["text", 7, {"kind": "update"}]}')
    assert [c.unparsed for c in changes] == ["text", 7, None]


def test_an_unreadable_answer_is_retried_once_with_the_error_fed_back():
    client = Scripted("I think the changes are...", GOOD)
    proposal = propose(client, REQUEST)
    assert len(client.sent) == 2 and "could not be used" in client.sent[1].input and "not JSON" in client.sent[1].input
    assert proposal.attempts == ["I think the changes are...", GOOD]
    assert proposal.fingerprint == fingerprint(REQUEST) == fingerprint(client.sent[1])


def test_a_transport_failure_is_retried_once_after_its_pause():
    slept = []
    proposal = propose(Scripted(LLMRetryable("rate limited", pause=3), GOOD), REQUEST, sleep=slept.append)
    assert slept == [3] and proposal.changes == []


def test_never_more_than_two_attempts_whatever_the_causes():
    client = Scripted(LLMRetryable("timeout"), "not json", GOOD)
    with pytest.raises(ModelRunFailed) as failed:
        propose(client, REQUEST, sleep=lambda s: None)
    assert len(client.sent) == 2 and failed.value.attempts == ["[error] timeout", "not json"]


def test_a_fatal_error_is_not_retried():
    client = Scripted(LLMFatal("bad key"), GOOD)
    with pytest.raises(LLMFatal):
        propose(client, REQUEST)
    assert len(client.sent) == 1


# --- saved answers


def test_record_then_replay_and_a_miss_stops(tmp_path):
    RecordingClient(Scripted(GOOD), tmp_path).complete(REQUEST)
    replayed = ReplayClient(tmp_path).complete(REQUEST)
    assert (replayed.text, replayed.provider) == (GOOD, "replay") and len(replayed.notes) == 1
    with pytest.raises(LLMUnavailable, match="No saved answer"):
        ReplayClient(tmp_path).complete(LLMRequest("rules", "today", {}, "2025-10-13-other"))


def test_replay_of_a_different_request_under_the_same_key_carries_a_note(tmp_path):
    RecordingClient(Scripted(GOOD), tmp_path).complete(REQUEST)
    changed = LLMRequest("rules", "today, with an edited list", {"type": "object"}, REQUEST.lookup_key)
    assert DIFFERENT_REQUEST in ReplayClient(tmp_path).complete(changed).notes


def test_a_recorded_retry_keeps_the_fingerprint_of_the_first_request(tmp_path):
    recorder = RecordingClient(Scripted("not json", GOOD), tmp_path)
    propose(recorder, REQUEST)
    saved = json.loads((tmp_path / f"{REQUEST.lookup_key}.json").read_text())
    assert saved["answer"] == GOOD and saved["request_fingerprint"] == fingerprint(REQUEST)
    assert ReplayClient(tmp_path).complete(REQUEST).notes == [f"Saved answer, recorded {saved['recorded_at'][:10]} from m."]


def test_the_rate_limit_pause_is_capped():
    with pytest.raises(LLMRetryable) as asked:
        chat(lambda r: httpx.Response(429, headers={"retry-after": "900"})).complete(REQUEST)
    assert asked.value.pause == 30.0


def test_a_sentence_around_the_json_does_not_cost_the_retry():
    changes, _ = parse_answer('Here are the changes:\n{"changes": [{"kind": "add"}]}\nLet me know if you need more.')
    assert len(changes) == 1
    client = Scripted('Sure. {"changes": []} Done.')
    assert propose(client, REQUEST).changes == [] and len(client.sent) == 1


@pytest.mark.parametrize("content", ["{ not json", '{"model": "m"}', '{"answer": 5}', "[]"])
def test_a_corrupt_saved_answer_is_an_llm_error(tmp_path, content):
    (tmp_path / f"{REQUEST.lookup_key}.json").write_text(content)
    with pytest.raises(LLMUnavailable, match="cannot be read"):
        ReplayClient(tmp_path).complete(REQUEST)
