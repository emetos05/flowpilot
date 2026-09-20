import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import Settings
from app.db import PostgresRunRepository, RunRepository
from app.errors import ERRORS, AgentError, ErrorCode
from app.schemas import AgentRunRequest, AgentRunResponse, ErrorDetail, ErrorResponse
from app.services.agent import AgentRunner
from app.services.model import ModelService, OpenAIModelService

app = FastAPI(title="FlowPilot API")
logger = logging.getLogger("flowpilot")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_repository(settings: Annotated[Settings, Depends(get_settings)]) -> RunRepository:
    if settings.database_url is None:
        raise AgentError(ErrorCode.STORAGE_UNAVAILABLE)
    return PostgresRunRepository(settings.database_url.get_secret_value())


def get_model_service(settings: Annotated[Settings, Depends(get_settings)]) -> ModelService:
    return OpenAIModelService(settings)


@app.exception_handler(AgentError)
async def agent_error_handler(request: Request, error: AgentError):
    status, message = ERRORS[error.code]
    logger.warning("agent_run_error code=%s run_id=%s", error.code, error.run_id)
    body = ErrorResponse(error=ErrorDetail(code=error.code, message=message, run_id=error.run_id))
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, error: RequestValidationError):
    # FastAPI's default validation errors echo input; keep user content out of errors.
    return await agent_error_handler(request, AgentError(ErrorCode.INVALID_REQUEST))


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, error: Exception):
    return await agent_error_handler(request, AgentError(ErrorCode.INTERNAL_ERROR))


@app.post(
    "/agent/run",
    response_model=AgentRunResponse,
    responses={status: {"model": ErrorResponse} for status in (422, 500, 502, 503, 504)},
)
def run_structured_agent(
    request: AgentRunRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    repository: Annotated[RunRepository, Depends(get_repository)],
    service: Annotated[ModelService, Depends(get_model_service)],
) -> AgentRunResponse:
    return AgentRunner(repository, service, settings.openai_model).run(request.message)


class AgentRequest(BaseModel):
    message: str


@app.post("/api/agent/run")
async def run_agent(request: AgentRequest):
    return {"message": f"Received message: {request.message}", "status": "received"}


@app.get("/health")
async def health():
    return {"status": "ok"}
