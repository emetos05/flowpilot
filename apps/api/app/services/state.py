import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4

from app.errors import ErrorCode

# Inherit Uvicorn's configured console handler without logging user/provider data.
logger = logging.getLogger("uvicorn.error.agent")


class Phase(StrEnum):
    READY = "ready"
    SELECTING = "selecting"
    EXECUTING = "executing"
    OBSERVING = "observing"
    DECIDING = "deciding"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class Transition:
    execution_id: UUID
    phase: Phase
    step: int
    error_code: ErrorCode | None = None


@dataclass
class RunState:
    observer: Callable[[Transition], None] | None = None
    execution_id: UUID = field(default_factory=uuid4)
    phase: Phase = Phase.READY
    step: int = 0

    def transition(self, phase: Phase, error_code: ErrorCode | None = None) -> None:
        allowed = {
            Phase.READY: {Phase.SELECTING, Phase.FAILED},
            Phase.SELECTING: {Phase.EXECUTING, Phase.SUCCEEDED, Phase.FAILED},
            Phase.EXECUTING: {Phase.OBSERVING, Phase.FAILED},
            Phase.OBSERVING: {Phase.DECIDING, Phase.FAILED},
            Phase.DECIDING: {Phase.SELECTING, Phase.FAILED},
            Phase.SUCCEEDED: set(),
            Phase.FAILED: set(),
        }
        if phase not in allowed[self.phase]:
            raise RuntimeError("Invalid agent state transition")
        if phase == Phase.SELECTING:
            self.step += 1
        self.phase = phase
        event = Transition(self.execution_id, phase, self.step, error_code)
        logger.info(
            "agent_transition execution_id=%s phase=%s step=%s error_code=%s",
            event.execution_id,
            event.phase,
            event.step,
            event.error_code,
        )
        if self.observer:
            self.observer(event)
