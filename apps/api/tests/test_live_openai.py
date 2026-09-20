import os
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db import PostgresRunRepository
from app.main import app, get_settings
from app.schemas import AgentRunResponse


@pytest.mark.live
@pytest.mark.skipif(os.getenv("RUN_LIVE_OPENAI") != "1", reason="Opt in with RUN_LIVE_OPENAI=1")
def test_live_openai_result_is_persisted():
    """One billable model request. Keeps the run as acceptance evidence."""
    config = Settings()
    assert config.openai_api_key and config.openai_api_key.get_secret_value(), (
        "Configure OPENAI_API_KEY"
    )
    assert config.database_url, "Configure DATABASE_URL"
    repository = PostgresRunRepository(config.database_url.get_secret_value())
    repository.initialize()
    get_settings.cache_clear()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/agent/run",
            json={
                "message": "A customer asks whether a refund is possible. We have no order or policy details. Summarize and suggest a safe next step."
            },
        )
    assert response.status_code == 200, response.text
    result = AgentRunResponse.model_validate(response.json())
    with repository.connect() as connection:
        row = connection.execute(
            "SELECT status, output FROM agent_runs WHERE id = %s", (UUID(str(result.run_id)),)
        ).fetchone()
    assert row == ("succeeded", result.output.model_dump())
    print(f"Verified live OpenAI run: {result.run_id}")
