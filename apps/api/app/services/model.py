from typing import Protocol

from openai import APIError, APITimeoutError, OpenAI
from pydantic import ValidationError

from app.core.config import Settings
from app.errors import AgentError, ErrorCode
from app.schemas import AgentOutput

INSTRUCTIONS = """You are FlowPilot, a business workflow assistant.
Summarize the user's request and suggest concise next steps using only the supplied
information. You cannot look up customers, orders, or policies, call tools, issue
refunds, or execute actions. Never claim an action was performed or invent business
facts. Indicate human review when information, authorization, or judgment is needed.
For an unrelated or unclear request, explain the limitation and suggest clarification.
"""


class ModelService(Protocol):
    def generate(self, message: str) -> AgentOutput: ...


class OpenAIModelService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, message: str) -> AgentOutput:
        key = self.settings.openai_api_key
        if key is None or not key.get_secret_value().strip():
            raise AgentError(ErrorCode.MODEL_NOT_CONFIGURED)

        try:
            with OpenAI(
                api_key=key.get_secret_value(),
                timeout=self.settings.openai_timeout_seconds,
                max_retries=0,
            ) as client:
                response = client.responses.parse(
                    model=self.settings.openai_model,
                    instructions=INSTRUCTIONS,
                    input=[{"role": "user", "content": message}],
                    text_format=AgentOutput,
                    max_output_tokens=self.settings.openai_max_output_tokens,
                    store=False,
                )
            for item in response.output:
                if item.type == "message" and any(part.type == "refusal" for part in item.content):
                    raise AgentError(ErrorCode.MODEL_REFUSED)
            if response.status != "completed" or response.output_parsed is None:
                raise AgentError(ErrorCode.INVALID_MODEL_OUTPUT)
            return AgentOutput.model_validate(response.output_parsed)
        except APITimeoutError:
            raise AgentError(ErrorCode.MODEL_TIMEOUT) from None
        except APIError:
            raise AgentError(ErrorCode.MODEL_UNAVAILABLE) from None
        except ValidationError:
            raise AgentError(ErrorCode.INVALID_MODEL_OUTPUT) from None
