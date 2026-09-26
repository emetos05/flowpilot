import json
import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db import PostgresRunRepository
from app.main import app, get_model_service, get_settings
from app.schemas import AgentRunResponse
from app.services.model import OpenAIModelService
from app.tools.registry import ToolRegistry

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.getenv("RUN_LIVE_OPENAI") != "1", reason="Opt in with RUN_LIVE_OPENAI=1"),
]


class ObservedTools(ToolRegistry):
    def __init__(self):
        super().__init__()
        self.calls = []

    def execute(self, name, arguments):
        result = super().execute(name, arguments)
        self.calls.append((name, json.loads(arguments), result))
        return result


@pytest.mark.parametrize(
    ("message", "expected_tool", "expected_arguments", "fact"),
    [
        (
            "Who is cus_001, and what service tier are they on?",
            "get_customer",
            {"customer_id": "cus_001"},
            "maya",
        ),
        ("Has ord_1001 arrived yet?", "get_order", {"order_id": "ord_1001"}, "delivered"),
        (
            "How long is the standard return window, and what conditions apply?",
            "get_refund_policy",
            {"policy_id": "standard"},
            "30",
        ),
    ],
)
def test_live_model_selects_executes_and_persists(message, expected_tool, expected_arguments, fact):
    """Billable calls are bounded by AGENT_MAX_STEPS; retain acceptance evidence."""
    settings = Settings()
    assert settings.database_url and settings.openai_api_key, "Configure database and OpenAI"
    repository = PostgresRunRepository(settings.database_url.get_secret_value())
    repository.initialize()
    registry = ObservedTools()
    service = OpenAIModelService(settings, registry)
    get_settings.cache_clear()
    app.dependency_overrides[get_model_service] = lambda: service
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post("/agent/run", json={"message": message})
        assert response.status_code == 200, response.text
        result = AgentRunResponse.model_validate(response.json())
        assert len(registry.calls) == 1
        name, arguments, tool_result = registry.calls[0]
        assert name == expected_tool
        assert arguments == expected_arguments
        assert tool_result.status == "found"
        assert fact in result.output.summary.lower()
        with repository.connect() as connection:
            row = connection.execute(
                "SELECT status, output FROM agent_runs WHERE id = %s", (result.run_id,)
            ).fetchone()
        assert row == ("succeeded", result.output.model_dump())
        print(f"Verified {expected_tool}: run {result.run_id}")
    finally:
        app.dependency_overrides.pop(get_model_service, None)
        get_settings.cache_clear()


def test_live_chained_order_customer_policy():
    settings = Settings()
    assert settings.database_url and settings.openai_api_key, "Configure database and OpenAI"
    repository = PostgresRunRepository(settings.database_url.get_secret_value())
    repository.initialize()
    registry = ObservedTools()
    events = []
    service = OpenAIModelService(settings, registry, observer=events.append)
    get_settings.cache_clear()
    app.dependency_overrides[get_model_service] = lambda: service
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/agent/run",
                json={
                    "message": (
                        "For order ord_1001, find its status, the associated customer's name and tier, "
                        "and the return window and conditions of the policy attached to that order. "
                        "Summarize all of these demo facts; do not issue a refund."
                    )
                },
            )
        assert response.status_code == 200, response.text
        result = AgentRunResponse.model_validate(response.json())
        assert len(registry.calls) == 3
        assert registry.calls[0][:2] == ("get_order", {"order_id": "ord_1001"})
        assert {(name, tuple(arguments.items())) for name, arguments, _ in registry.calls[1:]} == {
            ("get_customer", (("customer_id", "cus_001"),)),
            ("get_refund_policy", (("policy_id", "standard"),)),
        }
        assert all(record.status == "found" for _, _, record in registry.calls)
        text = result.output.model_dump_json().lower()
        assert all(fact in text for fact in ("maya", "standard", "delivered", "30"))
        assert events[-1].phase == "succeeded"
        assert events[-1].step == 4
        with repository.connect() as connection:
            row = connection.execute(
                "SELECT status, output FROM agent_runs WHERE id = %s", (result.run_id,)
            ).fetchone()
        assert row == ("succeeded", result.output.model_dump())
        print(f"Verified chained order/customer/policy: run {result.run_id}; 4 decisions, 3 tools")
    finally:
        app.dependency_overrides.pop(get_model_service, None)
        get_settings.cache_clear()
