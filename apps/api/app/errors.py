from enum import StrEnum
from uuid import UUID


class ErrorCode(StrEnum):
    INVALID_REQUEST = "invalid_request"
    MODEL_NOT_CONFIGURED = "model_not_configured"
    MODEL_UNAVAILABLE = "model_unavailable"
    MODEL_TIMEOUT = "model_timeout"
    MODEL_REFUSED = "model_refused"
    INVALID_MODEL_OUTPUT = "invalid_model_output"
    STORAGE_UNAVAILABLE = "storage_unavailable"
    INTERNAL_ERROR = "internal_error"


ERRORS = {
    ErrorCode.INVALID_REQUEST: (422, "Request does not match the required schema."),
    ErrorCode.MODEL_NOT_CONFIGURED: (503, "The model service is not configured."),
    ErrorCode.MODEL_UNAVAILABLE: (502, "The model service is unavailable."),
    ErrorCode.MODEL_TIMEOUT: (504, "The model service timed out."),
    ErrorCode.MODEL_REFUSED: (422, "The model could not fulfill this request."),
    ErrorCode.INVALID_MODEL_OUTPUT: (502, "The model returned an invalid result."),
    ErrorCode.STORAGE_UNAVAILABLE: (503, "Run storage is unavailable."),
    ErrorCode.INTERNAL_ERROR: (500, "The request could not be completed."),
}


class AgentError(Exception):
    def __init__(self, code: ErrorCode, run_id: UUID | None = None):
        self.code = code
        self.run_id = run_id
        super().__init__(code.value)
