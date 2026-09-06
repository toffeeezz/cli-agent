from enum import StrEnum
from typing import Literal, TypedDict

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallUnion,
    ChatCompletionToolUnionParam,
)
from pydantic import BaseModel, Field


class ReasoningDetail(BaseModel):
    type: str
    text: str
    format: str
    index: int


class ServerPayload(BaseModel):
    model: str
    max_completion_tokens: int | None
    temperature: float
    reasoning_effort: Literal["low", "medium", "high"]

    messages: list[ChatCompletionMessageParam] = []
    tools: list[ChatCompletionToolUnionParam] = []


class FinishReason(StrEnum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    FUNCTION_CALL = "function_call"


class ServerResponse(BaseModel):
    message: ChatCompletionMessageParam | None = None
    content: str = ""
    reasoning_details: list[ReasoningDetail] = Field(default_factory=list)
    reasoning: str = ""
    tool_calls: list[ChatCompletionMessageToolCallUnion] = Field(default_factory=list)
    finish_reason: FinishReason = FinishReason.STOP


class ToolCall(TypedDict):
    id: str
    name: str
    params: str


class OpenRouterAssistantMessageParam(ChatCompletionAssistantMessageParam):
    reasoning: str
    reasoning_details: list[ReasoningDetail]
