from pydantic import BaseModel

from modules.errors import ProgramError


class AgentEvent(BaseModel):
    pass


class GeneratingResponse(AgentEvent):
    pass


class StreamingResponse(AgentEvent):
    delta_content: str | None
    delta_reasoning: str | None


class StreamingFinished(AgentEvent):
    content: str
    reasoning: str


class GeneratingFinished(AgentEvent):
    content: str
    reasoning: str


class AgentError(ProgramError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
