import json
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from pydantic import ValidationError
from test_tool_calling import RecordingRegistry, answer, call, envelope, service_with_transport

from app.core.config import Settings
from app.errors import AgentError, ErrorCode
from app.main import app, get_model_service
from app.services.state import Phase, RunState


def test_chained_lookups_preserve_history_and_transitions(api, monkeypatch, caplog):
    client, repository, _ = api
    events, requests = [], []
    calls = [
        call(call_id="order"),
        call("get_customer", '{"customer_id":"cus_001"}', "customer"),
        call("get_refund_policy", '{"policy_id":"standard"}', "policy"),
    ]

    def respond(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert payload["tool_choice"] == "auto"
        assert payload["parallel_tool_calls"] is False
        results = [i for i in payload["input"] if i.get("type") == "function_call_output"]
        assert [i["call_id"] for i in results] == [c["call_id"] for c in calls[: len(requests) - 1]]
        if len(requests) == 2:
            record = json.loads(results[0]["output"])["record"]
            assert record["customer_id"] == "cus_001"
            assert record["refund_policy_id"] == "standard"
        item = calls[len(requests) - 1] if len(requests) <= 3 else answer()
        return httpx.Response(200, json=envelope([item]))

    registry = RecordingRegistry()
    service = service_with_transport(monkeypatch, respond, registry)
    service.observer = events.append
    app.dependency_overrides[get_model_service] = lambda: service
    caplog.set_level("INFO", logger="uvicorn.error.agent")
    response = client.post("/agent/run", json={"message": "secret-marker"})
    assert response.status_code == 200
    assert len(requests) == 4
    assert len(registry.executed) == 3
    assert [e.phase for e in events] == [
        Phase.SELECTING,
        Phase.EXECUTING,
        Phase.OBSERVING,
        Phase.DECIDING,
    ] * 3 + [Phase.SELECTING, Phase.SUCCEEDED]
    assert events[-1].step == 4
    assert len({e.execution_id for e in events}) == 1
    assert "phase=observing" in caplog.text
    assert "secret-marker" not in caplog.text
    assert next(iter(repository.records.values()))["status"] == "succeeded"


@pytest.mark.parametrize("limit", [1, 2, 6])
def test_endless_tool_calls_hit_exact_limit(api, monkeypatch, limit):
    client, repository, _ = api
    requests, events = [], []
    registry = RecordingRegistry()

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=envelope([call(call_id=f"call_{len(requests)}")]))

    service = service_with_transport(monkeypatch, respond, registry)
    service.settings.agent_max_steps = limit
    service.observer = events.append
    app.dependency_overrides[get_model_service] = lambda: service
    response = client.post("/agent/run", json={"message": "Keep looking"})
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "agent_step_limit"
    assert len(requests) == limit
    assert len(registry.executed) == limit - 1
    assert events[-1].phase == Phase.FAILED
    assert events[-1].error_code == ErrorCode.AGENT_STEP_LIMIT
    assert next(iter(repository.records.values()))["error_code"] == ErrorCode.AGENT_STEP_LIMIT


@pytest.mark.parametrize("mode", ["unknown", "arguments", "exception"])
def test_invalid_or_failing_tool_stops_before_next_decision(api, monkeypatch, mode):
    client, repository, _ = api
    requests, events = [], []
    registry = RecordingRegistry()

    def respond(request):
        requests.append(request)
        item = call("secret-marker", "{}") if mode == "unknown" else call()
        if mode == "arguments":
            item = call(arguments='{"order_id":123}')
        return httpx.Response(200, json=envelope([item]))

    if mode == "exception":

        def broken(*args):
            raise RuntimeError("secret-marker")

        monkeypatch.setattr(registry, "execute", broken)
    service = service_with_transport(monkeypatch, respond, registry)
    service.observer = events.append
    app.dependency_overrides[get_model_service] = lambda: service
    response = client.post("/agent/run", json={"message": "Review"})
    expected = "tool_failed" if mode == "exception" else "invalid_tool_call"
    assert response.status_code == 502
    assert response.json()["error"]["code"] == expected
    assert "secret-marker" not in response.text
    assert len(requests) == 1
    assert events[-1].phase == Phase.FAILED
    assert next(iter(repository.records.values()))["error_code"] == expected


@pytest.mark.parametrize("slow_stage", ["provider", "tool", "final"])
def test_deadline_rejects_late_results_and_stops_work(monkeypatch, slow_stage):
    now = [0.0]
    monkeypatch.setattr("app.services.model.monotonic", lambda: now[0])
    requests, events = [], []
    registry = RecordingRegistry()
    execute = registry.execute

    def slow_tool(*args):
        result = execute(*args)
        now[0] = 11
        return result

    if slow_stage == "tool":
        monkeypatch.setattr(registry, "execute", slow_tool)

    def respond(request):
        requests.append(request)
        assert request.extensions["timeout"]["read"] <= 10
        if slow_stage in {"provider", "final"}:
            now[0] = 11
        return httpx.Response(200, json=envelope([answer() if slow_stage == "final" else call()]))

    service = service_with_transport(monkeypatch, respond, registry)
    service.settings.agent_timeout_seconds = 10
    service.observer = events.append
    with pytest.raises(AgentError, match="agent_timeout"):
        service.generate("Review")
    assert len(requests) == 1
    assert len(registry.executed) == (1 if slow_stage == "tool" else 0)
    assert events[-1].phase == Phase.FAILED


def test_remaining_budget_reduces_next_request_timeout(monkeypatch):
    now = [0.0]
    requests = []
    monkeypatch.setattr("app.services.model.monotonic", lambda: now[0])

    def respond(request):
        requests.append(request)
        assert request.extensions["timeout"]["read"] == (10 if len(requests) == 1 else 3)
        now[0] = 7
        return httpx.Response(200, json=envelope([call() if len(requests) == 1 else answer()]))

    service = service_with_transport(monkeypatch, respond)
    service.settings.agent_timeout_seconds = 10
    service.generate("Review")
    assert len(requests) == 2


def test_reused_service_has_isolated_concurrent_state(monkeypatch):
    events = []
    service = service_with_transport(
        monkeypatch, lambda request: httpx.Response(200, json=envelope([answer()]))
    )
    service.observer = events.append
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(service.generate, ["first", "second"]))
    assert len(results) == 2
    ids = {e.execution_id for e in events}
    assert len(ids) == 2
    for execution_id in ids:
        assert [e.phase for e in events if e.execution_id == execution_id] == [
            Phase.SELECTING,
            Phase.SUCCEEDED,
        ]


def test_terminal_state_cannot_restart():
    state = RunState()
    state.transition(Phase.FAILED, ErrorCode.AGENT_TIMEOUT)
    with pytest.raises(RuntimeError):
        state.transition(Phase.SELECTING)


@pytest.mark.parametrize(
    "values",
    [
        {"agent_max_steps": 0},
        {"agent_max_steps": 21},
        {"agent_timeout_seconds": 0},
        {"agent_timeout_seconds": 301},
    ],
)
def test_loop_limits_are_validated(values):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)
