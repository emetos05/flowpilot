from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


class AgentRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)
    ]

    @field_validator("message")
    @classmethod
    def valid_postgres_text(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Message must not contain null characters")
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("Message must be valid Unicode") from None
        return value


class AgentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, revalidate_instances="always")

    summary: str = Field(min_length=1, max_length=2000)
    suggested_next_steps: list[str] = Field(max_length=10)
    needs_human_review: bool


class AgentRunResponse(BaseModel):
    run_id: UUID
    status: Literal["succeeded"] = "succeeded"
    output: AgentOutput
    created_at: datetime


class ErrorDetail(BaseModel):
    code: str
    message: str
    run_id: UUID | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
