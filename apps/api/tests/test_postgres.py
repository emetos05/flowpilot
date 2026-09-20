import os
from uuid import UUID

import psycopg
import pytest

from app.db import PostgresRunRepository
from app.errors import AgentError, ErrorCode
from app.main import app, get_repository

pytestmark = pytest.mark.integration


@pytest.fixture
def postgres():
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Set TEST_DATABASE_URL to run real PostgreSQL integration tests")
    repository = PostgresRunRepository(dsn)
    repository.initialize()
    # All tests use unique run IDs. Never truncate or drop a shared database.
    return repository


@pytest.mark.parametrize("failure", [False, True])
def test_endpoint_commits_rows_visible_to_new_connections(api, postgres, failure):
    client, _, model = api
    app.dependency_overrides[get_repository] = lambda: postgres
    if failure:
        model.error = AgentError(ErrorCode.MODEL_TIMEOUT)
    response = client.post("/agent/run", json={"message": "Day 2 persistence test"})
    assert response.status_code == (504 if failure else 200)
    body = response.json()
    run_id = UUID(body["error"]["run_id"] if failure else body["run_id"])
    try:
        with psycopg.connect(postgres.dsn) as connection:
            row = connection.execute(
                "SELECT status, output, error_code, completed_at FROM agent_runs WHERE id = %s",
                (run_id,),
            ).fetchone()
        assert row[0] == ("failed" if failure else "succeeded")
        assert row[1] == (None if failure else body["output"])
        assert row[2] == ("model_timeout" if failure else None)
        assert row[3] is not None
    finally:
        with psycopg.connect(postgres.dsn) as connection:
            connection.execute("DELETE FROM agent_runs WHERE id = %s", (run_id,))


def test_initialization_is_repeatable(postgres):
    postgres.initialize()
    postgres.initialize()
