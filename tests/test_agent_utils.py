from types import SimpleNamespace

import httpx
import pytest
from openai import APITimeoutError, BadRequestError

from src.agents.utils import AgentInvocationError, OpenAIClient


def test_chat_retries_retryable_openai_errors(monkeypatch):
    client = OpenAIClient(api_key="test", base_url="https://example.com/v1", request_timeout=5.0, max_retries=2)
    request = httpx.Request("POST", "https://example.com/v1/chat/completions")
    calls = {"count": 0}

    def fake_create(**kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise APITimeoutError(request=request)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))])

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)
    monkeypatch.setattr("src.agents.utils.time.sleep", lambda seconds: None)

    assert client.chat(model="gpt-4.1-mini", system="s", user="u") == "ok"
    assert calls["count"] == 2


def test_chat_fails_fast_on_non_retryable_openai_errors(monkeypatch):
    client = OpenAIClient(api_key="test", base_url="https://example.com/v1", request_timeout=5.0, max_retries=3)
    response = httpx.Response(400, request=httpx.Request("POST", "https://example.com/v1/chat/completions"))
    calls = {"count": 0}

    def fake_create(**kwargs):
        calls["count"] += 1
        raise BadRequestError(message="bad input", response=response, body={})

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)

    with pytest.raises(AgentInvocationError, match="rejected by API"):
        client.chat(model="gpt-4.1-mini", system="s", user="u")

    assert calls["count"] == 1
