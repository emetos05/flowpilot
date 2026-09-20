from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app, get_model_service, get_repository, get_settings
from app.schemas import AgentOutput


class MemoryRepository:
    def __init__(self):
        self.records = {}

    def create(self, message, model):
        run_id = uuid4()
        created_at = datetime.now(UTC)
        self.records[run_id] = {
            "message": message,
            "model": model,
            "status": "running",
            "created_at": created_at,
        }
        return run_id, created_at

    def succeed(self, run_id, output):
        self.records[run_id].update(status="succeeded", output=output.model_dump())

    def fail(self, run_id, code):
        self.records[run_id].update(status="failed", error_code=code)


class StubModel:
    def __init__(self):
        self.calls = []
        self.error = None
        self.result = AgentOutput(
            summary="A customer asks about a refund.",
            suggested_next_steps=["Ask a human to check the order and refund policy."],
            needs_human_review=True,
        )

    def generate(self, message):
        self.calls.append(message)
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def api():
    repository = MemoryRepository()
    model = StubModel()
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, openai_api_key="test-key", openai_model="test-model"
    )
    app.dependency_overrides[get_repository] = lambda: repository
    app.dependency_overrides[get_model_service] = lambda: model
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, repository, model
    app.dependency_overrides.clear()
