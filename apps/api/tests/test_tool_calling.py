import json

import httpx
import pytest
from openai import OpenAI

from app.core.config import Settings
from app.errors import AgentError, ErrorCode
from app.main import app, get_model_service
from app.services.model import OpenAIModelService
from app.tools.registry import ToolRegistry


def envelope(output, status="completed"):
    return {
        "id": "resp_test",
        "object": "response",
        "created_at": 1,
        "model": "gpt-4o-mini",
        "status": status,
        "output": output,
    }


def call(name="get_order", arguments='{"order_id":"ord_1001"}', call_id="call_1"):
    return {
        "type": "function_call",
        "id": "fc_1",
        "call_id": call_id,
        "name": name,
        "arguments": arguments,
        "status": "completed",
    }


def answer():
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "status": "completed",
        "content": [
            {
                "type": "output_text",
                "annotations": [],
                "text": json.dumps(
                    {
                        "summary": "The demo lookup has been processed.",
                        "suggested_next_steps": ["Ask a human to review."],
                        "needs_human_review": True,
                    }
                ),
            }
        ],
    }


class RecordingRegistry(ToolRegistry):
    def __init__(self):
        super().__init__()
        self.executed = []

    def execute(self, name, arguments):
        result = super().execute(name, arguments)
        self.executed.append((name, json.loads(arguments), result))
        return result


def service_with_transport(monkeypatch, respond, registry=None):
    monkeypatch.setattr(
        "app.services.model.OpenAI",
        lambda **kwargs: OpenAI(
            **kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond))
        ),
    )
    return OpenAIModelService(Settings(_env_file=None, openai_api_key="test-key"), registry)


@pytest.mark.parametrize(
    ("name", "arguments", "expected_status"),
    [
        ("get_customer", {"customer_id": "cus_001"}, "found"),
        ("get_order", {"order_id": "ord_1001"}, "found"),
        ("get_refund_policy", {"policy_id": "standard"}, "found"),
        ("get_order", {"order_id": "ord_9999"}, "not_found"),
        ("get_order", {"order_id": 123}, "invalid_arguments"),
        ("issue_refund", {}, "unknown_tool"),
    ],
)
def test_sdk_tool_call_result_and_final_persistence(
    api, monkeypatch, name, arguments, expected_status
):
    client, repository, _ = api
    requests = []
    registry = RecordingRegistry()

    def respond(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert payload["store"] is False
        if len(requests) == 1:
            assert payload["tool_choice"] == "auto"
            assert payload["parallel_tool_calls"] is False
            return httpx.Response(200, json=envelope([call(name, json.dumps(arguments))]))
        assert payload["tool_choice"] == "none"
        replay = payload["input"][1]
        assert replay["type"] == "function_call"
        assert "parsed_arguments" not in replay
        tool_result = payload["input"][2]
        assert tool_result["type"] == "function_call_output"
        assert tool_result["call_id"] == "call_1"
        assert json.loads(tool_result["output"])["status"] == expected_status
        return httpx.Response(200, json=envelope([answer()]))

    service = service_with_transport(monkeypatch, respond, registry)
    app.dependency_overrides[get_model_service] = lambda: service
    # No keyword branching: execution follows the provider-selected tool, not this text.
    response = client.post("/agent/run", json={"message": "Please look it up."})
    assert response.status_code == 200
    assert len(requests) == 2
    assert registry.executed[0][0] == name
    assert next(iter(repository.records.values()))["output"] == response.json()["output"]


@pytest.mark.parametrize(
    "mode",
    ["multiple", "incomplete", "malformed_json", "second_call", "second_refusal", "second_timeout"],
)
def test_bad_provider_calls_fail_safely(monkeypatch, mode):
    requests = []
    registry = RecordingRegistry()

    def respond(request):
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            if mode == "multiple":
                return httpx.Response(200, json=envelope([call(), call(call_id="call_2")]))
            if mode == "malformed_json":
                return httpx.Response(200, json=envelope([call(arguments="not-json")]))
            return httpx.Response(
                200, json=envelope([call()], "incomplete" if mode == "incomplete" else "completed")
            )
        if mode == "second_timeout":
            raise httpx.ReadTimeout("secret-marker", request=request)
        if mode == "second_refusal":
            item = answer()
            item["content"] = [{"type": "refusal", "refusal": "secret-marker"}]
            return httpx.Response(200, json=envelope([item]))
        return httpx.Response(200, json=envelope([call()]))

    service = service_with_transport(monkeypatch, respond, registry)
    with pytest.raises(AgentError) as caught:
        service.generate("Review order ord_1001")
    assert caught.value.code == {
        "second_refusal": ErrorCode.MODEL_REFUSED,
        "second_timeout": ErrorCode.MODEL_TIMEOUT,
    }.get(mode, ErrorCode.INVALID_MODEL_OUTPUT)
    assert "secret-marker" not in str(caught.value)
    assert len(requests) <= 2
    assert len(registry.executed) <= 1
