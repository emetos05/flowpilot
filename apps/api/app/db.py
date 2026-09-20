from datetime import datetime
from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

import psycopg
from psycopg.types.json import Jsonb

from app.core.config import Settings
from app.errors import AgentError, ErrorCode
from app.schemas import AgentOutput


class RunRepository(Protocol):
    def create(self, message: str, model: str) -> tuple[UUID, datetime]: ...

    def succeed(self, run_id: UUID, output: AgentOutput) -> None: ...

    def fail(self, run_id: UUID, code: ErrorCode) -> None: ...


class PostgresRunRepository:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def connect(self):
        return psycopg.connect(self.dsn, connect_timeout=5, options="-c statement_timeout=5000")

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute(Path(__file__).with_name("schema.sql").read_text())

    def create(self, message: str, model: str) -> tuple[UUID, datetime]:
        run_id = uuid4()
        try:
            with self.connect() as connection:
                row = connection.execute(
                    "INSERT INTO agent_runs (id, message, model, status) "
                    "VALUES (%s, %s, %s, 'running') RETURNING created_at",
                    (run_id, message, model),
                ).fetchone()
            return run_id, row[0]
        except psycopg.Error:
            raise AgentError(ErrorCode.STORAGE_UNAVAILABLE) from None

    def succeed(self, run_id: UUID, output: AgentOutput) -> None:
        self._finish(run_id, "succeeded", Jsonb(output.model_dump(mode="json")), None)

    def fail(self, run_id: UUID, code: ErrorCode) -> None:
        self._finish(run_id, "failed", None, code.value)

    def _finish(self, run_id: UUID, status: str, output: Jsonb | None, code: str | None):
        try:
            with self.connect() as connection:
                cursor = connection.execute(
                    "UPDATE agent_runs SET status = %s, output = %s, error_code = %s, "
                    "completed_at = clock_timestamp() WHERE id = %s AND status = 'running'",
                    (status, output, code, run_id),
                )
                if cursor.rowcount != 1:
                    raise AgentError(ErrorCode.STORAGE_UNAVAILABLE, run_id)
        except psycopg.Error:
            raise AgentError(ErrorCode.STORAGE_UNAVAILABLE, run_id) from None


def initialize_database() -> None:
    try:
        settings = Settings()
        if settings.database_url is None:
            raise ValueError("Missing database configuration")
        PostgresRunRepository(settings.database_url.get_secret_value()).initialize()
    except ValueError, psycopg.Error:
        raise SystemExit(
            "Database initialization failed. Check configuration and connectivity."
        ) from None
    print("Agent-run schema initialized.")


if __name__ == "__main__":
    initialize_database()
