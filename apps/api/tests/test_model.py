from types import SimpleNamespace

import httpx
import pytest
from openai import APIConnectionError, APITimeoutError, OpenAI

from app.core.config import Settings
from app.errors import AgentError, ErrorCode
from app.schemas import AgentOutput
from app.services.model import OpenAIModelService


@pytest.mark.parametrize("mode", ["valid", "invalid_json", "wrong_type"])
def test_sdk_parses_real_response_format(monkeypatch, mode):
    """Exercise the actual OpenAI SDK parser, replacing only its HTTP transport."""
    import json

    output = {
        "summary": "Review the refund request.",
        "suggested_next_steps": ["Ask for the order number."],
        "needs_human_review": True,
    }
    if mode == "wrong_type":
        output["needs_human_review"] = "yes"

    def respond(request):
        payload = json.loads(request.content)
        assert payload["text"]["format"]["type"] == "json_schema"
        assert payload["text"]["format"]["strict"] is True
        assert payload["store"] is False
        assert "tools" not in payload
        return httpx.Response(
            200,
            json={
                "id": "resp_test",
                "object": "response",
                "created_at": 1,
                "model": "gpt-4o-mini",
                "status": "completed",
                "output": [
                    {
                        "id": "msg_test",
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "invalid-json"
                                if mode == "invalid_json"
                                else json.dumps(output),
                                "annotations": [],
                            }
                        ],
                    }
                ],
            },
        )

    monkeypatch.setattr(
        "app.services.model.OpenAI",
        lambda **kwargs: OpenAI(
            **kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond))
        ),
    )
    service = OpenAIModelService(Settings(_env_file=None, openai_api_key="test-key"))
    if mode == "valid":
        assert service.generate("Review") == AgentOutput(**output)
    else:
        with pytest.raises(AgentError) as caught:
            service.generate("Review")
        assert caught.value.code == ErrorCode.INVALID_MODEL_OUTPUT


@pytest.mark.parametrize(
    ("mode", "code"),
    [
        ("refusal", ErrorCode.MODEL_REFUSED),
        ("incomplete", ErrorCode.INVALID_MODEL_OUTPUT),
        ("empty", ErrorCode.INVALID_MODEL_OUTPUT),
        ("timeout", ErrorCode.MODEL_TIMEOUT),
        ("connection", ErrorCode.MODEL_UNAVAILABLE),
    ],
)
def test_provider_error_mapping(monkeypatch, mode, code):
    def parse(**kwargs):
        request = httpx.Request("POST", "https://api.openai.com/v1/responses")
        if mode == "timeout":
            raise APITimeoutError(request=request)
        if mode == "connection":
            raise APIConnectionError(request=request)
        return SimpleNamespace(
            status="incomplete" if mode == "incomplete" else "completed",
            output_parsed=None,
            output=[SimpleNamespace(type="message", content=[SimpleNamespace(type="refusal")])]
            if mode == "refusal"
            else [],
        )

    class Client:
        responses = SimpleNamespace(parse=parse)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr("app.services.model.OpenAI", lambda **kwargs: Client())
    with pytest.raises(AgentError) as caught:
        OpenAIModelService(Settings(_env_file=None, openai_api_key="test-key")).generate("Review")
    assert caught.value.code == code


def test_missing_key_does_not_call_provider(monkeypatch):
    def unexpected(**kwargs):
        pytest.fail("Provider must not be constructed without a key")

    monkeypatch.setattr("app.services.model.OpenAI", unexpected)
    with pytest.raises(AgentError) as caught:
        OpenAIModelService(Settings(_env_file=None, openai_api_key="")).generate("Review")
    assert caught.value.code == ErrorCode.MODEL_NOT_CONFIGURED


def test_configuration_comes_from_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-marker")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:secret-marker@localhost/db")
    monkeypatch.setenv("OPENAI_MODEL", "configured-model")
    config = Settings(_env_file=None)
    assert config.openai_model == "configured-model"
    assert config.openai_api_key.get_secret_value() == "secret-marker"
    assert "secret-marker" not in repr(config)
