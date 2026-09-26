from uuid import UUID

import pytest

from app.errors import AgentError, ErrorCode
from app.main import app, get_model_service
from app.schemas import AgentRunResponse


def test_success_commits_validated_output(api):
    client, repository, model = api
    response = client.post("/agent/run", json={"message": "  Review a refund  "})
    assert response.status_code == 200
    result = AgentRunResponse.model_validate(response.json())
    assert result.created_at.tzinfo is not None
    assert repository.records[result.run_id]["output"] == result.output.model_dump()
    assert repository.records[result.run_id]["status"] == "succeeded"
    assert model.calls == ["Review a refund"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"message": ""},
        {"message": " \n "},
        {"message": "x" * 10001},
        {"message": 123},
        {"message": None},
        {"message": "hi", "api_key": "secret-marker"},
    ],
)
def test_invalid_requests_are_rejected_without_model_or_record(api, payload):
    client, repository, model = api
    response = client.post("/agent/run", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    assert "secret-marker" not in response.text
    assert not repository.records
    assert not model.calls


def test_malformed_json_is_sanitized(api):
    client, repository, model = api
    response = client.post(
        "/agent/run",
        content='{"message": "secret-marker"',
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert "secret-marker" not in response.text
    assert not repository.records
    assert not model.calls


@pytest.mark.parametrize(
    ("code", "status"),
    [
        (ErrorCode.AGENT_TIMEOUT, 504),
        (ErrorCode.AGENT_STEP_LIMIT, 502),
        (ErrorCode.INVALID_TOOL_CALL, 502),
        (ErrorCode.TOOL_FAILED, 502),
        (ErrorCode.MODEL_TIMEOUT, 504),
        (ErrorCode.MODEL_UNAVAILABLE, 502),
        (ErrorCode.MODEL_REFUSED, 422),
        (ErrorCode.MODEL_NOT_CONFIGURED, 503),
        (ErrorCode.INVALID_MODEL_OUTPUT, 502),
    ],
)
def test_provider_failures_have_durable_failed_record(api, code, status):
    client, repository, model = api
    model.error = AgentError(code)
    response = client.post("/agent/run", json={"message": "Refund request"})
    assert response.status_code == status
    run_id = UUID(response.json()["error"]["run_id"])
    assert repository.records[run_id]["status"] == "failed"
    assert repository.records[run_id]["error_code"] == code


def test_record_exists_before_provider_call(api):
    client, repository, _ = api

    class CheckingModel:
        def generate(self, message):
            assert len(repository.records) == 1
            assert next(iter(repository.records.values()))["status"] == "running"
            raise AgentError(ErrorCode.MODEL_REFUSED)

    app.dependency_overrides[get_model_service] = CheckingModel
    assert client.post("/agent/run", json={"message": "Review"}).status_code == 422


def test_invalid_output_cannot_be_reported_as_success(api):
    client, repository, model = api
    model.result = {"summary": "missing required fields"}
    response = client.post("/agent/run", json={"message": "Review"})
    assert response.status_code == 502
    assert next(iter(repository.records.values()))["status"] == "failed"


def test_unexpected_error_does_not_leak_secrets(api, caplog):
    client, repository, model = api
    model.error = RuntimeError("secret-marker: postgres password and provider detail")
    response = client.post("/agent/run", json={"message": "Review"})
    assert response.status_code == 500
    assert "secret-marker" not in response.text + caplog.text + str(repository.records)


def test_storage_failure_prevents_model_call(api, monkeypatch):
    client, repository, model = api

    def unavailable(*args):
        raise AgentError(ErrorCode.STORAGE_UNAVAILABLE)

    monkeypatch.setattr(repository, "create", unavailable)
    response = client.post("/agent/run", json={"message": "Review"})
    assert response.status_code == 503
    assert not model.calls


def test_final_commit_failure_is_not_success(api, monkeypatch):
    client, repository, _ = api

    def unavailable(run_id, output):
        raise AgentError(ErrorCode.STORAGE_UNAVAILABLE, run_id)

    monkeypatch.setattr(repository, "succeed", unavailable)
    response = client.post("/agent/run", json={"message": "Review"})
    assert response.status_code == 503
    assert next(iter(repository.records.values()))["status"] == "running"


def test_day_one_routes_are_preserved(api):
    client, _, _ = api
    assert client.get("/health").json() == {"status": "ok"}
    assert client.post("/api/agent/run", json={"message": "hello"}).json() == {
        "message": "Received message: hello",
        "status": "received",
    }


@pytest.mark.parametrize("message", ["null\x00character", "invalid\ud800unicode"])
def test_unstorable_input_is_rejected(api, message):
    import json

    client, repository, model = api
    response = client.post(
        "/agent/run",
        content=json.dumps({"message": message}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert not repository.records
    assert not model.calls


def test_each_submission_has_a_unique_record(api):
    client, repository, _ = api
    first = client.post("/agent/run", json={"message": "Review"})
    second = client.post("/agent/run", json={"message": "Review"})
    assert first.status_code == second.status_code == 200
    assert first.json()["run_id"] != second.json()["run_id"]
    assert len(repository.records) == 2
