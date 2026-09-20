from pydantic import ValidationError

from app.db import RunRepository
from app.errors import AgentError, ErrorCode
from app.schemas import AgentOutput, AgentRunResponse
from app.services.model import ModelService


class AgentRunner:
    def __init__(self, repository: RunRepository, service: ModelService, model: str):
        self.repository = repository
        self.service = service
        self.model = model

    def run(self, message: str) -> AgentRunResponse:
        # Commit before contacting OpenAI: even provider failures have a durable ID.
        run_id, created_at = self.repository.create(message, self.model)
        try:
            output = AgentOutput.model_validate(self.service.generate(message))
        except AgentError as error:
            self.repository.fail(run_id, error.code)
            raise AgentError(error.code, run_id) from None
        except ValidationError:
            self.repository.fail(run_id, ErrorCode.INVALID_MODEL_OUTPUT)
            raise AgentError(ErrorCode.INVALID_MODEL_OUTPUT, run_id) from None
        except Exception:  # noqa: BLE001 -- persist unexpected failures without exposing their details
            self.repository.fail(run_id, ErrorCode.INTERNAL_ERROR)
            raise AgentError(ErrorCode.INTERNAL_ERROR, run_id) from None

        # Never report success unless the final result has committed.
        self.repository.succeed(run_id, output)
        return AgentRunResponse(run_id=run_id, output=output, created_at=created_at)
