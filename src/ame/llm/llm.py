import os
from pathlib import Path
from typing import Literal, TypedDict, final

from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI, AsyncStream, BaseModel, Omit
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallUnion,
    ChatCompletionToolUnionParam,
)

_ = load_dotenv(find_dotenv())

API_KEY = os.getenv("OPENROUTER_API") or ""


class ReasoningDetail(TypedDict):
    type: str
    text: str
    format: str
    index: int


class ResponseModel(BaseModel):
    content: str
    refusal_msg: str
    tool_calls: list[ChatCompletionMessageToolCallUnion]
    finish_reason: Literal[
        "stop", "tool_calls", "length", "content_filter", "function_call"
    ]
    reasoning_details: list[ReasoningDetail]
    reasoning: str


@final
class LanguageModel:
    is_streaming: bool = False
    is_reasoning: bool = True
    url: str = "https://openrouter.ai/api/v1"

    async def get_response(
        self,
        url: str,
        api_key: str,
        tools: list[ChatCompletionToolUnionParam] | Omit,
        model: str,
        messages: list[ChatCompletionMessageParam],
    ) -> ChatCompletion:

        client = AsyncOpenAI(
            base_url=url,
            api_key=api_key,
        )
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            extra_body={"reasoning": {"enabled": self.is_reasoning}},
            tools=tools,
        )

        return response
